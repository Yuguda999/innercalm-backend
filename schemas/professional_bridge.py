"""
Professional Bridge schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from models.professional_bridge import TherapyModality, AppointmentStatus, PracticePlanStatus


# Therapist Profile Schemas
class TherapistProfileBase(BaseModel):
    """Base therapist profile schema."""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    license_number: str = Field(..., min_length=5, max_length=50)
    credentials: List[str] = Field(..., min_items=1)
    specialties: List[TherapyModality] = Field(..., min_items=1)
    years_experience: int = Field(..., ge=0, le=50)
    bio: Optional[str] = Field(None, max_length=2000)
    hourly_rate: float = Field(..., ge=0.0, le=1000.0)
    accepts_insurance: bool = False
    insurance_providers: Optional[List[str]] = None
    availability_schedule: Dict[str, Any] = Field(..., description="Weekly availability schedule")
    timezone: str = Field(default="UTC")


class TherapistProfileCreate(TherapistProfileBase):
    """Schema for creating therapist profiles."""
    pass


class TherapistProfileUpdate(BaseModel):
    """Schema for updating therapist profiles."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    credentials: Optional[List[str]] = None
    specialties: Optional[List[TherapyModality]] = None
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    bio: Optional[str] = Field(None, max_length=2000)
    hourly_rate: Optional[float] = Field(None, ge=0.0, le=1000.0)
    accepts_insurance: Optional[bool] = None
    insurance_providers: Optional[List[str]] = None
    availability_schedule: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    is_accepting_new_clients: Optional[bool] = None


class TherapistProfileResponse(TherapistProfileBase):
    """Schema for therapist profile response."""
    id: int
    average_rating: float
    total_reviews: int
    is_verified: bool
    is_active: bool
    is_accepting_new_clients: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Therapist Match Schemas
class TherapistMatchRequest(BaseModel):
    """Schema for requesting therapist matches."""
    preferred_modalities: List[TherapyModality] = Field(..., min_items=1)
    trauma_categories: List[str] = Field(..., min_items=1)
    healing_stage: str = Field(..., pattern="^(denial|anger|bargaining|depression|acceptance)$")
    max_hourly_rate: Optional[float] = Field(None, ge=0.0)
    insurance_required: bool = False
    preferred_gender: Optional[str] = None
    language_preferences: Optional[List[str]] = None


class TherapistMatchResponse(BaseModel):
    """Schema for therapist match response."""
    id: int
    user_id: int
    therapist_id: int
    compatibility_score: float
    match_reasons: List[str]
    preferred_modalities: List[TherapyModality]
    trauma_categories: List[str]
    healing_stage: str
    therapist_specialties_match: List[str]
    experience_relevance: float
    is_viewed: bool
    is_contacted: bool
    user_rating: Optional[int] = None
    user_notes: Optional[str] = None
    created_at: datetime
    therapist: TherapistProfileResponse

    class Config:
        from_attributes = True


# Appointment Schemas
class AppointmentCreate(BaseModel):
    """Schema for creating appointments."""
    therapist_id: int
    match_id: Optional[int] = None
    scheduled_datetime: datetime
    duration_minutes: int = Field(default=50, ge=15, le=180)
    session_type: str = Field(default="individual", pattern="^(individual|group|family)$")
    recording_consent: bool = False


class AppointmentUpdate(BaseModel):
    """Schema for updating appointments."""
    scheduled_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    session_type: Optional[str] = Field(None, pattern="^(individual|group|family)$")
    session_notes: Optional[str] = None
    user_feedback: Optional[str] = None
    session_rating: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[AppointmentStatus] = None
    recording_consent: Optional[bool] = None


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""
    id: int
    user_id: int
    therapist_id: int
    match_id: Optional[int] = None
    scheduled_datetime: datetime
    duration_minutes: int
    session_type: str
    session_notes: Optional[str] = None
    user_feedback: Optional[str] = None
    session_rating: Optional[int] = None
    video_call_link: Optional[str] = None
    meeting_id: Optional[str] = None
    status: AppointmentStatus
    reminder_sent: bool
    cost: Optional[float] = None
    payment_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    therapist: TherapistProfileResponse

    class Config:
        from_attributes = True


# Practice Plan Schemas
class PracticePlanCreate(BaseModel):
    """Schema for creating practice plans."""
    user_id: int
    appointment_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    goals: List[str] = Field(..., min_items=1)
    daily_tasks: List[Dict[str, Any]] = Field(..., min_items=1)
    weekly_goals: List[Dict[str, Any]] = Field(..., min_items=1)
    exercises: List[Dict[str, Any]] = Field(default_factory=list)
    start_date: datetime
    end_date: datetime
    reminder_frequency: str = Field(default="daily", pattern="^(daily|weekly|custom)$")


class PracticePlanUpdate(BaseModel):
    """Schema for updating practice plans."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    goals: Optional[List[str]] = None
    daily_tasks: Optional[List[Dict[str, Any]]] = None
    weekly_goals: Optional[List[Dict[str, Any]]] = None
    exercises: Optional[List[Dict[str, Any]]] = None
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    completed_tasks: Optional[List[str]] = None
    task_feedback: Optional[Dict[str, Any]] = None
    status: Optional[PracticePlanStatus] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    user_notes: Optional[str] = None
    end_date: Optional[datetime] = None
    reminder_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|custom)$")


class PracticePlanResponse(BaseModel):
    """Schema for practice plan response."""
    id: int
    user_id: int
    appointment_id: int
    title: str
    description: Optional[str] = None
    goals: List[str]
    daily_tasks: List[Dict[str, Any]]
    weekly_goals: List[Dict[str, Any]]
    exercises: List[Dict[str, Any]]
    completion_percentage: float
    completed_tasks: List[str]
    task_feedback: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    reminder_frequency: str
    status: PracticePlanStatus
    effectiveness_rating: Optional[int] = None
    user_notes: Optional[str] = None
    ai_adjustments: Optional[List[str]] = None
    progress_insights: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional utility schemas
class TherapistSearchFilters(BaseModel):
    """Schema for therapist search filters."""
    specialties: Optional[List[TherapyModality]] = None
    max_hourly_rate: Optional[float] = Field(None, ge=0.0)
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    accepts_insurance: Optional[bool] = None
    years_experience_min: Optional[int] = Field(None, ge=0)
    is_accepting_new_clients: Optional[bool] = True
    location: Optional[str] = None
    language: Optional[str] = None


class MatchingInsights(BaseModel):
    """Schema for AI matching insights."""
    total_matches: int
    top_compatibility_score: float
    common_specialties: List[str]
    recommended_modalities: List[TherapyModality]
    healing_stage_recommendations: List[str]
    next_steps: List[str]


class PracticePlanProgress(BaseModel):
    """Schema for practice plan progress tracking."""
    plan_id: int
    completion_percentage: float
    tasks_completed_today: int
    tasks_remaining_today: int
    weekly_progress: float
    streak_days: int
    insights: List[str]
    next_milestones: List[str]
