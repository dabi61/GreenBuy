from fastapi import APIRouter, Depends, HTTPException, status
from typing import  Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from api.user.utils import getUserFromDb
from api.auth.auth_utils import hash_password, oauth_scheme
from .model import RegisterUser, User, UpdateUser
import re
from api.db.config import DATABASE_URL
from .model import (
    get_utc_now
    )


router = APIRouter()
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,30}$"

@router.post("/register")
async def register_user(
    new_user: Annotated[RegisterUser, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    # Validate username
    if not re.match(USERNAME_REGEX, new_user.username):
        raise HTTPException(
            status_code=422,
            detail="Tên tài khoản không hợp lệ. Chỉ cho phép chữ, số, gạch dưới và 3-30 ký tự."
        )

    # Validate email
    if not re.match(EMAIL_REGEX, new_user.email):
        raise HTTPException(
            status_code=422,
            detail="Email không đúng định dạng."
        )

    # Validate password
    if len(new_user.password) < 6:
        raise HTTPException(
            status_code=422,
            detail="Mật khẩu phải có ít nhất 6 ký tự."
        )

    # Check trùng username hoặc email
    statement = select(User).where(
        (User.username == new_user.username) | (User.email == new_user.email)
    )
    existing_user = session.exec(statement).first()

    if existing_user:
        if existing_user.username == new_user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên tài khoản đã tồn tại!"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng!"
            )

    # Tạo user
    user = User(
        username=new_user.username,
        email=new_user.email,
        password_hash=hash_password(new_user.password)  # Fix: Use correct field name
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"message": f"Tài khoản '{user.username}' đăng ký thành công!"}

@router.post("/admin/register")
async def register_admin_user(
    new_user: Annotated[RegisterUser, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    """Tạo tài khoản admin - chỉ dành cho development/setup"""
    
    # Validate username
    if not re.match(USERNAME_REGEX, new_user.username):
        raise HTTPException(
            status_code=422,
            detail="Tên tài khoản không hợp lệ. Chỉ cho phép chữ, số, gạch dưới và 3-30 ký tự."
        )

    # Validate email
    if not re.match(EMAIL_REGEX, new_user.email):
        raise HTTPException(
            status_code=422,
            detail="Email không đúng định dạng."
        )

    # Validate password
    if len(new_user.password) < 6:
        raise HTTPException(
            status_code=422,
            detail="Mật khẩu phải có ít nhất 6 ký tự."
        )

    # Check trùng username hoặc email
    statement = select(User).where(
        (User.username == new_user.username) | (User.email == new_user.email)
    )
    existing_user = session.exec(statement).first()

    if existing_user:
        if existing_user.username == new_user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên tài khoản đã tồn tại!"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng!"
            )

    # Tạo admin user
    from .model import UserRole
    admin_user = User(
        username=new_user.username,
        email=new_user.email,
        password_hash=hash_password(new_user.password),
        role=UserRole.admin,  # Set role as admin
        is_verified=True  # Admin users are auto-verified
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)

    return {
        "message": f"Tài khoản admin '{admin_user.username}' đã được tạo thành công!",
        "role": "admin",
        "is_verified": True
    }