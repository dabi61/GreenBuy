from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from sqlmodel import Session, select, or_
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.chat.model import ChatRoom, ChatMessage
from api.chat.scheme import ChatRoomCreate, ChatRoomRead

router = APIRouter()

# Quản lý kết nối theo room
active_connections: Dict[int, list[WebSocket]] = {}
@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int):
    await websocket.accept()

    # Lấy session
    session = next(get_session())

    # Lấy tin nhắn cũ và gửi cho client mới vào
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.room_id == room_id).order_by(ChatMessage.timestamp)
    ).all()
    for msg in messages:
        await websocket.send_json({
            "sender_id": msg.sender_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        })

    # Quản lý kết nối
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # Lưu vào DB
            new_msg = ChatMessage(
                room_id=room_id,
                sender_id=data["sender_id"],
                content=data["content"]
            )
            session.add(new_msg)
            session.commit()
            session.refresh(new_msg)

            # Gửi lại cho tất cả client trong room
            for conn in active_connections[room_id]:
                await conn.send_json({
                    "sender_id": new_msg.sender_id,
                    "content": new_msg.content,
                    "timestamp": new_msg.timestamp.isoformat(),
                })

    except WebSocketDisconnect:
        active_connections[room_id].remove(websocket)
        if not active_connections[room_id]:
            del active_connections[room_id]


# ✅ API: Lấy tất cả các phòng chat của current_user
@router.get("/rooms", response_model=List[ChatRoomRead])
def get_chat_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    rooms = session.exec(
        select(ChatRoom).where(
            or_(
                ChatRoom.user1_id == current_user.id,
                ChatRoom.user2_id == current_user.id
            )
        )
    ).all()
    return rooms

@router.post("/rooms", response_model=ChatRoomRead)
def create_chat_room(
    payload: ChatRoomCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    # Không được tạo phòng với chính mình
    if payload.user2_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create room with yourself")

    # ✅ Kiểm tra user2 có tồn tại không
    user2 = session.get(User, payload.user2_id)
    if not user2:
        raise HTTPException(status_code=404, detail="User does not exist")

    # ✅ Kiểm tra phòng đã tồn tại chưa
    statement = select(ChatRoom).where(
        ((ChatRoom.user1_id == current_user.id) & (ChatRoom.user2_id == payload.user2_id)) |
        ((ChatRoom.user1_id == payload.user2_id) & (ChatRoom.user2_id == current_user.id))
    )
    existing_room = session.exec(statement).first()
    if existing_room:
        return existing_room

    # ✅ Tạo mới
    room = ChatRoom(user1_id=current_user.id, user2_id=payload.user2_id)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room
