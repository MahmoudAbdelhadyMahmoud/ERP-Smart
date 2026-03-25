import sqlite3
import os

db_path = os.path.join('backend', 'expenses.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Add 'code' column without UNIQUE for now
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN code TEXT")
        print("Column 'code' added to 'products' table.")
    except sqlite3.OperationalError as e:
        print(f"Error adding column 'code': {e}")
            
    # 2. Populate codes
    cursor.execute("SELECT id FROM products WHERE code IS NULL")
    missing_codes = cursor.fetchall()
    
    for i, (prod_id,) in enumerate(missing_codes):
        new_code = f"PRD-{(i + 1):04d}"
        cursor.execute("UPDATE products SET code = ? WHERE id = ?", (new_code, prod_id))
        print(f"Assigned code {new_code} to product ID {prod_id}")
    
    # 3. Add unique index for 'code'
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_product_code ON products(code)")
        print("Unique index on 'code' created.")
    except sqlite3.OperationalError as e:
        print(f"Error creating index: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")
else:
    print(f"Database file not found at {db_path}")
