import os
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from typing import List, Annotated
from .model import Product
from .scheme import ProductRead
from api.auth.dependency import get_current_user
from api.auth.permission import require_seller_or_approver, ensure_resource_access, require_approver
from api.auth.auth import get_session
from api.shop.model import Shop
from api.user.model import User
from api.attribute.model import Attribute
from pydantic import BaseModel
import uuid


router = APIRouter()

class ProductApprovalRequest(BaseModel):
    approved: bool
    approval_note: str = None

# 📄 Read all
@router.get("/", response_model=List[ProductRead])
def get_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    return products

# 🔍 Read by ID
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductRead)
async def create_product(
    current_user: Annotated[User, Depends(require_seller_or_approver)],
    session: Session = Depends(get_session),
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(None),
    sub_category_id: int = Form(...),
    cover: UploadFile = File(None),
):

    # Lấy shop từ user
    shop = session.exec(select(Shop).where(Shop.user_id == current_user.id)).first()
    if not shop:
        raise HTTPException(404, detail="No shop found")

    # Xử lý ảnh
    image_path = None
    if cover:
        ext = os.path.splitext(cover.filename)[1]
        filename = f"product_{uuid.uuid4().hex}{ext}"
        save_path = f"static/products/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await cover.read())

        image_path = f"/static/products/{filename}"

    # Tạo product
    product = Product(
        name=name,
        description=description,
        price=price,
        sub_category_id=sub_category_id,
        shop_id=shop.id,
        cover=image_path,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    name: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    sub_category_id: int = Form(None),
    cover: UploadFile = File(None),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")

    # Kiểm tra quyền sở hữu qua shop
    shop = session.exec(select(Shop).where(Shop.id == product.shop_id)).first()
    if not shop:
        raise HTTPException(404, detail="Shop not found")
    
    # Kiểm tra user có quyền sửa product này không (owner hoặc approver)
    ensure_resource_access(current_user, shop.user_id, "product")

    # Cập nhật các trường
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if sub_category_id is not None:
        product.sub_category_id = sub_category_id

    # Cập nhật ảnh nếu có
    if cover:
        ext = os.path.splitext(cover.filename)[1]
        filename = f"product_{uuid.uuid4().hex}{ext}"
        save_path = f"static/products/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await cover.read())

        product.cover = f"/static/products/{filename}"

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.patch("/{product_id}/approve", response_model=ProductRead)
def approve_product(
    product_id: int,
    approval_request: ProductApprovalRequest,
    current_user: Annotated[User, Depends(require_approver)],
    session: Session = Depends(get_session),
):
    """Approve hoặc reject product (chỉ dành cho approver)"""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")

    # Cập nhật trạng thái approval
    product.is_approved = approval_request.approved
    product.approval_note = approval_request.approval_note
    product.approver_id = current_user.id

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.get("/pending-approval", response_model=List[ProductRead])
def get_pending_products(
    current_user: Annotated[User, Depends(require_approver)],
    session: Session = Depends(get_session),
):
    """Lấy danh sách product chưa được approve (chỉ dành cho approver)"""
    products = session.exec(
        select(Product).where(Product.is_approved == None)
    ).all()
    return products

@router.get("/shop/{shop_id}", response_model=List[ProductRead])
def get_products_by_shop(shop_id: int, session: Session = Depends(get_session)):
    shop = session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    products = session.exec(
        select(Product).where(Product.shop_id == shop_id)
    ).all()

    return products