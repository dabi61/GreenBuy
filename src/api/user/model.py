from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field
from typing import List, Optional, Annotated
from datetime import datetime, timezone
import sqlmodel
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form


def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username:str
    email: str
    password: str


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