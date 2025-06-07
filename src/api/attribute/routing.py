from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List

from .model import Attribute
from .scheme import AttributeCreate, AttributeUpdate, AttributeRead
from api.auth.dependency import get_session  # session từ project của bạn

router = APIRouter()


@router.post("/", response_model=AttributeRead)
def create_attribute(attribute: AttributeCreate, session: Session = Depends(get_session)):
    new_attr = Attribute(**attribute.dict())
    session.add(new_attr)
    session.commit()
    session.refresh(new_attr)
    return new_attr


@router.get("/", response_model=List[AttributeRead])
def get_all_attributes(session: Session = Depends(get_session)):
    return session.exec(select(Attribute)).all()


@router.get("/product/{product_id}", response_model=List[AttributeRead])
def get_attributes_by_product(product_id: int, session: Session = Depends(get_session)):
    result = session.exec(select(Attribute).where(Attribute.product_id == product_id)).all()
    return result


@router.get("/{attribute_id}", response_model=AttributeRead)
def get_attribute(attribute_id: int, session: Session = Depends(get_session)):
    attr = session.get(Attribute, attribute_id)
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return attr


@router.put("/{attribute_id}", response_model=AttributeRead)
def update_attribute(attribute_id: int, payload: AttributeUpdate, session: Session = Depends(get_session)):
    attr = session.get(Attribute, attribute_id)
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(attr, key, value)

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


@router.get("/product/{product_id}", response_model=List[AttributeRead])
def get_attributes_by_product(product_id: int, session: Session = Depends(get_session)):
    attributes = session.exec(
        select(Attribute).where(Attribute.product_id == product_id)
    ).all()

    if not attributes:
        raise HTTPException(status_code=404, detail="No attributes found for this product")

    return attributes