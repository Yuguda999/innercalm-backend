"""
WebSocket manager for real-time chat functionality.
"""
import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from models.user import User
from models.community import CircleMembership, MembershipStatus, PeerCircle
from services.community_service import CommunityService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""

    def __init__(self):
        # Store active connections by circle_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store user info for each websocket
        self.connection_users: Dict[WebSocket, Dict] = {}
        # Store circle memberships for quick access
        self.user_circles: Dict[int, Set[int]] = {}
        self.community_service = CommunityService()

    async def connect(self, websocket: WebSocket, circle_id: int, user: User, db: Session):
        """Connect a user to a circle chat."""
        try:
            await websocket.accept()

            # Verify user has access to this circle
            membership = db.query(CircleMembership).filter(
                CircleMembership.user_id == user.id,
                CircleMembership.peer_circle_id == circle_id,
                CircleMembership.status == MembershipStatus.ACTIVE
            ).first()

            if not membership:
                await websocket.close(code=4003, reason="Access denied")
                return False

            # Add connection to circle
            if circle_id not in self.active_connections:
                self.active_connections[circle_id] = set()

            self.active_connections[circle_id].add(websocket)

            # Store user info
            self.connection_users[websocket] = {
                "user_id": user.id,
                "user_name": user.full_name or user.username,
                "circle_id": circle_id
            }

            # Update user circles mapping
            if user.id not in self.user_circles:
                self.user_circles[user.id] = set()
            self.user_circles[user.id].add(circle_id)

            # Update last seen
            membership.last_seen_at = datetime.utcnow()
            db.commit()

            # Notify other users that someone joined
            await self.broadcast_to_circle(circle_id, {
                "type": "user_joined",
                "user_name": user.full_name or user.username,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude=websocket)

            logger.info(f"User {user.id} connected to circle {circle_id}")
            return True

        except Exception as e:
            logger.error(f"Error connecting user {user.id} to circle {circle_id}: {e}")
            await websocket.close(code=4000, reason="Connection error")
            return False

    async def disconnect(self, websocket: WebSocket, db: Session = None):
        """Disconnect a user from circle chat."""
        try:
            if websocket not in self.connection_users:
                return

            user_info = self.connection_users[websocket]
            circle_id = user_info["circle_id"]
            user_id = user_info["user_id"]

            # Remove from active connections
            if circle_id in self.active_connections:
                self.active_connections[circle_id].discard(websocket)
                if not self.active_connections[circle_id]:
                    del self.active_connections[circle_id]

            # Remove user info
            del self.connection_users[websocket]

            # Update user circles mapping
            if user_id in self.user_circles:
                self.user_circles[user_id].discard(circle_id)
                if not self.user_circles[user_id]:
                    del self.user_circles[user_id]

            # Update last seen in database (only if db session is provided)
            if db:
                try:
                    membership = db.query(CircleMembership).filter(
                        CircleMembership.user_id == user_id,
                        CircleMembership.peer_circle_id == circle_id
                    ).first()

                    if membership:
                        membership.last_seen_at = datetime.utcnow()
                        db.commit()
                except Exception as e:
                    logger.error(f"Error updating last seen time: {e}")

            # Notify other users that someone left
            await self.broadcast_to_circle(circle_id, {
                "type": "user_left",
                "user_name": user_info["user_name"],
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"User {user_id} disconnected from circle {circle_id}")

        except Exception as e:
            logger.error(f"Error disconnecting websocket: {e}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific websocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket, None)

    async def broadcast_to_circle(self, circle_id: int, message: dict, exclude: WebSocket = None):
        """Broadcast a message to all users in a circle."""
        if circle_id not in self.active_connections:
            return

        message_str = json.dumps(message)
        disconnected = []

        for websocket in self.active_connections[circle_id].copy():
            if websocket == exclude:
                continue

            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.active_connections[circle_id].discard(websocket)
            if websocket in self.connection_users:
                del self.connection_users[websocket]

    async def handle_message(self, websocket: WebSocket, data: dict, db: Session):
        """Handle incoming WebSocket message."""
        try:
            if websocket not in self.connection_users:
                return

            user_info = self.connection_users[websocket]
            message_type = data.get("type")

            if message_type == "chat_message":
                await self.handle_chat_message(websocket, data, db)
            elif message_type == "typing":
                await self.handle_typing_indicator(websocket, data)
            elif message_type == "support_message":
                await self.handle_support_message(websocket, data, db)
            elif message_type == "ping":
                await self.send_personal_message(json.dumps({"type": "pong"}), websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_chat_message(self, websocket: WebSocket, data: dict, db: Session):
        """Handle chat message."""
        try:
            user_info = self.connection_users[websocket]
            circle_id = user_info["circle_id"]
            user_id = user_info["user_id"]

            content = data.get("content", "").strip()
            message_type = data.get("message_type", "text")

            if not content:
                return

            # Save message to database
            message = await self.community_service.send_circle_message(
                db, user_id, circle_id, content, message_type
            )

            # Broadcast to all users in circle
            await self.broadcast_to_circle(circle_id, {
                "type": "new_message",
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "user_id": message.user_id,
                    "user_name": user_info["user_name"],
                    "support_count": message.support_count,
                    "reply_count": message.reply_count,
                    "created_at": message.created_at.isoformat(),
                    "user_has_supported": False
                },
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await self.send_personal_message(json.dumps({
                "type": "error",
                "message": "Failed to send message"
            }), websocket)

    async def handle_typing_indicator(self, websocket: WebSocket, data: dict):
        """Handle typing indicator."""
        try:
            user_info = self.connection_users[websocket]
            circle_id = user_info["circle_id"]

            is_typing = data.get("is_typing", False)

            await self.broadcast_to_circle(circle_id, {
                "type": "typing",
                "user_name": user_info["user_name"],
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude=websocket)

        except Exception as e:
            logger.error(f"Error handling typing indicator: {e}")

    async def handle_support_message(self, websocket: WebSocket, data: dict, db: Session):
        """Handle message support (like/heart)."""
        try:
            user_info = self.connection_users[websocket]
            circle_id = user_info["circle_id"]
            user_id = user_info["user_id"]

            message_id = data.get("message_id")
            support_type = data.get("support_type", "heart")

            if not message_id:
                return

            # Add support to database
            await self.community_service.support_message(db, user_id, message_id, support_type)

            # Broadcast support update
            await self.broadcast_to_circle(circle_id, {
                "type": "message_supported",
                "message_id": message_id,
                "user_name": user_info["user_name"],
                "support_type": support_type,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error handling message support: {e}")

    def get_circle_users(self, circle_id: int) -> List[dict]:
        """Get list of users currently in a circle."""
        if circle_id not in self.active_connections:
            return []

        users = []
        for websocket in self.active_connections[circle_id]:
            if websocket in self.connection_users:
                user_info = self.connection_users[websocket]
                users.append({
                    "user_id": user_info["user_id"],
                    "user_name": user_info["user_name"]
                })

        return users

    def get_connection_count(self, circle_id: int) -> int:
        """Get number of active connections for a circle."""
        return len(self.active_connections.get(circle_id, set()))


# Global connection manager instance
connection_manager = ConnectionManager()
