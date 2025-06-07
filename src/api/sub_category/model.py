from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class SubCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="category.id")  # FK đến Category

    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    category: Optional["Category"] = Relationship(back_populates="sub_categories")
