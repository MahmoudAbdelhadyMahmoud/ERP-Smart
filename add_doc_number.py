"""
Migration: Add doc_number column to warehouse_movements table.
Run this ONCE before restarting the server.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(warehouse_movements)")
columns = [row[1] for row in cursor.fetchall()]

if "doc_number" not in columns:
    cursor.execute("ALTER TABLE warehouse_movements ADD COLUMN doc_number TEXT")
    conn.commit()
    print("OK: doc_number column added successfully!")
else:
    print("INFO: doc_number column already exists, skipping migration.")

conn.close()
