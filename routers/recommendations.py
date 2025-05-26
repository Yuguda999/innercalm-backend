"""
Recommendations router for personalized healing suggestions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.recommendation import Recommendation
from models.emotion import EmotionAnalysis
from schemas.recommendation import (
    RecommendationCreate, RecommendationResponse, 
    RecommendationUpdate, RecommendationSummary
)
from services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()


@router.post("/generate", response_model=List[RecommendationResponse])
async def generate_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(3, ge=1, le=10)
):
    """Generate personalized recommendations based on recent emotions."""
    try:
        # Get latest emotion analysis for context
        latest_analysis = db.query(EmotionAnalysis).filter(
            EmotionAnalysis.user_id == current_user.id
        ).order_by(EmotionAnalysis.analyzed_at.desc()).first()
        
        emotion_data = None
        if latest_analysis:
            emotion_data = {
                "joy": latest_analysis.joy,
                "sadness": latest_analysis.sadness,
                "anger": latest_analysis.anger,
                "fear": latest_analysis.fear,
                "surprise": latest_analysis.surprise,
                "disgust": latest_analysis.disgust,
                "sentiment_score": latest_analysis.sentiment_score,
                "sentiment_label": latest_analysis.sentiment_label,
                "themes": latest_analysis.themes or []
            }
        
        # Generate recommendations
        recommendations_data = recommendation_engine.generate_recommendations(
            db, current_user.id, emotion_data, limit
        )
        
        # Save recommendations to database
        saved_recommendations = []
        for rec_data in recommendations_data:
            recommendation = Recommendation(**rec_data)
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            saved_recommendations.append(recommendation)
        
        return [RecommendationResponse.model_validate(rec) for rec in saved_recommendations]
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    completed: Optional[bool] = Query(None)
):
    """Get user's recommendations."""
    try:
        query = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        )
        
        if completed is not None:
            query = query.filter(Recommendation.is_completed == completed)
        
        recommendations = query.order_by(
            Recommendation.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [RecommendationResponse.model_validate(rec) for rec in recommendations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific recommendation."""
    try:
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        return RecommendationResponse.model_validate(recommendation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation: {str(e)}"
        )


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: int,
    update_data: RecommendationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a recommendation (mark as completed, add rating, etc.)."""
    try:
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(recommendation, field, value)
        
        # Set completion timestamp if marked as completed
        if update_data.is_completed and not recommendation.completed_at:
            from datetime import datetime
            recommendation.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(recommendation)
        
        return RecommendationResponse.model_validate(recommendation)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recommendation: {str(e)}"
        )


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a recommendation."""
    try:
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )
        
        db.delete(recommendation)
        db.commit()
        
        return {"message": "Recommendation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recommendation: {str(e)}"
        )


@router.get("/summary/stats", response_model=RecommendationSummary)
async def get_recommendation_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recommendation statistics and summary."""
    try:
        # Get all recommendations
        all_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).all()
        
        total_count = len(all_recommendations)
        completed_count = sum(1 for rec in all_recommendations if rec.is_completed)
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        # Calculate average effectiveness
        rated_recommendations = [rec for rec in all_recommendations if rec.effectiveness_rating is not None]
        average_effectiveness = (
            sum(rec.effectiveness_rating for rec in rated_recommendations) / len(rated_recommendations)
            if rated_recommendations else None
        )
        
        # Find most effective recommendation type
        type_effectiveness = {}
        for rec in rated_recommendations:
            rec_type = rec.type.value
            if rec_type not in type_effectiveness:
                type_effectiveness[rec_type] = []
            type_effectiveness[rec_type].append(rec.effectiveness_rating)
        
        most_effective_type = None
        if type_effectiveness:
            type_averages = {
                rec_type: sum(ratings) / len(ratings)
                for rec_type, ratings in type_effectiveness.items()
            }
            most_effective_type = max(type_averages, key=type_averages.get)
        
        # Get recent recommendations
        recent_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == current_user.id
        ).order_by(Recommendation.created_at.desc()).limit(5).all()
        
        return RecommendationSummary(
            total_recommendations=total_count,
            completed_recommendations=completed_count,
            completion_rate=completion_rate,
            average_effectiveness=average_effectiveness,
            most_effective_type=most_effective_type,
            recent_recommendations=[
                RecommendationResponse.model_validate(rec) for rec in recent_recommendations
            ]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation summary: {str(e)}"
        )
