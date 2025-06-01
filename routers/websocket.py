"""
WebSocket router for real-time chat functionality.
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database import get_db
from models.user import User
from services.websocket_manager import connection_manager
from config import settings
from routers.auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_from_token(token: str, db: Session) -> User:
    """Get user from JWT token for WebSocket authentication."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user


@router.websocket("/ws/circles/{circle_id}")
async def websocket_circle_chat(
    websocket: WebSocket,
    circle_id: int,
    token: str
):
    """WebSocket endpoint for circle chat."""
    user = None
    try:
        # Authenticate user with a fresh database session
        db = next(get_db())
        try:
            user = await get_user_from_token(token, db)
        finally:
            db.close()

        # Connect to circle with a fresh database session
        db = next(get_db())
        try:
            connected = await connection_manager.connect(websocket, circle_id, user, db)
        finally:
            db.close()

        if not connected:
            return

        try:
            while True:
                # Receive message
                data = await websocket.receive_text()

                try:
                    message_data = json.loads(data)
                    # Handle message with a fresh database session
                    db = next(get_db())
                    try:
                        await connection_manager.handle_message(websocket, message_data, db)
                    finally:
                        db.close()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")
                    await connection_manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Invalid message format"}),
                        websocket
                    )
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await connection_manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Failed to process message"}),
                        websocket
                    )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'} in circle {circle_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user.id if user else 'unknown'} in circle {circle_id}: {e}")
        finally:
            # Disconnect with a fresh database session
            if user:
                db = next(get_db())
                try:
                    await connection_manager.disconnect(websocket, db)
                finally:
                    db.close()

    except HTTPException:
        logger.warning(f"Unauthorized WebSocket connection attempt for circle {circle_id}")
        await websocket.close(code=4001, reason="Unauthorized")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")


@router.get("/circles/{circle_id}/online-users")
async def get_online_users(
    circle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of users currently online in a circle."""
    try:
        # Verify user has access to circle
        from models.community import CircleMembership, MembershipStatus
        membership = db.query(CircleMembership).filter(
            CircleMembership.user_id == current_user.id,
            CircleMembership.peer_circle_id == circle_id,
            CircleMembership.status == MembershipStatus.ACTIVE
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this circle"
            )

        online_users = connection_manager.get_circle_users(circle_id)
        connection_count = connection_manager.get_connection_count(circle_id)

        return {
            "circle_id": circle_id,
            "online_users": online_users,
            "connection_count": connection_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting online users for circle {circle_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get online users"
        )
