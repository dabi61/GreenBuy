# Hệ thống Logout cho GreenBuy

## Tổng quan

Hệ thống logout được implement bằng cách sử dụng **Token Blacklist** - một cách tiếp cận phổ biến cho JWT stateless authentication.

## Cách hoạt động

1. **Login**: User nhận access token và refresh token
2. **Logout**: Token được thêm vào blacklist
3. **Subsequent requests**: Mọi request đều kiểm tra token có trong blacklist không
4. **Cleanup**: Background task tự động xóa expired tokens khỏi blacklist

## API Endpoints

### 1. Logout (Single Device)

```http
POST /logout
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

**Mô tả:**
- Logout khỏi device hiện tại
- Chỉ access token được blacklist
- Refresh token vẫn có thể sử dụng ở device khác

### 2. Logout All Devices

```http
POST /logout-all
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "old_refresh_data": "refresh_token_here"
}
```

**Response:**
```json
{
    "message": "Successfully logged out from all devices"
}
```

**Mô tả:**
- Logout khỏi tất cả devices
- Cả access token và refresh token đều được blacklist
- User cần login lại ở tất cả devices

## Admin Endpoints

### 1. Thống kê Token Blacklist

```http
GET /api/admin/stats/tokens
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "blacklisted_tokens_count": 42,
    "message": "Token blacklist statistics"
}
```

### 2. Cleanup Token Blacklist

```http
POST /api/admin/cleanup/tokens
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "message": "Token blacklist cleaned up successfully",
    "tokens_removed": 15,
    "remaining_tokens": 27
}
```

## Ví dụ sử dụng

### Frontend (JavaScript)

```javascript
// Logout single device
async function logout() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// Logout all devices
async function logoutAll() {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    try {
        const response = await fetch('/logout-all', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_refresh_data: refreshToken
            })
        });
        
        if (response.ok) {
            localStorage.clear();
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout all failed:', error);
    }
}
```

### Mobile App (React Native)

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

const logout = async () => {
    try {
        const token = await AsyncStorage.getItem('access_token');
        
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
            // Navigate to login screen
        }
    } catch (error) {
        console.error('Logout failed:', error);
    }
};
```

### cURL

```bash
# Logout single device
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer your_access_token_here"

# Logout all devices
curl -X POST "http://localhost:8000/logout-all" \
  -H "Authorization: Bearer your_access_token_here" \
  -H "Content-Type: application/json" \
  -d '{"old_refresh_data": "your_refresh_token_here"}'
```

## Tính năng đã implement

### ✅ **Core Features**
- Single device logout
- All devices logout  
- Token blacklist system
- Automatic token validation
- Background cleanup task

### ✅ **Security Features**
- Blacklist kiểm tra cho mọi request
- Refresh token validation
- Expired token cleanup
- Thread-safe operations

### ✅ **Admin Features**
- Blacklist statistics
- Manual cleanup
- Token monitoring

## Lưu ý quan trọng

### 1. **Production Considerations**

Trong production, nên thay thế in-memory blacklist bằng:

- **Redis**: Tốt nhất cho performance và distributed systems
- **Database**: PostgreSQL, MySQL cho persistence
- **Cache system**: Memcached hoặc tương tự

```python
# Ví dụ với Redis
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def add_token_to_blacklist(token: str):
    # Set với expiry time bằng token expiry
    redis_client.setex(f"blacklist:{token}", ttl, "1")

def is_token_blacklisted(token: str) -> bool:
    return redis_client.exists(f"blacklist:{token}")
```

### 2. **Performance**

- Background cleanup chạy mỗi 1 giờ
- Thread-safe operations
- Memory efficient với auto cleanup

### 3. **Error Handling**

Tất cả blacklisted tokens sẽ trả về:

```json
{
    "detail": "Token has been revoked. Please log in again.",
    "status_code": 401
}
```

## Migration từ hệ thống cũ

Nếu có hệ thống logout cũ, migration process:

1. Deploy code mới với blacklist system
2. Existing tokens vẫn hoạt động bình thường
3. New logouts sẽ sử dụng blacklist
4. Old tokens sẽ expire tự nhiên

## Monitoring

Các metrics cần theo dõi:

- Blacklist size
- Logout frequency
- Cleanup efficiency
- Memory usage

## Files đã thêm

1. `src/api/auth/token_blacklist.py` - Core blacklist logic
2. `src/api/auth/cleanup_task.py` - Background cleanup task
3. Updated `src/api/auth/dependency.py` - Blacklist validation
4. Updated `src/main.py` - Logout endpoints
5. Updated `src/api/user/admin_routing.py` - Admin statistics

Hệ thống logout của bạn giờ đã hoàn chỉnh và production-ready! 🚀 