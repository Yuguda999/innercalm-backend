"""
Pydantic schemas for voice journaling.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.voice_journal import VoiceJournalStatus


class VoiceJournalBase(BaseModel):
    """Base schema for voice journal."""
    title: Optional[str] = None
    description: Optional[str] = None


class VoiceJournalCreate(VoiceJournalBase):
    """Schema for creating a voice journal session."""
    pass


class VoiceJournalUpdate(BaseModel):
    """Schema for updating voice journal."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[VoiceJournalStatus] = None
    transcription: Optional[str] = None
    audio_duration: Optional[float] = None
    sentiment_timeline: Optional[Dict[str, Any]] = None
    emotion_spikes: Optional[List[Dict[str, Any]]] = None
    overall_sentiment: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    recommended_exercises: Optional[List[Dict[str, Any]]] = None
    breathing_exercise_suggested: Optional[str] = None


class VoiceJournalResponse(VoiceJournalBase):
    """Schema for voice journal response."""
    id: int
    user_id: int
    status: VoiceJournalStatus
    audio_file_path: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_format: str
    transcription: Optional[str] = None
    transcription_confidence: Optional[float] = None
    sentiment_timeline: Optional[Dict[str, Any]] = None
    emotion_spikes: Optional[List[Dict[str, Any]]] = None
    overall_sentiment: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    recommended_exercises: Optional[List[Dict[str, Any]]] = None
    breathing_exercise_suggested: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoiceJournalEntryBase(BaseModel):
    """Base schema for voice journal entry."""
    transcribed_text: Optional[str] = None
    segment_start_time: float = Field(..., ge=0.0)
    segment_duration: float = Field(..., gt=0.0)


class VoiceJournalEntryCreate(VoiceJournalEntryBase):
    """Schema for creating voice journal entry."""
    journal_id: int


class VoiceJournalEntryUpdate(BaseModel):
    """Schema for updating voice journal entry."""
    transcribed_text: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = None
    emotional_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    themes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_emotional_spike: Optional[bool] = None
    spike_type: Optional[str] = None
    triggered_recommendations: Optional[List[Dict[str, Any]]] = None


class VoiceJournalEntryResponse(VoiceJournalEntryBase):
    """Schema for voice journal entry response."""
    id: int
    journal_id: int
    user_id: int
    audio_segment_path: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    emotional_intensity: Optional[float] = None
    themes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_emotional_spike: bool
    spike_type: Optional[str] = None
    triggered_recommendations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BreathingExerciseSessionBase(BaseModel):
    """Base schema for breathing exercise session."""
    exercise_type: str = Field(..., description="Type of breathing exercise")
    exercise_name: str = Field(..., description="Name of the exercise")
    duration_minutes: int = Field(..., gt=0, le=60)


class BreathingExerciseSessionCreate(BreathingExerciseSessionBase):
    """Schema for creating breathing exercise session."""
    voice_journal_id: Optional[int] = None
    pre_session_mood: Optional[Dict[str, float]] = None


class BreathingExerciseSessionUpdate(BaseModel):
    """Schema for updating breathing exercise session."""
    completed: Optional[bool] = None
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    post_session_mood: Optional[Dict[str, float]] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)


class BreathingExerciseSessionResponse(BreathingExerciseSessionBase):
    """Schema for breathing exercise session response."""
    id: int
    user_id: int
    voice_journal_id: Optional[int] = None
    completed: bool
    completion_percentage: float
    pre_session_mood: Optional[Dict[str, float]] = None
    post_session_mood: Optional[Dict[str, float]] = None
    effectiveness_rating: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RealTimeSentimentUpdate(BaseModel):
    """Schema for real-time sentiment updates during recording."""
    journal_id: int
    timestamp: float = Field(..., description="Timestamp in seconds from start")
    emotions: Dict[str, float] = Field(..., description="Current emotion scores")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    emotional_intensity: float = Field(..., ge=0.0, le=1.0)
    is_spike: bool = False
    spike_type: Optional[str] = None


class VoiceJournalAnalytics(BaseModel):
    """Schema for voice journal analytics."""
    total_sessions: int
    total_duration_minutes: float
    average_session_duration: float
    most_common_emotions: List[Dict[str, Any]]
    emotion_trends: Dict[str, List[float]]
    spike_frequency: Dict[str, int]
    recommended_exercises_used: List[Dict[str, Any]]
    improvement_metrics: Dict[str, float]
