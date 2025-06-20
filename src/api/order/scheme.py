from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from .model import OrderStatus

class OrderItemCreate(BaseModel):
    product_id: int
    attribute_id: int
    quantity: int

class OrderItemRead(BaseModel):
    id: int
    product_id: int
    attribute_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    shipping_notes: Optional[str] = None

class OrderRead(BaseModel):
    id: int
    status: OrderStatus
    subtotal: float  # updated field name
    tax_amount: float
    shipping_fee: float
    discount_amount: float
    total_amount: float  # updated field name
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Shipping info - updated field names
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    phone_number: Optional[str] = None  # was shipping_phone
    recipient_name: Optional[str] = None
    delivery_notes: Optional[str] = None  # was shipping_notes
    order_number: Optional[str] = None
    
    # Notes - updated field names
    notes: Optional[str] = None
    internal_notes: Optional[str] = None  # was admin_notes
    
    items: List[OrderItemRead]
    
    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    shipping_notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    admin_notes: Optional[str] = None
    tracking_number: Optional[str] = None
    cancellation_reason: Optional[str] = None

class OrderSummary(BaseModel):
    """Tóm tắt đơn hàng cho mobile"""
    id: int
    status: OrderStatus
    total_items: int
    final_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True
