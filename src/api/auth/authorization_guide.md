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

## Endpoints Admin mới

### Quản lý User
- `GET /api/admin/users` - Lấy danh sách tất cả user
- `GET /api/admin/users/{user_id}` - Lấy thông tin user theo ID
- `PATCH /api/admin/users/{user_id}` - Cập nhật thông tin user
- `PATCH /api/admin/users/change-role` - Thay đổi role user
- `PATCH /api/admin/users/{user_id}/toggle-active` - Kích hoạt/vô hiệu hóa user
- `DELETE /api/admin/users/{user_id}` - Xóa user (cẩn thận!)

### Thống kê
- `GET /api/admin/stats/users` - Thống kê user theo role

### Duyệt sản phẩm (Approver)
- `GET /api/product/pending-approval` - Danh sách product chờ duyệt
- `PATCH /api/product/{product_id}/approve` - Duyệt/từ chối product

## Files đã được bổ sung

1. `src/api/auth/permission.py` - Chứa tất cả dependencies và utilities
2. `src/api/user/admin_routing.py` - Endpoints dành cho admin
3. Cập nhật `src/api/user/model.py` - Thêm role `admin`
4. Cập nhật các routing files để áp dụng authorization

## Tóm tắt cải tiến

✅ **Đã bổ sung:**
- Role-based authorization với 4 roles: buyer, seller, approve, admin
- Dependencies để kiểm tra role: `require_seller`, `require_approver`, `require_admin`
- Kiểm tra ownership: `ensure_resource_access`, `check_resource_ownership`
- Admin panel để quản lý users
- Product approval system cho approvers
- Permission protection cho create shop (seller only)
- Permission protection cho create/update products

✅ **Bảo mật đã được cải thiện:**
- Chỉ seller mới được tạo shop
- Chỉ seller/approver mới được tạo sản phẩm
- Chỉ owner hoặc admin/approver mới được sửa sản phẩm
- Admin có quyền quản lý tất cả users
- Approver có quyền duyệt sản phẩm
- Kiểm tra ownership trước khi cho phép thao tác 