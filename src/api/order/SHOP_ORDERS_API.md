# Shop Orders API Documentation

API này cung cấp các endpoint để shop có thể lấy và thống kê tất cả đơn hàng của mình.

## Endpoints

### 1. GET `/api/orders/shop-orders` - Lấy danh sách đơn hàng của shop với thống kê chi tiết

**Mô tả**: Lấy tất cả đơn hàng có chứa sản phẩm của shop hiện tại, kèm theo thống kê chi tiết và phân trang.

**Authentication**: Yêu cầu Bearer token của user có shop

**Query Parameters**:
- `status_filter` (optional): Lọc theo trạng thái (có thể dùng số hoặc tên trạng thái)
  - Số: 1=pending, 2=confirmed, 3=processing, 4=shipped, 5=delivered, 6=cancelled, 7=refunded, 8=returned
  - Tên: "pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded", "returned"
- `page` (optional, default=1): Trang hiện tại
- `limit` (optional, default=10, max=100): Số lượng đơn hàng mỗi trang
- `date_from` (optional): Lọc từ ngày (format: YYYY-MM-DD)
- `date_to` (optional): Lọc đến ngày (format: YYYY-MM-DD)

**Response Structure**:
```json
{
  "items": [
    {
      "id": 123,
      "order_number": "ORD-20241225-ABC12345",
      "status": "confirmed",
      "customer_name": "Nguyễn Văn A",
      "customer_phone": "0123456789",
      "shipping_address": "123 Đường ABC, Quận 1, TP.HCM",
      "total_items": 2,
      "total_amount": 500000.0,
      "created_at": "2024-12-25T10:00:00Z",
      "updated_at": "2024-12-25T10:30:00Z",
      "confirmed_at": "2024-12-25T10:30:00Z",
      "shipped_at": null,
      "delivered_at": null,
      "cancelled_at": null,
      "shop_items": [
        {
          "product_name": "Áo thun nam",
          "attribute_name": "Size M - Màu đen",
          "quantity": 1,
          "price": 200000.0,
          "total": 200000.0
        }
      ],
      "shop_subtotal": 200000.0
    }
  ],
  "stats": {
    "total_orders": 150,
    "pending_orders": 5,
    "confirmed_orders": 8,
    "processing_orders": 12,
    "shipped_orders": 20,
    "delivered_orders": 100,
    "cancelled_orders": 3,
    "refunded_orders": 1,
    "returned_orders": 1,
    "total_revenue": 50000000.0,
    "pending_revenue": 5000000.0,
    "orders_today": 3,
    "orders_this_week": 15,
    "orders_this_month": 45,
    "pending_ratings": 2
  },
  "total": 150,
  "page": 1,
  "limit": 10,
  "total_pages": 15,
  "has_next": true,
  "has_prev": false
}
```

### 2. GET `/api/orders/shop-stats` - Lấy chỉ thống kê tổng quan

**Mô tả**: Lấy chỉ thống kê tổng quan về đơn hàng của shop mà không bao gồm danh sách chi tiết. Phù hợp cho dashboard.

**Authentication**: Yêu cầu Bearer token của user có shop

**Query Parameters**: Không có

**Response Structure**:
```json
{
  "total_orders": 150,
  "pending_orders": 5,
  "confirmed_orders": 8,
  "processing_orders": 12,
  "shipped_orders": 20,
  "delivered_orders": 100,
  "cancelled_orders": 3,
  "refunded_orders": 1,
  "returned_orders": 1,
  "total_revenue": 50000000.0,
  "pending_revenue": 5000000.0,
  "orders_today": 3,
  "orders_this_week": 15,
  "orders_this_month": 45,
  "pending_ratings": 2
}
```

## Cách thức hoạt động

### Logic xác định đơn hàng thuộc shop:
1. Hệ thống tìm shop của user hiện tại thông qua `shop.user_id = current_user.id`
2. Lấy tất cả đơn hàng có chứa ít nhất 1 sản phẩm thuộc shop đó
3. Chỉ tính toán thống kê và hiển thị thông tin liên quan đến sản phẩm của shop

### Thống kê chi tiết:
- **total_revenue**: Tổng doanh thu từ các đơn đã giao (status = 5)
- **pending_revenue**: Doanh thu từ các đơn chờ xử lý (status = 1,2,3,4)
- **orders_today/week/month**: Đếm theo thời gian tạo đơn hàng
- **pending_ratings**: Số lượng đánh giá shop cần trả lời (nếu có bảng shop_rating_responses)

### Thông tin chi tiết mỗi đơn hàng:
- **shop_items**: Chỉ hiển thị các sản phẩm thuộc shop
- **shop_subtotal**: Tổng tiền chỉ tính các sản phẩm của shop trong đơn hàng đó
- **total_items**: Số lượng sản phẩm của shop trong đơn hàng
- **total_amount**: Tổng tiền của cả đơn hàng (bao gồm sản phẩm của shop khác)

## Ví dụ sử dụng

### Lấy tất cả đơn hàng pending của shop:
```
GET /api/orders/shop-orders?status_filter=pending&page=1&limit=20
```

### Lấy đơn hàng trong tháng 12/2024:
```
GET /api/orders/shop-orders?date_from=2024-12-01&date_to=2024-12-31
```

### Lấy thống kê nhanh cho dashboard:
```
GET /api/orders/shop-stats
```

## Lưu ý quan trọng

1. **Authentication**: User phải có shop thì mới có thể sử dụng API này
2. **Performance**: API sử dụng raw SQL để tối ưu hiệu suất với các JOIN phức tạp
3. **Data Scope**: Chỉ hiển thị đơn hàng có chứa sản phẩm của shop hiện tại
4. **Mixed Orders**: Nếu đơn hàng có sản phẩm từ nhiều shop, mỗi shop chỉ thấy phần sản phẩm của mình
5. **Status Mapping**: Hỗ trợ cả integer và string cho status filter để dễ sử dụng 