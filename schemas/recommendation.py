"""
Recommendation-related Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.recommendation import RecommendationType


class RecommendationBase(BaseModel):
    """Base recommendation schema."""
    type: RecommendationType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    instructions: str = Field(..., min_length=1, max_length=2000)
    target_emotions: List[str]
    difficulty_level: int = Field(..., ge=1, le=5)
    estimated_duration: Optional[int] = Field(None, ge=1, le=120)  # minutes


class RecommendationCreate(RecommendationBase):
    """Schema for recommendation creation."""
    pass


class RecommendationUpdate(BaseModel):
    """Schema for recommendation update."""
    is_completed: Optional[bool] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)


class RecommendationResponse(RecommendationBase):
    """Schema for recommendation response."""
    id: int
    user_id: int
    is_completed: bool
    effectiveness_rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RecommendationSummary(BaseModel):
    """Schema for recommendation summary."""
    total_recommendations: int
    completed_recommendations: int
    completion_rate: float
    average_effectiveness: Optional[float] = None
    most_effective_type: Optional[str] = None
    recent_recommendations: List[RecommendationResponse]
