from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Product(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)

    shop_id: int = Field(foreign_key="shop.id")
    sub_category_id: int = Field(foreign_key="subcategory.id")
    approved_by: Optional[int] = Field(default=None, foreign_key="user.id")

    name: str
    description: Optional[str] = None
    cover: Optional[str] = None  # ảnh sản phẩm
    price: Optional[float] = None
    create_at: datetime = Field(default_factory=datetime.utcnow)

     # 🔁 Relationships
    shop: Optional["Shop"] = Relationship(back_populates="products")
    sub_category: Optional["SubCategory"] = Relationship(back_populates="products")
    attributes: List["Attribute"] = Relationship(back_populates="product")
    approver: Optional["User"] = Relationship(back_populates="approved_product", sa_relationship_kwargs={"uselist": False})
