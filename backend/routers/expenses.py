from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import models, schemas, utils
from database import get_db
from datetime import date, datetime, timedelta
import json
from routers.dependencies import check_lock, is_system_locked, log_audit

router = APIRouter(prefix='', tags=['Expenses'])

@router.post("/cost_centers", response_model=schemas.CostCenter)
def create_cost_center(cc: schemas.CostCenterCreate, db: Session = Depends(get_db)):
    try:
        cc.name = cc.name.strip()
        db_cc = models.CostCenter(**cc.dict())
        db.add(db_cc)
        db.commit()
        db.refresh(db_cc)
        return db_cc
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="هذا المركز مسجل مسبقاً")

@router.get("/cost_centers", response_model=List[schemas.CostCenter])
def list_cost_centers(db: Session = Depends(get_db)):
    return db.query(models.CostCenter).all()

@router.put("/cost_centers/{cc_id}", response_model=schemas.CostCenter)
def update_cost_center(cc_id: int, cc: schemas.CostCenterCreate, db: Session = Depends(get_db)):
    try:
        db_cc = db.query(models.CostCenter).filter(models.CostCenter.id == cc_id).first()
        if not db_cc:
            raise HTTPException(status_code=404, detail="Cost Center not found")
        db_cc.name = cc.name.strip()
        db_cc.description = cc.description
        db.commit()
        db.refresh(db_cc)
        return db_cc
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="الاسم الجديد مسجل لمركز آخر")

@router.delete("/cost_centers/{cc_id}")
def delete_cost_center(cc_id: int, db: Session = Depends(get_db)):
    db_cc = db.query(models.CostCenter).filter(models.CostCenter.id == cc_id).first()
    if not db_cc:
        raise HTTPException(status_code=404, detail="Cost Center not found")
    # Check for linked expenses
    has_expenses = db.query(models.Expense).filter(models.Expense.cost_center_id == cc_id).first()
    if has_expenses:
        raise HTTPException(status_code=400, detail="Cannot delete cost center with linked expenses")
    db.delete(db_cc)
    db.commit()
    return {"message": "Deleted"}

@router.post("/expense_types", response_model=schemas.ExpenseType)
def create_expense_type(et: schemas.ExpenseTypeCreate, db: Session = Depends(get_db)):
    try:
        et.name = et.name.strip()
        # Translate to Chinese automatically if not provided
        if not et.name_chinese:
            et.name_chinese = utils.translate_to_chinese(et.name)
        
        db_et = models.ExpenseType(**et.dict())
        db.add(db_et)
        db.commit()
        db.refresh(db_et)
        return db_et
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="هذا النوع مسجل مسبقاً")

@router.get("/expense_types", response_model=List[schemas.ExpenseType])
def list_expense_types(db: Session = Depends(get_db)):
    return db.query(models.ExpenseType).all()

@router.put("/expense_types/{et_id}", response_model=schemas.ExpenseType)
def update_expense_type(et_id: int, et: schemas.ExpenseTypeCreate, db: Session = Depends(get_db)):
    try:
        db_et = db.query(models.ExpenseType).filter(models.ExpenseType.id == et_id).first()
        if not db_et:
            raise HTTPException(status_code=404, detail="Type not found")
        db_et.name = et.name.strip()
        db_et.name_chinese = et.name_chinese or utils.translate_to_chinese(et.name)
        db.commit()
        db.refresh(db_et)
        return db_et
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="الاسم الجديد مسجل لنوع آخر")

@router.delete("/expense_types/{et_id}")
def delete_expense_type(et_id: int, db: Session = Depends(get_db)):
    db_et = db.query(models.ExpenseType).filter(models.ExpenseType.id == et_id).first()
    if not db_et:
        raise HTTPException(status_code=404, detail="Type not found")
    # Check for linked items
    has_items = db.query(models.ExpenseItem).filter(models.ExpenseItem.expense_type_id == et_id).first()
    if has_items:
        raise HTTPException(status_code=400, detail="Cannot delete type with linked expense items")
    db.delete(db_et)
    db.commit()
    return {"message": "Deleted"}

@router.get("/expenses/template")
def get_expenses_template():
    content = utils.get_expense_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=expenses_template.xlsx"}
    )

@router.post("/expenses/import")
async def import_expenses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    count = utils.import_expenses_from_excel(content, db)
    return {"message": f"Successfully imported {count} expenses"}

@router.get("/expenses", response_model=List[schemas.Expense])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(models.Expense).all()

@router.post("/expenses", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # Calculate Total
    # amount_egp is the subtotal provided by the frontend (sum of items)
    total = expense.amount_egp + expense.taxes - (expense.amount_egp * expense.discount_pct / 100)
    
    # Extract items from schemas.ExpenseCreate
    items_data = expense.items
    expense_dict = expense.dict()
    del expense_dict['items']
    
    # Generate doc number for warehouse movements
    doc_num = utils.generate_doc_number(db, expense.date)
    
    # Use provided invoice number or generate one
    inv_num = expense.invoice_number if expense.invoice_number else utils.generate_invoice_number(db, expense.date)
    expense_dict['invoice_number'] = inv_num
    
    db_expense = models.Expense(**expense_dict, total=total)
    db.add(db_expense)
    db.flush() # To get the db_expense.id
    
    # Generate doc number for warehouse movements
    doc_num = utils.generate_doc_number(db, expense.date)
    
    for item in items_data:
        item_dict = item.dict()
        if item_dict.get('description') and not item_dict.get('description_chinese'):
            item_dict['description_chinese'] = utils.translate_to_chinese(item_dict['description'])
            
        db_item = models.ExpenseItem(**item_dict, expense_id=db_expense.id)
        db.add(db_item)
        
        # If product_id is provided, update product stock and average cost
        if item.product_id:
            db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if db_product:
                # Treat expense as Addition
                old_stock = db_product.current_stock
                db_product.current_stock += item.quantity
                db_product.purchase_price = item.unit_price
                
                # Recalculate average cost using total item amount (inclusive of tax/discount)
                if db_product.current_stock > 0:
                    db_product.average_cost = ((old_stock * db_product.average_cost) + item.amount) / db_product.current_stock
                
                # Create warehouse movement record
                movement = models.WarehouseMovement(
                    doc_number=doc_num,
                    product_id=item.product_id,
                    type="Addition",
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    date=expense.date,
                    notes=f"فاتورة مصروف رقم {db_expense.id}",
                    expense_id=db_expense.id
                )
                db.add(movement)
    
    db.commit()
    db.refresh(db_expense)
    
    # Update AI model
    # (Optional: might need adjustment for itemized expenses)
    # all_expenses = db.query(models.Expense).all()
    # utils.train_recommender(all_expenses)
    
    return db_expense

@router.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Update header fields
    total = expense.amount_egp + expense.taxes - (expense.amount_egp * expense.discount_pct / 100)
    
    expense_dict = expense.dict()
    items_data = expense_dict.pop('items')
    
    for key, value in expense_dict.items():
        setattr(db_expense, key, value)
    db_expense.total = total
    
    # Update items (Delete and Re-create for simplicity)
    # 1. Reverse stock effect of old movements linked to this expense
    old_movements = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.expense_id == expense_id).all()
    for m in old_movements:
        db_product = db.query(models.Product).filter(models.Product.id == m.product_id).first()
        if db_product:
            if m.type == "Addition":
                db_product.current_stock -= m.quantity
            elif m.type == "Disposal":
                db_product.current_stock += m.quantity
    
    # 2. Delete old movements and items
    db.query(models.WarehouseMovement).filter(models.WarehouseMovement.expense_id == expense_id).delete()
    db.query(models.ExpenseItem).filter(models.ExpenseItem.expense_id == expense_id).delete()
    
    # Generate doc number for warehouse movements
    doc_num = utils.generate_doc_number(db, db_expense.date)
    
    # 3. Create new items and movements
    for item in items_data:
        if item.get('description') and not item.get('description_chinese'):
            item['description_chinese'] = utils.translate_to_chinese(item['description'])
            
        # If item is a dict (from expense_dict.pop('items')), convert to model
        # Actually it's already a list of dicts because of expense_dict = expense.dict()
        db_item = models.ExpenseItem(**item, expense_id=expense_id)
        db.add(db_item)
        
        if db_item.product_id:
            db_product = db.query(models.Product).filter(models.Product.id == db_item.product_id).first()
            if db_product:
                old_stock = db_product.current_stock
                db_product.current_stock += db_item.quantity
                db_product.purchase_price = db_item.unit_price
                if db_product.current_stock > 0:
                    db_product.average_cost = ((old_stock * db_product.average_cost) + db_item.amount) / db_product.current_stock
                
                # Create movement
                movement = models.WarehouseMovement(
                    doc_number=doc_num,
                    product_id=db_item.product_id,
                    type="Addition",
                    quantity=db_item.quantity,
                    unit_price=db_item.unit_price,
                    date=db_expense.date,
                    notes=f"تعديل فاتورة مصروف رقم {db_expense.id}",
                    expense_id=db_expense.id
                )
                db.add(movement)
    
    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # 1. Reverse stock effect of old movements linked to this expense
    old_movements = db.query(models.WarehouseMovement).filter(models.WarehouseMovement.expense_id == expense_id).all()
    for m in old_movements:
        db_product = db.query(models.Product).filter(models.Product.id == m.product_id).first()
        if db_product:
            if m.type == "Addition":
                db_product.current_stock -= m.quantity
            elif m.type == "Disposal":
                db_product.current_stock += m.quantity
                
    # 2. Delete linked movements
    db.query(models.WarehouseMovement).filter(models.WarehouseMovement.expense_id == expense_id).delete()
    
    # 3. Delete expense
    db.delete(db_expense)
    db.commit()
    return {"message": "Deleted successfully"}

@router.post("/translate")
def translate_text(req: schemas.RecommendationRequest): # Reusing the same schema structure (notes -> text)
    if not req.notes:
        return {"translated": "", "zh": "", "en": ""}
    try:
        zh_translated = utils.translate_to_chinese(req.notes)
        en_translated = utils.translate_to_english(req.notes)
        return {"translated": zh_translated, "zh": zh_translated, "en": en_translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
