from sqlmodel import SQLModel
from typing import Optional

class AddressCreate(SQLModel):
    country: str
    city: str
    phone_number: str
    is_default: bool = False

class AddressUpdate(SQLModel):
    country: Optional[str]
    city: Optional[str]
    phone_number: Optional[str]
    is_default: Optional[bool]

class AddressRead(AddressCreate):
    id: int
    user_id: int
