from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import models, schemas, utils
from database import get_db
from datetime import date, datetime, timedelta
import json
from routers.dependencies import check_lock, is_system_locked, log_audit

router = APIRouter(prefix='', tags=['Analytics'])

@router.post("/recommend")
def recommend_type(req: schemas.RecommendationRequest):
    prediction = utils.predict_type(req.notes)
    return {"recommended_type": prediction or "Other"}

@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    content = utils.generate_excel(expenses)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=expenses.xlsx"}
    )

@router.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    content = utils.generate_pdf(expenses)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=expenses.pdf"}
    )

@router.get("/export/invoice/{expense_id}/excel")
def export_invoice_excel(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    content = utils.generate_excel([expense])
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=invoice_{expense_id}.xlsx"}
    )

@router.get("/export/invoice/{expense_id}/pdf")
def export_invoice_pdf(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    content = utils.generate_pdf([expense])
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{expense_id}.pdf"}
    )

@router.get("/export/warehouse/excel")
def export_warehouse_excel(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    content = utils.generate_warehouse_excel(products)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory.xlsx"}
    )

@router.get("/export/warehouse/pdf")
def export_warehouse_pdf(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    content = utils.generate_warehouse_pdf(products)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=inventory.pdf"}
    )

@router.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    # Query all expense items with their related types
    expenses = db.query(models.Expense).all()
    summary = {}
    for exp in expenses:
        for item in exp.items:
            type_name = item.expense_type
            if type_name not in summary:
                summary[type_name] = 0
            # For simplicity, we use the item amount.
            # In a real scenario, you might want to distribute tax/discount proportionally.
            summary[type_name] += item.amount
    
    # Generate simple recommendations
    recommendations = []
    if summary:
        max_type = max(summary, key=summary.get)
        total_all = sum(summary.values())
        avg_expense = total_all / len(summary)
        
        recommendations.append(f"أعلى بند مصروفات هو '{max_type}'، يمثل {int(summary[max_type]/total_all*100)}% من الإجمالي.")
        if summary[max_type] > avg_expense * 2:
            recommendations.append(f"نوصي بمراجعة تكاليف '{max_type}' نظراً لارتفاعها الملحوظ عن باقي البنود.")
        if total_all > 10000:
            recommendations.append("إجمالي المصروفات تجاوز 10,000 ج.م، يفضل مراجعة سياسة الخصومات مع الموردين.")
    else:
        recommendations.append("قم بإضافة بيانات لتلقي التوصيات.")
            
    return {
        "summary": summary,
        "recommendations": recommendations
    }

@router.get("/audit_logs", response_model=List[schemas.AuditLog])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).all()

@router.get("/products/{product_id}/price-history")
def get_product_price_history(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    history = []
    
    # Get from movements
    movements = db.query(models.WarehouseMovement).filter(
        models.WarehouseMovement.product_id == product_id,
        models.WarehouseMovement.type == "Addition",
        models.WarehouseMovement.unit_price > 0
    ).all()
    
    for m in movements:
        history.append({
            "date": m.date,
            "price": m.unit_price,
            "source": "مخزن",
            "quantity": m.quantity
        })
    
    # Get from expenses
    expense_items = db.query(models.ExpenseItem).filter(
        models.ExpenseItem.product_id == product_id,
        models.ExpenseItem.unit_price > 0
    ).all()
    
    for ei in expense_items:
        history.append({
            "date": ei.expense.date,
            "price": ei.unit_price,
            "source": "فاتورة",
            "quantity": ei.quantity
        })
    
    # Sort by date
    history.sort(key=lambda x: x["date"])
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "history": history
    }

@router.get("/analytics/stock-summary")
def get_stock_summary(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return {
        "labels": [p.name for p in products],
        "data": [p.current_stock for p in products]
    }

@router.get("/reports/warehouse/top-items")
def get_top_items(db: Session = Depends(get_db)):
    # "اكثر الاصناف تدوال" - let's count movements
    from sqlalchemy import func
    top = db.query(
        models.Product.name,
        func.count(models.WarehouseMovement.id).label('movement_count')
    ).join(models.WarehouseMovement).group_by(models.Product.id).order_by(func.count(models.WarehouseMovement.id).desc()).limit(10).all()
    
    return [{"name": name, "count": count} for name, count in top]

