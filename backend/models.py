from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    user = Column(String, default="مدير النظام")
    action = Column(String)  # e.g., "Create", "Update", "Delete"
    table_name = Column(String)
    record_id = Column(Integer)
    old_values = Column(Text, nullable=True) # JSON string
    new_values = Column(Text, nullable=True) # JSON string
    notes = Column(Text, nullable=True)

class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    expenses = relationship("Expense", back_populates="cost_center")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    movements = relationship("WarehouseMovement", back_populates="location")
    department = relationship("Department", back_populates="locations")

class ExpenseType(Base):
    __tablename__ = "expense_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)

    items = relationship("ExpenseItem", back_populates="type_rel")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, nullable=True, index=True) # e.g. EXP-20260317-0001
    date = Column(Date)
    amount_egp = Column(Float)  # Total of items before tax/discount
    taxes = Column(Float, default=0.0)
    discount_pct = Column(Float, default=0.0)
    total = Column(Float)  # Grand total
    notes = Column(Text, nullable=True)
    
    cost_center_id = Column(Integer, ForeignKey("cost_centers.id"))
    cost_center = relationship("CostCenter", back_populates="expenses")
    
    items = relationship("ExpenseItem", back_populates="expense", cascade="all, delete-orphan")

class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    expense_type_id = Column(Integer, ForeignKey("expense_types.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    description = Column(String, nullable=True)
    description_chinese = Column(String, nullable=True)
    description_en = Column(String, nullable=True)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    amount = Column(Float) # total: (quantity * unit_price) + tax - discount

    expense = relationship("Expense", back_populates="items")
    type_rel = relationship("ExpenseType", back_populates="items")
    product = relationship("Product", back_populates="expense_items")

    @property
    def expense_type(self):
        if self.type_rel:
            langs = [self.type_rel.name]
            if self.type_rel.name_chinese: langs.append(self.type_rel.name_chinese)
            if self.type_rel.name_en: langs.append(self.type_rel.name_en)
            return " - ".join(langs)
        return "Unknown"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    unit = Column(String)  # e.g., "kg", "unit", "box"
    current_stock = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    purchase_price = Column(Float, default=0.0)
    reorder_level = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    movements = relationship("WarehouseMovement", back_populates="product")
    audit_items = relationship("InventoryAuditItem", back_populates="product")
    expense_items = relationship("ExpenseItem", back_populates="product")
    recipes = relationship("Recipe", back_populates="product", foreign_keys="[Recipe.product_id]")
    recipe_usages = relationship("RecipeItem", back_populates="material_product")
    cost_layers = relationship("CostLayer", back_populates="product")
    cost_transactions = relationship("CostTransaction", back_populates="product")

class WarehouseMovement(Base):
    __tablename__ = "warehouse_movements"

    id = Column(Integer, primary_key=True, index=True)
    doc_number = Column(String, nullable=True, index=True)  # e.g. WH-20260316-0001
    product_id = Column(Integer, ForeignKey("products.id"))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    type = Column(String)  # "Addition", "Disposal", "Adjustment", "Transfer Out", "Transfer In"
    quantity = Column(Float)
    unit_price = Column(Float, nullable=True) # Purchase price at time of movement
    date = Column(Date)
    notes = Column(Text, nullable=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    transfer_link_id = Column(Integer, nullable=True) # To link Transfer Out and Transfer In

    product = relationship("Product", back_populates="movements")
    location = relationship("Location", back_populates="movements")

class InventoryAudit(Base):
    __tablename__ = "inventory_audits"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date) # Date of the audit (e.g., end of month)
    is_active = Column(Integer, default=0) # 0: Created but not active (no lock), 1: Active (lock)
    is_completed = Column(Integer, default=0) # 0: Pending, 1: Completed
    is_skipped = Column(Integer, default=0) # 1: Audit was bypassed by manager

    items = relationship("InventoryAuditItem", back_populates="audit")

class InventoryAuditItem(Base):
    __tablename__ = "inventory_audit_items"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("inventory_audits.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    expected_quantity = Column(Float)
    actual_quantity = Column(Float)

    audit = relationship("InventoryAudit", back_populates="items")
    product = relationship("Product", back_populates="audit_items")

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True) # Final product
    name = Column(String, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    base_quantity = Column(Float, default=1.0) # E.g., This recipe yields 100 units
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    gas_cost = Column(Float, default=0.0)
    electricity_cost = Column(Float, default=0.0)
    water_cost = Column(Float, default=0.0)
    rent_cost = Column(Float, default=0.0)
    marketing_cost = Column(Float, default=0.0)
    ad_cost = Column(Float, default=0.0)
    admin_cost = Column(Float, default=0.0)
    taxes = Column(Float, default=0.0)
    import_costs = Column(Float, default=0.0)
    other_costs = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0) # Added selling price per unit
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    product = relationship("Product", back_populates="recipes", foreign_keys=[product_id])
    items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")

class RecipeItem(Base):
    __tablename__ = "recipe_items"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    material_product_id = Column(Integer, ForeignKey("products.id")) # Raw material
    quantity = Column(Float, default=1.0)
    waste_pct = Column(Float, default=0.0) # e.g., 0.1 for 10% expected waste

    recipe = relationship("Recipe", back_populates="items")
    material_product = relationship("Product", back_populates="recipe_usages", foreign_keys=[material_product_id])

class CostLayer(Base):
    __tablename__ = "cost_layers"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    receipt_date = Column(DateTime, default=datetime.datetime.now)
    original_qty = Column(Float)
    remaining_qty = Column(Float)
    unit_cost = Column(Float)
    source_doc = Column(String, nullable=True) # E.g., WH-2026-0001, EXP-2026-0001

    product = relationship("Product", back_populates="cost_layers")

class CostTransaction(Base):
    __tablename__ = "cost_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.now)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    transaction_type = Column(String) # Purchase, Sale, Production In, Production Out, Adjustment, Waste
    quantity = Column(Float)
    unit_cost = Column(Float)
    total_cost = Column(Float)
    reference_id = Column(String, nullable=True) # Document number

    product = relationship("Product", back_populates="cost_transactions")

class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    code = Column(String, unique=True, index=True, nullable=True)
    manager_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    departments = relationship("Department", back_populates="branch")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    name = Column(String, index=True)
    name_chinese = Column(String, nullable=True)
    name_en = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    branch = relationship("Branch", back_populates="departments")
    locations = relationship("Location", back_populates="department")

class StockCount(Base):
    __tablename__ = "stock_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.now)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("locations.id"))
    count_type = Column(String, default="Daily") # Daily / Monthly
    status = Column(String, default="Draft") # Draft / Submitted / Reviewed / Approved / Posted
    blind_count = Column(Boolean, default=False)
    created_by = Column(String, default="System")
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    notes = Column(Text, nullable=True)

    warehouse = relationship("Location")
    items = relationship("StockCountItem", back_populates="stock_count", cascade="all, delete-orphan")

class StockCountItem(Base):
    __tablename__ = "stock_count_items"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_count_id = Column(Integer, ForeignKey("stock_counts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    system_qty = Column(Float, default=0.0)
    physical_qty = Column(Float, nullable=True)
    
    variance_qty = Column(Float, nullable=True) # physical - system
    variance_value = Column(Float, nullable=True) # var_qty * avg_cost or cost
    
    reason_code = Column(String, nullable=True)
    requires_recount = Column(Boolean, default=False)

    stock_count = relationship("StockCount", back_populates="items")
    product = relationship("Product")
