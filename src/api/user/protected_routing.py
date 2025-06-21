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
    return {"user": current_user}

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlmodel import Session, select
from typing import Annotated
from datetime import datetime
import os

@router.put("/me", response_model=UserUpdateResponse)  # hoặc một Pydantic schema nhẹ hơn nếu muốn
async def update_info(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),

    # File avatar (tuỳ chọn)
    avatar: UploadFile = File(None),

    # Các field cập nhật khác (tuỳ chọn, có thể mở rộng thêm tuỳ ý)
    first_name: str = Form(None),
    last_name: str = Form(None),
    phone_number: str = Form(None),
    birth_of_date: str = Form(None),  # truyền string, sẽ convert sang datetime
):
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
    if birth_of_date:
        try:
            user.birth_of_date = datetime.fromisoformat(birth_of_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid birth_of_date format (must be ISO 8601)")

    session.commit()
    session.refresh(user)
    return user



@router.patch("/me/change-role", response_model=User)
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
    return user

