from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi import Form

class ProductBase(BaseModel):
    shop_id: int
    sub_category_id: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None
    price: Optional[float] = None

class ProductFormCreate(BaseModel):
    name: str = Form(...)
    description: Optional[str] = Form(None)
    price: Optional[float] = Form(None)
    sub_category_id: int = Form(...)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    price: Optional[float] = None
    sub_category_id: Optional[int] = None

class ProductRead(ProductBase):
    product_id: int
    approved_by: Optional[int] = None
    create_at: datetime

    class Config:
        orm_mode = True
