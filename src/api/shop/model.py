from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.product.model import Product

class Shop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Reference to users table
    name: str
    avatar: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    create_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships using TYPE_CHECKING
    user: Optional["User"] = Relationship(back_populates="shop")
    products: List["Product"] = Relationship(back_populates="shop") 