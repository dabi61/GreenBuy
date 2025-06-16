# Hệ thống Authorization cho GreenBuy

## Tổng quan

Hệ thống authorization của GreenBuy được thiết kế với các role và permission rõ ràng để đảm bảo tính bảo mật và phân quyền hợp lý.

## Các Role có sẵn

### 1. `buyer` (Người mua)
- Role mặc định khi đăng ký
- Có thể mua hàng, đặt order, chat
- Có thể thay đổi role thành `seller` hoặc `approve`

### 2. `seller` (Người bán)
- Có thể tạo shop
- Có thể tạo và quản lý sản phẩm
- Có thể xem orders của shop mình
- Không thể tự thay đổi role

### 3. `approve` (Người duyệt)
- Có thể duyệt/từ chối sản phẩm
- Có thể truy cập tất cả resource (như admin nhưng giới hạn hơn)
- Có thể xem danh sách tất cả user
- Không thể tự thay đổi role

### 4. `admin` (Quản trị viên)
- Có quyền cao nhất
- Có thể quản lý tất cả user
- Có thể thay đổi role của bất kỳ user nào
- Có thể truy cập tất cả resource

## Cách sử dụng Dependencies

### 1. Dependencies cơ bản

```python
from api.auth.permission import require_seller, require_approver, require_admin

# Yêu cầu role seller
@router.post("/create-shop")
def create_shop(current_user: Annotated[User, Depends(require_seller)]):
    pass

# Yêu cầu role approver  
@router.patch("/approve-product")
def approve_product(current_user: Annotated[User, Depends(require_approver)]):
    pass

# Yêu cầu role admin
@router.get("/admin/users")
def get_all_users(current_user: Annotated[User, Depends(require_admin)]):
    pass
```

### 2. Dependencies kết hợp

```python
from api.auth.permission import require_seller_or_approver, require_admin_or_approver

# Cho phép seller hoặc approver
@router.post("/create-product")
def create_product(current_user: Annotated[User, Depends(require_seller_or_approver)]):
    pass

# Cho phép admin hoặc approver
@router.get("/admin/stats")
def get_stats(current_user: Annotated[User, Depends(require_admin_or_approver)]):
    pass
```

### 3. Role động

```python
from api.auth.permission import require_role
from api.user.model import UserRole

# Chấp nhận nhiều role
@router.get("/special-feature")
def special_feature(
    current_user: Annotated[User, Depends(require_role([UserRole.seller, UserRole.admin]))]
):
    pass
```

## Kiểm tra quyền sở hữu Resource

### 1. Sử dụng `ensure_resource_access`

```python
from api.auth.permission import ensure_resource_access

@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    product = session.get(Product, product_id)
    shop = session.get(Shop, product.shop_id)
    
    # Kiểm tra user có quyền sửa product này không
    ensure_resource_access(current_user, shop.user_id, "product")
    
    # Logic update...
```

### 2. Sử dụng `check_resource_ownership`

```python
from api.auth.permission import check_resource_ownership

@router.get("/my-orders")
def get_my_orders(current_user: Annotated[User, Depends(get_current_user)]):
    orders = session.exec(select(Order)).all()
    
    # Filter chỉ orders mà user có quyền xem
    accessible_orders = [
        order for order in orders 
        if check_resource_ownership(current_user, order.user_id)
    ]
    
    return accessible_orders
```

## Decorator cho Permission (Tùy chọn)

```python
from api.auth.permission import permission_required
from api.user.model import UserRole

@permission_required(UserRole.seller)
@router.post("/products")
def create_product():
    # Function này sẽ tự động kiểm tra role seller
    pass

@permission_required([UserRole.admin, UserRole.approve])
@router.get("/admin/reports")
def get_reports():
    # Function này yêu cầu admin hoặc approve
    pass
```

## Endpoints Admin

### Quản lý User
- `GET /api/admin/users` - Lấy danh sách tất cả user
- `GET /api/admin/users/{user_id}` - Lấy thông tin user theo ID
- `PATCH /api/admin/users/{user_id}` - Cập nhật thông tin user
- `PATCH /api/admin/users/change-role` - Thay đổi role user
- `PATCH /api/admin/users/{user_id}/toggle-active` - Kích hoạt/vô hiệu hóa user
- `DELETE /api/admin/users/{user_id}` - Xóa user (cẩn thận!)

### Thống kê
- `GET /api/admin/stats/users` - Thống kê user theo role

### Duyệt sản phẩm
- `GET /api/product/pending-approval` - Danh sách product chờ duyệt
- `PATCH /api/product/{product_id}/approve` - Duyệt/từ chối product

## Logic phân quyền

### Thay đổi Role
1. **Buyer** → Có thể thay đổi thành `seller` hoặc `approve`
2. **Seller** → Không thể tự thay đổi role
3. **Approve** → Không thể tự thay đổi role  
4. **Admin** → Có thể thay đổi thành bất kỳ role nào

### Quyền truy cập Resource
1. **Owner** → Luôn có quyền truy cập resource của mình
2. **Admin** → Có quyền truy cập tất cả resource
3. **Approve** → Có quyền truy cập tất cả resource
4. **Khác** → Không có quyền truy cập

## Best Practices

### 1. Luôn sử dụng Dependencies thay vì kiểm tra manual

❌ **Không tốt:**
```python
def some_endpoint(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.seller:
        raise HTTPException(403, "Access denied")
```

✅ **Tốt:**
```python
def some_endpoint(current_user: Annotated[User, Depends(require_seller)]):
    # Logic here
```

### 2. Sử dụng `ensure_resource_access` cho ownership

❌ **Không tốt:**
```python
if current_user.id != resource.user_id and current_user.role != UserRole.admin:
    raise HTTPException(403, "Access denied")
```

✅ **Tốt:**
```python
ensure_resource_access(current_user, resource.user_id, "resource_name")
```

### 3. Đặt tên endpoint rõ ràng

```python
# Admin endpoints
@router.get("/admin/users")  # Rõ ràng đây là admin endpoint

# Public endpoints
@router.get("/products")     # Public

# Protected endpoints  
@router.get("/me/orders")    # User's own data
```

## Lưu ý bảo mật

1. **Luôn kiểm tra quyền** trước khi thực hiện thao tác
2. **Không tin tưởng frontend** - luôn validate ở backend
3. **Log các hành động quan trọng** (admin actions, role changes)
4. **Kiểm tra ownership** trước khi cho phép sửa/xóa
5. **Không để admin tự xóa/vô hiệu hóa chính mình**

## Ví dụ Integration

```python
# File: api/product/routing.py
from api.auth.permission import require_seller_or_approver, ensure_resource_access

@router.post("/", response_model=ProductRead)
def create_product(
    current_user: Annotated[User, Depends(require_seller_or_approver)],
    session: Session = Depends(get_session),
    # ... other params
):
    # Chỉ seller và approver mới có thể tạo product
    shop = get_user_shop(current_user.id)
    product = Product(shop_id=shop.id, ...)
    # ... logic create

@router.put("/{product_id}", response_model=ProductRead)  
def update_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    shop = session.get(Shop, product.shop_id)
    
    # Chỉ owner shop hoặc admin/approver mới được sửa
    ensure_resource_access(current_user, shop.user_id, "product")
    
    # ... logic update
``` 