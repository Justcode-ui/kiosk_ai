"""
WebSocket Manager for Real-time Notifications
Handles WebSocket connections for in-app notifications
"""

from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user's connections"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def notify_new_message(
        self,
        user_id: str,
        customer_name: str,
        message_content: str,
        platform: str
    ):
        """Send real-time notification for new message"""
        notification = {
            'type': 'new_message',
            'data': {
                'customer_name': customer_name,
                'message': message_content,
                'platform': platform,
                'timestamp': str(datetime.utcnow())
            }
        }
        await self.send_personal_message(notification, user_id)
    
    async def notify_urgent_inquiry(
        self,
        user_id: str,
        customer_name: str,
        message_content: str
    ):
        """Send real-time notification for urgent inquiry"""
        notification = {
            'type': 'urgent_inquiry',
            'data': {
                'customer_name': customer_name,
                'message': message_content,
                'timestamp': str(datetime.utcnow())
            },
            'priority': 'high'
        }
        await self.send_personal_message(notification, user_id)
    
    async def notify_refund_request(
        self,
        user_id: str,
        customer_name: str,
        order_number: str,
        amount: float
    ):
        """Send real-time notification for refund request"""
        notification = {
            'type': 'refund_request',
            'data': {
                'customer_name': customer_name,
                'order_number': order_number,
                'amount': amount,
                'timestamp': str(datetime.utcnow())
            },
            'priority': 'high'
        }
        await self.send_personal_message(notification, user_id)
    
    async def notify_high_value_lead(
        self,
        user_id: str,
        customer_name: str,
        estimated_value: float
    ):
        """Send real-time notification for high-value lead"""
        notification = {
            'type': 'high_value_lead',
            'data': {
                'customer_name': customer_name,
                'estimated_value': estimated_value,
                'timestamp': str(datetime.utcnow())
            },
            'priority': 'high'
        }
        await self.send_personal_message(notification, user_id)
    
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))


# Global connection manager instance
manager = ConnectionManager()
