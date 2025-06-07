import os
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from typing import List, Annotated
from sqlmodel import Session, select

from api.auth.auth import get_session
from api.auth.dependency import get_current_user
from api.user.model import User
from api.shop.model import Shop
from api.shop.scheme import ShopRead, AddressRead
from api.address.model import Address


router = APIRouter()


# Tạo shop mới cho user hiện tại
@router.post("", response_model=Shop)
async def create_shop(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),

    name: str = Form(...),
    phone_number: str = Form(...),
    is_active: bool = Form(...),
    is_online: bool = Form(...),
    avatar: UploadFile = File(...)
):
    # --- Kiểm tra đã có shop chưa ---
    existing_shop = session.exec(
        select(Shop).where(Shop.user_id == current_user.id)
    ).first()
    if existing_shop:
        raise HTTPException(status_code=400, detail="You already own a shop.")

    # --- Lưu ảnh avatar ---
    file_ext = os.path.splitext(avatar.filename)[1]
    filename = f"shop_{current_user.id}_{int(datetime.utcnow().timestamp())}{file_ext}"
    save_path = f"static/shop_avatars/{filename}"

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(await avatar.read())

    avatar_url = f"/static/shop_avatars/{filename}"

    # --- Tạo shop ---
    shop = Shop(
        user_id=current_user.id,
        name=name,
        phone_number=phone_number,
        is_active=is_active,
        is_online=is_online,
        avatar=avatar_url
    )

    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop



# Lấy thông tin shop của user hiện tại
@router.get("/me", response_model=ShopRead)
def get_my_shop(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    shop = session.exec(
        select(Shop).where(Shop.user_id == current_user.id)
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")
    return shop


# Cập nhật thông tin shop
@router.put("/me", response_model=Shop)
async def update_my_shop(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),

    # Form data
    name: str = Form(...),
    phone_number: str = Form(...),
    is_active: bool = Form(...),
    is_online: bool = Form(...),
    avatar: UploadFile = File(None)
):
    # Tìm shop của user
    shop = session.exec(select(Shop).where(Shop.user_id == current_user.id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop to update.")

    # Nếu có ảnh mới thì ghi đè
    if avatar:
        file_ext = os.path.splitext(avatar.filename)[1]
        filename = f"shop_{current_user.id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        save_path = f"static/shop_avatars/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await avatar.read())

        shop.avatar = f"/static/shop_avatars/{filename}"

    # Cập nhật các thông tin khác
    shop.name = name
    shop.phone_number = phone_number
    shop.is_active = is_active
    shop.is_online = is_online

    session.add(shop)
    session.commit()
    session.refresh(shop)

    return shop

# Lấy shop theo ID
@router.get("/{shop_id}", response_model=ShopRead)
def get_shop_by_id(
    shop_id: int,
    session: Session = Depends(get_session),
):
    shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")
    return shop


# Tuỳ chọn: Admin lấy toàn bộ danh sách shop
@router.get("", response_model=List[ShopRead])
def list_shops(
    session: Session = Depends(get_session),
):
    shops = session.exec(select(Shop)).all()
    return shops


@router.get("/{shop_id}/addresses", response_model=List[AddressRead])
def get_shop_addresses(
    shop_id: int,
    session: Session = Depends(get_session)
):
    # Tìm shop
    shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Lấy địa chỉ từ user_id của shop
    addresses = session.exec(
        select(Address).where(Address.user_id == shop.user_id)
    ).all()

    return addresses