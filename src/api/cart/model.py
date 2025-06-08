from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    cart_id: int = Field(foreign_key="cart.id")
    product_id: int = Field(foreign_key="product.product_id")
    quantity: int = Field(default=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔁 Relationships
    cart: Optional["Cart"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="cart_items")


class Cart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # 🔁 Relationships
    user: Optional["User"] = Relationship(back_populates="cart")
    items: List["CartItem"] = Relationship(back_populates="cart")
