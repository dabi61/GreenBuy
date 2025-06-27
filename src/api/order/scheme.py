from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime
from api.order.model import OrderStatus

class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0, description="Product ID must be positive")
    attribute_id: int = Field(gt=0, description="Attribute ID must be positive")
    quantity: int = Field(gt=0, le=999, description="Quantity must be between 1 and 999")

class OrderItemRead(BaseModel):
    id: int
    product_id: int
    attribute_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(min_items=1, description="At least one item is required")
    shipping_address: str = Field(min_length=10, max_length=500, description="Shipping address is required")
    phone_number: str = Field(min_length=10, max_length=15, description="Phone number is required")
    recipient_name: str = Field(min_length=2, max_length=100, description="Recipient name is required")
    delivery_notes: Optional[str] = Field(default=None, max_length=1000)
    billing_address: Optional[str] = Field(default=None, max_length=500)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic phone number validation
        import re
        phone_pattern = r'^[\+]?[0-9\-\(\)\s]+$'
        if not re.match(phone_pattern, v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('shipping_address')
    def validate_shipping_address(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Shipping address cannot be empty')
        return v.strip()

class OrderRead(BaseModel):
    id: int
    order_number: str
    status: str  # Will be converted from integer to string in validator
    subtotal: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    shipping_fee: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Shipping info - match model field names
    billing_address: Optional[str] = None
    shipping_address: str
    phone_number: str
    recipient_name: str
    delivery_notes: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    items: List[OrderItemRead] = []
    
    @validator('status', pre=True)
    def convert_status_to_string(cls, v):
        """Convert integer status to string name"""
        if isinstance(v, int):
            return OrderStatus.get_name(v)
        return v
    
    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = Field(default=None, min_length=10, max_length=500)
    phone_number: Optional[str] = Field(default=None, min_length=10, max_length=15)
    recipient_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    delivery_notes: Optional[str] = Field(default=None, max_length=1000)
    billing_address: Optional[str] = Field(default=None, max_length=500)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            import re
            phone_pattern = r'^[\+]?[0-9\-\(\)\s]+$'
            if not re.match(phone_pattern, v):
                raise ValueError('Invalid phone number format')
        return v

class OrderStatusUpdate(BaseModel):
    status: int = Field(ge=1, le=8, description="Status must be between 1-8 (1=pending, 2=confirmed, 3=processing, 4=shipped, 5=delivered, 6=cancelled, 7=refunded, 8=returned)")
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    cancellation_reason: Optional[str] = Field(default=None, max_length=500)

    @validator('status')
    def validate_status_transition(cls, v):
        # Valid status values are 1-8
        valid_statuses = [1, 2, 3, 4, 5, 6, 7, 8]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v

class CancelOrderRequest(BaseModel):
    cancellation_reason: str = Field(min_length=5, max_length=500, description="Cancellation reason is required")

class OrderSummary(BaseModel):
    """Tóm tắt đơn hàng cho mobile"""
    id: int
    order_number: str
    status: str
    total_items: int
    total_amount: float  # Match field name in model
    created_at: datetime
    
    @validator('status', pre=True)
    def convert_status_to_string(cls, v):
        """Convert integer status to string name"""
        if isinstance(v, int):
            return OrderStatus.get_name(v)
        return v
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    """Response for paginated order list"""
    items: List[OrderSummary]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
