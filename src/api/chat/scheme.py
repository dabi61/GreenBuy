from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from api.chat.model import MessageType, MessageStatus

class ChatRoomCreate(BaseModel):
    user2_id: int  # user1 là current_user

class ChatMessageRead(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: str
    type: MessageType
    status: MessageStatus
    timestamp: datetime
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reply_to_id: Optional[int] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True

class ChatRoomRead(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    last_message_id: Optional[int] = None
    last_activity: datetime
    # Thêm thông tin người chat cùng
    other_user_name: Optional[str] = None
    other_user_avatar: Optional[str] = None
    other_user_online: Optional[bool] = None
    unread_count: Optional[int] = None
    last_message: Optional[ChatMessageRead] = None

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str
    type: MessageType = MessageType.text
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reply_to_id: Optional[int] = None

class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[MessageStatus] = None

class WebSocketMessage(BaseModel):
    """Message format for WebSocket communication"""
    type: str  # 'message', 'typing', 'read_receipt', 'user_status'
    data: dict

class MessageData(BaseModel):
    """Data for message type WebSocket message"""
    room_id: int
    content: str
    message_type: MessageType = MessageType.text
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reply_to_id: Optional[int] = None

class TypingData(BaseModel):
    """Data for typing indicator"""
    room_id: int
    is_typing: bool

class ReadReceiptData(BaseModel):
    """Data for read receipt"""
    room_id: int
    message_id: int

class UserStatusData(BaseModel):
    """Data for user online status"""
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None

class OnlineStatusRead(BaseModel):
    user_id: int
    is_online: bool
    last_seen: datetime
    device_info: Optional[str] = None

    class Config:
        from_attributes = True