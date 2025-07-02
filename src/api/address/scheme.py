from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class AddressCreate(SQLModel):
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    phone_number: Optional[str] = None
    is_default: bool = False

class AddressUpdate(SQLModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    is_default: Optional[bool] = None

class AddressRead(SQLModel):
    id: int
    user_id: int
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    phone_number: Optional[str] = None
    is_default: Optional[bool] = False
    created_at: datetime

    class Config:
        from_attributes = True
