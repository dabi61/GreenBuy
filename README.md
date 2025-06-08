# GreenBuy
Migrate db bang alembic
alembic revision --autogenerate -m "Replace is_buyer with role enum"
confirm
alembic upgrade head


Để ứng dụng Android dùng WebSocket chat một cách đúng đắn và không bị lỗi hiển thị lịch sử phòng cũ sau khi chuyển phòng, bạn cần triển khai đúng logic xử lý phòng chat và kết nối WebSocket trên cả phía backend (FastAPI) và frontend (Android). Dưới đây là hướng dẫn chi tiết:

✅ 1. Mục tiêu
Khi người dùng chuyển sang phòng chat mới, chỉ nhận và hiển thị tin nhắn của phòng mới.

Không bị giữ lại lịch sử chat của phòng cũ trên giao diện.

🧩 2. Vấn đề đang gặp
Trên web, khi chuyển sang phòng khác, WebSocket vẫn còn nhận/gửi tin nhắn từ phòng cũ do chưa đóng kết nối cũ hoặc chưa thay đổi đúng tham số phòng.

🧑‍💻 3. Cách xử lý đúng phía Android
A. Mỗi phòng chat → mở 1 WebSocket riêng
Giả sử backend đang dùng route như sau:

ruby
Sao chép
Chỉnh sửa
ws://yourdomain.com/ws/chat/{room_id}
✅ Khi chọn phòng chat mới:
Đóng WebSocket cũ (nếu đang mở).

Tạo kết nối mới đến /ws/chat/{new_room_id}.

Xoá danh sách tin nhắn cũ trong UI.

Tải lại lịch sử chat từ REST API (nếu có).

Nghe tin nhắn mới từ WebSocket mới.

💡 Kotlin ví dụ (Android)
kotlin
Sao chép
Chỉnh sửa
var webSocket: WebSocket? = null

fun connectToRoom(roomId: Int) {
    // Đóng kết nối cũ nếu có
    webSocket?.close(1000, "Leaving room")

    // Xoá tin nhắn cũ khỏi RecyclerView
    messageAdapter.clearMessages()

    val request = Request.Builder()
        .url("wss://yourdomain.com/ws/chat/$roomId")
        .build()

    webSocket = client.newWebSocket(request, object : WebSocketListener() {
        override fun onMessage(webSocket: WebSocket, text: String) {
            // Parse và hiển thị tin nhắn mới
        }

        override fun onOpen(webSocket: WebSocket, response: Response) {
            // Load lịch sử từ REST API nếu cần
        }

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
            Log.d("WebSocket", "Closed: $reason")
        }
    })
}
🧠 4. Backend (FastAPI) cần đảm bảo
WebSocket route được gắn với từng room_id.

python
Sao chép
Chỉnh sửa
@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    # Kiểm tra room tồn tại
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        await websocket.close()
        return

    # Lưu connection vào room
    active_connections[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Parse data, lưu vào DB với room_id
            # Gửi lại cho các client cùng room_id
            for ws in active_connections[room_id]:
                await ws.send_text(data)
    except WebSocketDisconnect:
        active_connections[room_id].remove(websocket)
🧾 5. Tải lịch sử chat (REST API)
WebSocket không nên gửi toàn bộ lịch sử khi mới kết nối – thay vào đó, bạn nên có một REST API như:

http
Sao chép
Chỉnh sửa
GET /api/chat/rooms/{room_id}/messages
→ Client gọi API này khi onOpen rồi hiển thị lịch sử trong RecyclerView trước khi nhận thêm tin nhắn mới qua WebSocket.

✅ Tóm tắt
Bước	Nội dung
1	Khi đổi phòng, đóng WebSocket cũ
2	Xoá dữ liệu UI cũ
3	Mở WebSocket mới với room_id mới
4	Gọi REST API để tải lịch sử chat
5	Lắng nghe WebSocket để nhận tin nhắn mới

Nếu bạn cần mình viết mẫu WebSocket + REST API đầy đủ (cả FastAPI lẫn Android), cứ nói nhé!