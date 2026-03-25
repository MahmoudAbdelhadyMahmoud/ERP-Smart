import sqlite3
import os

db_path = "c:\\Users\\LENOVO\\Desktop\\Neferdidi\\expenses.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add expense_id to warehouse_movements
    try:
        cursor.execute("ALTER TABLE warehouse_movements ADD COLUMN expense_id INTEGER REFERENCES expenses(id)")
        print("Column 'expense_id' added to 'warehouse_movements' table.")
    except sqlite3.OperationalError as e:
        print(f"Column 'expense_id' already exists or error: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")
else:
    print(f"Database file not found at {db_path}")
