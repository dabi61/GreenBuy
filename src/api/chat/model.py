from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class ChatRoom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user1_id: int = Field(foreign_key="user.id")
    user2_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List["ChatMessage"] = Relationship(back_populates="room")

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="chatroom.id")
    sender_id: int = Field(foreign_key="user.id")
    content: str
    type: str = Field(default="text")  # "text" hoặc "image"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    room: Optional["ChatRoom"] = Relationship(back_populates="messages")