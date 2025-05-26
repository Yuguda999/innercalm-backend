"""
Analytics router for advanced progress tracking and insights.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.analytics import (
    AnalyticsEvent, MoodTrend, ProgressInsight,
    ConversationAnalytics, UserProgressMetrics
)
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_service = AnalyticsService()


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get comprehensive analytics dashboard data."""
    try:
        # Calculate recent progress metrics
        progress_metrics = await analytics_service.calculate_user_progress_metrics(
            db, current_user.id, "weekly"
        )

        # Analyze mood trends
        mood_trend = await analytics_service.analyze_mood_trends(
            db, current_user.id, days_back
        )

        # Get recent insights
        recent_insights = db.query(ProgressInsight).filter(
            ProgressInsight.user_id == current_user.id
        ).order_by(ProgressInsight.generated_at.desc()).limit(5).all()

        # Get recent analytics events
        recent_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == current_user.id
        ).order_by(AnalyticsEvent.event_timestamp.desc()).limit(10).all()

        # Get conversation analytics summary
        conversation_analytics = db.query(ConversationAnalytics).filter(
            ConversationAnalytics.user_id == current_user.id
        ).order_by(ConversationAnalytics.analyzed_at.desc()).limit(5).all()

        # Calculate streak days
        streak_days = await analytics_service.calculate_streak_days(db, current_user.id)

        return {
            "user_id": current_user.id,
            "analysis_period_days": days_back,
            "progress_metrics": {
                "overall_progress_score": progress_metrics.overall_progress_score if progress_metrics else 0.0,
                "emotional_growth_score": progress_metrics.emotional_growth_score if progress_metrics else 0.5,
                "mood_stability": progress_metrics.mood_stability if progress_metrics else 0.5,
                "engagement_consistency": progress_metrics.engagement_consistency if progress_metrics else 0.0,
                "therapeutic_engagement": progress_metrics.therapeutic_engagement_score if progress_metrics else 0.0,
                "crisis_episodes": progress_metrics.crisis_episodes if progress_metrics else 0,
                "breakthrough_moments": progress_metrics.breakthrough_moments if progress_metrics else 0,
                "streak_days": streak_days
            },
            "mood_trend": {
                "trend_type": mood_trend.trend_type if mood_trend else "stable",
                "trend_strength": mood_trend.trend_strength if mood_trend else 0.0,
                "dominant_emotion": mood_trend.dominant_emotion if mood_trend else "neutral",
                "average_sentiment": mood_trend.average_sentiment if mood_trend else 0.0,
                "emotion_stability": mood_trend.emotion_stability if mood_trend else 0.5
            } if mood_trend else None,
            "recent_insights": [
                {
                    "id": insight.id,
                    "type": insight.insight_type,
                    "title": insight.insight_title,
                    "description": insight.insight_description,
                    "confidence": insight.confidence_score,
                    "impact_level": insight.impact_level,
                    "is_actionable": insight.is_actionable,
                    "suggested_actions": insight.suggested_actions,
                    "generated_at": insight.generated_at
                }
                for insight in recent_insights
            ],
            "recent_events": [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "name": event.event_name,
                    "severity": event.severity,
                    "timestamp": event.event_timestamp,
                    "tags": event.tags
                }
                for event in recent_events
            ],
            "conversation_summary": [
                {
                    "conversation_id": ca.conversation_id,
                    "total_messages": ca.total_messages,
                    "engagement_score": ca.engagement_score,
                    "mood_change": ca.mood_change,
                    "therapeutic_approach": ca.therapeutic_approach_used,
                    "analyzed_at": ca.analyzed_at
                }
                for ca in conversation_analytics
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics dashboard: {str(e)}"
        )


@router.get("/mood-trends", response_model=Dict[str, Any])
async def get_mood_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days_back: int = Query(30, ge=7, le=365, description="Number of days to analyze")
):
    """Get detailed mood trend analysis."""
    try:
        # Analyze mood trends
        mood_trend = await analytics_service.analyze_mood_trends(
            db, current_user.id, days_back
        )

        if not mood_trend:
            return {
                "message": "Insufficient data for mood trend analysis",
                "minimum_data_points": 3,
                "analysis_period_days": days_back
            }

        return {
            "trend_analysis": {
                "trend_type": mood_trend.trend_type,
                "trend_strength": mood_trend.trend_strength,
                "trend_duration_days": mood_trend.trend_duration_days,
                "dominant_emotion": mood_trend.dominant_emotion,
                "emotion_stability": mood_trend.emotion_stability,
                "average_sentiment": mood_trend.average_sentiment
            },
            "emotion_progression": mood_trend.emotion_progression,
            "key_events": mood_trend.key_events,
            "analysis_period": {
                "start_date": mood_trend.start_date,
                "end_date": mood_trend.end_date,
                "analyzed_at": mood_trend.analyzed_at
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mood trends: {str(e)}"
        )


@router.get("/insights", response_model=List[Dict[str, Any]])
async def get_progress_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    limit: int = Query(10, ge=1, le=50, description="Number of insights to return")
):
    """Get AI-generated progress insights."""
    try:
        # Generate new insights
        new_insights = await analytics_service.generate_progress_insights(
            db, current_user.id
        )

        # Get existing insights
        query = db.query(ProgressInsight).filter(
            ProgressInsight.user_id == current_user.id
        )

        if insight_type:
            query = query.filter(ProgressInsight.insight_type == insight_type)

        insights = query.order_by(
            ProgressInsight.generated_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": insight.id,
                "type": insight.insight_type,
                "title": insight.insight_title,
                "description": insight.insight_description,
                "supporting_data": insight.supporting_data,
                "confidence_score": insight.confidence_score,
                "impact_level": insight.impact_level,
                "is_actionable": insight.is_actionable,
                "suggested_actions": insight.suggested_actions,
                "data_period": {
                    "start": insight.data_period_start,
                    "end": insight.data_period_end
                },
                "generated_at": insight.generated_at,
                "is_acknowledged": insight.is_acknowledged,
                "user_feedback": insight.user_feedback
            }
            for insight in insights
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress insights: {str(e)}"
        )


@router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(
    insight_id: int,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Acknowledge a progress insight with optional feedback."""
    try:
        insight = db.query(ProgressInsight).filter(
            ProgressInsight.id == insight_id,
            ProgressInsight.user_id == current_user.id
        ).first()

        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insight not found"
            )

        insight.is_acknowledged = True
        insight.acknowledged_at = datetime.now()
        if feedback:
            insight.user_feedback = feedback

        db.commit()

        return {
            "message": "Insight acknowledged successfully",
            "insight_id": insight_id,
            "acknowledged_at": insight.acknowledged_at
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge insight: {str(e)}"
        )


@router.get("/progress-metrics", response_model=Dict[str, Any])
async def get_progress_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    period_type: str = Query("weekly", regex="^(daily|weekly|monthly)$", description="Metrics period type")
):
    """Get detailed progress metrics for a specific period."""
    try:
        # Calculate progress metrics
        metrics = await analytics_service.calculate_user_progress_metrics(
            db, current_user.id, period_type
        )

        if not metrics:
            return {
                "message": "No data available for the specified period",
                "period_type": period_type
            }

        return {
            "period_info": {
                "type": metrics.period_type,
                "start_date": metrics.period_start,
                "end_date": metrics.period_end,
                "calculated_at": metrics.calculated_at
            },
            "engagement_metrics": {
                "total_conversations": metrics.total_conversations,
                "total_messages": metrics.total_messages,
                "average_session_duration": metrics.average_session_duration,
                "engagement_consistency": metrics.engagement_consistency
            },
            "emotional_metrics": {
                "average_mood_score": metrics.average_mood_score,
                "mood_stability": metrics.mood_stability,
                "emotional_growth_score": metrics.emotional_growth_score
            },
            "therapeutic_metrics": {
                "recommendations_completed": metrics.recommendations_completed,
                "recommendations_completion_rate": metrics.recommendations_completion_rate,
                "therapeutic_engagement_score": metrics.therapeutic_engagement_score
            },
            "progress_indicators": {
                "crisis_episodes": metrics.crisis_episodes,
                "breakthrough_moments": metrics.breakthrough_moments,
                "overall_progress_score": metrics.overall_progress_score
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress metrics: {str(e)}"
        )


@router.get("/daily-focus", response_model=Dict[str, Any])
async def get_daily_focus(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personalized daily focus based on user's current state and patterns."""
    try:
        # Get today's focus recommendation
        daily_focus = await analytics_service.generate_daily_focus(db, current_user.id)

        return daily_focus

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily focus: {str(e)}"
        )


@router.get("/conversation-analytics/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation_analytics(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific conversation."""
    try:
        # Analyze the conversation
        analytics = await analytics_service.analyze_conversation(db, conversation_id)

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or no analytics available"
            )

        # Verify user owns this conversation
        if analytics.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )

        return {
            "conversation_id": analytics.conversation_id,
            "message_metrics": {
                "total_messages": analytics.total_messages,
                "user_messages": analytics.user_messages,
                "ai_messages": analytics.ai_messages,
                "conversation_duration_minutes": analytics.conversation_duration_minutes
            },
            "emotional_journey": {
                "emotion_trajectory": analytics.emotion_trajectory,
                "emotional_range": analytics.emotional_range,
                "dominant_emotions": analytics.dominant_emotions,
                "mood_change": analytics.mood_change
            },
            "therapeutic_analysis": {
                "approach_used": analytics.therapeutic_approach_used,
                "approach_effectiveness": analytics.approach_effectiveness,
                "crisis_indicators": analytics.crisis_indicators_detected
            },
            "quality_metrics": {
                "engagement_score": analytics.engagement_score,
                "empathy_score": analytics.empathy_score,
                "resolution_score": analytics.resolution_score
            },
            "outcomes": {
                "insights_generated": analytics.insights_generated,
                "recommendations_provided": analytics.recommendations_provided
            },
            "timeline": {
                "conversation_start": analytics.conversation_start,
                "conversation_end": analytics.conversation_end,
                "analyzed_at": analytics.analyzed_at
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation analytics: {str(e)}"
        )
