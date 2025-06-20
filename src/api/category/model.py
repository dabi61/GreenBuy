from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.sub_category.model import SubCategory

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sub_categories: List["SubCategory"] = Relationship(back_populates="category")
