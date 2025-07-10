# 🛒 GreenBuy - E-commerce API Platform

## 📋 Tổng quan dự án

GreenBuy là một nền tảng thương mại điện tử hiện đại được xây dựng với FastAPI và PostgreSQL. Hệ thống hỗ trợ đầy đủ các tính năng từ quản lý sản phẩm, giỏ hàng, đơn hàng đến thanh toán và chat real-time.

## 🏗️ Kiến trúc hệ thống

### **Backend Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │   WebSocket     │
│   (Python 3.12) │◄──►│   (TimescaleDB) │    │   (Chat)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   REST API      │    │   Database      │    │   Real-time     │
│   Endpoints     │    │   Migrations    │    │   Messaging     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Technology Stack**

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | FastAPI | 0.115.12 | Modern, fast web framework |
| **Database** | PostgreSQL + TimescaleDB | 17 | Time-series & relational data |
| **ORM** | SQLModel | Latest | Type-safe database operations |
| **Authentication** | JWT + bcrypt | Latest | Secure user authentication |
| **Real-time** | WebSocket | Latest | Live chat functionality |
| **Container** | Docker | Latest | Containerization |
| **Deployment** | Docker Compose | Latest | Multi-service orchestration |

## 🗄️ Database Schema

### **Core Entities & Relationships**

```mermaid
erDiagram
    users ||--o{ addresses : has
    users ||--o{ orders : places
    users ||--o{ payment_methods : owns
    users ||--o{ user_follows : follows
    users ||--o{ shop_follows : follows
    users ||--o{ user_ratings : rates
    users ||--o{ shop_ratings : rates
    users ||--o{ chat_rooms : participates
    users ||--o{ chat_messages : sends
    users ||--o{ events : tracks
    users ||--|| cart : has
    users ||--|| shop : owns
    users ||--o{ approved_products : approves
    users ||--o{ refund_requests : requests
    users ||--o{ online_status : tracks

    shop ||--o{ products : sells
    shop ||--o{ shop_follows : followed_by
    shop ||--o{ shop_ratings : rated_by

    category ||--o{ sub_categories : contains
    sub_categories ||--o{ products : categorizes

    products ||--o{ attributes : has
    products ||--o{ order_items : included_in
    products ||--o{ approved_products : approved_by

    attributes ||--o{ cart_items : selected_in
    attributes ||--o{ order_items : specified_in

    cart ||--o{ cart_items : contains

    orders ||--o{ order_items : contains
    orders ||--o{ payments : paid_by

    payment_methods ||--o{ payments : used_for
    payments ||--o{ refund_requests : refunded_by

    chat_rooms ||--o{ chat_messages : contains
    chat_messages ||--o{ chat_messages : replies_to

    users {
        int id PK
        string email
        string password_hash
        string username
        string first_name
        string last_name
        string avatar
        datetime birth_date
        string phone_number
        string bio
        boolean is_active
        boolean is_online
        boolean is_verified
        enum role
        datetime created_at
        datetime updated_at
        datetime last_login
        int failed_login_attempts
        datetime locked_until
        datetime password_changed_at
        string email_verification_token
        datetime email_verified_at
        string password_reset_token
        datetime password_reset_expires
    }

    shop {
        int id PK
        int user_id FK
        string name
        string avatar
        string phone_number
        boolean is_active
        boolean is_online
        datetime create_at
    }

    category {
        int id PK
        string name
        string description
        datetime created_at
    }

    sub_categories {
        int id PK
        int category_id FK
        string name
        string description
        datetime created_at
    }

    products {
        int product_id PK
        int shop_id FK
        int sub_category_id FK
        string name
        string description
        string cover
        float price
        boolean is_approved
        string approval_note
        int approver_id FK
        datetime create_at
    }

    attributes {
        int attribute_id PK
        int product_id FK
        string color
        string size
        float price
        string image
        int quantity
        datetime create_at
    }

    cart {
        int id PK
        int user_id FK
        datetime created_at
        datetime updated_at
    }

    cart_items {
        int id PK
        int cart_id FK
        int attribute_id FK
        int quantity
        datetime added_at
    }

    orders {
        int id PK
        string order_number
        int user_id FK
        int status
        float subtotal
        float tax_amount
        float shipping_fee
        float discount_amount
        float total_amount
        string shipping_address
        string billing_address
        string phone_number
        string recipient_name
        string delivery_notes
        datetime created_at
        datetime updated_at
        datetime confirmed_at
        datetime shipped_at
        datetime delivered_at
        datetime cancelled_at
        string notes
        string internal_notes
    }

    order_items {
        int id PK
        int order_id FK
        int product_id FK
        int attribute_id FK
        string product_name
        string product_image
        string attribute_details
        int quantity
        float unit_price
        float total_price
        datetime created_at
    }

    payment_method {
        int id PK
        int user_id FK
        enum type
        string card_number
        string card_holder_name
        int expiry_month
        int expiry_year
        string paypal_email
        string bank_name
        string account_number
        string account_holder
        boolean is_default
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    payments {
        int id PK
        int order_id FK
        int payment_method_id FK
        float amount
        string currency
        string status
        string transaction_id
        string gateway_response
        string failure_reason
        datetime created_at
        datetime processed_at
        datetime completed_at
        string notes
    }

    refund_requests {
        int id PK
        int payment_id FK
        int user_id FK
        float amount
        string reason
        string status
        string admin_note
        int processed_by FK
        datetime created_at
        datetime processed_at
    }

    addresses {
        int id PK
        int user_id FK
        string street
        string city
        string state
        string zipcode
        string country
        string phone_number
        boolean is_default
        datetime created_at
    }

    user_follows {
        int id PK
        int follower_id FK
        int following_id FK
        datetime created_at
    }

    shop_follows {
        int id PK
        int user_id FK
        int shop_id FK
        datetime created_at
    }

    user_ratings {
        int id PK
        int rater_id FK
        int rated_user_id FK
        int rating
        string comment
        datetime created_at
        datetime updated_at
    }

    shop_ratings {
        int id PK
        int user_id FK
        int shop_id FK
        int rating
        string comment
        datetime created_at
        datetime updated_at
    }

    chat_rooms {
        int id PK
        int user1_id FK
        int user2_id FK
        datetime created_at
        datetime updated_at
        boolean is_active
        int last_message_id
        datetime last_activity
    }

    chat_messages {
        int id PK
        int room_id FK
        int sender_id FK
        string content
        enum type
        enum status
        datetime timestamp
        string file_url
        int file_size
        string file_name
        string thumbnail_url
        int duration
        float latitude
        float longitude
        int reply_to_id FK
        boolean is_edited
        datetime edited_at
        boolean is_deleted
        datetime deleted_at
    }

    online_status {
        int user_id PK
        boolean is_online
        datetime last_seen
        string device_info
        datetime updated_at
    }

    events {
        int id PK
        int user_id FK
        string page
        string descriptions
        datetime created_at
        datetime update_at
    }
```

## 🚀 API Endpoints

### **Authentication & User Management**
```http
POST   /token                    # Login
POST   /token/refresh           # Refresh token
POST   /logout                  # Logout
POST   /logout-all              # Logout all devices
GET    /api/user/me             # Get current user
PUT    /api/user/profile        # Update profile
```

### **Shop Management**
```http
GET    /api/shops/me            # Get my shop
POST   /api/shops/              # Create shop
PUT    /api/shops/me            # Update shop
GET    /api/shops/{id}          # Get shop by ID
GET    /api/shops/me/stats      # Shop statistics
```

### **Product Management**
```http
GET    /api/product/            # List products (with pagination)
POST   /api/product/            # Create product
GET    /api/product/{id}        # Get product details
PUT    /api/product/{id}        # Update product
DELETE /api/product/{id}        # Delete product
GET    /api/product/by-status/{status}  # Filter by status
```

### **Cart & Orders**
```http
GET    /api/cart/me             # Get my cart
POST   /api/cart/items          # Add to cart
PUT    /api/cart/items/{id}     # Update cart item
DELETE /api/cart/items/{id}     # Remove from cart

GET    /api/order/              # List orders
POST   /api/order/              # Create order
GET    /api/order/{id}          # Get order details
PATCH  /api/order/{id}/status   # Update order status
```

### **Payment System**
```http
GET    /api/payment/methods     # List payment methods
POST   /api/payment/methods     # Add payment method
POST   /api/payment/process/{order_id}  # Process payment
POST   /api/payment/refund      # Request refund
```

### **Real-time Chat**
```http
GET    /api/chat/rooms          # List chat rooms
POST   /api/chat/rooms          # Create chat room
GET    /api/chat/rooms/{id}/messages  # Get messages
POST   /api/chat/rooms/{id}/messages  # Send message
```

## 🔧 Cài đặt & Chạy

### **Prerequisites**
- Docker & Docker Compose
- Python 3.12+
- PostgreSQL (TimescaleDB)

### **Quick Start**

1. **Clone repository**
```bash
git clone <repository-url>
cd GreenBuy
```

2. **Setup environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Run with Docker**
```bash
docker-compose up -d
```

4. **Run migrations**
```bash
docker-compose exec app alembic upgrade head
```

5. **Access API**
- API Documentation: http://localhost:8002/docs
- Health Check: http://localhost:8002/healthz

### **Development Setup**

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run development server**
```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## 📊 Tính năng chính

### **🛍️ E-commerce Features**
- ✅ Quản lý sản phẩm với attributes (màu sắc, kích thước)
- ✅ Giỏ hàng thông minh
- ✅ Hệ thống đơn hàng với trạng thái chi tiết
- ✅ Thanh toán đa phương thức
- ✅ Đánh giá và review
- ✅ Theo dõi shop/user

### **💬 Social Features**
- ✅ Chat real-time giữa users
- ✅ Follow/Unfollow users và shops
- ✅ Rating và review system
- ✅ Event tracking

### **🔐 Security Features**
- ✅ JWT Authentication
- ✅ Password hashing với bcrypt
- ✅ Role-based access control
- ✅ Token blacklisting
- ✅ Rate limiting

### **📱 Mobile-Friendly**
- ✅ RESTful API design
- ✅ Pagination support
- ✅ File upload handling
- ✅ Real-time notifications
- ✅ Optimized responses

## 🗂️ Project Structure

```
GreenBuy/
├── src/
│   ├── api/
│   │   ├── auth/           # Authentication & JWT
│   │   ├── user/           # User management
│   │   ├── shop/           # Shop management
│   │   ├── product/        # Product management
│   │   ├── cart/           # Shopping cart
│   │   ├── order/          # Order management
│   │   ├── payment/        # Payment processing
│   │   ├── chat/           # Real-time chat
│   │   ├── address/        # Address management
│   │   ├── category/       # Product categories
│   │   ├── attribute/      # Product attributes
│   │   └── db/             # Database configuration
│   ├── static/             # Static files (images)
│   ├── alembic/            # Database migrations
│   └── main.py             # FastAPI application
├── docker-compose.yml       # Docker orchestration
├── Dockerfile.web          # Docker configuration
├── requirements.txt         # Python dependencies
└── README.md              # This file
```

## 🔄 Database Migrations

Hệ thống sử dụng Alembic để quản lý database migrations:

```bash
# Tạo migration mới
alembic revision --autogenerate -m "Description"

# Chạy migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

```bash
# Run tests (if available)
pytest

# Run with coverage
pytest --cov=src
```

## 📈 Performance

- **Database**: TimescaleDB cho time-series data
- **Caching**: Redis (có thể thêm)
- **Load Balancing**: Docker Compose
- **Monitoring**: Health check endpoints

## 🔒 Security

- **Authentication**: JWT tokens
- **Password**: bcrypt hashing
- **CORS**: Configured for cross-origin requests
- **Input Validation**: Pydantic models
- **SQL Injection**: SQLModel ORM protection

## 📝 API Documentation

Truy cập Swagger UI tại: `http://localhost:8002/docs`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Email**: support@greenbuy.com
- **Documentation**: [API Docs](http://localhost:8002/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

**GreenBuy** - Modern E-commerce Platform 🚀