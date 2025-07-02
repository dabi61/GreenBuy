from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.shop.model import Shop
    from api.sub_category.model import SubCategory
    from api.user.model import User
    from api.attribute.model import Attribute
    from api.order.model import OrderItem

class Product(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)

    shop_id: int = Field(foreign_key="shop.id")
    sub_category_id: int = Field(foreign_key="subcategory.id")
    is_approved: Optional[bool] = Field(default=None)
    approval_note: Optional[str] = None
    approver_id: Optional[int] = Field(default=None, foreign_key="users.id")

    name: str
    description: Optional[str] = None
    cover: Optional[str] = None  # ảnh sản phẩm
    price: Optional[float] = None
    create_at: datetime = Field(default_factory=datetime.utcnow)

    # Re-enable all relationships
    shop: Optional["Shop"] = Relationship(back_populates="products")
    sub_category: Optional["SubCategory"] = Relationship(back_populates="products")
    approver: Optional["User"] = Relationship(
        back_populates="approved_products",
        sa_relationship_kwargs={"foreign_keys": "Product.approver_id"}
    )
    attributes: List["Attribute"] = Relationship(back_populates="product")
    order_items: List["OrderItem"] = Relationship(back_populates="product")
