from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Dict, List, Annotated, Optional
from sqlmodel import Session, select, or_, and_, func, desc
from api.auth.dependency import get_current_user
from api.db.session import get_session
from api.user.model import User
from api.chat.model import ChatRoom, ChatMessage, OnlineStatus, MessageType, MessageStatus
from api.chat.scheme import (
    ChatRoomCreate, ChatRoomRead, ChatMessageRead, ChatMessageCreate, 
    ChatMessageUpdate, WebSocketMessage, MessageData, TypingData, 
    ReadReceiptData, UserStatusData, OnlineStatusRead
)
from api.chat.connection_manager import connection_manager
from jose import jwt, JWTError
from api.auth.constants import SECRET_KEY, ALGOGRYTHYM
from api.auth.token_blacklist import is_token_blacklisted
import json
import os
import uuid
from datetime import datetime, timedelta
import asyncio

router = APIRouter()

async def authenticate_websocket(token: str) -> Optional[User]:
    """Authenticate WebSocket connection using JWT token"""
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return None
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGOGRYTHYM])
        username: str = payload.get("sub")
        if username is None:
            return None
            
        # Get user from database
        session = next(get_session())
        from api.user.utils import getUserFromDb
        user = getUserFromDb(session, username)
        return user
    except JWTError:
        return None



@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):
    """
    Enhanced WebSocket endpoint for mobile chat
    Requires JWT token for authentication
    """
    await websocket.accept()
    
    # Authenticate user
    user = await authenticate_websocket(token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    user_id = user.id
    session = next(get_session())
    
    # Connect user through connection manager
    await connection_manager.connect_user(user_id, websocket, "mobile")
    
    # Start background tasks if not running
    await connection_manager.start_background_tasks()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                message_data = message.get("data", {})
                
                if message_type == "join_room":
                    # Join a specific chat room
                    room_id = message_data.get("room_id")
                    if room_id:
                        # Join room through connection manager
                        success = await connection_manager.join_room(user_id, room_id)
                        
                        if success:
                            
                            # Send recent messages
                            messages = session.exec(
                                select(ChatMessage)
                                .where(ChatMessage.room_id == room_id)
                                .where(ChatMessage.is_deleted == False)
                                .order_by(desc(ChatMessage.timestamp))
                                .limit(50)
                            ).all()
                            
                            for msg in reversed(messages):
                                msg_data = {
                                    "type": "message",
                                    "data": {
                                        "id": msg.id,
                                        "room_id": msg.room_id,
                                        "sender_id": msg.sender_id,
                                        "content": msg.content,
                                        "message_type": msg.type,
                                        "status": msg.status,
                                        "timestamp": msg.timestamp.isoformat(),
                                        "file_url": msg.file_url,
                                        "file_size": msg.file_size,
                                        "file_name": msg.file_name,
                                        "thumbnail_url": msg.thumbnail_url,
                                        "duration": msg.duration,
                                        "latitude": msg.latitude,
                                        "longitude": msg.longitude,
                                        "reply_to_id": msg.reply_to_id,
                                        "is_edited": msg.is_edited
                                    }
                                }
                                await websocket.send_text(json.dumps(msg_data))
                
                elif message_type == "message":
                    # Send a new message
                    room_id = message_data.get("room_id")
                    content = message_data.get("content", "")
                    msg_type = message_data.get("message_type", "text")
                    
                    if room_id and content:
                        # Verify user has access to this room
                        room = session.exec(
                            select(ChatRoom).where(
                                and_(
                                    ChatRoom.id == room_id,
                                    or_(
                                        ChatRoom.user1_id == user_id,
                                        ChatRoom.user2_id == user_id
                                    )
                                )
                            )
                        ).first()
                        
                        if room:
                            # Create new message
                            new_msg = ChatMessage(
                                room_id=room_id,
                                sender_id=user_id,
                                content=content,
                                type=MessageType(msg_type),
                                file_url=message_data.get("file_url"),
                                file_size=message_data.get("file_size"),
                                file_name=message_data.get("file_name"),
                                thumbnail_url=message_data.get("thumbnail_url"),
                                duration=message_data.get("duration"),
                                latitude=message_data.get("latitude"),
                                longitude=message_data.get("longitude"),
                                reply_to_id=message_data.get("reply_to_id")
                            )
                            session.add(new_msg)
                            session.commit()
                            session.refresh(new_msg)
                            
                            # Update room last activity
                            room.last_message_id = new_msg.id
                            room.last_activity = datetime.utcnow()
                            room.updated_at = datetime.utcnow()
                            session.commit()
                            
                            # Broadcast to all users in room
                            broadcast_data = {
                                "type": "message",
                                "data": {
                                    "id": new_msg.id,
                                    "room_id": new_msg.room_id,
                                    "sender_id": new_msg.sender_id,
                                    "content": new_msg.content,
                                    "message_type": new_msg.type,
                                    "status": new_msg.status,
                                    "timestamp": new_msg.timestamp.isoformat(),
                                    "file_url": new_msg.file_url,
                                    "file_size": new_msg.file_size,
                                    "file_name": new_msg.file_name,
                                    "thumbnail_url": new_msg.thumbnail_url,
                                    "duration": new_msg.duration,
                                    "latitude": new_msg.latitude,
                                    "longitude": new_msg.longitude,
                                    "reply_to_id": new_msg.reply_to_id,
                                    "is_edited": new_msg.is_edited
                                }
                            }
                            await connection_manager.broadcast_to_room(room_id, broadcast_data)
                
                elif message_type == "typing":
                    # Handle typing indicator
                    room_id = message_data.get("room_id")
                    is_typing = message_data.get("is_typing", False)
                    
                    if room_id:
                        await connection_manager.update_typing_status(user_id, room_id, is_typing)
                
                elif message_type == "read_receipt":
                    # Handle read receipt
                    room_id = message_data.get("room_id")
                    message_id = message_data.get("message_id")
                    
                    if room_id and message_id:
                        # Update message status to read
                        message = session.exec(
                            select(ChatMessage).where(ChatMessage.id == message_id)
                        ).first()
                        
                        if message and message.sender_id != user_id:
                            message.status = MessageStatus.read
                            session.commit()
                            
                            receipt_data = {
                                "type": "read_receipt",
                                "data": {
                                    "room_id": room_id,
                                    "message_id": message_id,
                                    "reader_id": user_id
                                }
                            }
                            await connection_manager.broadcast_to_room(room_id, receipt_data, exclude_user_id=user_id)
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "data": {"message": str(e)}
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup on disconnect through connection manager
        await connection_manager.disconnect_user(user_id)

# REST API Endpoints

@router.get("/rooms", response_model=List[ChatRoomRead])
def get_chat_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """Get all chat rooms for current user with enhanced info for mobile"""
    rooms = session.exec(
        select(ChatRoom).where(
            or_(
                ChatRoom.user1_id == current_user.id,
                ChatRoom.user2_id == current_user.id
            )
        ).order_by(desc(ChatRoom.last_activity))
    ).all()
    
    enhanced_rooms = []
    for room in rooms:
        # Get other user info
        other_user_id = room.user2_id if room.user1_id == current_user.id else room.user1_id
        other_user = session.get(User, other_user_id)
        
        # Get online status
        online_status = session.exec(
            select(OnlineStatus).where(OnlineStatus.user_id == other_user_id)
        ).first()
        
        # Get last message
        last_message = None
        if room.last_message_id:
            last_msg = session.get(ChatMessage, room.last_message_id)
            if last_msg and not last_msg.is_deleted:
                last_message = ChatMessageRead.from_orm(last_msg)
        
        # Count unread messages
        unread_count = session.exec(
            select(func.count(ChatMessage.id)).where(
                and_(
                    ChatMessage.room_id == room.id,
                    ChatMessage.sender_id != current_user.id,
                    ChatMessage.status != MessageStatus.read,
                    ChatMessage.is_deleted == False
                )
            )
        ).first()
        
        room_data = ChatRoomRead(
            id=room.id,
            user1_id=room.user1_id,
            user2_id=room.user2_id,
            created_at=room.created_at,
            updated_at=room.updated_at,
            is_active=room.is_active,
            last_message_id=room.last_message_id,
            last_activity=room.last_activity,
            other_user_name=f"{other_user.first_name or ''} {other_user.last_name or ''}".strip() or other_user.username,
            other_user_avatar=other_user.avatar,
            other_user_online=online_status.is_online if online_status else False,
            unread_count=unread_count or 0,
            last_message=last_message
        )
        enhanced_rooms.append(room_data)
    
    return enhanced_rooms

@router.post("/rooms", response_model=ChatRoomRead)
def create_chat_room(
    payload: ChatRoomCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """Create a new chat room"""
    if payload.user2_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create room with yourself")

    user2 = session.get(User, payload.user2_id)
    if not user2:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Check if room already exists
    existing_room = session.exec(
        select(ChatRoom).where(
            or_(
                and_(ChatRoom.user1_id == current_user.id, ChatRoom.user2_id == payload.user2_id),
                and_(ChatRoom.user1_id == payload.user2_id, ChatRoom.user2_id == current_user.id)
            )
        )
    ).first()
    
    if existing_room:
        return existing_room

    room = ChatRoom(user1_id=current_user.id, user2_id=payload.user2_id)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room

@router.get("/rooms/{room_id}/messages", response_model=List[ChatMessageRead])
def get_room_messages(
    room_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get messages for a specific room with pagination"""
    # Verify user has access to this room
    room = session.exec(
        select(ChatRoom).where(
            and_(
                ChatRoom.id == room_id,
                or_(
                    ChatRoom.user1_id == current_user.id,
                    ChatRoom.user2_id == current_user.id
                )
            )
        )
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or access denied")
    
    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.room_id == room_id)
        .where(ChatMessage.is_deleted == False)
        .order_by(desc(ChatMessage.timestamp))
        .offset(offset)
        .limit(limit)
    ).all()
    
    return [ChatMessageRead.from_orm(msg) for msg in reversed(messages)]

@router.post("/upload")
async def upload_file(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    type: str = Form("file")  # file, image, voice
):
    """Upload file for chat (image, voice, document)"""
    
    # Validate file type and size
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    # Create directory based on type
    upload_dir = f"static/chat/{type}s"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = f"{upload_dir}/{unique_filename}"
    
    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    file_url = f"/{file_path}"
    
    # Generate thumbnail for images
    thumbnail_url = None
    if type == "image":
        # TODO: Implement thumbnail generation
        thumbnail_url = file_url  # For now, same as original
    
    return {
        "file_url": file_url,
        "file_name": file.filename,
        "file_size": len(content),
        "thumbnail_url": thumbnail_url
    }

@router.patch("/messages/{message_id}")
def update_message(
    message_id: int,
    update_data: ChatMessageUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """Edit or update message status"""
    message = session.exec(
        select(ChatMessage).where(ChatMessage.id == message_id)
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender can edit content, anyone can update status
    if update_data.content is not None:
        if message.sender_id != current_user.id:
            raise HTTPException(status_code=403, detail="Can only edit your own messages")
        
        message.content = update_data.content
        message.is_edited = True
        message.edited_at = datetime.utcnow()
    
    if update_data.status is not None:
        message.status = update_data.status
    
    session.commit()
    return {"message": "Message updated successfully"}

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """Delete a message (soft delete)"""
    message = session.exec(
        select(ChatMessage).where(ChatMessage.id == message_id)
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own messages")
    
    message.is_deleted = True
    message.deleted_at = datetime.utcnow()
    session.commit()
    
    return {"message": "Message deleted successfully"}

@router.get("/online-status/{user_id}", response_model=OnlineStatusRead)
def get_user_online_status(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """Get online status of a specific user"""
    status = session.exec(
        select(OnlineStatus).where(OnlineStatus.user_id == user_id)
    ).first()
    
    if not status:
        # Return default offline status
        return OnlineStatusRead(
            user_id=user_id,
            is_online=False,
            last_seen=datetime.utcnow() - timedelta(days=1),
            device_info=None
        )
    
    return OnlineStatusRead.from_orm(status)
