from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel

# from api.address.model import Address


def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

class UserRole(str, Enum):
    buyer = "buyer"
    seller = "seller"
    approve = "approve"
    admin = "admin"

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username:Optional[str]
    email: str
    password: str
    birth_of_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_online: Optional[bool] = False
    role: UserRole =  Field(default=UserRole.buyer)
    create_at: datetime = Field(default_factory=datetime.utcnow)
    addresses: list["Address"] = Relationship(back_populates="user")
    approved_product: Optional["Product"] = Relationship(back_populates="approver")
    cart: Optional["Cart"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})
    shop: Optional["Shop"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False}) # Quan hệ 1-1 với Shop


class UserUpdateResponse(BaseModel):
    avatar: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    birth_of_date: Optional[datetime]

    class Config:
        orm_mode = True

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str

class RoleChangeRequest(BaseModel):
    new_role: UserRole  # seller hoặc approve




class UpdateUser(SQLModel):
    id: int
    avatar: str
    first_name: str
    last_name: str
    email: str
    birth_of_date: datetime
    phone_number: str
