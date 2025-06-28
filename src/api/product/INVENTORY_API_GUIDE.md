# 📦 Hướng dẫn API Quản lý Tồn kho Sản phẩm

## Tổng quan

Hệ thống quản lý tồn kho sản phẩm cho **shop của user hiện tại** với 3 trạng thái chính:
- **Chờ duyệt** (`pending`): Sản phẩm có `is_approved = null`
- **Còn hàng** (`in_stock`): Sản phẩm đã duyệt và có ít nhất 1 attribute với `quantity > 0`
- **Hết hàng** (`out_of_stock`): Sản phẩm đã duyệt nhưng tất cả attribute đều có `quantity = 0`

## 📊 API Endpoints

### 1. Lấy thống kê tồn kho

```http
GET /api/product/inventory-stats
```

**Quyền truy cập:**
- Chỉ user có shop (seller) mới được sử dụng
- Tự động lấy thống kê cho shop của user hiện tại

**Response:**
```json
{
  "summary": {
    "total_products": 150,
    "pending_approval": 10,
    "in_stock": 120,
    "out_of_stock": 20
  },
  "shop_id": 1,
  "shop_name": "Cửa hàng ABC"
}
```

### 2. Lấy danh sách sản phẩm theo trạng thái

```http
GET /api/product/by-status/{status}?page=1&limit=10&search=keyword
```

**Tham số:**
- `status` (required): Một trong `pending`, `in_stock`, `out_of_stock`
- `page` (optional, default=1): Trang hiện tại
- `limit` (optional, default=10): Số sản phẩm mỗi trang
- `search` (optional): Từ khóa tìm kiếm trong tên và mô tả

**Quyền truy cập:**
- Chỉ user có shop (seller) mới được sử dụng
- Tự động lấy sản phẩm của shop user hiện tại

**Response:**
```json
{
  "items": [
    {
      "product_id": 1,
      "name": "Áo thun nam",
      "description": "Áo thun cotton cao cấp",
      "price": 299000,
      "cover": "/static/products/product_abc.jpg",
      "shop_id": 1,
      "sub_category_id": 5,
      "is_approved": true,
      "approval_note": null,
      "create_at": "2024-01-15T10:30:00",
      "stock_info": {
        "total_quantity": 50,
        "variant_count": 6,
        "status": "in_stock"
      }
    }
  ],
  "total": 120,
  "page": 1,
  "limit": 10,
  "total_pages": 12,
  "has_next": true,
  "has_prev": false,
  "status": "in_stock",
  "shop_id": 1,
  "shop_name": "Cửa hàng ABC"
}
```

### 3. Lấy chi tiết sản phẩm với thông tin tồn kho

```http
GET /api/product/stock-detail/{product_id}
```

**Tham số:**
- `product_id` (required): ID của sản phẩm

**Quyền truy cập:**
- Chỉ shop owner được xem sản phẩm của shop mình
- Sản phẩm phải thuộc về shop của user hiện tại

**Response:**
```json
{
  "product_id": 1,
  "name": "Áo thun nam",
  "description": "Áo thun cotton cao cấp",
  "price": 299000,
  "cover": "/static/products/product_abc.jpg",
  "shop_id": 1,
  "sub_category_id": 5,
  "is_approved": true,
  "approval_note": null,
  "create_at": "2024-01-15T10:30:00",
  "stock_info": {
    "total_quantity": 50,
    "variant_count": 6,
    "status": "in_stock"
  },
  "attributes": [
    {
      "attribute_id": 101,
      "color": "Đỏ",
      "size": "M",
      "price": 299000,
      "quantity": 10,
      "image": "/static/attribute_images/attr_101.jpg",
      "create_at": "2024-01-15T10:30:00"
    },
    {
      "attribute_id": 102,
      "color": "Đỏ",
      "size": "L",
      "price": 299000,
      "quantity": 15,
      "image": "/static/attribute_images/attr_102.jpg",
      "create_at": "2024-01-15T10:30:00"
    }
  ],
  "total_stock": 50,
  "lowest_price": 299000,
  "highest_price": 299000
}
```

## 🔍 Ví dụ sử dụng

### Lấy thống kê shop của mình
```javascript
const response = await fetch('/api/product/inventory-stats', {
  headers: {
    'Authorization': 'Bearer your_token'
  }
});
const stats = await response.json();
console.log(`Shop: ${stats.shop_name}`);
console.log(`Tổng sản phẩm: ${stats.summary.total_products}`);
console.log(`Chờ duyệt: ${stats.summary.pending_approval}`);
console.log(`Còn hàng: ${stats.summary.in_stock}`);
console.log(`Hết hàng: ${stats.summary.out_of_stock}`);
```

### Lấy danh sách sản phẩm hết hàng
```javascript
const response = await fetch('/api/product/by-status/out_of_stock?page=1&limit=20', {
  headers: {
    'Authorization': 'Bearer your_token'
  }
});
const data = await response.json();
console.log(`Có ${data.total} sản phẩm hết hàng trong shop ${data.shop_name}`);
data.items.forEach(product => {
  console.log(`${product.name}: ${product.stock_info.total_quantity} sản phẩm`);
});
```

### Tìm kiếm sản phẩm chờ duyệt
```javascript
const response = await fetch('/api/product/by-status/pending?search=áo&page=1', {
  headers: {
    'Authorization': 'Bearer your_token'
  }
});
const data = await response.json();
console.log(`Tìm thấy ${data.total} sản phẩm chờ duyệt có từ khóa "áo"`);
```

### Xem chi tiết tồn kho sản phẩm
```javascript
const response = await fetch('/api/product/stock-detail/123', {
  headers: {
    'Authorization': 'Bearer your_token'
  }
});
const product = await response.json();
console.log(`Sản phẩm: ${product.name}`);
console.log(`Tổng tồn kho: ${product.total_stock}`);
console.log(`Số biến thể: ${product.stock_info.variant_count}`);
product.attributes.forEach(attr => {
  console.log(`- ${attr.color} ${attr.size}: ${attr.quantity} sản phẩm`);
});
```

## 📝 Lưu ý

### Về quyền truy cập:
- **Seller (Shop owner)**: Chỉ được xem sản phẩm của shop mình
- **Customer**: Không có quyền truy cập các API này
- **Admin**: Cần implement riêng nếu muốn xem tất cả shop

### Về trạng thái sản phẩm:
- Sản phẩm có thể chuyển từ `pending` → `in_stock` hoặc `out_of_stock` khi được duyệt
- Sản phẩm có thể chuyển giữa `in_stock` ↔ `out_of_stock` khi attribute quantity thay đổi
- Sản phẩm `pending` có thể bị từ chối (is_approved = false)

### Về tính toán tồn kho:
- `total_quantity` = tổng `quantity` của tất cả attributes
- `variant_count` = số lượng attributes (biến thể màu/size)
- Sản phẩm được coi là "hết hàng" khi tất cả attributes đều có quantity = 0

### Performance:
- Các query đã được tối ưu với index trên các trường thường xuyên filter
- Hỗ trợ pagination để xử lý danh sách lớn
- Cache được khuyến nghị cho API thống kê

### Error Handling:
- **404 - Shop not found**: User chưa có shop (chưa đăng ký seller)
- **403 - Product does not belong to your shop**: Cố gắng xem sản phẩm của shop khác
- **400 - Invalid status**: Status không hợp lệ (phải là pending/in_stock/out_of_stock) 