"""
User model for authentication and user management.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from database import Base


class UserType(str, Enum):
    """User type enumeration."""
    CLIENT = "client"
    THERAPIST = "therapist"
    ADMIN = "admin"


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    user_type = Column(String, default=UserType.CLIENT)  # client, therapist, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # For therapist verification
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    emotion_analyses = relationship("EmotionAnalysis", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)

    # Analytics relationships
    analytics_events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")
    mood_trends = relationship("MoodTrend", back_populates="user", cascade="all, delete-orphan")
    progress_insights = relationship("ProgressInsight", back_populates="user", cascade="all, delete-orphan")
    conversation_analytics = relationship("ConversationAnalytics", back_populates="user", cascade="all, delete-orphan")
    progress_metrics = relationship("UserProgressMetrics", back_populates="user", cascade="all, delete-orphan")

    # Trauma mapping relationships
    life_events = relationship("LifeEvent", cascade="all, delete-orphan")
    trauma_mappings = relationship("TraumaMapping", cascade="all, delete-orphan")
    reframe_sessions = relationship("ReframeSession", cascade="all, delete-orphan")

    # Inner Ally memory relationships
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")
    personal_triggers = relationship("PersonalTrigger", back_populates="user", cascade="all, delete-orphan")
    coping_preferences = relationship("CopingPreference", back_populates="user", cascade="all, delete-orphan")
    supportive_phrases = relationship("SupportivePhrase", back_populates="user", cascade="all, delete-orphan")
    conversation_patterns = relationship("ConversationPattern", back_populates="user", cascade="all, delete-orphan")

    # Agent persona relationships
    persona_customizations = relationship("UserPersonaCustomization", back_populates="user", cascade="all, delete-orphan")
    micro_checkins = relationship("MicroCheckIn", back_populates="user", cascade="all, delete-orphan")
    widget_interactions = relationship("WidgetInteraction", back_populates="user", cascade="all, delete-orphan")

    # Notification relationships
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan", uselist=False)
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")

    # Voice journaling relationships
    voice_journals = relationship("VoiceJournal", back_populates="user", cascade="all, delete-orphan")

    # Emotion art relationships
    emotion_arts = relationship("EmotionArt", back_populates="user", cascade="all, delete-orphan")

    # Therapist profile relationship (for therapist users)
    therapist_profile = relationship("TherapistProfile", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserPreferences(Base):
    """User preferences model for storing user settings."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Appearance preferences
    theme = Column(String, default="light")  # light, dark
    language = Column(String, default="en")
    timezone = Column(String, default="UTC")

    # Notification preferences
    daily_reminders = Column(Boolean, default=True)
    weekly_reports = Column(Boolean, default=True)
    recommendations = Column(Boolean, default=True)
    achievements = Column(Boolean, default=False)

    # Inner Ally Agent preferences
    agent_persona = Column(String, default="gentle_mentor")  # gentle_mentor, warm_friend, wise_elder, custom
    custom_persona_name = Column(String, nullable=True)
    custom_persona_description = Column(Text, nullable=True)
    favorite_affirmations = Column(Text, nullable=True)  # JSON string of affirmations
    preferred_coping_styles = Column(Text, nullable=True)  # JSON string of coping preferences
    crisis_contact_enabled = Column(Boolean, default=True)
    widget_enabled = Column(Boolean, default=True)
    micro_checkin_frequency = Column(Integer, default=4)  # hours between check-ins

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, theme='{self.theme}')>"
