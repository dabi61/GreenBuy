from typing import Annotated, List, Callable, Any
from fastapi import Depends, HTTPException, status
from functools import wraps
from api.auth.dependency import get_current_user
from api.user.model import User, UserRole
import inspect

# Dependency để kiểm tra role cụ thể
def require_role(required_roles: UserRole | List[UserRole]):
    """
    Dependency để kiểm tra user có role yêu cầu không
    
    Args:
        required_roles: Role hoặc list các role được phép
    """
    if isinstance(required_roles, UserRole):
        required_roles = [required_roles]
    
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
            )
        return current_user
    
    return role_checker

# Các dependency shortcuts cho từng role
def require_seller(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency yêu cầu role seller"""
    if current_user.role != UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Seller role required."
        )
    return current_user

def require_approver(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency yêu cầu role approver"""
    if current_user.role != UserRole.approve:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Approver role required."
        )
    return current_user

def require_seller_or_approver(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency yêu cầu role seller hoặc approver"""
    if current_user.role not in [UserRole.seller, UserRole.approve]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Seller or Approver role required."
        )
    return current_user

def require_admin(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency yêu cầu role admin"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user

def require_admin_or_approver(current_user: Annotated[User, Depends(get_current_user)]):
    """Dependency yêu cầu role admin hoặc approver"""
    if current_user.role not in [UserRole.admin, UserRole.approve]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or Approver role required."
        )
    return current_user

# Kiểm tra ownership của resource
def require_owner_or_approver(resource_user_id: int):
    """
    Dependency để kiểm tra user là chủ sở hữu resource hoặc có quyền approver
    
    Args:
        resource_user_id: ID của user sở hữu resource
    """
    def owner_checker(current_user: Annotated[User, Depends(get_current_user)]):
        if current_user.id != resource_user_id and current_user.role != UserRole.approve:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own resources or you need approver role."
            )
        return current_user
    
    return owner_checker

# Decorator cho permission checking
def permission_required(required_roles: UserRole | List[UserRole]):
    """
    Decorator để kiểm tra permission cho route handler
    
    Args:
        required_roles: Role hoặc list các role được phép
    """
    if isinstance(required_roles, UserRole):
        required_roles = [required_roles]
        
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Lấy signature của function để tìm parameter current_user
        sig = inspect.signature(func)
        has_current_user = any(
            param.annotation == Annotated[User, Depends(get_current_user)] or 
            str(param.annotation).startswith("typing.Annotated[api.user.model.User")
            for param in sig.parameters.values()
        )
        
        if not has_current_user:
            # Nếu function chưa có current_user parameter, thêm dependency
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Inject current_user dependency
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if current_user.role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
                    )
                
                return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Inject current_user dependency  
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if current_user.role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
                    )
                
                return func(*args, **kwargs)
            
            # Kiểm tra xem function có phải async không
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        else:
            # Nếu đã có current_user parameter, chỉ cần check permission
            @wraps(func)
            async def async_wrapper_with_user(*args, **kwargs):
                current_user = None
                # Tìm current_user trong kwargs hoặc args
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        current_user = value
                        break
                
                if not current_user:
                    # Tìm trong args theo signature
                    for i, param in enumerate(sig.parameters.values()):
                        if (param.annotation == Annotated[User, Depends(get_current_user)] or 
                            str(param.annotation).startswith("typing.Annotated[api.user.model.User")) and i < len(args):
                            current_user = args[i]
                            break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if current_user.role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
                    )
                
                return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper_with_user(*args, **kwargs):
                current_user = None
                # Tìm current_user trong kwargs hoặc args
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        current_user = value
                        break
                
                if not current_user:
                    # Tìm trong args theo signature
                    for i, param in enumerate(sig.parameters.values()):
                        if (param.annotation == Annotated[User, Depends(get_current_user)] or 
                            str(param.annotation).startswith("typing.Annotated[api.user.model.User")) and i < len(args):
                            current_user = args[i]
                            break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if current_user.role not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
                    )
                
                return func(*args, **kwargs)
            
            if inspect.iscoroutinefunction(func):
                return async_wrapper_with_user
            else:
                return sync_wrapper_with_user
    
    return decorator

# Hàm tiện ích để kiểm tra ownership
def check_resource_ownership(current_user: User, resource_user_id: int) -> bool:
    """
    Kiểm tra user có quyền truy cập resource không
    
    Args:
        current_user: User hiện tại
        resource_user_id: ID của user sở hữu resource
        
    Returns:
        True nếu có quyền truy cập, False nếu không
    """
    # Owner luôn có quyền truy cập
    if current_user.id == resource_user_id:
        return True
    
    # Admin có quyền truy cập tất cả
    if current_user.role == UserRole.admin:
        return True
    
    # Approver có quyền truy cập tất cả
    if current_user.role == UserRole.approve:
        return True
    
    return False

def ensure_resource_access(current_user: User, resource_user_id: int, resource_name: str = "resource"):
    """
    Đảm bảo user có quyền truy cập resource, raise exception nếu không
    
    Args:
        current_user: User hiện tại
        resource_user_id: ID của user sở hữu resource
        resource_name: Tên resource để hiển thị trong error message
    """
    if not check_resource_ownership(current_user, resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. You don't have permission to access this {resource_name}."
        ) 