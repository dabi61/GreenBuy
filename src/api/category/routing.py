from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from api.category.model import Category
from api.category.scheme import CategoryCreate, CategoryUpdate, CategoryRead
from api.auth.auth import get_session
from api.sub_category.scheme import SubCategoryRead
from api.sub_category.model import SubCategory

router = APIRouter()

@router.post("", response_model=CategoryRead)
def create_category(payload: CategoryCreate, session: Session = Depends(get_session)):
    category = Category(**payload.dict())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.get("", response_model=List[CategoryRead])
def list_categories(session: Session = Depends(get_session)):
    return session.exec(select(Category)).all()

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(category, key, value)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
    return {"detail": "Category deleted"}


@router.get("/{category_id}/subcategories", response_model=List[SubCategoryRead])
def get_subcategories_by_category(
    category_id: int,
    session: Session = Depends(get_session),
):
    subcategories = session.exec(
        select(SubCategory).where(SubCategory.category_id == category_id)
    ).all()

    if not subcategories:
        raise HTTPException(status_code=404, detail="No subcategories found for this category.")

    return subcategories