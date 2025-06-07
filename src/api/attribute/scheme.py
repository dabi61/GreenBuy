from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AttributeCreate(BaseModel):
    product_id: int
    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    image: Optional[str] = None

class AttributeUpdate(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None

class AttributeRead(BaseModel):
    attribute_id: int
    product_id: int
    color: Optional[str]
    size: Optional[str]
    price: float
    image: Optional[str]
    create_at: datetime

    class Config:
        orm_mode = True
