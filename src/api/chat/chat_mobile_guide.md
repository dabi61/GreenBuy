# Mobile Chat API Guide - GreenBuy

## Tổng quan

API Chat của GreenBuy được thiết kế đặc biệt cho ứng dụng mobile với các tính năng:

- **Real-time messaging** qua WebSocket
- **Authenticated connections** với JWT token
- **Multi-media support** (text, image, voice, file, location)
- **Typing indicators** và **read receipts**
- **Online status tracking**
- **Message status** (sent, delivered, read)
- **Message editing/deletion**
- **Reply to messages**
- **File upload** với thumbnail support

## WebSocket Connection

### 1. Kết nối WebSocket

**Endpoint:** `ws://localhost:8000/api/chat/ws/chat?token=YOUR_JWT_TOKEN`

```javascript
// React Native / JavaScript
const token = await AsyncStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/api/chat/ws/chat?token=${token}`);

ws.onopen = function(event) {
    console.log('WebSocket connected');
    
    // Join a chat room
    ws.send(JSON.stringify({
        type: "join_room",
        data: {
            room_id: 1
        }
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    handleIncomingMessage(message);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
    if (event.code === 4001) {
        console.log('Authentication failed');
        // Redirect to login
    }
};
```

### 2. Message Types

#### A. Join Room
```json
{
    "type": "join_room",
    "data": {
        "room_id": 1
    }
}
```

#### B. Send Message
```json
{
    "type": "message",
    "data": {
        "room_id": 1,
        "content": "Hello world!",
        "message_type": "text",
        "reply_to_id": null
    }
}
```

#### C. Send Image/File
```json
{
    "type": "message",
    "data": {
        "room_id": 1,
        "content": "Sent an image",
        "message_type": "image",
        "file_url": "/static/chat/images/abc123.jpg",
        "file_size": 204800,
        "file_name": "photo.jpg",
        "thumbnail_url": "/static/chat/images/abc123_thumb.jpg"
    }
}
```

#### D. Send Voice Message
```json
{
    "type": "message", 
    "data": {
        "room_id": 1,
        "content": "Voice message",
        "message_type": "voice",
        "file_url": "/static/chat/voices/def456.m4a",
        "duration": 15,
        "file_size": 102400
    }
}
```

#### E. Send Location
```json
{
    "type": "message",
    "data": {
        "room_id": 1,
        "content": "My location",
        "message_type": "location",
        "latitude": 21.0285,
        "longitude": 105.8542
    }
}
```

#### F. Typing Indicator
```json
{
    "type": "typing",
    "data": {
        "room_id": 1,
        "is_typing": true
    }
}
```

#### G. Read Receipt
```json
{
    "type": "read_receipt",
    "data": {
        "room_id": 1,
        "message_id": 123
    }
}
```

## REST API Endpoints

### 1. Get Chat Rooms
**GET** `/api/chat/rooms`

**Response:**
```json
[
    {
        "id": 1,
        "user1_id": 1,
        "user2_id": 2,
        "other_user_name": "John Doe",
        "other_user_avatar": "/static/avatars/user2.jpg",
        "other_user_online": true,
        "unread_count": 3,
        "last_message": {
            "id": 123,
            "content": "Hello!",
            "message_type": "text",
            "timestamp": "2024-01-15T10:30:00.000Z"
        }
    }
]
```

### 2. Upload File
**POST** `/api/chat/upload`

**Body:**
```
file: [FILE]
type: "image" | "voice" | "file"
```

**Response:**
```json
{
    "file_url": "/static/chat/images/abc123.jpg",
    "file_name": "photo.jpg", 
    "file_size": 204800,
    "thumbnail_url": "/static/chat/images/abc123_thumb.jpg"
}
```

## Mobile Implementation Examples

### React Native
```javascript
class ChatService {
    constructor() {
        this.ws = null;
        this.currentRoomId = null;
    }

    async connect() {
        const token = await AsyncStorage.getItem('access_token');
        this.ws = new WebSocket(`ws://localhost:8000/api/chat/ws/chat?token=${token}`);
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
    }

    joinRoom(roomId) {
        this.currentRoomId = roomId;
        this.send({
            type: "join_room",
            data: { room_id: roomId }
        });
    }

    sendMessage(content, type = 'text') {
        this.send({
            type: "message",
            data: {
                room_id: this.currentRoomId,
                content: content,
                message_type: type
            }
        });
    }

    async uploadFile(fileUri, type = 'image') {
        const token = await AsyncStorage.getItem('access_token');
        
        const formData = new FormData();
        formData.append('file', {
            uri: fileUri,
            type: 'image/jpeg',
            name: 'image.jpg'
        });
        formData.append('type', type);

        const response = await fetch('http://localhost:8000/api/chat/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'multipart/form-data',
            },
            body: formData
        });

        return await response.json();
    }
}
```

### Flutter
```dart
class ChatService {
    WebSocketChannel? _channel;
    
    Future<void> connect() async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('access_token');
        
        _channel = WebSocketChannel.connect(
            Uri.parse('ws://localhost:8000/api/chat/ws/chat?token=$token')
        );

        _channel!.stream.listen((data) {
            final message = json.decode(data);
            handleMessage(message);
        });
    }

    void sendMessage(String content) {
        _channel!.sink.add(json.encode({
            'type': 'message',
            'data': {
                'room_id': currentRoomId,
                'content': content,
                'message_type': 'text'
            }
        }));
    }
}
```

## Tính năng đã nâng cấp

### ✅ **New Features**
- **JWT Authentication** cho WebSocket
- **Multi-media messaging** (text, image, voice, file, location)
- **Message status tracking** (sent, delivered, read)
- **Typing indicators** real-time
- **Online status** tracking
- **Message editing/deletion**
- **Reply to messages**
- **File upload** với progress
- **Pagination** cho message history
- **Unread message count**
- **Enhanced room info** với user details

### ✅ **Mobile Optimizations**
- **Efficient message loading** với pagination
- **File compression** support
- **Thumbnail generation** cho images
- **Background reconnection**
- **Message queuing** khi offline
- **Memory management** cho large conversations

### ✅ **Security & Performance**
- **Token-based authentication**
- **Rate limiting** ready
- **File validation**
- **Connection pooling**
- **Auto cleanup** expired connections

API Chat mobile của GreenBuy giờ đã production-ready với đầy đủ tính năng cho ứng dụng thương mại điện tử! 🚀📱 