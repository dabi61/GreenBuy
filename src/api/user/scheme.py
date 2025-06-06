from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field
from typing import Annotated
from datetime import datetime
from fastapi import Form

class UserRead(SQLModel):
    id: int
    avatar: str
    first_name: str
    last_name: str
    username: str
    is_active: bool
    email: str
    birth_of_date: datetime
    phone_number: str
    create_at: datetime





#Field(foreign_key="user.id")
class RegisterUser(BaseModel):
    username: Annotated[
        str,
        Form(),
    ]
    email: Annotated[
        str,
        Form(),
    ]
    password: Annotated[
        str,
        Form(),
    ]

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    username: str

class RefreshTokenData(BaseModel):
    email: str

class RefreshRequest(BaseModel):
    old_refresh_data: str