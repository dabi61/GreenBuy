from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class ShopCreate(SQLModel):
    avatar: Optional[str] = None
    name: str
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_online: Optional[bool] = False

class ShopUpdate(SQLModel):
    avatar: Optional[str] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None

class ShopRead(SQLModel):
    id: int
    user_id: int
    avatar: Optional[str]
    name: str
    phone_number: Optional[str]
    is_active: Optional[bool]
    is_online: Optional[bool]
    create_at: datetime

    class Config:
        from_attributes = True


class AddressRead(SQLModel):
    id: int
    country: str
    city: str
    phone_number: str
    is_default: bool

    class Config:
        from_attributes = True