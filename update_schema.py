import sqlite3
import os

db_path = os.path.join('backend', 'expenses.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Add unit_price to warehouse_movements
    try:
        cursor.execute("ALTER TABLE warehouse_movements ADD COLUMN unit_price FLOAT")
        print("Column 'unit_price' added to 'warehouse_movements' table.")
    except sqlite3.OperationalError as e:
        print(f"Column 'unit_price' already exists or error: {e}")

    # 2. Add product_id to expense_items
    try:
        cursor.execute("ALTER TABLE expense_items ADD COLUMN product_id INTEGER REFERENCES products(id)")
        print("Column 'product_id' added to 'expense_items' table.")
    except sqlite3.OperationalError as e:
        print(f"Column 'product_id' already exists or error: {e}")

    conn.commit()
    conn.close()
    print("Database update process completed.")
else:
    print(f"Database file not found at {db_path}")
