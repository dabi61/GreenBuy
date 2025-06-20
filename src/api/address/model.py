from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from api.user.model import User

class Address(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Updated to match User table name
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    phone_number: Optional[str] = None
    is_default: Optional[bool] = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Re-enable relationship
    user: Optional["User"] = Relationship(back_populates="addresses")
