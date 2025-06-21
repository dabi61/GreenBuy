from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from pydantic import BaseModel

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.address.model import Address
    from api.cart.model import Cart
    from api.shop.model import Shop
    from api.product.model import Product
    from api.payment.model import PaymentMethod
    from api.order.model import Order

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

class UserRole(str, Enum):
    buyer = "buyer"
    seller = "seller"
    moderator = "moderator"  # Changed from "approve" to match database enum
    admin = "admin"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: int = Field(default=None, primary_key=True)
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    password_hash: str  # Fix: Match database schema
    birth_date: Optional[datetime] = None  # Fix: Match database schema
    phone_number: Optional[str] = None
    bio: Optional[str] = None  # Add missing field
    is_active: bool = Field(default=True)  # Required field
    is_online: bool = Field(default=False)  # Required field
    is_verified: bool = Field(default=False)  # Required field
    last_login: Optional[datetime] = None  # Add missing field
    role: UserRole = Field(default=UserRole.buyer)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Required field
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Required field
    failed_login_attempts: int = Field(default=0)  # Required field
    locked_until: Optional[datetime] = None  # Add missing field
    password_changed_at: Optional[datetime] = None  # Add missing field
    email_verification_token: Optional[str] = None  # Add missing field
    email_verified_at: Optional[datetime] = None  # Add missing field
    password_reset_token: Optional[str] = None  # Add missing field
    password_reset_expires: Optional[datetime] = None  # Add missing field
    
    # Re-enable all relationships
    addresses: List["Address"] = Relationship(back_populates="user")
    approved_products: List["Product"] = Relationship(
        back_populates="approver",
        sa_relationship_kwargs={"foreign_keys": "Product.approver_id"}
    )
    cart: Optional["Cart"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})
    shop: Optional["Shop"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False}) 
    
    # Payment relationships
    payment_methods: List["PaymentMethod"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")

# Pydantic model for user registration and updates
class UserCreate(BaseModel):
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    password: str  # Keep as password in the API, will be hashed
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    role: UserRole = UserRole.buyer

class UserUpdate(BaseModel):
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None

class UserRead(BaseModel):
    id: int
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    role: UserRole
    created_at: datetime  # Fix: Match database schema

class UserUpdateResponse(BaseModel):
    avatar: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    birth_of_date: Optional[datetime]

    class Config:
        from_attributes = True

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str

class RoleChangeRequest(BaseModel):
    new_role: UserRole  # seller hoặc moderator

class UpdateUser(SQLModel):
    id: int
    avatar: str
    first_name: str
    last_name: str
    email: str
    birth_of_date: datetime
    phone_number: str 