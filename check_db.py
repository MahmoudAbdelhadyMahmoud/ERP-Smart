import sqlite3
import os

db_path = r"c:\Users\LENOVO\Desktop\Neferdidi\expenses.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")

for table in tables:
    name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {name}")
    count = cursor.fetchone()[0]
    print(f"Table {name}: {count} rows")

conn.close()
