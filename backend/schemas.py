from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List

class CostCenterBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None

class CostCenterCreate(CostCenterBase):
    pass

class CostCenter(CostCenterBase):
    id: int
    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    department_id: Optional[int] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    class Config:
        from_attributes = True

class ExpenseTypeBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None

class ExpenseTypeCreate(ExpenseTypeBase):
    pass

class ExpenseType(ExpenseTypeBase):
    id: int
    class Config:
        from_attributes = True

class ExpenseItemBase(BaseModel):
    expense_type_id: int
    product_id: Optional[int] = None
    description: Optional[str] = None
    description_chinese: Optional[str] = None
    description_en: Optional[str] = None
    quantity: float = 1.0
    unit_price: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    amount: float

class ExpenseItemCreate(ExpenseItemBase):
    pass

class ExpenseItem(ExpenseItemBase):
    id: int
    expense_type: Optional[str] = None
    type_rel: Optional[ExpenseType] = None
    product: Optional[ProductBase] = None
    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    date: date
    amount_egp: float
    taxes: float = 0.0
    discount_pct: float = 0.0
    notes: Optional[str] = None
    cost_center_id: int
    invoice_number: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    items: List[ExpenseItemCreate]

class Expense(ExpenseBase):
    id: int
    invoice_number: Optional[str] = None
    total: float
    cost_center: Optional[CostCenter] = None
    items: List[ExpenseItem] = []
    class Config:
        from_attributes = True

class RecommendationRequest(BaseModel):
    notes: str
    amount: float

# Warehouse Schemas
class ProductBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    unit: str
    current_stock: float = 0.0
    code: Optional[str] = None
    average_cost: float = 0.0
    purchase_price: float = 0.0
    reorder_level: float = 0.0
    notes: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True

class WarehouseMovementBase(BaseModel):
    doc_number: Optional[str] = None
    product_id: int
    location_id: Optional[int] = None
    type: str # "Addition", "Disposal", "Adjustment", "Transfer Out", "Transfer In"
    quantity: float
    unit_price: Optional[float] = None
    date: date
    notes: Optional[str] = None
    expense_id: Optional[int] = None
    transfer_link_id: Optional[int] = None

class WarehouseMovementCreate(WarehouseMovementBase):
    pass

class WarehouseMovement(WarehouseMovementBase):
    id: int
    product: Optional[Product] = None
    location: Optional[Location] = None
    class Config:
        from_attributes = True

class TransferRequest(BaseModel):
    product_id: int
    from_location_id: int
    to_location_id: int
    quantity: float
    date: date
    notes: Optional[str] = None

class InventoryAuditItemBase(BaseModel):
    product_id: int
    expected_quantity: float
    actual_quantity: float

class InventoryAuditItemCreate(InventoryAuditItemBase):
    pass

class InventoryAuditItem(InventoryAuditItemBase):
    id: int
    product: Optional[Product] = None
    class Config:
        from_attributes = True

class InventoryAuditBase(BaseModel):
    date: date
    is_active: int = 0
    is_completed: int = 0
    is_skipped: int = 0

class InventoryAuditCreate(InventoryAuditBase):
    pass

class InventoryAudit(InventoryAuditBase):
    id: int
    items: List[InventoryAuditItem] = []
    class Config:
        from_attributes = True

class AuditItemActual(BaseModel):
    product_id: int
    actual_quantity: float

class AuditSubmitRequest(BaseModel):
    items: List[AuditItemActual]

class PriceHistoryEntry(BaseModel):
    date: date
    price: float
    source: str # "Expense" or "Movement"
    quantity: float

class ProductPriceHistory(BaseModel):
    product_id: int
    product_name: str
    history: List[PriceHistoryEntry]

class WarehouseMovementUpdate(BaseModel):
    doc_number: Optional[str] = None
    type: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    date: Optional[date] = None
    notes: Optional[str] = None

class OpeningBalanceItem(BaseModel):
    product_id: int
    location_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    date: Optional[date] = None
    notes: Optional[str] = None

class OpeningBalanceRequest(BaseModel):
    items: List[OpeningBalanceItem]

class BulkWarehouseMovementItem(BaseModel):
    product_id: int
    quantity: float
    unit_price: Optional[float] = 0.0
    notes: Optional[str] = None

class BulkWarehouseMovementRequest(BaseModel):
    date: date
    location_id: int
    type: str # "Addition", "Disposal"
    notes: Optional[str] = None
    items: List[BulkWarehouseMovementItem]

class BulkTransferItem(BaseModel):
    product_id: int
    quantity: float
    notes: Optional[str] = None

class BulkTransferRequest(BaseModel):
    date: date
    from_location_id: int
    to_location_id: int
    notes: Optional[str] = None
    items: List[BulkTransferItem]

class AuditLogBase(BaseModel):
    timestamp: datetime
    user: str
    action: str
    table_name: str
    record_id: int
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    notes: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    class Config:
        from_attributes = True

# Cost Accounting Schemas

class RecipeItemBase(BaseModel):
    material_product_id: int
    quantity: float = 1.0
    waste_pct: float = 0.0

class RecipeItemCreate(RecipeItemBase):
    pass

class RecipeItem(RecipeItemBase):
    id: int
    recipe_id: int
    material_product: Optional[Product] = None
    
    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    product_id: int
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    base_quantity: float = 1.0
    labor_cost: float = 0.0
    overhead_cost: float = 0.0
    gas_cost: float = 0.0
    electricity_cost: float = 0.0
    water_cost: float = 0.0
    rent_cost: float = 0.0
    marketing_cost: float = 0.0
    ad_cost: float = 0.0
    admin_cost: float = 0.0
    taxes: float = 0.0
    import_costs: float = 0.0
    other_costs: float = 0.0
    selling_price: float = 0.0
    is_active: bool = True
    notes: Optional[str] = None

class RecipeCreate(RecipeBase):
    items: List[RecipeItemCreate]

class Recipe(RecipeBase):
    id: int
    product: Optional[Product] = None
    items: List[RecipeItem] = []
    
    class Config:
        from_attributes = True

class CostLayerBase(BaseModel):
    product_id: int
    receipt_date: datetime
    original_qty: float
    remaining_qty: float
    unit_cost: float
    source_doc: Optional[str] = None

class CostLayer(CostLayerBase):
    id: int
    
    class Config:
        from_attributes = True

class CostTransactionBase(BaseModel):
    date: datetime
    product_id: int
    transaction_type: str
    quantity: float
    unit_cost: float
    total_cost: float
    reference_id: Optional[str] = None

class CostTransaction(CostTransactionBase):
    id: int
    
    class Config:
        from_attributes = True

# Branches and Departments Schemas

class BranchBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    code: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool = True

class BranchCreate(BranchBase):
    pass

class Branch(BranchBase):
    id: int
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    branch_id: int
    name: str
    name_chinese: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# Stock Count Schemas

class StockCountItemBase(BaseModel):
    product_id: int
    system_qty: float = 0.0
    physical_qty: Optional[float] = None
    reason_code: Optional[str] = None

class StockCountItemCreate(StockCountItemBase):
    pass

class StockCountItemUpdate(BaseModel):
    physical_qty: Optional[float] = None
    reason_code: Optional[str] = None

class StockCountItem(StockCountItemBase):
    id: int
    stock_count_id: int
    variance_qty: Optional[float] = None
    variance_value: Optional[float] = None
    requires_recount: bool = False
    
    product: Optional[Product] = None
    
    class Config:
        from_attributes = True

class StockCountBase(BaseModel):
    branch_id: Optional[int] = None
    warehouse_id: int
    count_type: str = "Daily"
    blind_count: bool = False
    notes: Optional[str] = None

class StockCountCreate(StockCountBase):
    pass

class StockCount(StockCountBase):
    id: int
    date: datetime
    status: str
    created_by: str
    approved_by: Optional[str] = None
    created_at: datetime
    
    items: List[StockCountItem] = []
    
    class Config:
        from_attributes = True


