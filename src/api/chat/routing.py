from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from sqlmodel import Session, select
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.chat.model import ChatRoom
from api.chat.scheme import ChatRoomCreate, ChatRoomRead

router = APIRouter()

# Quản lý kết nối theo room
active_connections: Dict[int, list[WebSocket]] = {}

@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int):
    await websocket.accept()
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # data: {"sender_id":..., "content":..., "type":...}
            # Broadcast tới tất cả client trong room
            for conn in active_connections[room_id]:
                await conn.send_json(data)
    except WebSocketDisconnect:
        active_connections[room_id].remove(websocket)
        if not active_connections[room_id]:
            del active_connections[room_id] 


@router.get("/chat/rooms")
async def get_rooms():
    return {"rooms": list(active_connections.keys())}


@router.post("/", response_model=ChatRoomRead)
def create_chat_room(
    payload: ChatRoomCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    # Kiểm tra đã tồn tại phòng chưa
    statement = select(ChatRoom).where(
        ((ChatRoom.user1_id == current_user.id) & (ChatRoom.user2_id == payload.user2_id)) |
        ((ChatRoom.user1_id == payload.user2_id) & (ChatRoom.user2_id == current_user.id))
    )
    existing_room = session.exec(statement).first()
    if existing_room:
        return existing_room

    # Tạo mới
    room = ChatRoom(user1_id=current_user.id, user2_id=payload.user2_id)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room
