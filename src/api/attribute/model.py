from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Attribute(SQLModel, table=True):
    attribute_id: Optional[int] = Field(default=None, primary_key=True)

    product_id: int = Field(foreign_key="product.product_id")  # FK liên kết tới Product

    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    image: Optional[str] = None

    create_at: datetime = Field(default_factory=datetime.utcnow)

    # Quan hệ ngược về Product
    product: Optional["Product"] = Relationship(back_populates="attributes")
