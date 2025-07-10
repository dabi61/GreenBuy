# 🏗️ GreenBuy Architecture Diagrams

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[Mobile App] 
        B[Web App]
        C[Admin Dashboard]
    end
    
    subgraph "API Gateway"
        D[FastAPI Server]
        E[WebSocket Server]
    end
    
    subgraph "Business Logic"
        F[User Management]
        G[Product Management]
        H[Order Management]
        I[Payment Processing]
        J[Chat System]
    end
    
    subgraph "Data Layer"
        K[(PostgreSQL + TimescaleDB)]
        L[File Storage]
    end
    
    subgraph "External Services"
        M[Payment Gateway]
        N[Email Service]
        O[Push Notifications]
    end
    
    A --> D
    B --> D
    C --> D
    A --> E
    B --> E
    
    D --> F
    D --> G
    D --> H
    D --> I
    E --> J
    
    F --> K
    G --> K
    H --> K
    I --> K
    J --> K
    
    G --> L
    I --> M
    F --> N
    J --> O
```

## 2. Database Entity Relationship Diagram

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
    }

    payments {
        int id PK
        int order_id FK
        int payment_method_id FK
        float amount
        string currency
        string status
        string transaction_id
        datetime created_at
        datetime completed_at
    }

    chat_rooms {
        int id PK
        int user1_id FK
        int user2_id FK
        datetime created_at
        datetime updated_at
        boolean is_active
    }
```

## 3. API Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant A as Auth API
    participant P as Product API
    participant C as Cart API
    participant O as Order API
    participant PM as Payment API
    participant DB as Database
    participant WS as WebSocket

    U->>A: Login (POST /token)
    A->>DB: Verify credentials
    A->>U: Return JWT token

    U->>P: Browse products (GET /api/product/)
    P->>DB: Query products
    P->>U: Return product list

    U->>C: Add to cart (POST /api/cart/items)
    C->>DB: Save cart item
    C->>U: Return cart updated

    U->>O: Create order (POST /api/order/)
    O->>DB: Create order
    O->>U: Return order details

    U->>PM: Process payment (POST /api/payment/process/{order_id})
    PM->>DB: Update payment status
    PM->>U: Return payment result

    U->>WS: Connect to chat (WebSocket)
    WS->>U: Real-time messages
```

## 4. User Journey Flow

```mermaid
flowchart TD
    A[User Registration] --> B[Email Verification]
    B --> C[Login]
    C --> D{Buyer or Seller?}
    
    D -->|Buyer| E[Browse Products]
    D -->|Seller| F[Create Shop]
    
    E --> G[Add to Cart]
    G --> H[Checkout]
    H --> I[Payment]
    I --> J[Order Confirmation]
    
    F --> K[Add Products]
    K --> L[Manage Orders]
    L --> M[Process Orders]
    
    J --> N[Track Order]
    M --> O[Ship Products]
    
    N --> P[Rate & Review]
    O --> Q[Order Delivered]
    
    P --> R[Chat Support]
    Q --> S[Complete Transaction]
```

## 5. Security Architecture

```mermaid
graph TB
    subgraph "Client Security"
        A[JWT Token Storage]
        B[HTTPS Communication]
        C[Input Validation]
    end
    
    subgraph "API Security"
        D[Authentication Middleware]
        E[Authorization Checks]
        F[Rate Limiting]
        G[CORS Configuration]
    end
    
    subgraph "Data Security"
        H[Password Hashing - bcrypt]
        I[SQL Injection Prevention]
        J[Data Encryption]
        K[Token Blacklisting]
    end
    
    subgraph "Infrastructure Security"
        L[Docker Containerization]
        M[Database Access Control]
        N[File Upload Validation]
        O[Logging & Monitoring]
    end
    
    A --> D
    B --> D
    C --> E
    D --> H
    E --> I
    F --> J
    G --> K
    H --> L
    I --> M
    J --> N
    K --> O
```

## 6. Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        A[Nginx/HAProxy]
    end
    
    subgraph "Application Layer"
        B[FastAPI Container 1]
        C[FastAPI Container 2]
        D[FastAPI Container N]
    end
    
    subgraph "Database Layer"
        E[(PostgreSQL Primary)]
        F[(PostgreSQL Replica)]
        G[TimescaleDB Extension]
    end
    
    subgraph "Storage Layer"
        H[File Storage]
        I[Backup Storage]
    end
    
    subgraph "Monitoring"
        J[Health Checks]
        K[Logs Collection]
        L[Metrics Dashboard]
    end
    
    A --> B
    A --> C
    A --> D
    B --> E
    C --> E
    D --> E
    E --> F
    E --> G
    B --> H
    C --> H
    D --> H
    B --> J
    C --> J
    D --> J
    J --> K
    K --> L
```

## 7. Chat System Architecture

```mermaid
graph TB
    subgraph "Client Apps"
        A[Mobile App]
        B[Web App]
    end
    
    subgraph "WebSocket Layer"
        C[WebSocket Server]
        D[Connection Manager]
        E[Message Router]
    end
    
    subgraph "Chat Logic"
        F[Room Management]
        G[Message Processing]
        H[File Upload Handler]
        I[Notification Service]
    end
    
    subgraph "Data Storage"
        J[(Chat Rooms)]
        K[(Messages)]
        L[File Storage]
    end
    
    subgraph "External Services"
        M[Push Notifications]
        N[Email Service]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    E --> G
    E --> H
    F --> J
    G --> K
    H --> L
    G --> I
    I --> M
    I --> N
```

## 8. Payment Flow

```mermaid
flowchart TD
    A[User Selects Payment Method] --> B{Payment Type?}
    
    B -->|Credit Card| C[Card Validation]
    B -->|PayPal| D[PayPal OAuth]
    B -->|Bank Transfer| E[Bank Details]
    B -->|COD| F[Cash on Delivery]
    B -->|MOMO| G[MOMO Integration]
    B -->|ZaloPay| H[ZaloPay Integration]
    
    C --> I[Payment Gateway]
    D --> I
    E --> I
    F --> J[Order Confirmed]
    G --> I
    H --> I
    
    I --> K{Payment Success?}
    K -->|Yes| L[Update Order Status]
    K -->|No| M[Payment Failed]
    
    L --> N[Send Confirmation]
    M --> O[Retry Payment]
    
    N --> P[Order Processing]
    O --> A
```

## 9. Order Status Flow

```mermaid
stateDiagram-v2
    [*] --> Pending: Order Created
    Pending --> Confirmed: Admin Confirms
    Pending --> Cancelled: User Cancels
    Confirmed --> Processing: Shop Processes
    Confirmed --> Cancelled: Admin Cancels
    Processing --> Shipped: Shop Ships
    Processing --> Cancelled: Admin Cancels
    Shipped --> Delivered: Delivery Complete
    Shipped --> Returned: User Returns
    Delivered --> Returned: User Returns
    Returned --> Refunded: Admin Refunds
    Cancelled --> [*]
    Refunded --> [*]
```

## 10. Product Approval Flow

```mermaid
flowchart TD
    A[Seller Creates Product] --> B[Product Pending]
    B --> C{Admin Review}
    C -->|Approve| D[Product Active]
    C -->|Reject| E[Product Rejected]
    C -->|Request Changes| F[Product Needs Update]
    
    D --> G[Product Available for Sale]
    E --> H[Seller Notified]
    F --> I[Seller Updates Product]
    I --> B
    
    G --> J[Product Sold]
    H --> K[Seller Can Resubmit]
    K --> B
```

---

## 📊 Diagram Usage

Các diagram này có thể được sử dụng để:

1. **Documentation** - Tài liệu kỹ thuật
2. **Presentations** - Trình bày cho stakeholders
3. **Development** - Hướng dẫn cho developers
4. **Architecture Reviews** - Đánh giá kiến trúc
5. **Onboarding** - Hướng dẫn cho team mới

## 🛠️ Tools để tạo diagram:

- **Mermaid** - Tích hợp với GitHub/GitLab
- **Draw.io** - Diagram editor online
- **Lucidchart** - Professional diagramming
- **PlantUML** - Code-based diagrams
- **Figma** - Design & prototyping

## 📝 Export Options:

- **PNG** - Cho presentations
- **SVG** - Cho web
- **PDF** - Cho documentation
- **Mermaid** - Cho version control 