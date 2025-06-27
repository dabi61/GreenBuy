from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.order.model import Order

class PaymentMethodType(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    COD = "cod"  # Cash on Delivery
    MOMO = "momo"
    ZALO_PAY = "zalo_pay"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(SQLModel, table=True):
    """Phương thức thanh toán của user"""
    __tablename__ = "payment_method"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    type: PaymentMethodType
    
    # Thông tin thẻ tín dụng (encrypted)
    card_number: Optional[str] = None  # 4 số cuối
    card_holder_name: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    
    # Thông tin PayPal
    paypal_email: Optional[str] = None
    
    # Thông tin ngân hàng
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    
    # Metadata
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships using TYPE_CHECKING
    user: Optional["User"] = Relationship(back_populates="payment_methods")
    payments: List["Payment"] = Relationship(back_populates="payment_method")

class Payment(SQLModel, table=True):
    """Giao dịch thanh toán"""
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    payment_method_id: Optional[int] = Field(default=None, foreign_key="payment_method.id")
    
    amount: float
    currency: str = Field(default="VND")
    status: str = Field(default="pending")  # Temporary: use string instead of enum
    
    # Transaction details
    transaction_id: Optional[str] = None  # ID từ payment gateway
    gateway_response: Optional[str] = None  # Response từ gateway
    failure_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    
    # Relationships using TYPE_CHECKING
    # Temporarily disable order relationship to avoid circular dependency issues
    # order: Optional["Order"] = Relationship(back_populates="payments")
    payment_method: Optional[PaymentMethod] = Relationship(back_populates="payments")

class RefundRequest(SQLModel, table=True):
    """Yêu cầu hoàn tiền"""
    id: Optional[int] = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payment.id")
    user_id: int = Field(foreign_key="users.id")
    
    amount: float
    reason: str
    status: str = Field(default="pending")  # pending, approved, rejected, completed
    
    admin_note: Optional[str] = None
    processed_by: Optional[int] = Field(default=None, foreign_key="users.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Relationships - Fix ambiguous foreign keys
    payment: Optional[Payment] = Relationship()
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "RefundRequest.user_id"}
    )
    processor: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "RefundRequest.processed_by"}
    ) 