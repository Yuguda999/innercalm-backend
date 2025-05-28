"""
Trauma mapping and life event models for the Inner Wound Explorer.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class EventType(enum.Enum):
    """Types of life events."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    TRAUMATIC = "TRAUMATIC"
    MILESTONE = "MILESTONE"


class EventCategory(enum.Enum):
    """Categories of life events."""
    FAMILY = "FAMILY"
    RELATIONSHIPS = "RELATIONSHIPS"
    CAREER = "CAREER"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    LOSS = "LOSS"
    ACHIEVEMENT = "ACHIEVEMENT"
    TRAUMA = "TRAUMA"
    OTHER = "OTHER"


class ReframeSessionStatus(enum.Enum):
    """Status of reframe sessions."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class LifeEvent(Base):
    """Life event model for timeline tracking."""

    __tablename__ = "life_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Event details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False)
    age_at_event = Column(Integer, nullable=True)

    # Event classification
    event_type = Column(Enum(EventType), nullable=False)
    category = Column(Enum(EventCategory), nullable=False)

    # Emotional impact
    emotional_impact_score = Column(Float, nullable=False)  # -10 to 10 scale
    trauma_severity = Column(Float, default=0.0)  # 0 to 10 scale

    # Event metadata
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)

    # Timeline positioning
    timeline_position = Column(Integer, nullable=True)  # For drag-and-drop ordering

    # Associated emotions and themes
    associated_emotions = Column(JSON, nullable=True)  # Emotion scores at time of event
    triggers = Column(JSON, nullable=True)  # List of identified triggers
    themes = Column(JSON, nullable=True)  # Recurring themes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    trauma_mappings = relationship("TraumaMapping", back_populates="life_event")
    reframe_sessions = relationship("ReframeSession", back_populates="life_event")

    def __repr__(self):
        return f"<LifeEvent(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class TraumaMapping(Base):
    """Trauma mapping analysis for pattern recognition."""

    __tablename__ = "trauma_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    life_event_id = Column(Integer, ForeignKey("life_events.id"), nullable=False)

    # Pattern analysis
    pattern_name = Column(String, nullable=False)
    pattern_description = Column(Text, nullable=True)

    # Trauma indicators
    trauma_indicators = Column(JSON, nullable=False)  # List of identified indicators
    severity_score = Column(Float, nullable=False)  # 0 to 10

    # Emotional patterns
    emotion_clusters = Column(JSON, nullable=False)  # Grouped emotions
    trigger_patterns = Column(JSON, nullable=True)  # Common trigger patterns

    # Healing progress
    healing_stage = Column(String, nullable=False)  # denial, anger, bargaining, depression, acceptance
    progress_score = Column(Float, default=0.0)  # 0 to 10

    # AI insights
    ai_insights = Column(JSON, nullable=True)  # AI-generated insights
    recommended_approaches = Column(JSON, nullable=True)  # Therapeutic approaches

    # Analysis metadata
    confidence_score = Column(Float, nullable=False)  # AI confidence in analysis
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    life_event = relationship("LifeEvent", back_populates="trauma_mappings")

    def __repr__(self):
        return f"<TraumaMapping(id={self.id}, pattern='{self.pattern_name}')>"


class ReframeSession(Base):
    """Cognitive reframing session for trauma healing."""

    __tablename__ = "reframe_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    life_event_id = Column(Integer, ForeignKey("life_events.id"), nullable=False)
    trauma_mapping_id = Column(Integer, ForeignKey("trauma_mappings.id"), nullable=True)

    # Session details
    session_title = Column(String, nullable=False)
    session_description = Column(Text, nullable=True)
    status = Column(Enum(ReframeSessionStatus), default=ReframeSessionStatus.PENDING)

    # Reframing process
    original_narrative = Column(Text, nullable=False)  # User's original story
    reframed_narrative = Column(Text, nullable=True)  # New perspective

    # Cognitive techniques used
    techniques_used = Column(JSON, nullable=True)  # List of techniques
    exercises_completed = Column(JSON, nullable=True)  # Completed exercises

    # Progress tracking
    progress_percentage = Column(Float, default=0.0)  # 0 to 100
    breakthrough_moments = Column(JSON, nullable=True)  # Key insights

    # Self-compassion elements
    self_compassion_score = Column(Float, nullable=True)  # Before/after comparison
    compassion_exercises = Column(JSON, nullable=True)  # Specific exercises

    # Session outcomes
    emotional_shift = Column(JSON, nullable=True)  # Before/after emotions
    insights_gained = Column(JSON, nullable=True)  # Key insights
    action_items = Column(JSON, nullable=True)  # Next steps

    # AI guidance
    ai_prompts = Column(JSON, nullable=True)  # AI-generated prompts
    ai_feedback = Column(JSON, nullable=True)  # AI feedback on progress

    # Session timing
    estimated_duration_minutes = Column(Integer, default=30)
    actual_duration_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    life_event = relationship("LifeEvent", back_populates="reframe_sessions")
    trauma_mapping = relationship("TraumaMapping")

    def __repr__(self):
        return f"<ReframeSession(id={self.id}, title='{self.session_title}', status='{self.status.value}')>"
