from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from sqlmodel import Session, select
from api.db.session import get_session
from api.user.model import User, UserRole, RoleChangeRequest
from api.auth.permission import require_admin, require_admin_or_approver
from api.auth.token_blacklist import token_blacklist, cleanup_blacklist
from pydantic import BaseModel

router = APIRouter()

class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class AdminRoleChangeRequest(BaseModel):
    user_id: int
    new_role: UserRole

@router.get("/users", response_model=list[User])
def get_all_users(
    admin_user: Annotated[User, Depends(require_admin_or_approver)],
    session: Annotated[Session, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Lấy danh sách tất cả user (chỉ admin và approver)"""
    query = select(User)
    
    # Filter theo role nếu có
    if role:
        query = query.where(User.role == role)
    
    # Filter theo trạng thái active nếu có
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Phân trang
    query = query.offset(skip).limit(limit)
    
    users = session.exec(query).all()
    return users

@router.get("/users/{user_id}", response_model=User)
def get_user_by_id(
    user_id: int,
    admin_user: Annotated[User, Depends(require_admin_or_approver)],
    session: Annotated[Session, Depends(get_session)]
):
    """Lấy thông tin user theo ID (chỉ admin và approver)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}", response_model=User)
def update_user_by_admin(
    user_id: int,
    update_data: AdminUserUpdate,
    admin_user: Annotated[User, Depends(require_admin)],
    session: Annotated[Session, Depends(get_session)]
):
    """Cập nhật thông tin user bởi admin"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cập nhật các field được gửi
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.patch("/users/change-role")
def change_user_role_by_admin(
    request: AdminRoleChangeRequest,
    admin_user: Annotated[User, Depends(require_admin)],
    session: Annotated[Session, Depends(get_session)]
):
    """Admin thay đổi role của user khác"""
    user = session.exec(select(User).where(User.id == request.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Admin có thể thay đổi role của bất kỳ user nào
    user.role = request.new_role
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar": user.avatar,
            "phone_number": user.phone_number,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "bio": user.bio,
            "role": user.role,
            "is_active": user.is_active,
            "is_online": user.is_online,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    }

@router.patch("/users/{user_id}/toggle-active", response_model=User)
def toggle_user_active_status(
    user_id: int,
    admin_user: Annotated[User, Depends(require_admin)],
    session: Annotated[Session, Depends(get_session)]
):
    """Kích hoạt/vô hiệu hóa user"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Không cho phép admin tự vô hiệu hóa chính mình
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot deactivate your own account"
        )
    
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: int,
    admin_user: Annotated[User, Depends(require_admin)],
    session: Annotated[Session, Depends(get_session)]
):
    """Xóa user (chỉ admin, cần thận trọng)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Không cho phép admin tự xóa chính mình
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot delete your own account"
        )
    
    # Kiểm tra user có dữ liệu liên quan không (shop, products, orders...)
    # TODO: Thêm logic kiểm tra foreign key constraints
    
    session.delete(user)
    session.commit()
    return {"message": f"User {user_id} has been deleted successfully"}

@router.get("/stats/users")
def get_user_statistics(
    admin_user: Annotated[User, Depends(require_admin_or_approver)],
    session: Annotated[Session, Depends(get_session)]
):
    """Thống kê số lượng user theo role"""
    stats = {}
    
    for role in UserRole:
        count = session.exec(
            select(User).where(User.role == role)
        ).all()
        stats[role.value] = len(count)
    
    # Thống kê user active/inactive
    active_users = session.exec(
        select(User).where(User.is_active == True)
    ).all()
    inactive_users = session.exec(
        select(User).where(User.is_active == False)
    ).all()
    
    stats["active_users"] = len(active_users)
    stats["inactive_users"] = len(inactive_users)
    stats["total_users"] = len(active_users) + len(inactive_users)
    
    return stats

@router.get("/stats/tokens")
def get_token_statistics(
    admin_user: Annotated[User, Depends(require_admin)],
):
    """Thống kê token blacklist"""
    return {
        "blacklisted_tokens_count": token_blacklist.get_blacklist_size(),
        "message": "Token blacklist statistics"
    }

@router.post("/cleanup/tokens")
def cleanup_token_blacklist(
    admin_user: Annotated[User, Depends(require_admin)],
):
    """Dọn dẹp token blacklist (xóa các token đã expired)"""
    old_size = token_blacklist.get_blacklist_size()
    cleanup_blacklist()
    new_size = token_blacklist.get_blacklist_size()
    
    return {
        "message": "Token blacklist cleaned up successfully",
        "tokens_removed": old_size - new_size,
        "remaining_tokens": new_size
    } 