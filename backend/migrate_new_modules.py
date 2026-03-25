import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "expenses.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

migrations = []

# 1. Add department_id to locations (if not exists)
cursor.execute("PRAGMA table_info(locations)")
location_cols = [row[1] for row in cursor.fetchall()]
if "department_id" not in location_cols:
    migrations.append("ALTER TABLE locations ADD COLUMN department_id INTEGER REFERENCES departments(id)")
    print("OK: Queued department_id to locations")
else:
    print("SKIP: department_id already in locations")

# 2. Create branches table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branches'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR UNIQUE NOT NULL,
        code VARCHAR UNIQUE,
        manager_id VARCHAR,
        is_active BOOLEAN DEFAULT 1
    )""")
    print("OK: Queued branches table")
else:
    print("SKIP: branches already exists")

# 3. Create departments table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='departments'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER REFERENCES branches(id),
        name VARCHAR NOT NULL,
        description TEXT
    )""")
    print("OK: Queued departments table")
else:
    print("SKIP: departments already exists")

# 4. Create recipes table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipes'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES products(id),
        name VARCHAR NOT NULL,
        base_quantity FLOAT DEFAULT 1.0,
        labor_cost FLOAT DEFAULT 0.0,
        overhead_cost FLOAT DEFAULT 0.0,
        is_active BOOLEAN DEFAULT 1,
        notes TEXT
    )""")
    print("OK: Queued recipes table")
else:
    print("SKIP: recipes already exists")

# 5. Create recipe_items table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipe_items'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE recipe_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER REFERENCES recipes(id),
        material_product_id INTEGER REFERENCES products(id),
        quantity FLOAT DEFAULT 1.0,
        waste_pct FLOAT DEFAULT 0.0
    )""")
    print("OK: Queued recipe_items table")
else:
    print("SKIP: recipe_items already exists")

# 6. Create cost_layers table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cost_layers'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE cost_layers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES products(id),
        receipt_date DATETIME,
        original_qty FLOAT,
        remaining_qty FLOAT,
        unit_cost FLOAT,
        source_doc VARCHAR
    )""")
    print("OK: Queued cost_layers table")
else:
    print("SKIP: cost_layers already exists")

# 7. Create cost_transactions table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cost_transactions'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE cost_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATETIME,
        product_id INTEGER REFERENCES products(id),
        transaction_type VARCHAR,
        quantity FLOAT,
        unit_cost FLOAT,
        total_cost FLOAT,
        reference_id VARCHAR
    )""")
    print("OK: Queued cost_transactions table")
else:
    print("SKIP: cost_transactions already exists")

# 8. Create stock_counts table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_counts'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE stock_counts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATETIME,
        branch_id INTEGER REFERENCES branches(id),
        warehouse_id INTEGER REFERENCES locations(id),
        count_type VARCHAR DEFAULT 'Daily',
        status VARCHAR DEFAULT 'Draft',
        blind_count BOOLEAN DEFAULT 0,
        created_by VARCHAR DEFAULT 'System',
        approved_by VARCHAR,
        created_at DATETIME,
        notes TEXT
    )""")
    print("OK: Queued stock_counts table")
else:
    print("SKIP: stock_counts already exists")

# 9. Create stock_count_items table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_count_items'")
if not cursor.fetchone():
    migrations.append("""
    CREATE TABLE stock_count_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_count_id INTEGER REFERENCES stock_counts(id),
        product_id INTEGER REFERENCES products(id),
        system_qty FLOAT DEFAULT 0.0,
        physical_qty FLOAT,
        variance_qty FLOAT,
        variance_value FLOAT,
        reason_code VARCHAR,
        requires_recount BOOLEAN DEFAULT 0
    )""")
    print("OK: Queued stock_count_items table")
else:
    print("SKIP: stock_count_items already exists")

print("Running", len(migrations), "migration(s)...")
for sql in migrations:
    cursor.execute(sql)
    conn.commit()

print("Done! All migrations completed successfully.")
conn.close()
