import sqlite3
import os

db_path = "c:\\Users\\LENOVO\\Desktop\\Neferdidi\\expenses.db"

def check_table(cursor, table_name):
    print(f"\n--- Columns in {table_name} ---")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(col[1]) # Column name

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        check_table(cursor, table[0])
        
    conn.close()
else:
    print(f"Database file not found at {db_path}")
