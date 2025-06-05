from fastapi import APIRouter, Depends, HTTPException
from typing import  Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from api.user.utils import getUserFromDb
from api.auth.auth_utils import hash_password, oauth_scheme
from .model import RegisterUser, User
import os
from api.db.config import DATABASE_URL




from .model import (
    get_utc_now
    )


router = APIRouter()

@router.get("/")
async def read_user():
    return {"message": "Wellcome to GreenBuy!"}

@router.post("/register")
async def register_user(new_user: Annotated[RegisterUser, Depends()],
                        session: Annotated[Session, Depends(get_session)]):
    db_user = getUserFromDb(session, new_user.username, new_user.email)
    if db_user:
        HTTPException(status_code=409, detail="User with these credentials already exists")
    user = User(username = new_user.username,
                email = new_user.email,
                password = hash_password(new_user.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f""" User with {user.username} successfull registed"""}


@router.get("/me")
async def user_profile(current_user: Annotated[User, Depends(oauth_scheme)]):   #Depends la gan phu thuoc, o day api nay phu thuoc vao viec xac thuc moi cho su dung
    return current_user