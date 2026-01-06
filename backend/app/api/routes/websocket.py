"""
WebSocket API Routes for Real-time Notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.dependencies import get_current_user_from_token
from app.services.websocket.websocket_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time notifications
    Connect with: ws://localhost:8000/ws/notifications?token=YOUR_JWT_TOKEN
    """
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        # Verify token and get user
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Connect WebSocket
        await manager.connect(websocket, str(user.id))
        
        try:
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "message": "Connected to KioskAI notifications",
                "user_id": str(user.id)
            })
            
            # Keep connection alive and listen for messages
            while True:
                # Receive messages from client (for heartbeat/ping)
                data = await websocket.receive_text()
                
                # Echo back for heartbeat
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, str(user.id))
            logger.info(f"WebSocket disconnected for user {user.id}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.get("/active-connections")
async def get_active_connections():
    """Get list of active WebSocket connections (for debugging)"""
    return {
        "active_users": manager.get_active_users(),
        "total_connections": sum(
            manager.get_connection_count(user_id) 
            for user_id in manager.get_active_users()
        )
    }
