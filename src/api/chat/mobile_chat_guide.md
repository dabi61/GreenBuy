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

### 3. Incoming Message Format

```json
{
    "type": "message",
    "data": {
        "id": 123,
        "room_id": 1,
        "sender_id": 2,
        "content": "Hello!",
        "message_type": "text",
        "status": "sent",
        "timestamp": "2024-01-15T10:30:00.000Z",
        "file_url": null,
        "file_size": null,
        "file_name": null,
        "thumbnail_url": null,
        "duration": null,
        "latitude": null,
        "longitude": null,
        "reply_to_id": null,
        "is_edited": false
    }
}
```

## REST API Endpoints

### 1. Get Chat Rooms
**GET** `/api/chat/rooms`

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
[
    {
        "id": 1,
        "user1_id": 1,
        "user2_id": 2,
        "created_at": "2024-01-15T10:00:00.000Z",
        "updated_at": "2024-01-15T10:30:00.000Z",
        "is_active": true,
        "last_message_id": 123,
        "last_activity": "2024-01-15T10:30:00.000Z",
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

### 2. Create Chat Room
**POST** `/api/chat/rooms`

**Body:**
```json
{
    "user2_id": 2
}
```

### 3. Get Room Messages
**GET** `/api/chat/rooms/{room_id}/messages?limit=50&offset=0`

**Response:**
```json
[
    {
        "id": 123,
        "room_id": 1,
        "sender_id": 2,
        "content": "Hello!",
        "type": "text",
        "status": "read",
        "timestamp": "2024-01-15T10:30:00.000Z",
        "file_url": null,
        "file_size": null,
        "file_name": null,
        "thumbnail_url": null,
        "duration": null,
        "latitude": null,
        "longitude": null,
        "reply_to_id": null,
        "is_edited": false,
        "edited_at": null,
        "is_deleted": false
    }
]
```

### 4. Upload File
**POST** `/api/chat/upload`

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: multipart/form-data
```

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

### 5. Edit Message
**PATCH** `/api/chat/messages/{message_id}`

**Body:**
```json
{
    "content": "Updated message content",
    "status": "read"
}
```

### 6. Delete Message
**DELETE** `/api/chat/messages/{message_id}`

### 7. Get User Online Status
**GET** `/api/chat/online-status/{user_id}`

**Response:**
```json
{
    "user_id": 2,
    "is_online": true,
    "last_seen": "2024-01-15T10:30:00.000Z",
    "device_info": "mobile"
}
```

## Mobile Implementation Examples

### React Native Example

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

class ChatService {
    constructor() {
        this.ws = null;
        this.currentRoomId = null;
        this.messageCallbacks = [];
        this.typingCallbacks = [];
        this.statusCallbacks = [];
    }

    async connect() {
        const token = await AsyncStorage.getItem('access_token');
        this.ws = new WebSocket(`ws://localhost:8000/api/chat/ws/chat?token=${token}`);
        
        this.ws.onopen = () => {
            console.log('Chat connected');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('Chat error:', error);
        };

        this.ws.onclose = (event) => {
            if (event.code === 4001) {
                // Authentication failed, redirect to login
                this.redirectToLogin();
            }
        };
    }

    joinRoom(roomId) {
        this.currentRoomId = roomId;
        this.send({
            type: "join_room",
            data: { room_id: roomId }
        });
    }

    sendMessage(content, type = 'text', extraData = {}) {
        if (!this.currentRoomId) return;

        this.send({
            type: "message",
            data: {
                room_id: this.currentRoomId,
                content: content,
                message_type: type,
                ...extraData
            }
        });
    }

    sendTyping(isTyping) {
        if (!this.currentRoomId) return;

        this.send({
            type: "typing",
            data: {
                room_id: this.currentRoomId,
                is_typing: isTyping
            }
        });
    }

    markAsRead(messageId) {
        if (!this.currentRoomId) return;

        this.send({
            type: "read_receipt",
            data: {
                room_id: this.currentRoomId,
                message_id: messageId
            }
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    handleMessage(message) {
        switch (message.type) {
            case 'message':
                this.messageCallbacks.forEach(callback => callback(message.data));
                break;
            case 'typing':
                this.typingCallbacks.forEach(callback => callback(message.data));
                break;
            case 'user_status':
                this.statusCallbacks.forEach(callback => callback(message.data));
                break;
            case 'read_receipt':
                this.readReceiptCallbacks.forEach(callback => callback(message.data));
                break;
        }
    }

    onMessage(callback) {
        this.messageCallbacks.push(callback);
    }

    onTyping(callback) {
        this.typingCallbacks.push(callback);
    }

    onUserStatus(callback) {
        this.statusCallbacks.push(callback);
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

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Usage
const chatService = new ChatService();
await chatService.connect();

// Join room
chatService.joinRoom(1);

// Send text message
chatService.sendMessage("Hello world!");

// Send image
const uploadResult = await chatService.uploadFile(imageUri, 'image');
chatService.sendMessage("Sent an image", 'image', {
    file_url: uploadResult.file_url,
    file_size: uploadResult.file_size,
    file_name: uploadResult.file_name,
    thumbnail_url: uploadResult.thumbnail_url
});

// Listen for messages
chatService.onMessage((message) => {
    console.log('New message:', message);
    // Update UI
});

// Listen for typing
chatService.onTyping((data) => {
    console.log('User typing:', data);
    // Show typing indicator
});
```

### Flutter Example

```dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ChatService {
    WebSocketChannel? _channel;
    int? currentRoomId;
    
    Function(Map<String, dynamic>)? onMessage;
    Function(Map<String, dynamic>)? onTyping;
    Function(Map<String, dynamic>)? onUserStatus;

    Future<void> connect() async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('access_token');
        
        _channel = WebSocketChannel.connect(
            Uri.parse('ws://localhost:8000/api/chat/ws/chat?token=$token')
        );

        _channel!.stream.listen(
            (data) {
                final message = json.decode(data);
                _handleMessage(message);
            },
            onError: (error) {
                print('WebSocket error: $error');
            },
            onDone: () {
                print('WebSocket closed');
            }
        );
    }

    void joinRoom(int roomId) {
        currentRoomId = roomId;
        _send({
            'type': 'join_room',
            'data': {'room_id': roomId}
        });
    }

    void sendMessage(String content, {String type = 'text', Map<String, dynamic>? extraData}) {
        if (currentRoomId == null) return;

        final data = {
            'room_id': currentRoomId,
            'content': content,
            'message_type': type,
            ...?extraData
        };

        _send({
            'type': 'message',
            'data': data
        });
    }

    void sendTyping(bool isTyping) {
        if (currentRoomId == null) return;

        _send({
            'type': 'typing',
            'data': {
                'room_id': currentRoomId,
                'is_typing': isTyping
            }
        });
    }

    void _send(Map<String, dynamic> data) {
        if (_channel != null) {
            _channel!.sink.add(json.encode(data));
        }
    }

    void _handleMessage(Map<String, dynamic> message) {
        switch (message['type']) {
            case 'message':
                onMessage?.call(message['data']);
                break;
            case 'typing':
                onTyping?.call(message['data']);
                break;
            case 'user_status':
                onUserStatus?.call(message['data']);
                break;
        }
    }

    void disconnect() {
        _channel?.sink.close();
        _channel = null;
    }
}
```

### iOS Swift Example

```swift
import Foundation
import Starscream

class ChatService: WebSocketDelegate {
    private var socket: WebSocket?
    private var currentRoomId: Int?
    
    var onMessage: ((Data) -> Void)?
    var onTyping: ((Data) -> Void)?
    var onUserStatus: ((Data) -> Void)?

    func connect() {
        guard let token = UserDefaults.standard.string(forKey: "access_token") else { return }
        
        var request = URLRequest(url: URL(string: "ws://localhost:8000/api/chat/ws/chat?token=\(token)")!)
        socket = WebSocket(request: request)
        socket?.delegate = self
        socket?.connect()
    }

    func joinRoom(roomId: Int) {
        currentRoomId = roomId
        let data: [String: Any] = [
            "type": "join_room",
            "data": ["room_id": roomId]
        ]
        send(data: data)
    }

    func sendMessage(content: String, type: String = "text", extraData: [String: Any] = [:]) {
        guard let roomId = currentRoomId else { return }
        
        var messageData: [String: Any] = [
            "room_id": roomId,
            "content": content,
            "message_type": type
        ]
        messageData.merge(extraData) { (_, new) in new }
        
        let data: [String: Any] = [
            "type": "message",
            "data": messageData
        ]
        send(data: data)
    }

    private func send(data: [String: Any]) {
        guard let jsonData = try? JSONSerialization.data(withJSONObject: data) else { return }
        socket?.write(data: jsonData)
    }

    // MARK: - WebSocketDelegate
    func didReceive(event: WebSocketEvent, client: WebSocket) {
        switch event {
        case .connected:
            print("WebSocket connected")
        case .text(let string):
            if let data = string.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                handleMessage(json)
            }
        case .disconnected(let reason, let code):
            print("WebSocket disconnected: \(reason) Code: \(code)")
        case .error(let error):
            print("WebSocket error: \(error?.localizedDescription ?? "")")
        default:
            break
        }
    }

    private func handleMessage(_ message: [String: Any]) {
        guard let type = message["type"] as? String,
              let data = message["data"] as? [String: Any] else { return }
        
        switch type {
        case "message":
            onMessage?(try! JSONSerialization.data(withJSONObject: data))
        case "typing":
            onTyping?(try! JSONSerialization.data(withJSONObject: data))
        case "user_status":
            onUserStatus?(try! JSONSerialization.data(withJSONObject: data))
        default:
            break
        }
    }
}
```

### Android Kotlin Example

```kotlin
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class ChatService {
    private var webSocket: WebSocket? = null
    private var currentRoomId: Int? = null
    
    var onMessage: ((JSONObject) -> Unit)? = null
    var onTyping: ((JSONObject) -> Unit)? = null
    var onUserStatus: ((JSONObject) -> Unit)? = null

    fun connect() {
        val token = getToken() // Get from SharedPreferences
        val client = OkHttpClient.Builder()
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .build()

        val request = Request.Builder()
            .url("ws://localhost:8000/api/chat/ws/chat?token=$token")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("WebSocket connected")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                val message = JSONObject(text)
                handleMessage(message)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                println("WebSocket closing: $reason")
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("WebSocket error: ${t.message}")
            }
        })
    }

    fun joinRoom(roomId: Int) {
        currentRoomId = roomId
        val data = JSONObject().apply {
            put("type", "join_room")
            put("data", JSONObject().put("room_id", roomId))
        }
        send(data)
    }

    fun sendMessage(content: String, type: String = "text", extraData: JSONObject = JSONObject()) {
        val roomId = currentRoomId ?: return
        
        val messageData = JSONObject().apply {
            put("room_id", roomId)
            put("content", content)
            put("message_type", type)
        }
        
        // Merge extraData
        extraData.keys().forEach { key ->
            messageData.put(key, extraData.get(key))
        }

        val data = JSONObject().apply {
            put("type", "message")
            put("data", messageData)
        }
        send(data)
    }

    private fun send(data: JSONObject) {
        webSocket?.send(data.toString())
    }

    private fun handleMessage(message: JSONObject) {
        val type = message.getString("type")
        val data = message.getJSONObject("data")
        
        when (type) {
            "message" -> onMessage?.invoke(data)
            "typing" -> onTyping?.invoke(data)
            "user_status" -> onUserStatus?.invoke(data)
        }
    }

    fun disconnect() {
        webSocket?.close(1000, "Goodbye")
        webSocket = null
    }
}
```

## Error Handling

### WebSocket Error Codes
- **4001**: Authentication failed
- **1000**: Normal closure
- **1006**: Abnormal closure

### HTTP Error Codes
- **401**: Unauthorized (invalid token)
- **403**: Forbidden (no access to room/message)
- **404**: Room/Message not found
- **400**: Bad request (validation error)

## Best Practices

### 1. **Connection Management**
```javascript
// Reconnection logic
function connectWithRetry() {
    connect().catch(() => {
        setTimeout(connectWithRetry, 5000); // Retry after 5 seconds
    });
}
```

### 2. **Message Queuing**
```javascript
// Queue messages when offline
const messageQueue = [];

function sendMessage(message) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        messageQueue.push(message);
    }
}

// Send queued messages when reconnected
ws.onopen = () => {
    while (messageQueue.length > 0) {
        ws.send(JSON.stringify(messageQueue.shift()));
    }
};
```

### 3. **Typing Debouncing**
```javascript
let typingTimer;

function onTyping() {
    chatService.sendTyping(true);
    
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        chatService.sendTyping(false);
    }, 1000); // Stop typing after 1 second of inactivity
}
```

### 4. **Message Caching**
```javascript
// Cache messages locally
const messageCache = new Map();

function cacheMessage(roomId, message) {
    if (!messageCache.has(roomId)) {
        messageCache.set(roomId, []);
    }
    messageCache.get(roomId).push(message);
}

function getCachedMessages(roomId) {
    return messageCache.get(roomId) || [];
}
```

### 5. **File Upload Progress**
```javascript
async function uploadWithProgress(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);
    
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const progress = (e.loaded / e.total) * 100;
                onProgress(progress);
            }
        });
        
        xhr.onload = () => {
            if (xhr.status === 200) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error('Upload failed'));
            }
        };
        
        xhr.open('POST', '/api/chat/upload');
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        xhr.send(formData);
    });
}
```

## Security Considerations

1. **Token Validation**: Luôn validate JWT token trước khi cho phép WebSocket connection
2. **Rate Limiting**: Implement rate limiting cho message sending
3. **File Validation**: Validate file type và size trước khi upload
4. **Content Filtering**: Filter harmful content trong messages
5. **Room Access**: Verify user có quyền truy cập room trước khi join

## Performance Tips

1. **Message Pagination**: Load messages theo batch để tránh lag
2. **Image Compression**: Compress images trước khi upload
3. **Connection Pooling**: Reuse connections khi có thể
4. **Background Sync**: Sync messages khi app trở lại foreground
5. **Memory Management**: Clear old messages khỏi memory khi không cần

## Testing

### 1. **Unit Tests**
```javascript
// Test message formatting
test('should format message correctly', () => {
    const message = formatMessage('Hello', 'text', 1);
    expect(message.type).toBe('message');
    expect(message.data.content).toBe('Hello');
});
```

### 2. **Integration Tests**
```javascript
// Test WebSocket connection
test('should connect to WebSocket successfully', async () => {
    const chatService = new ChatService();
    await chatService.connect();
    expect(chatService.isConnected()).toBe(true);
});
```

### 3. **E2E Tests**
```javascript
// Test full chat flow
test('should send and receive messages', async () => {
    const user1 = new ChatService();
    const user2 = new ChatService();
    
    await Promise.all([user1.connect(), user2.connect()]);
    
    user1.joinRoom(1);
    user2.joinRoom(1);
    
    user1.sendMessage('Hello');
    
    // Wait for message to be received
    await new Promise(resolve => {
        user2.onMessage((message) => {
            expect(message.content).toBe('Hello');
            resolve();
        });
    });
});
```

Hệ thống chat mobile của GreenBuy giờ đã sẵn sàng cho production với đầy đủ tính năng và documentation! 🚀📱 