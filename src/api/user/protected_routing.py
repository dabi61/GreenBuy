from fastapi import APIRouter, Depends
from typing import Annotated
from api.user.model import User, UserUpdateResponse
from api.auth.dependency import get_current_user, get_session
from api.user.model import UpdateUser, RoleChangeRequest, UserRole
from fastapi import HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select

router = APIRouter()

@router.get("/me")
async def user_profile(current_user: Annotated[User, Depends(get_current_user)]):
    """Lấy thông tin profile của user hiện tại"""
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "avatar": current_user.avatar,
            "phone_number": current_user.phone_number,
            "birth_date": current_user.birth_date.isoformat() if current_user.birth_date else None,
            "bio": current_user.bio,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_online": current_user.is_online,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
    }

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlmodel import Session, select
from typing import Annotated
from datetime import datetime
import os

@router.put("/me", response_model=UserUpdateResponse)
async def update_info(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),

    # File avatar (tuỳ chọn)
    avatar: UploadFile = File(None),

    # Các field cập nhật khác (tuỳ chọn)
    first_name: str = Form(None),
    last_name: str = Form(None),
    phone_number: str = Form(None),
    birth_date: str = Form(None),  # Format: YYYY-MM-DD hoặc YYYY-MM-DDTHH:MM:SS
):
    """
    Cập nhật thông tin user.
    
    birth_date format: 
    - YYYY-MM-DD (ví dụ: 1990-05-15)
    - YYYY-MM-DDTHH:MM:SS (ví dụ: 1990-05-15T00:00:00)
    """
    user = session.exec(select(User).where(User.id == current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- Xử lý ảnh đại diện ---
    if avatar:
        file_ext = os.path.splitext(avatar.filename)[1]
        filename = f"{user.id}_avatar{file_ext}"
        save_path = f"static/avatars/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await avatar.read())

        user.avatar = f"/static/avatars/{filename}"

    # --- Cập nhật các trường còn lại nếu có ---
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if phone_number is not None:
        user.phone_number = phone_number
    if birth_date:
        try:
            # Hỗ trợ multiple formats
            if 'T' in birth_date:
                # Full ISO format: 1990-05-15T00:00:00
                user.birth_date = datetime.fromisoformat(birth_date)
            else:
                # Date only format: 1990-05-15
                user.birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid birth_date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
            )

    session.commit()
    session.refresh(user)
    return user



@router.patch("/me/change-role")
def change_user_role(
    request: RoleChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    # Logic phân quyền thay đổi role
    if current_user.role == UserRole.buyer:
        # Buyer chỉ có thể đổi thành seller hoặc approve
        if request.new_role not in [UserRole.seller, UserRole.moderator]:
            raise HTTPException(status_code=400, detail="Buyer can only change to 'seller' or 'moderator'.")
    elif current_user.role == UserRole.admin:
        # Admin có thể đổi thành bất kỳ role nào
        pass
    else:
        # Seller và approver không thể tự đổi role
        raise HTTPException(status_code=400, detail="You cannot change your current role.")

    user = session.exec(select(User).where(User.id == current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = request.new_role
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar": user.avatar,
            "phone_number": user.phone_number,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "bio": user.bio,
            "role": user.role,
            "is_active": user.is_active,
            "is_online": user.is_online,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    }

