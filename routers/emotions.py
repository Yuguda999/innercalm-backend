"""
Emotions router for emotion analysis and pattern tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.emotion import EmotionAnalysis, EmotionPattern
from schemas.emotion import EmotionAnalysisResponse, EmotionPatternResponse, EmotionTrendResponse
from services.emotion_analyzer import EmotionAnalyzer

router = APIRouter(prefix="/emotions", tags=["emotions"])

# Initialize emotion analyzer
emotion_analyzer = EmotionAnalyzer()


@router.get("/analysis", response_model=List[EmotionAnalysisResponse])
async def get_emotion_analyses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    days: Optional[int] = Query(None, ge=1, le=365)
):
    """Get user's emotion analyses."""
    try:
        query = db.query(EmotionAnalysis).filter(
            EmotionAnalysis.user_id == current_user.id
        )
        
        # Filter by date range if specified
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(EmotionAnalysis.analyzed_at >= cutoff_date)
        
        analyses = query.order_by(
            EmotionAnalysis.analyzed_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [EmotionAnalysisResponse.model_validate(analysis) for analysis in analyses]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emotion analyses: {str(e)}"
        )


@router.get("/patterns", response_model=List[EmotionPatternResponse])
async def get_emotion_patterns(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=365)
):
    """Get user's emotion patterns."""
    try:
        # Get existing patterns from database
        existing_patterns = db.query(EmotionPattern).filter(
            EmotionPattern.user_id == current_user.id
        ).all()
        
        # Detect new patterns
        new_patterns = emotion_analyzer.detect_patterns(db, current_user.id, days)
        
        # Save new patterns to database
        for pattern_data in new_patterns:
            # Check if pattern already exists
            existing = db.query(EmotionPattern).filter(
                EmotionPattern.user_id == current_user.id,
                EmotionPattern.pattern_name == pattern_data["pattern_name"]
            ).first()
            
            if existing:
                # Update existing pattern
                existing.frequency = pattern_data["frequency"]
                existing.intensity = pattern_data["intensity"]
                existing.last_detected = datetime.utcnow()
                existing.emotions = pattern_data["emotions"]
            else:
                # Create new pattern
                new_pattern = EmotionPattern(
                    user_id=current_user.id,
                    pattern_name=pattern_data["pattern_name"],
                    pattern_description=pattern_data["pattern_description"],
                    frequency=pattern_data["frequency"],
                    intensity=pattern_data["intensity"],
                    emotions=pattern_data["emotions"]
                )
                db.add(new_pattern)
        
        db.commit()
        
        # Return all patterns
        all_patterns = db.query(EmotionPattern).filter(
            EmotionPattern.user_id == current_user.id
        ).order_by(EmotionPattern.last_detected.desc()).all()
        
        return [EmotionPatternResponse.model_validate(pattern) for pattern in all_patterns]
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emotion patterns: {str(e)}"
        )


@router.get("/trends", response_model=EmotionTrendResponse)
async def get_emotion_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    period: str = Query("weekly", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=7, le=365)
):
    """Get emotion trends over time."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        analyses = db.query(EmotionAnalysis).filter(
            EmotionAnalysis.user_id == current_user.id,
            EmotionAnalysis.analyzed_at >= cutoff_date
        ).order_by(EmotionAnalysis.analyzed_at).all()
        
        if not analyses:
            return EmotionTrendResponse(
                period=period,
                data_points=[],
                overall_trend="stable",
                dominant_emotions=[],
                recommendations_count=0
            )
        
        # Group data by period
        data_points = []
        if period == "daily":
            # Group by day
            current_date = cutoff_date.date()
            end_date = datetime.utcnow().date()
            
            while current_date <= end_date:
                day_analyses = [a for a in analyses if a.analyzed_at.date() == current_date]
                if day_analyses:
                    avg_sentiment = sum(a.sentiment_score for a in day_analyses) / len(day_analyses)
                    dominant_emotion = max(
                        ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
                        key=lambda e: sum(getattr(a, e, 0) for a in day_analyses) / len(day_analyses)
                    )
                    
                    data_points.append({
                        "date": current_date.isoformat(),
                        "sentiment_score": avg_sentiment,
                        "dominant_emotion": dominant_emotion,
                        "message_count": len(day_analyses)
                    })
                
                current_date += timedelta(days=1)
        
        # Calculate overall trend
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(dp["sentiment_score"] for dp in first_half) / len(first_half)
            second_avg = sum(dp["sentiment_score"] for dp in second_half) / len(second_half)
            
            if second_avg > first_avg + 0.1:
                overall_trend = "improving"
            elif second_avg < first_avg - 0.1:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "stable"
        
        # Find dominant emotions
        emotion_totals = {
            "joy": sum(a.joy for a in analyses),
            "sadness": sum(a.sadness for a in analyses),
            "anger": sum(a.anger for a in analyses),
            "fear": sum(a.fear for a in analyses),
            "surprise": sum(a.surprise for a in analyses),
            "disgust": sum(a.disgust for a in analyses)
        }
        
        dominant_emotions = sorted(
            emotion_totals.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        dominant_emotions = [emotion for emotion, _ in dominant_emotions if _ > 0]
        
        # Count recommendations (placeholder)
        from models.recommendation import Recommendation
        recommendations_count = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id,
            Recommendation.created_at >= cutoff_date
        ).count()
        
        return EmotionTrendResponse(
            period=period,
            data_points=data_points,
            overall_trend=overall_trend,
            dominant_emotions=dominant_emotions,
            recommendations_count=recommendations_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emotion trends: {str(e)}"
        )
