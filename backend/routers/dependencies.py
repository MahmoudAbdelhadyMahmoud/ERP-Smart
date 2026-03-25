from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import models
from database import get_db

def log_audit(db: Session, action: str, table_name: str, record_id: int, old_values: dict = None, new_values: dict = None, notes: str = None):
    audit_entry = models.AuditLog(
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=json.dumps(old_values, default=str) if old_values else None,
        new_values=json.dumps(new_values, default=str) if new_values else None,
        notes=notes
    )
    db.add(audit_entry)

def is_system_locked(db: Session):
    now = datetime.now()
    # Check for previous month's audit status
    prev_month_last_day = now.replace(day=1) - timedelta(days=1)
    
    audit = db.query(models.InventoryAudit).filter(
        models.InventoryAudit.date == prev_month_last_day.date()
    ).first()
    
    # 1. If audit is completed or skipped, no lock.
    if audit and (audit.is_completed == 1 or audit.is_skipped == 1):
        return False
        
    # 2. If today is <= 5th of the month:
    if now.day <= 5:
        # Lock ONLY if the audit has been manually started (is_active=1)
        if audit and audit.is_active == 1:
            return True
        return False
        
    # 3. If today is > 5th of the month:
    # Lock if previous month's audit is not completed/skipped (automatic activation)
    if not audit:
        products_count = db.query(models.Product).count()
        return products_count > 0

    # If audit exists but is NOT completed and NOT skipped, it should be locked
    return True

def check_lock(db: Session = Depends(get_db)):
    if is_system_locked(db):
        raise HTTPException(status_code=403, detail="النظام متوقف مؤقتاً لحين تسجيل جرد المخزن للشهر الماضي")

