"""
WebSocket Endpoints
Real-time communication endpoints
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.websocket import manager
from app.core.logging import get_logger
from typing import Optional

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        token: Optional authentication token
    """
    # TODO: Add token validation here
    # For now, we'll accept any connection for development

    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "join_room":
                room = data.get("room")
                if room:
                    await manager.join_room(user_id, room)
                    await websocket.send_json({
                        "type": "room_joined",
                        "room": room
                    })

            elif message_type == "leave_room":
                room = data.get("room")
                if room:
                    await manager.leave_room(user_id, room)
                    await websocket.send_json({
                        "type": "room_left",
                        "room": room
                    })

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                # Echo unknown messages back
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket client {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.disconnect(websocket, user_id)


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket server status.

    Returns:
        dict: WebSocket status information
    """
    return {
        "active_users": manager.get_active_users(),
        "connection_count": manager.get_connection_count(),
        "rooms": {
            room: manager.get_room_users(room)
            for room in manager.rooms.keys()
        }
    }