from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    voice = "voice"
    location = "location"

class MessageStatus(str, Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class ChatRoom(SQLModel, table=True):
    __tablename__ = "chat_rooms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user1_id: int = Field(foreign_key="users.id")
    user2_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    # Thêm field để track last message - không tạo relationship
    last_message_id: Optional[int] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Chỉ định rõ foreign key để tránh ambiguous
    messages: List["ChatMessage"] = Relationship(back_populates="room")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="chat_rooms.id")
    sender_id: int = Field(foreign_key="users.id")
    content: str
    type: MessageType = Field(default=MessageType.text)
    status: MessageStatus = Field(default=MessageStatus.sent)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Thêm fields cho mobile
    file_url: Optional[str] = None  # URL cho file/image/voice
    file_size: Optional[int] = None  # Kích thước file (bytes)
    file_name: Optional[str] = None  # Tên file gốc
    thumbnail_url: Optional[str] = None  # Thumbnail cho image/video
    duration: Optional[int] = None  # Thời lượng voice message (seconds)
    latitude: Optional[float] = None  # Cho location message
    longitude: Optional[float] = None  # Cho location message
    reply_to_id: Optional[int] = Field(default=None, foreign_key="chat_messages.id")  # Reply to message
    is_edited: bool = Field(default=False)
    edited_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    
    room: Optional["ChatRoom"] = Relationship(back_populates="messages")

class OnlineStatus(SQLModel, table=True):
    """Track user online status for chat"""
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    is_online: bool = Field(default=False)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    device_info: Optional[str] = None  # Device identifier for mobile
    updated_at: datetime = Field(default_factory=datetime.utcnow)