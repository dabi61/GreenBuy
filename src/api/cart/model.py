from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.user.model import User
    from api.attribute.model import Attribute

class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    cart_id: int = Field(foreign_key="cart.id")
    attribute_id: int = Field(foreign_key="attribute.attribute_id")
    quantity: int = Field(default=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔁 Relationships
    cart: Optional["Cart"] = Relationship(back_populates="items")
    attribute: Optional["Attribute"] = Relationship(back_populates="cart_items")


class Cart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # 🔁 Relationships
    user: Optional["User"] = Relationship(back_populates="cart")
    items: List["CartItem"] = Relationship(back_populates="cart")
