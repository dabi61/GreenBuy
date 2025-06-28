from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from fastapi import Form

class ProductBase(BaseModel):
    shop_id: int
    sub_category_id: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None
    price: Optional[float] = None

class ProductFormCreate(BaseModel):
    name: str = Form(...)
    description: Optional[str] = Form(None)
    price: Optional[float] = Form(None)
    sub_category_id: int = Form(...)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    price: Optional[float] = None
    sub_category_id: Optional[int] = None

class ProductRead(ProductBase):
    product_id: int
    approved_by: Optional[int] = None
    create_at: datetime

    class Config:
        from_attributes = True

# 📊 Inventory Schemas

class StockInfo(BaseModel):
    """Thông tin tồn kho của sản phẩm"""
    total_quantity: int
    variant_count: int
    status: str  # "pending", "in_stock", "out_of_stock"

class ProductWithStock(BaseModel):
    """Sản phẩm với thông tin tồn kho"""
    product_id: int
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    cover: Optional[str] = None
    shop_id: int
    sub_category_id: int
    is_approved: Optional[bool] = None
    approval_note: Optional[str] = None
    create_at: Optional[str] = None
    stock_info: StockInfo

class InventoryStatsSummary(BaseModel):
    """Tổng quan thống kê tồn kho"""
    total_products: int
    pending_approval: int
    in_stock: int
    out_of_stock: int

class InventoryStatsResponse(BaseModel):
    """Response cho inventory stats API"""
    summary: InventoryStatsSummary
    shop_id: Optional[int] = None

class ProductsByStatusResponse(BaseModel):
    """Response cho products by status API"""
    items: List[ProductWithStock]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    status: str
    shop_id: Optional[int] = None

# 📦 Attribute with detailed stock info

class AttributeStockInfo(BaseModel):
    """Thông tin chi tiết về attribute và tồn kho"""
    attribute_id: int
    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    quantity: int
    image: Optional[str] = None
    create_at: Optional[str] = None

class ProductDetailWithStock(ProductWithStock):
    """Chi tiết sản phẩm với tất cả thông tin attribute và tồn kho"""
    attributes: List[AttributeStockInfo]
    total_stock: int
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
