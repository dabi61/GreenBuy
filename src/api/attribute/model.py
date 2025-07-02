from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.product.model import Product
    from api.cart.model import CartItem

class Attribute(SQLModel, table=True):
    attribute_id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.product_id")

    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    image: Optional[str] = None
    quantity: int = Field(default=1)
    create_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships using TYPE_CHECKING
    product: Optional["Product"] = Relationship(back_populates="attributes")
    cart_items: List["CartItem"] = Relationship(back_populates="attribute") 