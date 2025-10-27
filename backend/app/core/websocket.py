"""
WebSocket Manager for Real-time Updates
Provides WebSocket connection management and message broadcasting
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
from datetime import datetime
import json
import asyncio
from app.core.logging import get_logger
from app.core.config import settings
import redis.asyncio as aioredis

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.

    Supports:
    - Per-user connections
    - Room-based broadcasting
    - Redis pub/sub for horizontal scaling
    """

    def __init__(self):
        # Active connections: {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # Room subscriptions: {room_name: {user_id1, user_id2, ...}}
        self.rooms: Dict[str, Set[str]] = {}

        # Redis pub/sub for distributed messaging
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub = None

    async def connect_redis(self):
        """Initialize Redis connection for pub/sub"""
        try:
            self.redis = await aioredis.from_url(
                settings.WS_MESSAGE_QUEUE,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Redis connected for WebSocket pub/sub")

            # Subscribe to broadcast channel
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("ws:broadcast")

            # Start listening for messages
            asyncio.create_task(self._listen_redis())
        except Exception as e:
            logger.warning(f"Redis connection failed for WebSocket: {e}")
            self.redis = None

    async def disconnect_redis(self):
        """Close Redis connection and clean up"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe("ws:broadcast")
                await self.pubsub.close()
                logger.info("Redis pub/sub closed")
            if self.redis:
                await self.redis.close()
                logger.info("Redis connection closed for WebSocket")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    async def _listen_redis(self):
        """Listen for messages from Redis pub/sub"""
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._broadcast_local(
                        data["message"],
                        data.get("user_id"),
                        data.get("room")
                    )
        except Exception as e:
            logger.error(f"Redis pub/sub error: {e}")

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Disconnect a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                logger.warning(f"WebSocket not found in connections for user {user_id}")

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from all rooms
        for room_name in list(self.rooms.keys()):
            if user_id in self.rooms[room_name]:
                self.rooms[room_name].discard(user_id)
                if not self.rooms[room_name]:
                    del self.rooms[room_name]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def join_room(self, user_id: str, room: str):
        """
        Add user to a room.

        Args:
            user_id: User ID
            room: Room name
        """
        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(user_id)
        logger.info(f"User {user_id} joined room {room}")

    async def leave_room(self, user_id: str, room: str):
        """
        Remove user from a room.

        Args:
            user_id: User ID
            room: Room name
        """
        if room in self.rooms and user_id in self.rooms[room]:
            self.rooms[room].discard(user_id)

            if not self.rooms[room]:
                del self.rooms[room]

            logger.info(f"User {user_id} left room {room}")

    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send message to a specific user.

        Args:
            message: Message data
            user_id: User ID
        """
        if user_id in self.active_connections:
            # Send to all connections for this user
            # Note: timestamp should be added by the caller, not here
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")

    async def broadcast_to_room(self, message: dict, room: str):
        """
        Broadcast message to all users in a room.

        Args:
            message: Message data
            room: Room name
        """
        if room in self.rooms:
            # Add timestamp once
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            for user_id in self.rooms[room]:
                await self.send_personal_message(message, user_id)

        # Publish to Redis for other instances
        if self.redis:
            try:
                await self.redis.publish(
                    "ws:broadcast",
                    json.dumps({
                        "message": message,
                        "room": room
                    })
                )
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected users.

        Args:
            message: Message data
        """
        # Add timestamp once
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        for user_id in self.active_connections:
            await self.send_personal_message(message, user_id)

        # Publish to Redis for other instances
        if self.redis:
            try:
                await self.redis.publish(
                    "ws:broadcast",
                    json.dumps({"message": message})
                )
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    async def _broadcast_local(self, message: dict, user_id: Optional[str] = None, room: Optional[str] = None):
        """
        Local broadcast without Redis pub/sub.

        Args:
            message: Message data
            user_id: User ID (optional)
            room: Room name (optional)
        """
        if user_id:
            await self.send_personal_message(message, user_id)
        elif room:
            await self.broadcast_to_room(message, room)
        else:
            await self.broadcast(message)

    def get_active_users(self) -> List[str]:
        """Get list of active user IDs"""
        return list(self.active_connections.keys())

    def get_room_users(self, room: str) -> List[str]:
        """Get list of users in a room"""
        return list(self.rooms.get(room, set()))

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


async def notify_scan_update(scan_id: str, status: str, progress: int, message: str = ""):
    """
    Send scan update notification to all users in scan room.

    Args:
        scan_id: Scan task ID
        status: Scan status
        progress: Progress percentage (0-100)
        message: Optional message
    """
    await manager.broadcast_to_room(
        {
            "type": "scan_update",
            "scan_id": scan_id,
            "status": status,
            "progress": progress,
            "message": message
        },
        f"scan:{scan_id}"
    )


async def notify_vulnerability_found(vulnerability_id: str, severity: str, title: str):
    """
    Send vulnerability notification to all connected users.

    Args:
        vulnerability_id: Vulnerability ID
        severity: Vulnerability severity
        title: Vulnerability title
    """
    await manager.broadcast(
        {
            "type": "vulnerability_found",
            "vulnerability_id": vulnerability_id,
            "severity": severity,
            "title": title
        }
    )


async def notify_asset_discovered(asset_id: str, asset_type: str, name: str):
    """
    Send asset discovery notification.

    Args:
        asset_id: Asset ID
        asset_type: Asset type
        name: Asset name
    """
    await manager.broadcast(
        {
            "type": "asset_discovered",
            "asset_id": asset_id,
            "asset_type": asset_type,
            "name": name
        }
    )