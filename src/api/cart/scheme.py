from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
from pydantic import conint

# ----- Input Schemas -----

class CartItemCreate(SQLModel):
    product_id: int
    quantity: conint(ge=1)


class UpdateCartItemQuantity(SQLModel):
    quantity: conint(ge=1)


# ----- Output Schemas -----

class CartItemRead(SQLModel):
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    price: Optional[float] = None
    cover: Optional[str] = None

    class Config:
        from_attributes = True

class CartShopGroup(SQLModel):
    shop_id: int
    shop_name: Optional[str]
    items: List[CartItemRead]


class CartRead(SQLModel):
    user_id: int
    shops: List[CartShopGroup]

class CartItemCreate(SQLModel):
    product_id: int
    quantity: int

# ----- Response Schemas -----

class CartActionResponse(SQLModel):
    message: str


class CartItemActionResponse(SQLModel):
    message: str
    product_id: int
    quantity: Optional[int] = None
