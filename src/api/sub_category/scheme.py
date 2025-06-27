from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubCategoryCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None

class SubCategoryUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

class SubCategoryRead(SubCategoryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
