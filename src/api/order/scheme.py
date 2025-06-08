from pydantic import BaseModel
from typing import List

class OrderItemCreate(BaseModel):
    product_id: int
    attribute_id: int
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemRead(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderRead(BaseModel):
    id: int
    total_price: float
    items: List[OrderItemRead]

class OrderUpdate(BaseModel):
    items: List[OrderItemCreate]
