from fastapi import APIRouter, Depends, HTTPException, status
from typing import  Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from api.user.utils import getUserFromDb
from api.auth.auth_utils import hash_password, oauth_scheme
from .model import RegisterUser, User, UpdateUser
import os
from api.db.config import DATABASE_URL




from .model import (
    get_utc_now
    )


router = APIRouter()

@router.post("/register")
async def register_user(
    new_user: Annotated[RegisterUser, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    # Kiểm tra tồn tại username hoặc email
    statement = select(User).where(
        (User.username == new_user.username)
    )
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên tài khoản đã tồn tại rồi!."
        )

    # Nếu không có thì tiếp tục đăng ký
    user = User(
        username=new_user.username,
        email=new_user.email,
        password=hash_password(new_user.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"message": f"Tài khoản '{user.username}' đăng ký thành công!"}

