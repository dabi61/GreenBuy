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
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    attribute_details: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    created_at: Optional[datetime] = None
    
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

class OrderForShop(BaseModel):
    """Chi tiết đơn hàng cho shop"""
    id: int
    order_number: str
    status: str
    customer_name: str  # recipient_name
    customer_phone: str  # phone_number
    shipping_address: str
    total_items: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Thông tin sản phẩm của shop trong đơn hàng này
    shop_items: List[dict]  # [{product_name, quantity, price}]
    shop_subtotal: float  # Tổng tiền chỉ tính các sản phẩm của shop này
    
    @validator('status', pre=True)
    def convert_status_to_string(cls, v):
        """Convert integer status to string name"""
        if isinstance(v, int):
            return OrderStatus.get_name(v)
        return v
    
    class Config:
        from_attributes = True

class ShopOrderStats(BaseModel):
    """Thống kê đơn hàng cho shop"""
    total_orders: int
    pending_orders: int      # status = 1
    confirmed_orders: int    # status = 2  
    processing_orders: int   # status = 3
    shipped_orders: int      # status = 4
    delivered_orders: int    # status = 5
    cancelled_orders: int    # status = 6
    refunded_orders: int     # status = 7
    returned_orders: int     # status = 8
    
    total_revenue: float     # Tổng doanh thu từ các đơn đã hoàn thành
    pending_revenue: float   # Doanh thu từ các đơn chờ xử lý
    
    # Thống kê theo thời gian
    orders_today: int
    orders_this_week: int
    orders_this_month: int
    
    # Rating info - số lượng đánh giá cần trả lời
    pending_ratings: int = 0

class ShopOrderListResponse(BaseModel):
    """Response cho danh sách đơn hàng của shop"""
    items: List[OrderForShop]
    stats: ShopOrderStats
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ==================== ADMIN ORDER MANAGEMENT ====================

class AdminOrderRead(BaseModel):
    """Chi tiết đơn hàng cho admin với thông tin thanh toán"""
    id: int
    order_number: str
    user_id: int
    customer_name: str  # recipient_name
    customer_email: Optional[str] = None
    customer_phone: str  # phone_number
    status: str
    
    # Pricing info
    subtotal: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    shipping_fee: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    
    # Address info
    shipping_address: str
    billing_address: Optional[str] = None
    delivery_notes: Optional[str] = None
    
    # Payment info
    payment_status: Optional[str] = None  # pending, completed, failed, etc.
    payment_method: Optional[str] = None
    payment_amount: Optional[float] = None
    transaction_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Order items
    items: List[OrderItemRead] = []
    
    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    @validator('status', pre=True)
    def convert_status_to_string(cls, v):
        """Convert integer status to string name"""
        if isinstance(v, int):
            return OrderStatus.get_name(v)
        return v
    
    class Config:
        from_attributes = True

class AdminOrderSummary(BaseModel):
    """Tóm tắt đơn hàng cho admin"""
    id: int
    order_number: str
    user_id: int
    customer_name: str  # recipient_name
    customer_phone: str  # phone_number
    status: str
    total_amount: float
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @validator('status', pre=True)
    def convert_status_to_string(cls, v):
        """Convert integer status to string name"""
        if isinstance(v, int):
            return OrderStatus.get_name(v)
        return v
    
    class Config:
        from_attributes = True

class AdminOrderListResponse(BaseModel):
    """Response cho danh sách đơn hàng admin"""
    items: List[AdminOrderSummary]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

class AdminOrderStats(BaseModel):
    """Thống kê đơn hàng cho admin"""
    total_orders: int
    
    # Orders by status
    pending_orders: int      # status = 1
    confirmed_orders: int    # status = 2  
    processing_orders: int   # status = 3
    shipped_orders: int      # status = 4
    delivered_orders: int    # status = 5
    cancelled_orders: int    # status = 6
    refunded_orders: int     # status = 7
    returned_orders: int     # status = 8
    
    # Payment stats
    paid_orders: int         # payment status = completed
    unpaid_orders: int       # no payment or payment status != completed
    failed_payments: int     # payment status = failed
    
    # Revenue stats
    total_revenue: float     # Tổng doanh thu từ các đơn đã thanh toán
    pending_revenue: float   # Doanh thu từ các đơn chưa thanh toán
    
    # Time-based stats
    orders_today: int
    orders_this_week: int
    orders_this_month: int
    
    # Average order value
    avg_order_value: float

class AdminOrderStatusUpdateRequest(BaseModel):
    """Request để admin cập nhật status order"""
    status: int = Field(ge=1, le=8, description="Status must be between 1-8")
    internal_notes: Optional[str] = Field(default=None, max_length=1000)
    notify_customer: bool = Field(default=True, description="Có gửi thông báo cho khách hàng không")
    
    @validator('status')
    def validate_status_transition(cls, v):
        valid_statuses = [1, 2, 3, 4, 5, 6, 7, 8]
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v

class AdminOrderFilter(BaseModel):
    """Filter cho admin order list"""
    status: Optional[str] = None  # pending, confirmed, processing, shipped, delivered, cancelled, refunded, returned
    payment_status: Optional[str] = None  # pending, completed, failed, cancelled, refunded
    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None    # YYYY-MM-DD
    customer_search: Optional[str] = None  # Search by customer name, phone, email
    order_number: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
