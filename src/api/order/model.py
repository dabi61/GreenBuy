from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import random
import string
import uuid

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.product.model import Product
    from api.attribute.model import Attribute
    from api.payment.model import Payment

# Order Status Constants - Using integers instead of enum for simplicity
# Database enum exists but we use int mapping to avoid casting issues
class OrderStatus:
    PENDING = 1      # pending
    CONFIRMED = 2    # confirmed
    PROCESSING = 3   # processing
    SHIPPED = 4      # shipped
    DELIVERED = 5    # delivered
    CANCELLED = 6    # cancelled
    REFUNDED = 7     # refunded
    RETURNED = 8     # returned
    
    # Mapping for display purposes
    STATUS_NAMES = {
        1: "pending",
        2: "confirmed", 
        3: "processing",
        4: "shipped",
        5: "delivered",
        6: "cancelled",
        7: "refunded",
        8: "returned"
    }
    
    @classmethod
    def get_name(cls, status_id: int) -> str:
        """Get status name from status ID"""
        return cls.STATUS_NAMES.get(status_id, "unknown")
    
    @classmethod
    def get_id(cls, status_name: str) -> int:
        """Get status ID from status name"""
        for id, name in cls.STATUS_NAMES.items():
            if name == status_name:
                return id
        return cls.PENDING  # Default to pending

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="product.product_id")
    attribute_id: int = Field(foreign_key="attribute.attribute_id")
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")
    price: float = Field(ge=0, description="Price must be non-negative")
    
    # Re-enable relationships
    order: Optional["Order"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="order_items")
    attribute: Optional["Attribute"] = Relationship()

def generate_order_number() -> str:
    """Generate unique order number format: ORD-YYYYMMDD-XXXXXX with UUID suffix"""
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
    return f"ORD-{date_part}-{unique_part}"

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    
    # Core fields - exactly match database schema
    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(default_factory=generate_order_number, unique=True)
    user_id: int = Field(foreign_key="users.id")
    status: int = Field(
        default=OrderStatus.PENDING, 
        description="Order status as integer (1=pending, 2=confirmed, 3=processing, 4=shipped, 5=delivered, 6=cancelled, 7=refunded, 8=returned)"
    )
    
    # Pricing fields - match database schema with validation
    subtotal: Optional[float] = Field(default=0.0, ge=0, description="Subtotal must be non-negative")
    tax_amount: Optional[float] = Field(default=0.0, ge=0, description="Tax amount must be non-negative")
    shipping_fee: Optional[float] = Field(default=0.0, ge=0, description="Shipping fee must be non-negative")
    discount_amount: Optional[float] = Field(default=0.0, ge=0, description="Discount amount must be non-negative")
    total_amount: Optional[float] = Field(default=0.0, ge=0, description="Total amount must be non-negative")
    
    # Address and contact fields - match database schema
    shipping_address: str = Field(min_length=10, max_length=500, description="Shipping address is required")
    billing_address: Optional[str] = Field(default=None, max_length=500)
    phone_number: str = Field(min_length=10, max_length=15, description="Phone number is required")
    recipient_name: str = Field(min_length=2, max_length=100, description="Recipient name is required")
    delivery_notes: Optional[str] = Field(default=None, max_length=1000)
    
    # Timestamp fields - match database schema
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Notes fields - match database schema
    notes: Optional[str] = Field(default=None, max_length=1000)
    internal_notes: Optional[str] = Field(default=None, max_length=1000)
    
    # Re-enable relationships
    user: Optional["User"] = Relationship(back_populates="orders")
    items: List[OrderItem] = Relationship(back_populates="order")
    # Temporarily disable payments relationship to avoid circular dependency issues
    # payments: List["Payment"] = Relationship(back_populates="order")
    
    def is_editable(self) -> bool:
        """Check if order can be edited (only pending orders)"""
        return self.status == OrderStatus.PENDING
    
    def is_cancellable(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    def get_valid_next_statuses(self) -> List[int]:
        """Get valid next statuses for this order"""
        transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: [],
            OrderStatus.RETURNED: [OrderStatus.REFUNDED]
        }
        return transitions.get(self.status, [])
    
    def get_status_name(self) -> str:
        """Get human readable status name"""
        return OrderStatus.get_name(self.status) 