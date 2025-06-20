from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import random
import string

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.product.model import Product
    from api.attribute.model import Attribute
    from api.payment.model import Payment

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="product.product_id")
    attribute_id: int = Field(foreign_key="attribute.attribute_id")
    quantity: int
    price: float
    
    # Re-enable relationships
    order: Optional["Order"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="order_items")
    attribute: Optional["Attribute"] = Relationship()

def generate_order_number() -> str:
    """Generate unique order number format: ORD-YYYYMMDD-XXXXXX"""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"ORD-{date_part}-{random_part}"

class Order(SQLModel, table=True):
    __tablename__ = "orders"  # Use proper orders table with full schema
    
    # Core fields - exactly match database schema
    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(default_factory=generate_order_number)
    user_id: int = Field(foreign_key="users.id")
    status: str = Field(default="pending")  # Temporary: use string instead of enum
    
    # Pricing fields - match database schema
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    shipping_fee: Optional[float] = None
    discount_amount: Optional[float] = None
    total_amount: Optional[float] = None
    
    # Address and contact fields - match database schema
    shipping_address: str
    billing_address: Optional[str] = None
    phone_number: str
    recipient_name: str
    delivery_notes: Optional[str] = None
    
    # Timestamp fields - match database schema
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Notes fields - match database schema
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Re-enable relationships
    user: Optional["User"] = Relationship(back_populates="orders")
    items: List[OrderItem] = Relationship(back_populates="order")
    payments: List["Payment"] = Relationship(back_populates="order") 