"""
Content moderation router for admin functions and crisis management.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.community import CircleMessage, ReflectionEntry
from services.content_moderation import moderation_service
from services.notification_service import notification_service

router = APIRouter(prefix="/moderation", tags=["moderation"])
logger = logging.getLogger(__name__)


@router.post("/moderate-content")
async def moderate_content(
    content: str,
    content_type: str = "message",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Moderate content and return moderation results."""
    try:
        result = await moderation_service.moderate_content(
            content, current_user.id, content_type
        )
        
        # Handle crisis alerts
        if result["auto_action"] == "crisis_alert":
            crisis_resources = await moderation_service.handle_crisis_alert(
                content, current_user.id, db, content_type
            )
            if crisis_resources:
                await notification_service.send_crisis_alert(
                    db, current_user.id, crisis_resources
                )
                result["crisis_resources"] = crisis_resources
        
        return result
        
    except Exception as e:
        logger.error(f"Error moderating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to moderate content"
        )


@router.get("/flagged-content")
async def get_flagged_content(
    content_type: Optional[str] = Query(None),
    flag_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get flagged content for review (admin only)."""
    try:
        # Note: In production, add admin role check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # This would query a moderation_logs table
        # For now, return mock data structure
        flagged_items = []
        
        return {
            "flagged_content": flagged_items,
            "total_count": len(flagged_items),
            "filters": {
                "content_type": content_type,
                "flag_type": flag_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting flagged content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load flagged content"
        )


@router.post("/crisis-alert")
async def send_crisis_alert(
    user_id: int,
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send crisis alert to a user (admin only)."""
    try:
        # Note: In production, add admin role check
        
        crisis_resources = await moderation_service.handle_crisis_alert(
            message, user_id, db, "manual_alert"
        )
        
        if crisis_resources:
            await notification_service.send_crisis_alert(
                db, user_id, crisis_resources
            )
            
        return {
            "message": "Crisis alert sent successfully",
            "resources_provided": crisis_resources
        }
        
    except Exception as e:
        logger.error(f"Error sending crisis alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send crisis alert"
        )


@router.get("/moderation-stats")
async def get_moderation_stats(
    days_back: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get moderation statistics (admin only)."""
    try:
        # Note: In production, add admin role check
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # This would query moderation logs
        # For now, return mock statistics
        stats = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back
            },
            "total_content_moderated": 0,
            "flagged_content": {
                "toxic_language": 0,
                "spam": 0,
                "inappropriate": 0,
                "crisis_language": 0,
                "personal_information": 0
            },
            "actions_taken": {
                "approved": 0,
                "flagged": 0,
                "blocked": 0,
                "crisis_alerts": 0
            },
            "crisis_interventions": 0,
            "false_positives": 0
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting moderation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load moderation statistics"
        )


@router.post("/review-content/{content_id}")
async def review_flagged_content(
    content_id: int,
    action: str,  # "approve", "block", "escalate"
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Review and take action on flagged content (admin only)."""
    try:
        # Note: In production, add admin role check
        
        if action not in ["approve", "block", "escalate"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'approve', 'block', or 'escalate'"
            )
        
        # This would update the moderation record
        # For now, just log the action
        logger.info(f"Content {content_id} reviewed by {current_user.id}: {action}")
        
        return {
            "message": f"Content {action}ed successfully",
            "content_id": content_id,
            "action": action,
            "reviewer": current_user.id,
            "notes": notes
        }
        
    except Exception as e:
        logger.error(f"Error reviewing content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review content"
        )


@router.get("/crisis-resources")
async def get_crisis_resources():
    """Get available crisis resources."""
    try:
        resources = {
            "immediate_help": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "phone": "988",
                    "available": "24/7",
                    "description": "Free and confidential emotional support"
                },
                {
                    "name": "Crisis Text Line",
                    "text": "Text HOME to 741741",
                    "available": "24/7",
                    "description": "Free crisis support via text message"
                }
            ],
            "international": [
                {
                    "name": "International Association for Suicide Prevention",
                    "website": "https://www.iasp.info/resources/Crisis_Centres/",
                    "description": "Global crisis center directory"
                }
            ],
            "online_support": [
                {
                    "name": "7 Cups",
                    "website": "https://www.7cups.com",
                    "description": "Free emotional support and counseling"
                }
            ]
        }
        
        return resources
        
    except Exception as e:
        logger.error(f"Error getting crisis resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load crisis resources"
        )
