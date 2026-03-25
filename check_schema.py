import sqlite3
import os

db_path = os.path.join('backend', 'expenses.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
else:
    print(f"Database file not found at {db_path}")
