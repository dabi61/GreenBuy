from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

class Shop(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")  # Khóa ngoại đến bảng User

    avatar: Optional[str] = None
    name: str
    phone_number: Optional[str] = None

    is_active: Optional[bool] = True
    is_online: Optional[bool] = False

    create_at: datetime = Field(default_factory=datetime.utcnow)

    # Nếu bạn muốn truy xuất user ngược lại
    user: Optional["User"] = Relationship(back_populates="shop")
    products: List["Product"] = Relationship(back_populates="shop")
