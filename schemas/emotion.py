"""
Emotion analysis-related Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EmotionAnalysisResponse(BaseModel):
    """Schema for emotion analysis response."""
    id: int
    user_id: int
    message_id: Optional[int] = None

    # Primary emotions
    joy: float = Field(..., ge=0.0, le=1.0)
    sadness: float = Field(..., ge=0.0, le=1.0)
    anger: float = Field(..., ge=0.0, le=1.0)
    fear: float = Field(..., ge=0.0, le=1.0)
    surprise: float = Field(..., ge=0.0, le=1.0)
    disgust: float = Field(..., ge=0.0, le=1.0)

    # Overall sentiment
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str

    # Detected themes and keywords
    themes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

    # Analysis metadata
    confidence: float = Field(..., ge=0.0, le=1.0)
    analyzed_at: datetime

    class Config:
        from_attributes = True


class EmotionPatternResponse(BaseModel):
    """Schema for emotion pattern response."""
    id: int
    user_id: int
    pattern_name: str
    pattern_description: Optional[str] = None
    frequency: int
    intensity: float = Field(..., ge=0.0, le=1.0)
    first_detected: datetime
    last_detected: datetime
    triggers: Optional[List[str]] = None
    emotions: Dict[str, float]

    class Config:
        from_attributes = True


class EmotionTrendResponse(BaseModel):
    """Schema for emotion trend analysis."""
    period: str  # daily, weekly, monthly
    data_points: List[Dict[str, Any]]
    overall_trend: str  # improving, declining, stable
    dominant_emotions: List[str]
    recommendations_count: int
