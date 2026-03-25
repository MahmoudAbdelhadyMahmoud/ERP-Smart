import ast
import traceback
import sys

def get_node_text(node, source_lines):
    return '\n'.join(source_lines[node.lineno - 1:node.end_lineno])

def main():
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            source = f.read()
        source_lines = source.splitlines()

        tree = ast.parse(source)

        imports = [
            "from fastapi import APIRouter, Depends, HTTPException, Response",
            "from sqlalchemy.orm import Session",
            "from sqlalchemy.exc import IntegrityError",
            "from typing import List",
            "import models, schemas, utils",
            "from database import get_db",
            "from datetime import date, datetime, timedelta",
            "import json",
            "from routers.dependencies import check_lock, is_system_locked, log_audit"
        ]

        def create_router_file(filename, prefix, tags, func_names):
            content = "\n".join(imports) + f"\n\nrouter = APIRouter(prefix='{prefix}', tags=['{tags}'])\n\n"
            added = 0
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in func_names:
                    # Modify the decorator from @app.XXX to @router.XXX
                    text = get_node_text(node, source_lines)
                    text = text.replace("@app.", "@router.", 1)
                    # For routes that have no prefix in the router yet, we might need to strip the prefix
                    # But it's easier to just keep prefix="" in APIRouter and use the full path, 
                    # OR we define prefix and replace the route path. Let's just use prefix="" and keep full paths.
                    content += text + "\n\n"
                    added += 1
            if added > 0:
                with open(f'routers/{filename}', 'w', encoding='utf-8') as f:
                    f.write(content.replace(f"prefix='{prefix}'", "prefix=''"))
                print(f"Created routers/{filename} with {added} functions")

        # 1. dependencies.py (shared functions)
        deps_content = """from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import models
from database import get_db

"""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in ['log_audit', 'is_system_locked', 'check_lock']:
                deps_content += get_node_text(node, source_lines) + "\n\n"
        with open('routers/dependencies.py', 'w', encoding='utf-8') as f:
            f.write(deps_content)
        print("Created routers/dependencies.py")

        # Define route assignments
        expense_funcs = [
            'create_cost_center', 'list_cost_centers', 'update_cost_center', 'delete_cost_center',
            'create_expense_type', 'list_expense_types', 'update_expense_type', 'delete_expense_type',
            'list_expenses', 'create_expense', 'update_expense', 'delete_expense'
        ]
        create_router_file('expenses.py', '', 'Expenses', expense_funcs)

        warehouse_funcs = [
            'list_products', 'create_product', 'update_product', 'delete_product',
            'set_opening_balances', 'approve_current_stock_as_opening',
            'list_movements', 'create_movement', 'update_movement', 'delete_movement',
            'recalculate_stock'
        ]
        create_router_file('warehouse.py', '', 'Warehouse', warehouse_funcs)

        analytics_funcs = [
            'recommend_type', 'export_excel', 'export_pdf', 'get_analytics_summary',
            'get_stock_summary', 'get_top_items', 'list_audit_logs', 'get_product_price_history'
        ]
        create_router_file('analytics.py', '', 'Analytics', analytics_funcs)

        system_funcs = [
            'skip_audit', 'start_audit', 'get_system_status', 
            'list_audits', 'get_current_audit', 'submit_audit'
        ]
        create_router_file('system.py', '', 'System', system_funcs)

        # Generate new main.py
        main_imports = """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import expenses, warehouse, analytics, system

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Manager AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses.router)
app.include_router(warehouse.router)
app.include_router(analytics.router)
app.include_router(system.router)
"""
        
        # Add remaining functions (HTML routes)
        main_content = main_imports + "\n"
        # We also need to add the STATIC mounts
        mount_added = False
        for node in tree.body:
             if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and getattr(node.value.func.value, 'id', '') == 'app' and node.value.func.attr == 'mount':
                 main_content += get_node_text(node, source_lines) + "\n\n"
                 mount_added = True
             elif isinstance(node, ast.FunctionDef) and node.name in ['favicon', 'read_index', 'read_add_expense', 'read_opening_balances']:
                 main_content += get_node_text(node, source_lines) + "\n\n"
        
        if not mount_added:
            main_content += """import os
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

"""

        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(main_content)
        print("Updated main.py")

    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    main()
