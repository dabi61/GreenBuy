from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

class CategoryRead(CategoryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
