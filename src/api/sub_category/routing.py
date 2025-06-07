from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from api.sub_category.model import SubCategory
from api.sub_category.scheme import SubCategoryCreate, SubCategoryUpdate, SubCategoryRead
from api.auth.auth import get_session

router = APIRouter()

@router.post("", response_model=SubCategoryRead)
def create_sub_category(payload: SubCategoryCreate, session: Session = Depends(get_session)):
    sub = SubCategory(**payload.dict())
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub

@router.get("", response_model=List[SubCategoryRead])
def list_sub_categories(session: Session = Depends(get_session)):
    return session.exec(select(SubCategory)).all()

@router.get("/{sub_category_id}", response_model=SubCategoryRead)
def get_sub_category(sub_category_id: int, session: Session = Depends(get_session)):
    sub = session.get(SubCategory, sub_category_id)
    if not sub:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    return sub

@router.put("/{sub_category_id}", response_model=SubCategoryRead)
def update_sub_category(sub_category_id: int, payload: SubCategoryUpdate, session: Session = Depends(get_session)):
    sub = session.get(SubCategory, sub_category_id)
    if not sub:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(sub, key, value)
    session.commit()
    session.refresh(sub)
    return sub

@router.delete("/{sub_category_id}")
def delete_sub_category(sub_category_id: int, session: Session = Depends(get_session)):
    sub = session.get(SubCategory, sub_category_id)
    if not sub:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    session.delete(sub)
    session.commit()
    return {"detail": "SubCategory deleted"}

