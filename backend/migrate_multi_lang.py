import sqlite3

def add_column_if_not_exists(cursor, table, column, datatype):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    if column not in columns:
        print(f"Adding {column} to {table}...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
    else:
        print(f"Column {column} already exists in {table}.")

def migrate():
    print("Connecting to database...")
    db_path = r"C:\Users\LENOVO\Desktop\Neferdidi\expenses.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # CostCenter
    add_column_if_not_exists(cur, "cost_centers", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "cost_centers", "name_en", "VARCHAR")
    add_column_if_not_exists(cur, "cost_centers", "description_en", "TEXT")

    # Location
    add_column_if_not_exists(cur, "locations", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "locations", "name_en", "VARCHAR")
    add_column_if_not_exists(cur, "locations", "description_en", "TEXT")

    # ExpenseType
    add_column_if_not_exists(cur, "expense_types", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "expense_types", "name_en", "VARCHAR")

    # ExpenseItem
    add_column_if_not_exists(cur, "expense_items", "description_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "expense_items", "description_en", "VARCHAR")

    # Product
    add_column_if_not_exists(cur, "products", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "products", "name_en", "VARCHAR")

    # Recipe
    add_column_if_not_exists(cur, "recipes", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "recipes", "name_en", "VARCHAR")

    # Branch
    add_column_if_not_exists(cur, "branches", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "branches", "name_en", "VARCHAR")

    # Department
    add_column_if_not_exists(cur, "departments", "name_chinese", "VARCHAR")
    add_column_if_not_exists(cur, "departments", "name_en", "VARCHAR")
    add_column_if_not_exists(cur, "departments", "description_en", "TEXT")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
