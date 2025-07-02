from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
from pydantic import conint

# ----- Input Schemas -----

class CartItemCreate(SQLModel):
    attribute_id: int
    quantity: conint(ge=1)


class UpdateCartItemQuantity(SQLModel):
    quantity: conint(ge=1)


# ----- Output Schemas -----

class CartItemRead(SQLModel):
    attribute_id: int
    quantity: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    cover: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    attribute_image: Optional[str] = None
    available_quantity: Optional[int] = None

    class Config:
        from_attributes = True

class CartShopGroup(SQLModel):
    shop_id: int
    shop_name: Optional[str]
    items: List[CartItemRead]


class CartRead(SQLModel):
    user_id: int
    shops: List[CartShopGroup]

# ----- Response Schemas -----

class CartActionResponse(SQLModel):
    message: str


class CartItemActionResponse(SQLModel):
    message: str
    attribute_id: int
    quantity: Optional[int] = None
