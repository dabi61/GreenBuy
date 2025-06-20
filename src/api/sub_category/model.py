from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.category.model import Category
    from api.product.model import Product

class SubCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="category.id")  # FK đến Category

    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships using TYPE_CHECKING
    category: Optional["Category"] = Relationship(back_populates="sub_categories")
    products: List["Product"] = Relationship(back_populates="sub_category") 