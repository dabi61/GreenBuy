from pydantic import BaseModel

class ChatRoomCreate(BaseModel):
    user2_id: int  # user1 là current_user

class ChatRoomRead(BaseModel):
    id: int
    user1_id: int
    user2_id: int

    class Config:
        from_attributes = True