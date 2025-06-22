from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from pydantic import BaseModel

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from api.address.model import Address
    from api.cart.model import Cart
    from api.shop.model import Shop
    from api.product.model import Product
    from api.payment.model import PaymentMethod
    from api.order.model import Order

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

class UserRole(str, Enum):
    buyer = "buyer"
    seller = "seller"
    moderator = "moderator"  # Changed from "approve" to match database enum
    admin = "admin"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: int = Field(default=None, primary_key=True)
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    password_hash: str  # Fix: Match database schema
    birth_date: Optional[datetime] = None  # Fix: Match database schema
    phone_number: Optional[str] = None
    bio: Optional[str] = None  # Add missing field
    is_active: bool = Field(default=True)  # Required field
    is_online: bool = Field(default=False)  # Required field
    is_verified: bool = Field(default=False)  # Required field
    last_login: Optional[datetime] = None  # Add missing field
    role: UserRole = Field(default=UserRole.buyer)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Required field
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Required field
    failed_login_attempts: int = Field(default=0)  # Required field
    locked_until: Optional[datetime] = None  # Add missing field
    password_changed_at: Optional[datetime] = None  # Add missing field
    email_verification_token: Optional[str] = None  # Add missing field
    email_verified_at: Optional[datetime] = None  # Add missing field
    password_reset_token: Optional[str] = None  # Add missing field
    password_reset_expires: Optional[datetime] = None  # Add missing field
    
    # Re-enable all relationships
    addresses: List["Address"] = Relationship(back_populates="user")
    approved_products: List["Product"] = Relationship(
        back_populates="approver",
        sa_relationship_kwargs={"foreign_keys": "Product.approver_id"}
    )
    cart: Optional["Cart"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})
    shop: Optional["Shop"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False}) 
    
    # Payment relationships
    payment_methods: List["PaymentMethod"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")

# Pydantic model for user registration and updates
class UserCreate(BaseModel):
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    password: str  # Keep as password in the API, will be hashed
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    role: UserRole = UserRole.buyer

class UserUpdate(BaseModel):
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None

class UserRead(BaseModel):
    id: int
    avatar: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    role: UserRole
    created_at: datetime  # Fix: Match database schema

class UserUpdateResponse(BaseModel):
    avatar: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    birth_date: Optional[datetime]

    class Config:
        from_attributes = True

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str

class RoleChangeRequest(BaseModel):
    new_role: UserRole  # seller hoặc moderator

class UpdateUser(SQLModel):
    id: int
    avatar: str
    first_name: str
    last_name: str
    email: str
    birth_date: datetime
    phone_number: str

# =========================
# FOLLOW MODELS
# =========================

class UserFollow(SQLModel, table=True):
    """Model cho việc user theo dõi user khác"""
    __tablename__ = "user_follows"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="users.id")  # Người theo dõi
    following_id: int = Field(foreign_key="users.id")  # Người được theo dõi
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    follower: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UserFollow.follower_id"}
    )
    following: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UserFollow.following_id"}
    )

class ShopFollow(SQLModel, table=True):
    """Model cho việc user theo dõi shop"""
    __tablename__ = "shop_follows"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Người theo dõi
    shop_id: int = Field(foreign_key="shop.id")  # Shop được theo dõi
    created_at: datetime = Field(default_factory=datetime.utcnow)

# =========================
# RATING MODELS
# =========================

class UserRating(SQLModel, table=True):
    """Model cho việc đánh giá user"""
    __tablename__ = "user_ratings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rater_id: int = Field(foreign_key="users.id")  # Người đánh giá
    rated_user_id: int = Field(foreign_key="users.id")  # Người được đánh giá
    rating: int = Field(ge=1, le=5)  # Điểm từ 1-5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    rater: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UserRating.rater_id"}
    )
    rated_user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UserRating.rated_user_id"}
    )

class ShopRating(SQLModel, table=True):
    """Model cho việc đánh giá shop"""
    __tablename__ = "shop_ratings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # Người đánh giá
    shop_id: int = Field(foreign_key="shop.id")  # Shop được đánh giá
    rating: int = Field(ge=1, le=5)  # Điểm từ 1-5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# =========================
# PYDANTIC SCHEMAS
# =========================

class FollowUserRequest(BaseModel):
    """Schema cho việc follow user"""
    following_id: int

class FollowShopRequest(BaseModel):
    """Schema cho việc follow shop"""
    shop_id: int

class RateUserRequest(BaseModel):
    """Schema cho việc đánh giá user"""
    rated_user_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class RateShopRequest(BaseModel):
    """Schema cho việc đánh giá shop"""
    shop_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class UserFollowResponse(BaseModel):
    """Response cho user follow"""
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
    
    # User info
    follower_username: Optional[str] = None
    following_username: Optional[str] = None

class ShopFollowResponse(BaseModel):
    """Response cho shop follow"""
    id: int
    user_id: int
    shop_id: int
    created_at: datetime
    
    # Shop info
    shop_name: Optional[str] = None

class UserRatingResponse(BaseModel):
    """Response cho user rating"""
    id: int
    rater_id: int
    rated_user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # User info
    rater_username: Optional[str] = None
    rated_user_username: Optional[str] = None

class ShopRatingResponse(BaseModel):
    """Response cho shop rating"""
    id: int
    user_id: int
    shop_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Additional info
    user_username: Optional[str] = None
    shop_name: Optional[str] = None

class FollowStatsResponse(BaseModel):
    """Thống kê follow của user"""
    followers_count: int
    following_count: int
    shop_following_count: int
    my_shop_followers_count: int  # Số người follow shop của mình

class RatingStatsResponse(BaseModel):
    """Thống kê rating của user/shop"""
    total_ratings: int
    average_rating: float
    rating_breakdown: dict  # {1: 0, 2: 1, 3: 2, 4: 5, 5: 10}