import sqlite3
import os

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "..", "expenses.db")

print(f"Migrating database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add name_chinese to products if not exists
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN name_chinese TEXT")
        print("Added column 'name_chinese' to 'products' table.")
    except sqlite3.OperationalError:
        print("Column 'name_chinese' already exists in 'products' table.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")
except Exception as e:
    print(f"Error during migration: {e}")
