"""
Users router for user profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from database import get_db
from routers.auth import get_current_active_user
from models.user import User, UserPreferences
from models.conversation import Conversation
from models.emotion import EmotionAnalysis
from models.recommendation import Recommendation
from schemas.user import UserResponse, UserUpdate, PasswordChange, UserPreferences as UserPreferencesSchema
from services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile."""
    return current_user


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_user_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard data with statistics."""
    try:
        # Get conversation statistics
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).count()

        # Get emotion analysis statistics
        total_analyses = db.query(EmotionAnalysis).filter(
            EmotionAnalysis.user_id == current_user.id
        ).count()

        # Get recent emotion analysis for mood
        latest_analysis = db.query(EmotionAnalysis).filter(
            EmotionAnalysis.user_id == current_user.id
        ).order_by(EmotionAnalysis.analyzed_at.desc()).first()

        current_mood = "neutral"
        if latest_analysis:
            emotions = {
                "joy": latest_analysis.joy,
                "sadness": latest_analysis.sadness,
                "anger": latest_analysis.anger,
                "fear": latest_analysis.fear
            }
            dominant_emotion = max(emotions, key=emotions.get)
            if emotions[dominant_emotion] > 0.5:
                current_mood = dominant_emotion

        # Get recommendation statistics
        total_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).count()

        completed_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id,
            Recommendation.is_completed == True
        ).count()

        # Get recent activity
        recent_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).order_by(Conversation.updated_at.desc()).limit(3).all()

        recent_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).order_by(Recommendation.created_at.desc()).limit(3).all()

        return {
            "user": UserResponse.model_validate(current_user),
            "statistics": {
                "total_conversations": total_conversations,
                "total_emotion_analyses": total_analyses,
                "total_recommendations": total_recommendations,
                "completed_recommendations": completed_recommendations,
                "completion_rate": (
                    completed_recommendations / total_recommendations * 100
                    if total_recommendations > 0 else 0
                )
            },
            "current_mood": current_mood,
            "recent_activity": {
                "conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "updated_at": conv.updated_at
                    }
                    for conv in recent_conversations
                ],
                "recommendations": [
                    {
                        "id": rec.id,
                        "title": rec.title,
                        "type": rec.type.value,
                        "is_completed": rec.is_completed,
                        "created_at": rec.created_at
                    }
                    for rec in recent_recommendations
                ]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.delete("/profile")
async def delete_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user profile and all associated data."""
    try:
        # This will cascade delete all related data due to relationships
        db.delete(current_user)
        db.commit()

        return {"message": "User profile deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user profile: {str(e)}"
        )


@router.patch("/profile", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    try:
        # Check if username is being updated and if it's already taken
        if update_data.username and update_data.username != current_user.username:
            existing_user = db.query(User).filter(User.username == update_data.username).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(current_user, field, value)

        db.commit()
        db.refresh(current_user)

        return UserResponse.model_validate(current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        # Verify current password
        if not AuthService.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password
        new_hashed_password = AuthService.get_password_hash(password_data.new_password)
        current_user.hashed_password = new_hashed_password

        db.commit()

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.get("/preferences", response_model=UserPreferencesSchema)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user preferences."""
    try:
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        if not preferences:
            # Create default preferences
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)

        return UserPreferencesSchema(
            theme=preferences.theme,
            daily_reminders=preferences.daily_reminders,
            weekly_reports=preferences.weekly_reports,
            recommendations=preferences.recommendations,
            achievements=preferences.achievements,
            language=preferences.language,
            timezone=preferences.timezone
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.patch("/preferences", response_model=UserPreferencesSchema)
async def update_user_preferences(
    preferences_data: UserPreferencesSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    try:
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        if not preferences:
            # Create new preferences
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)

        # Update fields
        update_dict = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(preferences, field, value)

        db.commit()
        db.refresh(preferences)

        return UserPreferencesSchema(
            theme=preferences.theme,
            daily_reminders=preferences.daily_reminders,
            weekly_reports=preferences.weekly_reports,
            recommendations=preferences.recommendations,
            achievements=preferences.achievements,
            language=preferences.language,
            timezone=preferences.timezone
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )
