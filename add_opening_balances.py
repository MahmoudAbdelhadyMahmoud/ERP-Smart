
import os
import datetime
from sqlalchemy.orm import sessionmaker
from backend.database import engine
from backend.models import Product, WarehouseMovement

# --- البيانات المطلوبة ---
# الرجاء تعديل القائمة التالية لتشمل المنتجات والأرصدة الفعلية
# يتكون كل صف من: [كود المنتج, الكمية الافتتاحية, متوسط تكلفة الوحدة]
OPENING_BALANCES_DATA = [
    ["PROD-001", 100.0, 15.50],
    ["PROD-002", 50.0, 25.00],
    ["PROD-003", 200.0, 8.75],
    # أضف المزيد من المنتجات هنا
]

def add_opening_balances():
    """
    Script to add opening inventory balances for products.
    """
    Session = sessionmaker(bind=engine)
    db_session = Session()

    print("بدء عملية إضافة الأرصدة الافتتاحية...")

    for code, quantity, unit_price in OPENING_BALANCES_DATA:
        product = db_session.query(Product).filter(Product.code == code).first()

        if product:
            # 1. إنشاء حركة مخزون للرصيد الافتتاحي
            movement = WarehouseMovement(
                product_id=product.id,
                type="رصيد افتتاحي",
                quantity=quantity,
                unit_price=unit_price,
                date=datetime.date.today(),
                notes=f"رصيد افتتاحي للمنتج {product.name}"
            )
            db_session.add(movement)

            # 2. تحديث الرصيد الحالي للمنتج ومتوسط التكلفة
            product.current_stock = quantity
            product.average_cost = unit_price
            product.purchase_price = unit_price # Also update purchase price

            print(f"✔️ تمت إضافة رصيد افتتاحي للمنتج: {product.name} (الكمية: {quantity})")

        else:
            print(f"⚠️ تحذير: المنتج بالكود '{code}' غير موجود في قاعدة البيانات. سيتم تجاهله.")

    try:
        db_session.commit()
        print("
✅ تم حفظ جميع التغييرات بنجاح في قاعدة البيانات.")
    except Exception as e:
        db_session.rollback()
        print(f"
❌ حدث خطأ أثناء حفظ التغييرات: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    add_opening_balances()
