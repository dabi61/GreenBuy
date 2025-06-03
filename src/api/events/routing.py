from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from api.db.session import get_session
import os
from api.db.config import DATABASE_URL




from .model import (
    EventModel,
    EventListScheme,
    EventCreateSchema,
    EventUploadSchema,
    get_utc_now
    )
router = APIRouter()
# GET DATA HERE
#List View
@router.get("/", response_model=EventListScheme)
def read_events(session: Session = Depends(get_session)):
    query = select(EventModel).order_by(EventModel.update_at.desc()).limit(10)
    results = session.exec(query).all()
    return {
        "results": results,
        "count": len(results)
    }

# SEND DATA HERE
# Create View
# POST /api/events
@router.post("/", response_model=EventModel)
def create_event(
    payload: EventCreateSchema,
    session: Session = Depends(get_session)):
    data = payload.model_dump() #payload -> dict -> pydantic
    obj = EventModel.model_validate(data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get("/{event_id}", response_model=EventModel)
def get_event(event_id: int, session: Session = Depends(get_session)):
    query = select(EventModel).where(EventModel.id == event_id)
    results = session.exec(query).first()
    if not results:
        raise HTTPException(status_code=404, detail="Event Not Found")
    # a single row
    return results

@router.delete("{event_id}", response_model=EventModel)
def delete_event(event_id: int, session: Session = Depends(get_session)):
    query = select(EventModel).where(EventModel.id == event_id)
    results = session.exec(query).first()
    if not results:
        raise HTTPException(status_code=404, detail="Event Not Found")
    # a single row
    session.delete(results) #Delete
    session.commit() #commit
    return results



@router.put("/{event_id}", response_model=EventModel)
def update_event(
    event_id: int,
    payload: EventUploadSchema,
    session: Session = Depends(get_session)):
    query = select(EventModel).where(EventModel.id == event_id)
    obj = session.exec(query).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Event Not Found")

    data = payload.model_dump()
    for k, v in data.items():
        # if k == 'id':  #Mo len de tranh cap nhat field id Nhung minh thiet ke payload kia thi khong can thiet
        #     continue
        setattr(obj, k, v)
    obj.update_at = get_utc_now()
        # obj.create_at =

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

