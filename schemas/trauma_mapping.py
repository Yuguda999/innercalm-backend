"""
Pydantic schemas for trauma mapping and life events.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import the database enums to ensure consistency
from models.trauma_mapping import EventType, EventCategory, ReframeSessionStatus


# Life Event Schemas
class LifeEventCreate(BaseModel):
    """Schema for creating a life event."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_date: datetime
    age_at_event: Optional[int] = Field(None, ge=0, le=120)
    event_type: EventType
    category: EventCategory
    emotional_impact_score: float = Field(..., ge=-10.0, le=10.0)
    trauma_severity: float = Field(0.0, ge=0.0, le=10.0)
    associated_emotions: Optional[Dict[str, float]] = None
    triggers: Optional[List[str]] = None
    themes: Optional[List[str]] = None


class LifeEventUpdate(BaseModel):
    """Schema for updating a life event."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_date: Optional[datetime] = None
    age_at_event: Optional[int] = Field(None, ge=0, le=120)
    event_type: Optional[EventType] = None
    category: Optional[EventCategory] = None
    emotional_impact_score: Optional[float] = Field(None, ge=-10.0, le=10.0)
    trauma_severity: Optional[float] = Field(None, ge=0.0, le=10.0)
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    timeline_position: Optional[int] = None
    associated_emotions: Optional[Dict[str, float]] = None
    triggers: Optional[List[str]] = None
    themes: Optional[List[str]] = None


class LifeEventResponse(BaseModel):
    """Schema for life event response."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    event_date: datetime
    age_at_event: Optional[int] = None
    event_type: EventType
    category: EventCategory
    emotional_impact_score: float
    trauma_severity: float
    is_resolved: bool
    resolution_notes: Optional[str] = None
    timeline_position: Optional[int] = None
    associated_emotions: Optional[Dict[str, float]] = None
    triggers: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Trauma Mapping Schemas
class TraumaMappingCreate(BaseModel):
    """Schema for creating trauma mapping."""
    life_event_id: int
    pattern_name: str = Field(..., min_length=1, max_length=200)
    pattern_description: Optional[str] = Field(None, max_length=2000)
    trauma_indicators: List[str]
    severity_score: float = Field(..., ge=0.0, le=10.0)
    emotion_clusters: Dict[str, List[str]]
    trigger_patterns: Optional[List[str]] = None
    healing_stage: str = Field(..., pattern="^(denial|anger|bargaining|depression|acceptance)$")
    progress_score: float = Field(0.0, ge=0.0, le=10.0)
    ai_insights: Optional[List[str]] = None
    recommended_approaches: Optional[List[str]] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class TraumaMappingResponse(BaseModel):
    """Schema for trauma mapping response."""
    id: int
    user_id: int
    life_event_id: int
    pattern_name: str
    pattern_description: Optional[str] = None
    trauma_indicators: List[str]
    severity_score: float
    emotion_clusters: Dict[str, List[str]]
    trigger_patterns: Optional[List[str]] = None
    healing_stage: str
    progress_score: float
    ai_insights: Optional[List[str]] = None
    recommended_approaches: Optional[List[str]] = None
    confidence_score: float
    analyzed_at: datetime
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# Reframe Session Schemas
class ReframeSessionCreate(BaseModel):
    """Schema for creating a reframe session."""
    life_event_id: int
    trauma_mapping_id: Optional[int] = None
    session_title: str = Field(..., min_length=1, max_length=200)
    session_description: Optional[str] = Field(None, max_length=2000)
    original_narrative: str = Field(..., min_length=10, max_length=5000)
    techniques_used: Optional[List[str]] = None
    estimated_duration_minutes: int = Field(30, ge=5, le=180)


class ReframeSessionUpdate(BaseModel):
    """Schema for updating a reframe session."""
    status: Optional[ReframeSessionStatus] = None
    reframed_narrative: Optional[str] = Field(None, max_length=5000)
    techniques_used: Optional[List[str]] = None
    exercises_completed: Optional[List[Dict[str, Any]]] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    breakthrough_moments: Optional[List[str]] = None
    self_compassion_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    compassion_exercises: Optional[List[Dict[str, Any]]] = None
    emotional_shift: Optional[Dict[str, float]] = None
    insights_gained: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    ai_prompts: Optional[List[str]] = None
    ai_feedback: Optional[List[str]] = None
    actual_duration_minutes: Optional[int] = Field(None, ge=1, le=300)


class ReframeSessionResponse(BaseModel):
    """Schema for reframe session response."""
    id: int
    user_id: int
    life_event_id: int
    trauma_mapping_id: Optional[int] = None
    session_title: str
    session_description: Optional[str] = None
    status: ReframeSessionStatus
    original_narrative: str
    reframed_narrative: Optional[str] = None
    techniques_used: Optional[List[str]] = None
    exercises_completed: Optional[List[Dict[str, Any]]] = None
    progress_percentage: float
    breakthrough_moments: Optional[List[str]] = None
    self_compassion_score: Optional[float] = None
    compassion_exercises: Optional[List[Dict[str, Any]]] = None
    emotional_shift: Optional[Dict[str, float]] = None
    insights_gained: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    ai_prompts: Optional[List[str]] = None
    ai_feedback: Optional[List[str]] = None
    estimated_duration_minutes: int
    actual_duration_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Timeline and Analysis Schemas
class TimelineAnalysisResponse(BaseModel):
    """Schema for timeline analysis response."""
    total_events: int
    traumatic_events_count: int
    positive_events_count: int
    unresolved_events_count: int
    emotion_heatmap: List[Dict[str, Any]]
    pattern_clusters: List[Dict[str, Any]]
    healing_progress: Dict[str, float]
    recommendations: List[str]


class EmotionHeatmapPoint(BaseModel):
    """Schema for emotion heatmap data point."""
    event_id: int
    date: datetime
    emotional_impact: float
    trauma_severity: float
    dominant_emotion: str
    is_resolved: bool
    category: EventCategory


class PatternCluster(BaseModel):
    """Schema for pattern cluster analysis."""
    cluster_name: str
    events: List[int]  # Event IDs
    common_themes: List[str]
    average_severity: float
    healing_stage: str
    recommended_interventions: List[str]
