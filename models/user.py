"""
User model for authentication and user management.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
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

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, theme='{self.theme}')>"
