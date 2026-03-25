from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import models, schemas, utils
from database import get_db
from datetime import date, datetime, timedelta
import json
from routers.dependencies import check_lock, is_system_locked, log_audit

router = APIRouter(prefix='', tags=['Warehouse'])




# --- Locations ---
@router.post("/locations", response_model=schemas.Location)
def create_location(loc: schemas.LocationCreate, db: Session = Depends(get_db)):
    try:
        db_loc = models.Location(**loc.dict())
        db.add(db_loc)
        db.commit()
        db.refresh(db_loc)
        return db_loc
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="هذا المخزن مسجل مسبقاً")

@router.get("/locations", response_model=List[schemas.Location])
def list_locations(db: Session = Depends(get_db)):
    return db.query(models.Location).all()

@router.delete("/locations/{loc_id}")
def delete_location(loc_id: int, db: Session = Depends(get_db)):
    db_loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if not db_loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location has movements
    has_movements = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.location_id == loc_id).first()
    if has_movements:
        raise HTTPException(status_code=400, detail="لا يمكن حذف مخزن له حركات مسجلة")
        
    db.delete(db_loc)
    db.commit()
    return {"message": "Deleted"}

@router.get("/products", response_model=List[schemas.Product])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.get("/products/template")
def get_products_template():
    content = utils.get_product_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_template.xlsx"}
    )

@router.post("/products/import")
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    count = utils.import_products_from_excel(content, db)
    return {"message": f"Successfully imported {count} products"}

@router.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    # Auto-generate code if not provided
    if not product.code:
        count = db.query(models.Product).count()
        product.code = f"PRD-{(count + 1):04d}"
        
    # Translate name to Chinese if not provided
    if not product.name_chinese:
        product.name_chinese = utils.translate_to_chinese(product.name)
        
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.dict(exclude_unset=True)
    
    # If name changed and name_chinese not explicitly provided, re-translate
    if 'name' in update_data and not update_data.get('name_chinese'):
        update_data['name_chinese'] = utils.translate_to_chinese(update_data['name'])

    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product has movements or audit items
    has_movements = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.product_id == product_id).first()
    if has_movements:
        raise HTTPException(status_code=400, detail="لا يمكن حذف صنف له حركات مخزنية مسجلة")
        
    db.delete(db_product)
        
    db.commit()
    return {"message": "Deleted successfully"}

@router.post("/opening-balances")
def set_opening_balances(req: schemas.OpeningBalanceRequest, db: Session = Depends(get_db)):
    """
    Sets the opening balance for a list of products.
    This will overwrite current stock and create a new "رصيد افتتاحي" movement.
    """
    for item in req.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            continue

        # 1. Update product stock and cost
        product.current_stock = item.quantity
        product.average_cost = item.unit_price
        product.purchase_price = item.unit_price

        # 2. Create warehouse movement
        movement = models.WarehouseMovement(
            product_id=product.id,
            location_id=item.location_id,
            type="رصيد افتتاحي",
            quantity=item.quantity,
            unit_price=item.unit_price,
            date=date.today(),
            notes="تحديد الرصيد الافتتاحي يدويًا"
        )
        db.add(movement)
    
    db.commit()
    return {"message": "Opening balances set successfully"}

@router.post("/approve-opening")
def approve_current_stock_as_opening(db: Session = Depends(get_db)):
    """
    Creates an "رصيد افتتاحي" movement for all products based on their current stock level.
    """
    products = db.query(models.Product).all()
    for product in products:
        if product.current_stock > 0:
            movement = models.WarehouseMovement(
                product_id=product.id,
                type="رصيد افتتاحي",
                quantity=product.current_stock,
                unit_price=product.average_cost, # Use average cost as the price
                date=date.today(),
                notes="اعتماد الرصيد الحالي كرصيد افتتاحي"
            )
            db.add(movement)
    
    db.commit()
    return {"message": "Current stock approved as opening balance"}

@router.get("/movements", response_model=List[schemas.WarehouseMovement])
def list_movements(doc_number: str = None, db: Session = Depends(get_db)):
    q = db.query(models.WarehouseMovement)
    if doc_number:
        q = q.filter(models.WarehouseMovement.doc_number.like(f"%{doc_number}%"))
    return q.order_by(models.WarehouseMovement.id.desc()).all()

@router.post("/movements/bulk")
def create_bulk_movements(req: schemas.BulkWarehouseMovementRequest, db: Session = Depends(get_db)):
    # Generate one doc number for the entire batch
    doc_num = utils.generate_doc_number(db, req.date)

    for item in req.items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            continue
        
        # Update current stock
        if req.type == "Addition":
            old_stock = db_product.current_stock
            db_product.current_stock += item.quantity
            if item.unit_price:
                db_product.purchase_price = item.unit_price
                if db_product.current_stock > 0:
                    db_product.average_cost = ((old_stock * db_product.average_cost) + (item.quantity * item.unit_price)) / db_product.current_stock
        elif req.type == "Disposal":
            db_product.current_stock -= item.quantity
        
        db_mov = models.WarehouseMovement(
            doc_number=doc_num,
            product_id=item.product_id,
            location_id=req.location_id,
            type=req.type,
            quantity=item.quantity,
            unit_price=item.unit_price,
            date=req.date,
            notes=item.notes or req.notes
        )
        db.add(db_mov)
    
    db.commit()
    recalculate_stock(db)
    return {"message": "Bulk movements created successfully", "doc_number": doc_num}

@router.post("/movements", response_model=schemas.WarehouseMovement)
def create_movement(mov: schemas.WarehouseMovementCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == mov.product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Generate doc number if not provided
    if not mov.doc_number:
        mov.doc_number = utils.generate_doc_number(db, mov.date)

    # Update current stock
    if mov.type == "Addition":
        old_stock = db_product.current_stock
        db_product.current_stock += mov.quantity
        if mov.unit_price:
            db_product.purchase_price = mov.unit_price
            if db_product.current_stock > 0:
                db_product.average_cost = ((old_stock * db_product.average_cost) + (mov.quantity * mov.unit_price)) / db_product.current_stock
    elif mov.type in ["Disposal", "Adjustment"]:
        if mov.type == "Adjustment":
            db_product.current_stock = mov.quantity
        else:
            db_product.current_stock -= mov.quantity
    
    db_mov = models.WarehouseMovement(**mov.dict())
    db.add(db_mov)
    db.flush()
    
    # Audit log
    log_audit(db, "Create", "warehouse_movements", db_mov.id, new_values=mov.dict())
    
    db.commit()
    db.refresh(db_mov)
    
    # Smarter: update stock cache if needed
    recalculate_stock(db) # Force refresh for simple apps
    
    return db_mov

@router.post("/transfers/bulk")
def create_bulk_transfers(req: schemas.BulkTransferRequest, db: Session = Depends(get_db)):
    """
    Transfers multiple products from one location to another in a single operation.
    Creates both a Transfer Out and a Transfer In movement for each item.
    """
    # One doc number for the entire transfer batch
    doc_num = utils.generate_doc_number(db, req.date)

    for item in req.items:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not db_product:
            continue

        note_out = item.notes or req.notes or f"تحويل جماعي إلى مخزن {req.to_location_id}"
        note_in  = item.notes or req.notes or f"تحويل جماعي من مخزن {req.from_location_id}"

        # Transfer Out
        mov_out = models.WarehouseMovement(
            doc_number=doc_num,
            product_id=item.product_id,
            location_id=req.from_location_id,
            type="Transfer Out",
            quantity=item.quantity,
            date=req.date,
            notes=note_out
        )
        db.add(mov_out)
        db.flush()

        # Transfer In
        mov_in = models.WarehouseMovement(
            doc_number=doc_num,
            product_id=item.product_id,
            location_id=req.to_location_id,
            type="Transfer In",
            quantity=item.quantity,
            date=req.date,
            notes=note_in,
            transfer_link_id=mov_out.id
        )
        db.add(mov_in)
        db.flush()

        mov_out.transfer_link_id = mov_in.id

    db.commit()
    recalculate_stock(db)
    return {"message": "Bulk transfer completed successfully"}

@router.post("/transfers")
def create_transfer(req: schemas.TransferRequest, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == req.product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 1. Outgoing movement
    mov_out = models.WarehouseMovement(
        product_id=req.product_id,
        location_id=req.from_location_id,
        type="Transfer Out",
        quantity=req.quantity,
        date=req.date,
        notes=req.notes or f"تحويل إلى {req.to_location_id}"
    )
    db.add(mov_out)
    db.flush()

    # 2. Incoming movement
    mov_in = models.WarehouseMovement(
        product_id=req.product_id,
        location_id=req.to_location_id,
        type="Transfer In",
        quantity=req.quantity,
        date=req.date,
        notes=req.notes or f"تحويل من {req.from_location_id}",
        transfer_link_id=mov_out.id
    )
    db.add(mov_in)
    
    # Update mov_out with link back to mov_in
    db.flush()
    mov_out.transfer_link_id = mov_in.id

    db.commit()
    recalculate_stock(db)
    return {"message": "Transfer completed successfully"}

@router.put("/movements/{movement_id}", response_model=schemas.WarehouseMovement)
def update_movement(movement_id: int, mov_update: schemas.WarehouseMovementUpdate, db: Session = Depends(get_db)):
    db_mov = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.id == movement_id).first()
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    db_product = db_mov.product
    old_values = {
        "type": db_mov.type,
        "quantity": db_mov.quantity,
        "unit_price": db_mov.unit_price,
        "date": db_mov.date,
        "notes": db_mov.notes
    }

    # Reverse old effect on stock
    if db_mov.type == "Addition":
        db_product.current_stock -= db_mov.quantity
    elif db_mov.type == "Disposal":
        db_product.current_stock += db_mov.quantity
    elif db_mov.type == "Adjustment":
        # Adjustments are tricky to reverse without previous state. 
        # For simplicity, we skip reversal and just apply new state if it's still an adjustment.
        pass

    # Apply updates
    update_data = mov_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mov, key, value)
    
    # Apply new effect on stock
    if db_mov.type == "Addition":
        db_product.current_stock += db_mov.quantity
        if db_mov.unit_price:
            db_product.purchase_price = db_mov.unit_price
    elif db_mov.type == "Disposal":
        db_product.current_stock -= db_mov.quantity
    elif db_mov.type == "Adjustment":
        db_product.current_stock = db_mov.quantity

    # Audit Log
    log_audit(db, "Update", "warehouse_movements", db_mov.id, old_values=old_values, new_values=update_data)
    
    db.commit()
    db.refresh(db_mov)
    return db_mov

@router.delete("/movements/{movement_id}")
def delete_movement(movement_id: int, db: Session = Depends(get_db)):
    db_mov = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.id == movement_id).first()
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    db_product = db_mov.product
    # Reverse effect on stock
    if db_mov.type == "Addition":
        db_product.current_stock -= db_mov.quantity
    elif db_mov.type == "Disposal":
        db_product.current_stock += db_mov.quantity
    
    # Audit Log
    log_audit(db, "Delete", "warehouse_movements", db_mov.id, old_values={
        "type": db_mov.type,
        "quantity": db_mov.quantity,
        "product_id": db_mov.product_id
    })
    
    db.delete(db_mov)
    db.commit()
    return {"message": "Deleted successfully"}

@router.post("/products/recalculate-stock")
def recalculate_stock(db: Session = Depends(get_db)):
    # This endpoint syncs current_stock with the recorded WarehouseMovement history
    # For a smarter system, we could also compute stock PER location here.
    products = db.query(models.Product).all()
    for p in products:
        p.current_stock = 0.0
    
    movements = db.query(models.WarehouseMovement).order_by(models.WarehouseMovement.date.asc(), models.WarehouseMovement.id.asc()).all()
    for m in movements:
        p = db.query(models.Product).filter(models.Product.id == m.product_id).first()
        if not p: continue
        
        if m.type in ["Addition", "Transfer In", "Adjustment", "رصيد افتتاحي"]:
            if m.type == "Adjustment":
                p.current_stock = m.quantity
            else:
                p.current_stock += m.quantity
        elif m.type in ["Disposal", "Transfer Out"]:
            p.current_stock -= m.quantity
    
    db.commit()
    return {"message": "Stock recalculated successfully"}

@router.get("/reports/stock-per-location")
def get_stock_per_location(db: Session = Depends(get_db)):
    # Computes current stock for each product in each location
    locations = db.query(models.Location).all()
    products = db.query(models.Product).all()
    
    results = []
    for loc in locations:
        loc_data = {"id": loc.id, "name": loc.name, "stocks": []}
        for prod in products:
            # Sum movements for this product at this location
            # Addition, Transfer In, Adjustment (if recent) - this logic is complex for SQLite
            # Simpler: filter movements in memory
            stock = 0
            movs = db.query(models.WarehouseMovement).filter(
                models.WarehouseMovement.product_id == prod.id,
                models.WarehouseMovement.location_id == loc.id
            ).all()
            
            for m in movs:
                if m.type in ["Addition", "Transfer In", "رصيد افتتاحي"]:
                    stock += m.quantity
                elif m.type in ["Disposal", "Transfer Out"]:
                    stock -= m.quantity
                elif m.type == "Adjustment":
                    stock = m.quantity
                    
            if stock != 0:
                loc_data["stocks"].append({
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "product_name_chinese": prod.name_chinese,
                    "quantity": stock
                })
        results.append(loc_data)
    return results

@router.get("/dashboard/stats")
def get_warehouse_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # 1. Low stock items
    low_stock = db.query(models.Product).filter(models.Product.current_stock <= models.Product.reorder_level).all()
    
    # 2. Top 10 moving items (by movement frequency)
    top_moving_ids = db.query(
        models.WarehouseMovement.product_id,
        func.count(models.WarehouseMovement.id).label('freq')
    ).group_by(models.WarehouseMovement.product_id).order_by(func.count(models.WarehouseMovement.id).desc()).limit(10).all()
    
    top_moving = []
    for pid, freq in top_moving_ids:
        p = db.query(models.Product).filter(models.Product.id == pid).first()
        if p:
            top_moving.append({
                "id": p.id,
                "name": p.name,
                "name_chinese": p.name_chinese,
                "frequency": freq,
                "current_stock": p.current_stock
            })
            
    # 3. Most purchased item (by count of Addition operations)
    most_purchased_data = db.query(
        models.WarehouseMovement.product_id,
        func.count(models.WarehouseMovement.id).label('purchase_count')
    ).filter(models.WarehouseMovement.type == 'Addition').group_by(models.WarehouseMovement.product_id).order_by(func.count(models.WarehouseMovement.id).desc()).first()
    
    most_purchased = None
    if most_purchased_data:
        p = db.query(models.Product).filter(models.Product.id == most_purchased_data.product_id).first()
        if p:
            most_purchased = {
                "id": p.id,
                "name": p.name,
                "name_chinese": p.name_chinese,
                "count": most_purchased_data.purchase_count,
                "current_stock": p.current_stock
            }
            
    return {
        "low_stock_count": len(low_stock),
        "low_stock_list": [{"id": p.id, "name": p.name, "current": p.current_stock, "min": p.reorder_level} for p in low_stock],
        "top_moving": top_moving,
        "most_purchased": most_purchased
    }
