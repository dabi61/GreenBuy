from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from sqlmodel import Session, select
from .scheme import AddressRead, AddressCreate, AddressUpdate
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.address.model import Address
router = APIRouter()

@router.get("/addresses", response_model=List[AddressRead])
def get_all_addresses(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    addresses = session.exec(
        select(Address).where(Address.user_id == current_user.id)
    ).all()
    return addresses


@router.get("/addresses/{address_id}", response_model=AddressRead)
def get_address(
    address_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    address = session.exec(
        select(Address).where(Address.id == address_id, Address.user_id == current_user.id)
    ).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.post("/addresses", response_model=AddressRead)
def create_address(
    payload: AddressCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    address = Address(**payload.dict(), user_id=current_user.id)
    session.add(address)
    session.commit()
    session.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=AddressRead)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    address = session.exec(
        select(Address).where(Address.id == address_id, Address.user_id == current_user.id)
    ).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(address, field, value)

    session.add(address)
    session.commit()
    session.refresh(address)
    return address
