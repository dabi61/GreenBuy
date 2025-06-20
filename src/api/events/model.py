# from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import sqlmodel

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

class EventModel(SQLModel, table=True):  #table= True
    id: Optional[int] = Field(default=None, primary_key=True)
    # id: int
    page: Optional[str] = None  #Optional Khong bat buoc mac dinh la chuoi rong
    descriptions: Optional[str] = None
    created_at: datetime = Field(
        default_factory=get_utc_now,  # Tu dong gan time neu time o co
        sa_type= sqlmodel.DateTime(timezone=True),
        nullable=False
    )
    update_at: datetime = Field(
        default_factory=get_utc_now,  # Tu dong gan time neu time o co
        sa_type= sqlmodel.DateTime(timezone=True),
        nullable=False
    )
    user_id: int = Field(foreign_key="users.id")  # Updated to match User table name


class EventListScheme(SQLModel):
    results: List[EventModel]
    count: int

class EventCreateSchema(SQLModel):
    path: str
    desscription: Optional[str] = Field(default="my description") #Field de hien thi ngoai scheme doc

class EventUploadSchema(SQLModel):
    descriptions: str