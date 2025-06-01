"""
Professional Bridge models for therapist matching, scheduling, and practice plans.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from database import Base


class TherapyModality(str, Enum):
    """Therapy modalities supported by therapists."""
    CBT = "cognitive_behavioral_therapy"
    EMDR = "emdr"
    SOMATIC = "somatic_therapy"
    DBT = "dialectical_behavior_therapy"
    PSYCHODYNAMIC = "psychodynamic"
    HUMANISTIC = "humanistic"
    TRAUMA_INFORMED = "trauma_informed"
    MINDFULNESS_BASED = "mindfulness_based"
    FAMILY_THERAPY = "family_therapy"
    GROUP_THERAPY = "group_therapy"


class AppointmentStatus(str, Enum):
    """Appointment status options."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class PracticePlanStatus(str, Enum):
    """Practice plan status options."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    EXPIRED = "expired"


class TherapistProfile(Base):
    """Therapist profile with credentials, specialties, and availability."""

    __tablename__ = "therapist_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Basic information
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    license_number = Column(String, unique=True, nullable=False)
    
    # Professional details
    credentials = Column(JSON, nullable=False)  # List of credentials/certifications
    specialties = Column(JSON, nullable=False)  # List of therapy modalities
    years_experience = Column(Integer, nullable=False)
    bio = Column(Text, nullable=True)
    
    # Availability and pricing
    hourly_rate = Column(Float, nullable=False)
    accepts_insurance = Column(Boolean, default=False)
    insurance_providers = Column(JSON, nullable=True)  # List of accepted insurance
    availability_schedule = Column(JSON, nullable=False)  # Weekly availability
    timezone = Column(String, default="UTC")
    
    # Platform integration
    video_platform_url = Column(String, nullable=True)  # Secure video call link
    calendar_integration = Column(JSON, nullable=True)  # Calendar API settings
    
    # Ratings and reviews
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Profile status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_accepting_new_clients = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    matches = relationship("TherapistMatch", back_populates="therapist")
    appointments = relationship("Appointment", back_populates="therapist")


class TherapistMatch(Base):
    """AI-generated therapist matches based on user's trauma map and preferences."""

    __tablename__ = "therapist_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapist_profiles.id"), nullable=False)
    
    # Matching algorithm results
    compatibility_score = Column(Float, nullable=False)  # 0.0 to 1.0
    match_reasons = Column(JSON, nullable=False)  # Why this therapist was matched
    
    # User preferences considered
    preferred_modalities = Column(JSON, nullable=False)  # User's preferred therapy types
    trauma_categories = Column(JSON, nullable=False)  # Trauma types from user's map
    healing_stage = Column(String, nullable=False)  # Current healing stage
    
    # Therapist suitability
    therapist_specialties_match = Column(JSON, nullable=False)  # Matching specialties
    experience_relevance = Column(Float, nullable=False)  # How relevant therapist's experience is
    
    # User interaction
    is_viewed = Column(Boolean, default=False)
    is_contacted = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating if user provides feedback
    user_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    contacted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    therapist = relationship("TherapistProfile", back_populates="matches")
    appointments = relationship("Appointment", back_populates="match")


class Appointment(Base):
    """Scheduled appointments between users and therapists."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapist_profiles.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("therapist_matches.id"), nullable=True)
    
    # Appointment details
    scheduled_datetime = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=50)
    session_type = Column(String, default="individual")  # individual, group, family
    
    # Session information
    session_notes = Column(Text, nullable=True)  # Therapist notes (encrypted)
    user_feedback = Column(Text, nullable=True)  # User feedback after session
    session_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Technical details
    video_call_link = Column(String, nullable=True)
    meeting_id = Column(String, nullable=True)
    recording_consent = Column(Boolean, default=False)
    
    # Status and tracking
    status = Column(String, default=AppointmentStatus.SCHEDULED)
    reminder_sent = Column(Boolean, default=False)
    no_show_reason = Column(String, nullable=True)
    
    # Billing
    cost = Column(Float, nullable=True)
    payment_status = Column(String, default="pending")  # pending, paid, refunded
    insurance_claim_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    therapist = relationship("TherapistProfile", back_populates="appointments")
    match = relationship("TherapistMatch", back_populates="appointments")
    practice_plans = relationship("PracticePlan", back_populates="appointment")


class PracticePlan(Base):
    """Post-session homework and accountability tracking."""

    __tablename__ = "practice_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    
    # Plan details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goals = Column(JSON, nullable=False)  # List of specific goals
    
    # Tasks and exercises
    daily_tasks = Column(JSON, nullable=False)  # Daily micro-tasks
    weekly_goals = Column(JSON, nullable=False)  # Weekly objectives
    exercises = Column(JSON, nullable=False)  # Specific therapeutic exercises
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    completed_tasks = Column(JSON, default=list)  # List of completed task IDs
    task_feedback = Column(JSON, default=dict)  # User feedback on tasks
    
    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    reminder_frequency = Column(String, default="daily")  # daily, weekly, custom
    
    # Status and effectiveness
    status = Column(String, default=PracticePlanStatus.ACTIVE)
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_notes = Column(Text, nullable=True)
    
    # AI insights
    ai_adjustments = Column(JSON, nullable=True)  # AI-suggested plan adjustments
    progress_insights = Column(JSON, nullable=True)  # AI analysis of progress
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    appointment = relationship("Appointment", back_populates="practice_plans")
