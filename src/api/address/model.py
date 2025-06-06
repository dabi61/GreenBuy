from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Address(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")  # assuming table name is 'user'
    country: Optional[str] = None
    city: Optional[str] = None
    phone_number: Optional[str] = None
    is_default: Optional[bool] = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional["User"] = Relationship(back_populates="addresses")
