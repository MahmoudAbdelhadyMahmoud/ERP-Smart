import sqlite3
import os

db_path = "c:\\Users\\LENOVO\\Desktop\\Neferdidi\\expenses.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create locations table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)
        print("Table 'locations' created or already exists.")
    except Exception as e:
        print(f"Error creating locations table: {e}")

    # 2. Add columns to warehouse_movements
    columns_to_add = [
        ("location_id", "INTEGER REFERENCES locations(id)"),
        ("transfer_link_id", "INTEGER")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE warehouse_movements ADD COLUMN {col_name} {col_type}")
            print(f"Column '{col_name}' added to 'warehouse_movements'.")
        except sqlite3.OperationalError:
            print(f"Column '{col_name}' already exists.")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
