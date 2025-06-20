from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from .model import PaymentMethodType, PaymentStatus

# Payment Method Schemes
class PaymentMethodCreate(BaseModel):
    type: PaymentMethodType
    
    # Credit card fields
    card_number: Optional[str] = None
    card_holder_name: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    
    # PayPal fields
    paypal_email: Optional[str] = None
    
    # Bank transfer fields
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    
    is_default: bool = False
    
    @validator('expiry_month')
    def validate_month(cls, v):
        if v and (v < 1 or v > 12):
            raise ValueError('Tháng hết hạn phải từ 1-12')
        return v
    
    @validator('expiry_year')
    def validate_year(cls, v):
        if v and v < datetime.now().year:
            raise ValueError('Năm hết hạn không thể là quá khứ')
        return v

class PaymentMethodRead(BaseModel):
    id: int
    type: PaymentMethodType
    
    # Masked/safe fields only
    card_number: Optional[str] = None  # Last 4 digits only
    card_holder_name: Optional[str] = None
    paypal_email: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    
    is_default: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentMethodUpdate(BaseModel):
    card_holder_name: Optional[str] = None
    paypal_email: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

# Payment Schemes
class PaymentCreate(BaseModel):
    order_id: int
    payment_method_id: Optional[int] = None
    amount: float
    currency: str = "VND"
    notes: Optional[str] = None

class PaymentRead(BaseModel):
    id: int
    order_id: int
    amount: float
    currency: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    gateway_response: Optional[str] = None
    failure_reason: Optional[str] = None
    notes: Optional[str] = None

# Refund Schemes
class RefundRequestCreate(BaseModel):
    payment_id: int
    amount: float
    reason: str

class RefundRequestRead(BaseModel):
    id: int
    payment_id: int
    amount: float
    reason: str
    status: str
    admin_note: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RefundRequestUpdate(BaseModel):
    status: str
    admin_note: Optional[str] = None

# Payment Processing
class ProcessPaymentRequest(BaseModel):
    payment_method_id: Optional[int] = None
    save_payment_method: bool = False
    
    # For new payment methods
    new_payment_method: Optional[PaymentMethodCreate] = None

class PaymentResponse(BaseModel):
    success: bool
    payment_id: int
    transaction_id: Optional[str] = None
    status: str  # Use string to avoid enum serialization issues
    amount: Optional[float] = None  # Payment amount
    message: str
    redirect_url: Optional[str] = None  # For external payment gateways 