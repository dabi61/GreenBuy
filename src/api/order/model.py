from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.product_id")
    attribute_id: int = Field(foreign_key="attribute.attribute_id")
    quantity: int
    price: float
    order: Optional["Order"] = Relationship(back_populates="items")


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_price: float

    items: List[OrderItem] = Relationship(back_populates="order")

OrderItem.order = Relationship(back_populates="items", sa_relationship_kwargs={"lazy": "selectin"})
