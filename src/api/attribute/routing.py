import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Annotated

from api.auth.dependency import get_session, get_current_user
from api.user.model import User
from .model import Attribute
from .scheme import AttributeRead

router = APIRouter()


@router.post("", response_model=AttributeRead)
async def create_attribute(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),

    # Form fields
    product_id: int = Form(...),
    color: str = Form(...),
    size: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    image: UploadFile = File(...)
):
    # --- Tạo folder theo product ---
    file_ext = os.path.splitext(image.filename)[1]
    folder = f"static/attribute_images/product_{product_id}"
    os.makedirs(folder, exist_ok=True)

    # --- Đặt tên file tránh trùng (UUID) ---
    filename = f"{uuid.uuid4()}{file_ext}"
    save_path = os.path.join(folder, filename)

    # --- Lưu file ảnh ---
    with open(save_path, "wb") as f:
        f.write(await image.read())

    image_url = f"/static/attribute_images/product_{product_id}/{filename}"

    # --- Tạo Attribute ---
    attribute = Attribute(
        product_id=product_id,
        color=color,
        size=size,
        price=price,
        quantity=quantity,
        image=image_url,
    )

    session.add(attribute)
    session.commit()
    session.refresh(attribute)

    return attribute


@router.get("", response_model=List[AttributeRead])
def get_all_attributes(session: Session = Depends(get_session)):
    return session.exec(select(Attribute)).all()


@router.get("/product/{product_id}", response_model=List[AttributeRead])
def get_attributes_by_product(product_id: int, session: Session = Depends(get_session)):
    attributes = session.exec(
        select(Attribute).where(Attribute.product_id == product_id)
    ).all()

    if not attributes:
        raise HTTPException(status_code=404, detail="No attributes found for this product")

    return attributes


@router.get("/{attribute_id}", response_model=AttributeRead)
def get_attribute(attribute_id: int, session: Session = Depends(get_session)):
    attr = session.get(Attribute, attribute_id)
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return attr


@router.put("/{attribute_id}", response_model=AttributeRead)
async def update_attribute(
    attribute_id: int,
    session: Session = Depends(get_session),
    product_id: int = Form(...),
    color: str = Form(...),
    size: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    image: UploadFile = File(...)
):
    attr = session.get(Attribute, attribute_id)
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Nếu có ảnh mới -> ghi đè
    if image:
        product_id = attr.product_id
        file_ext = os.path.splitext(image.filename)[1]
        folder = f"static/attribute_images/product_{product_id}"
        os.makedirs(folder, exist_ok=True)

        filename = f"{uuid.uuid4()}{file_ext}"
        save_path = os.path.join(folder, filename)

        with open(save_path, "wb") as f:
            f.write(await image.read())

        attr.image = f"/static/attribute_images/product_{product_id}/{filename}"

    # Cập nhật các thông tin còn lại
    attr.color = color
    attr.size = size
    attr.price = price
    attr.quantity = quantity

    session.add(attr)
    session.commit()
    session.refresh(attr)

    return attr


@router.delete("/{attribute_id}")
def delete_attribute(attribute_id: int, session: Session = Depends(get_session)):
    attr = session.get(Attribute, attribute_id)
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    session.delete(attr)
    session.commit()
    return {"message": "Attribute deleted successfully"}
