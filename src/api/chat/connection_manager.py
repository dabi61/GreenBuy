"""
WebSocket Connection Manager for Mobile Chat
Manages WebSocket connections, user presence, and message routing
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
from fastapi import WebSocket
from sqlmodel import Session
from api.chat.model import OnlineStatus, ChatRoom, ChatMessage
from api.auth.auth import get_session

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for mobile chat"""
    
    def __init__(self):
        # {user_id: websocket}
        self.user_connections: Dict[int, WebSocket] = {}
        
        # {room_id: {user_id: websocket}}
        self.room_connections: Dict[int, Dict[int, WebSocket]] = {}
        
        # {room_id: {user_id: is_typing}}
        self.typing_status: Dict[int, Dict[int, bool]] = {}
        
        # Track connection heartbeats for mobile apps
        self.connection_heartbeats: Dict[int, datetime] = {}
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_checker())
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
    
    async def connect_user(self, user_id: int, websocket: WebSocket, device_info: str = "mobile"):
        """Connect a user to the chat system"""
        # Close existing connection if any
        await self.disconnect_user(user_id)
        
        # Store new connection
        self.user_connections[user_id] = websocket
        self.connection_heartbeats[user_id] = datetime.utcnow()
        
        # Update online status in database
        await self._update_online_status(user_id, True, device_info)
        
        # Notify other users about online status
        await self._broadcast_user_status(user_id, True)
        
        logger.info(f"User {user_id} connected from {device_info}")
    
    async def disconnect_user(self, user_id: int):
        """Disconnect a user from the chat system"""
        # Remove from user connections
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].close()
            except:
                pass
            del self.user_connections[user_id]
        
        # Remove from room connections
        for room_id in list(self.room_connections.keys()):
            if user_id in self.room_connections[room_id]:
                del self.room_connections[room_id][user_id]
                # Clean empty rooms
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
        
        # Clear typing status
        for room_id in self.typing_status:
            if user_id in self.typing_status[room_id]:
                del self.typing_status[room_id][user_id]
        
        # Remove heartbeat tracking
        if user_id in self.connection_heartbeats:
            del self.connection_heartbeats[user_id]
        
        # Update online status in database
        await self._update_online_status(user_id, False)
        
        # Notify other users about offline status
        await self._broadcast_user_status(user_id, False)
        
        logger.info(f"User {user_id} disconnected")
    
    async def join_room(self, user_id: int, room_id: int) -> bool:
        """Add user to a chat room"""
        if user_id not in self.user_connections:
            return False
        
        # Verify user has access to this room
        session = next(get_session())
        room = session.get(ChatRoom, room_id)
        if not room or (room.user1_id != user_id and room.user2_id != user_id):
            return False
        
        # Add to room connections
        if room_id not in self.room_connections:
            self.room_connections[room_id] = {}
        
        self.room_connections[room_id][user_id] = self.user_connections[user_id]
        
        logger.info(f"User {user_id} joined room {room_id}")
        return True
    
    async def leave_room(self, user_id: int, room_id: int):
        """Remove user from a chat room"""
        if room_id in self.room_connections and user_id in self.room_connections[room_id]:
            del self.room_connections[room_id][user_id]
            
            # Clean empty room
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        
        # Clear typing status for this room
        if room_id in self.typing_status and user_id in self.typing_status[room_id]:
            del self.typing_status[room_id][user_id]
        
        logger.info(f"User {user_id} left room {room_id}")
    
    async def broadcast_to_room(self, room_id: int, message: dict, exclude_user_id: Optional[int] = None):
        """Broadcast message to all users in a room"""
        if room_id not in self.room_connections:
            return
        
        message_str = json.dumps(message)
        dead_connections = []
        
        for user_id, websocket in self.room_connections[room_id].items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            try:
                await websocket.send_text(message_str)
                # Update heartbeat
                self.connection_heartbeats[user_id] = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                dead_connections.append(user_id)
        
        # Clean up dead connections
        for user_id in dead_connections:
            await self.disconnect_user(user_id)
    
    async def send_to_user(self, user_id: int, message: dict) -> bool:
        """Send message directly to a specific user"""
        if user_id not in self.user_connections:
            return False
        
        try:
            await self.user_connections[user_id].send_text(json.dumps(message))
            self.connection_heartbeats[user_id] = datetime.utcnow()
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")
            await self.disconnect_user(user_id)
            return False
    
    async def update_typing_status(self, user_id: int, room_id: int, is_typing: bool):
        """Update typing status for a user in a room"""
        if room_id not in self.typing_status:
            self.typing_status[room_id] = {}
        
        self.typing_status[room_id][user_id] = is_typing
        
        # Broadcast typing status to other users in room
        typing_message = {
            "type": "typing",
            "data": {
                "room_id": room_id,
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self.broadcast_to_room(room_id, typing_message, exclude_user_id=user_id)
    
    def get_room_users(self, room_id: int) -> Set[int]:
        """Get list of users currently in a room"""
        if room_id in self.room_connections:
            return set(self.room_connections[room_id].keys())
        return set()
    
    def get_online_users(self) -> Set[int]:
        """Get list of all online users"""
        return set(self.user_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is currently online"""
        return user_id in self.user_connections
    
    def get_user_rooms(self, user_id: int) -> List[int]:
        """Get list of rooms a user is currently in"""
        rooms = []
        for room_id, users in self.room_connections.items():
            if user_id in users:
                rooms.append(room_id)
        return rooms
    
    async def heartbeat(self, user_id: int):
        """Update heartbeat for a user connection"""
        if user_id in self.user_connections:
            self.connection_heartbeats[user_id] = datetime.utcnow()
    
    async def _update_online_status(self, user_id: int, is_online: bool, device_info: Optional[str] = None):
        """Update user online status in database"""
        try:
            session = next(get_session())
            
            status = session.get(OnlineStatus, user_id)
            if status:
                status.is_online = is_online
                status.last_seen = datetime.utcnow()
                status.updated_at = datetime.utcnow()
                if device_info:
                    status.device_info = device_info
            else:
                status = OnlineStatus(
                    user_id=user_id,
                    is_online=is_online,
                    device_info=device_info or "unknown"
                )
                session.add(status)
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update online status for user {user_id}: {e}")
    
    async def _broadcast_user_status(self, user_id: int, is_online: bool):
        """Broadcast user online status to relevant rooms"""
        try:
            session = next(get_session())
            
            # Find all rooms where this user participates
            from sqlmodel import select, or_
            rooms = session.exec(
                select(ChatRoom).where(
                    or_(ChatRoom.user1_id == user_id, ChatRoom.user2_id == user_id)
                )
            ).all()
            
            status_message = {
                "type": "user_status",
                "data": {
                    "user_id": user_id,
                    "is_online": is_online,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Broadcast to all relevant rooms
            for room in rooms:
                await self.broadcast_to_room(room.id, status_message, exclude_user_id=user_id)
            
        except Exception as e:
            logger.error(f"Failed to broadcast user status for user {user_id}: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of dead connections and old data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old typing status (older than 30 seconds)
                cutoff_time = datetime.utcnow() - timedelta(seconds=30)
                
                for room_id in list(self.typing_status.keys()):
                    for user_id in list(self.typing_status[room_id].keys()):
                        if user_id not in self.connection_heartbeats:
                            del self.typing_status[room_id][user_id]
                        elif self.connection_heartbeats[user_id] < cutoff_time:
                            # Auto-stop typing for inactive users
                            if self.typing_status[room_id][user_id]:
                                await self.update_typing_status(user_id, room_id, False)
                    
                    # Clean empty rooms
                    if not self.typing_status[room_id]:
                        del self.typing_status[room_id]
                
                logger.debug("Completed periodic cleanup")
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _heartbeat_checker(self):
        """Check for stale connections based on heartbeat"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)  # 5 minute timeout
                stale_users = []
                
                for user_id, last_heartbeat in self.connection_heartbeats.items():
                    if last_heartbeat < cutoff_time:
                        stale_users.append(user_id)
                
                # Disconnect stale users
                for user_id in stale_users:
                    logger.warning(f"Disconnecting stale user {user_id}")
                    await self.disconnect_user(user_id)
                
            except Exception as e:
                logger.error(f"Error in heartbeat checker: {e}")

# Global connection manager instance
connection_manager = ConnectionManager()

async def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager 