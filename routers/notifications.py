"""
Notification router for managing push notifications and preferences.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.notification import NotificationPreference, Notification, DeviceToken
from services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


class NotificationPreferencesUpdate(BaseModel):
    circle_messages: Optional[bool] = None
    message_support: Optional[bool] = None
    circle_invitations: Optional[bool] = None
    reflection_helpful: Optional[bool] = None
    crisis_alerts: Optional[bool] = None
    daily_check_in: Optional[bool] = None
    weekly_summary: Optional[bool] = None
    push_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class DeviceTokenCreate(BaseModel):
    token: str
    platform: str  # ios, android, web
    device_id: Optional[str] = None
    device_name: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    data: Dict[str, Any]
    priority: str
    category: str
    is_read: bool
    created_at: str
    read_at: Optional[str] = None


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences."""
    try:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == current_user.id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=current_user.id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return {
            "circle_messages": prefs.circle_messages,
            "message_support": prefs.message_support,
            "circle_invitations": prefs.circle_invitations,
            "reflection_helpful": prefs.reflection_helpful,
            "crisis_alerts": prefs.crisis_alerts,
            "daily_check_in": prefs.daily_check_in,
            "weekly_summary": prefs.weekly_summary,
            "push_notifications": prefs.push_notifications,
            "email_notifications": prefs.email_notifications,
            "in_app_notifications": prefs.in_app_notifications,
            "quiet_hours_enabled": prefs.quiet_hours_enabled,
            "quiet_hours_start": prefs.quiet_hours_start,
            "quiet_hours_end": prefs.quiet_hours_end
        }
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences."""
    try:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = NotificationPreference(user_id=current_user.id)
            db.add(prefs)
        
        # Update only provided fields
        update_data = preferences.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)
        
        db.commit()
        db.refresh(prefs)
        
        return {"message": "Notification preferences updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.post("/device-token")
async def register_device_token(
    device_data: DeviceTokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register a device token for push notifications."""
    try:
        # Check if token already exists
        existing_token = db.query(DeviceToken).filter(
            DeviceToken.token == device_data.token
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.user_id = current_user.id
            existing_token.platform = device_data.platform
            existing_token.device_id = device_data.device_id
            existing_token.device_name = device_data.device_name
            existing_token.is_active = True
        else:
            # Create new token
            new_token = DeviceToken(
                user_id=current_user.id,
                token=device_data.token,
                platform=device_data.platform,
                device_id=device_data.device_id,
                device_name=device_data.device_name
            )
            db.add(new_token)
        
        db.commit()
        
        return {"message": "Device token registered successfully"}
        
    except Exception as e:
        logger.error(f"Error registering device token: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.delete("/device-token/{token}")
async def unregister_device_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unregister a device token."""
    try:
        device_token = db.query(DeviceToken).filter(
            DeviceToken.token == token,
            DeviceToken.user_id == current_user.id
        ).first()
        
        if not device_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found"
            )
        
        device_token.is_active = False
        db.commit()
        
        return {"message": "Device token unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering device token: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notifications."""
    try:
        notifications = await notification_service.get_user_notifications(
            db, current_user.id, limit, unread_only
        )
        
        return [NotificationResponse(**notif) for notif in notifications]
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.post("/mark-read")
async def mark_notifications_read(
    notification_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark notifications as read."""
    try:
        success = await notification_service.mark_notifications_read(
            db, current_user.id, notification_ids
        )
        
        if success:
            return {"message": f"Marked {len(notification_ids)} notifications as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notifications as read"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications."""
    try:
        count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.post("/test")
async def send_test_notification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test notification (for development)."""
    try:
        success = await notification_service.send_notification(
            db,
            current_user.id,
            "daily_check_in",
            {"type": "test", "message": "This is a test notification"}
        )
        
        if success:
            return {"message": "Test notification sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test notification"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )
