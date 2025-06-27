import os
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from typing import List, Annotated
from sqlmodel import Session, select
from datetime import datetime
from api.auth.auth import get_session
from api.auth.dependency import get_current_user
from api.auth.permission import require_seller
from api.user.model import User
from api.shop.model import Shop
from api.shop.scheme import ShopRead, AddressRead
from api.address.model import Address


router = APIRouter()


# Tạo shop mới cho user hiện tại (chỉ seller)
@router.post("", response_model=Shop)
async def create_shop(
    current_user: Annotated[User, Depends(require_seller)],
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


@router.get("/me/stats", response_model=dict)
def get_shop_order_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Thống kê đơn hàng cho shop của user hiện tại
    - Số lượng đơn hàng chờ lấy hàng (status: 2=confirmed, 3=processing)
    - Số lượng đơn hàng đã hủy (status: 6=cancelled)
    - Số lượng phản hồi đánh giá
    """
    from sqlmodel import func, and_, or_
    from api.order.model import Order, OrderItem
    from api.user.model import ShopRating
    from api.product.model import Product
    
    # Lấy shop của user hiện tại
    shop = session.exec(
        select(Shop).where(Shop.user_id == current_user.id)
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # 1. Số lượng đơn hàng chờ lấy hàng (confirmed, processing)
    from sqlalchemy import String
    pending_pickup_count = session.exec(
        select(func.count(func.distinct(Order.id)))
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.product_id)
        .where(
            and_(
                Product.shop_id == shop.id,
                or_(
                    Order.status == 2,  # confirmed
                    Order.status == 3   # processing
                )
            )
        )
    ).one()

    # 2. Số lượng đơn hàng đã hủy (cancelled)
    cancelled_orders_count = session.exec(
        select(func.count(func.distinct(Order.id)))
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.product_id)
        .where(
            and_(
                Product.shop_id == shop.id,
                Order.status == 6  # cancelled
            )
        )
    ).one()

    # 3. Số lượng phản hồi đánh giá
    ratings_count = session.exec(
        select(func.count(ShopRating.id))
        .where(ShopRating.shop_id == shop.id)
    ).one()

    # 4. Thống kê bổ sung
    # Tổng số đơn hàng
    total_orders_count = session.exec(
        select(func.count(func.distinct(Order.id)))
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.product_id)
        .where(Product.shop_id == shop.id)
    ).one()

    # Đơn hàng đã giao thành công
    delivered_orders_count = session.exec(
        select(func.count(func.distinct(Order.id)))
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.product_id)
        .where(
            and_(
                Product.shop_id == shop.id,
                Order.status == 5  # delivered
            )
        )
    ).one()

    # Điểm đánh giá trung bình
    avg_rating = session.exec(
        select(func.avg(ShopRating.rating))
        .where(ShopRating.shop_id == shop.id)
    ).one() or 0.0

    return {
        "shop_id": shop.id,
        "shop_name": shop.name,
        "pending_pickup": pending_pickup_count,
        "cancelled_orders": cancelled_orders_count,
        "ratings_count": ratings_count,
        "total_orders": total_orders_count,
        "delivered_orders": delivered_orders_count,
        "average_rating": round(float(avg_rating), 2) if avg_rating else 0.0,
        "stats_generated_at": datetime.utcnow().isoformat()
    }