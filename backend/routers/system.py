from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import models, schemas, utils
from database import get_db
from datetime import date, datetime, timedelta
import json
from routers.dependencies import check_lock, is_system_locked, log_audit

router = APIRouter(prefix='', tags=['System'])

@router.post("/inventory-audits/skip")
def skip_audit(db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        prev_month_last_day = now.replace(day=1) - timedelta(days=1)
        
        audit = db.query(models.InventoryAudit).filter(
            models.InventoryAudit.date == prev_month_last_day.date()
        ).first()
        
        if not audit:
            # Create it and mark as skipped
            audit = models.InventoryAudit(date=prev_month_last_day.date(), is_active=0, is_completed=1, is_skipped=1)
            db.add(audit)
        else:
            audit.is_skipped = 1
            audit.is_active = 0 # Deactivate if it was active
            audit.is_completed = 1 # Mark as completed so logic unlocks it
            
        db.commit()
        return {"message": "Audit skipped"}
    except Exception as e:
        print(f"Error skipping audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory-audits/start")
def start_audit(db: Session = Depends(get_db)):
    # Manual start of the current needed audit
    now = datetime.now()
    prev_month_last_day = now.replace(day=1) - timedelta(days=1)
    
    audit = db.query(models.InventoryAudit).filter(
        models.InventoryAudit.date == prev_month_last_day.date()
    ).first()
    
    if not audit:
        # Create it and make it active
        audit = models.InventoryAudit(date=prev_month_last_day.date(), is_active=1, is_completed=0)
        db.add(audit)
        db.flush()
        products = db.query(models.Product).all()
        for p in products:
            item = models.InventoryAuditItem(
                audit_id=audit.id, product_id=p.id, expected_quantity=p.current_stock, actual_quantity=p.current_stock
            )
            db.add(item)
    else:
        audit.is_active = 1
        
    db.commit()
    return {"message": "Audit started manually"}

@router.get("/system-status")
def get_system_status(db: Session = Depends(get_db)):
    locked = is_system_locked(db)
    return {"locked": locked}

@router.get("/audits", response_model=List[schemas.InventoryAudit])
def list_audits(db: Session = Depends(get_db)):
    return db.query(models.InventoryAudit).all()

@router.get("/inventory-audits/current")
def get_current_audit(db: Session = Depends(get_db)):
    # Find a pending audit for the previous month's last day
    now = datetime.now()
    prev_month_last_day = now.replace(day=1) - timedelta(days=1)
    
    audit = db.query(models.InventoryAudit).filter(
        models.InventoryAudit.date == prev_month_last_day.date()
    ).first()
    
    if not audit:
        # If today is > 5, we create it automatically (Auto-lock)
        if now.day > 5:
            audit = models.InventoryAudit(date=prev_month_last_day.date(), is_active=1, is_completed=0)
            db.add(audit)
            db.flush()
            products = db.query(models.Product).all()
            for p in products:
                item = models.InventoryAuditItem(
                    audit_id=audit.id, product_id=p.id, expected_quantity=p.current_stock, actual_quantity=p.current_stock
                )
                db.add(item)
            db.commit()
            db.refresh(audit)
        else:
            return {"date": prev_month_last_day.date(), "is_active": 0, "is_completed": 0, "items": []}
    
    return audit

@router.post("/inventory-audits/submit")
def submit_audit(req: schemas.AuditSubmitRequest, db: Session = Depends(get_db)):
    now = datetime.now()
    prev_month_last_day = now.replace(day=1) - timedelta(days=1)
    
    audit = db.query(models.InventoryAudit).filter(
        models.InventoryAudit.date == prev_month_last_day.date()
    ).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    if audit.is_completed:
        raise HTTPException(status_code=400, detail="Audit already completed")
    
    # Update actual quantities
    for item_data in req.items:
        db_item = db.query(models.InventoryAuditItem).filter(
            models.InventoryAuditItem.audit_id == audit.id,
            models.InventoryAuditItem.product_id == item_data.product_id
        ).first()
        if db_item:
            db_item.actual_quantity = item_data.actual_quantity
            # Update product stock to match actual
            db_product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
            if db_product:
                db_product.current_stock = item_data.actual_quantity
                
                # Create adjustment movement to record this change in history
                movement = models.WarehouseMovement(
                    product_id=db_product.id,
                    type="Adjustment",
                    quantity=item_data.actual_quantity,
                    date=now.date(),
                    notes=f"جرد شهري بتاريخ {audit.date}"
                )
                db.add(movement)
    
    audit.is_completed = 1
    db.commit()
    return {"message": "Audit completed and stock updated"}

