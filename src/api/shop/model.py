from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.product.model import Product

class ShopStatus(str, Enum):
    PENDING = "pending"       # Chờ phê duyệt
    APPROVED = "approved"     # Đã phê duyệt
    REJECTED = "rejected"     # Bị từ chối
    SUSPENDED = "suspended"   # Bị tạm ngưng

class Shop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Updated to match User table name
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: ShopStatus = Field(default=ShopStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships using TYPE_CHECKING
    user: Optional["User"] = Relationship(back_populates="shop")
    products: List["Product"] = Relationship(back_populates="shop") 