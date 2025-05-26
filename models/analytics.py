"""
Advanced analytics models for detailed progress tracking and insights.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from database import Base


class AnalyticsEventType(PyEnum):
    """Types of analytics events."""
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    EMOTION_PEAK = "emotion_peak"
    THERAPEUTIC_BREAKTHROUGH = "therapeutic_breakthrough"
    CRISIS_DETECTED = "crisis_detected"
    RECOMMENDATION_COMPLETED = "recommendation_completed"
    MOOD_IMPROVEMENT = "mood_improvement"
    PATTERN_IDENTIFIED = "pattern_identified"


class MoodTrendType(PyEnum):
    """Types of mood trends."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class AnalyticsEvent(Base):
    """Analytics event model for tracking user interactions and milestones."""
    
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    
    # Event details
    event_type = Column(String, nullable=False)  # AnalyticsEventType enum value
    event_name = Column(String, nullable=False)
    event_description = Column(Text, nullable=True)
    
    # Event data
    event_data = Column(JSON, nullable=True)  # Flexible data storage
    emotion_snapshot = Column(JSON, nullable=True)  # Emotion state at event time
    
    # Event metadata
    severity = Column(String, default="normal")  # low, normal, high, critical
    confidence = Column(Float, default=1.0)
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    conversation = relationship("Conversation")
    
    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, user_id={self.user_id}, type='{self.event_type}')>"


class MoodTrend(Base):
    """Mood trend model for tracking emotional patterns over time."""
    
    __tablename__ = "mood_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trend analysis
    trend_type = Column(String, nullable=False)  # MoodTrendType enum value
    trend_strength = Column(Float, nullable=False)  # 0.0 to 1.0
    trend_duration_days = Column(Integer, nullable=False)
    
    # Emotion metrics
    dominant_emotion = Column(String, nullable=False)
    emotion_stability = Column(Float, nullable=False)  # Variance measure
    average_sentiment = Column(Float, nullable=False)  # -1 to 1
    
    # Trend data
    emotion_progression = Column(JSON, nullable=False)  # Time series data
    key_events = Column(JSON, nullable=True)  # Significant events during trend
    
    # Analysis period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="mood_trends")
    
    def __repr__(self):
        return f"<MoodTrend(id={self.id}, user_id={self.user_id}, type='{self.trend_type}')>"


class ProgressInsight(Base):
    """Progress insight model for storing AI-generated insights about user progress."""
    
    __tablename__ = "progress_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Insight details
    insight_type = Column(String, nullable=False)  # pattern, breakthrough, concern, recommendation
    insight_title = Column(String, nullable=False)
    insight_description = Column(Text, nullable=False)
    
    # Insight data
    supporting_data = Column(JSON, nullable=True)  # Data that supports this insight
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    impact_level = Column(String, default="medium")  # low, medium, high
    
    # Actionability
    is_actionable = Column(Boolean, default=False)
    suggested_actions = Column(JSON, nullable=True)  # List of suggested actions
    
    # Insight metadata
    data_period_start = Column(DateTime(timezone=True), nullable=False)
    data_period_end = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # User interaction
    is_acknowledged = Column(Boolean, default=False)
    user_feedback = Column(Text, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="progress_insights")
    
    def __repr__(self):
        return f"<ProgressInsight(id={self.id}, user_id={self.user_id}, type='{self.insight_type}')>"


class ConversationAnalytics(Base):
    """Conversation analytics model for detailed conversation metrics."""
    
    __tablename__ = "conversation_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conversation metrics
    total_messages = Column(Integer, nullable=False)
    user_messages = Column(Integer, nullable=False)
    ai_messages = Column(Integer, nullable=False)
    conversation_duration_minutes = Column(Float, nullable=True)
    
    # Emotional journey
    emotion_trajectory = Column(JSON, nullable=False)  # Emotion changes throughout conversation
    emotional_range = Column(Float, nullable=False)  # How much emotions varied
    dominant_emotions = Column(JSON, nullable=False)  # Most prominent emotions
    
    # Therapeutic effectiveness
    therapeutic_approach_used = Column(String, nullable=False)
    approach_effectiveness = Column(Float, nullable=True)  # User feedback or inferred
    crisis_indicators_detected = Column(JSON, nullable=True)
    
    # Conversation quality
    engagement_score = Column(Float, nullable=False)  # Based on message length, frequency
    empathy_score = Column(Float, nullable=False)  # AI empathy rating
    resolution_score = Column(Float, nullable=True)  # How well issues were addressed
    
    # Outcomes
    mood_change = Column(Float, nullable=True)  # Start vs end mood
    insights_generated = Column(Integer, default=0)
    recommendations_provided = Column(Integer, default=0)
    
    # Timestamps
    conversation_start = Column(DateTime(timezone=True), nullable=False)
    conversation_end = Column(DateTime(timezone=True), nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation")
    user = relationship("User", back_populates="conversation_analytics")
    
    def __repr__(self):
        return f"<ConversationAnalytics(id={self.id}, conversation_id={self.conversation_id})>"


class UserProgressMetrics(Base):
    """User progress metrics model for aggregated progress tracking."""
    
    __tablename__ = "user_progress_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time period
    period_type = Column(String, nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Engagement metrics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    average_session_duration = Column(Float, default=0.0)
    engagement_consistency = Column(Float, default=0.0)  # How regularly they engage
    
    # Emotional metrics
    average_mood_score = Column(Float, default=0.0)  # -1 to 1
    mood_stability = Column(Float, default=0.0)  # Lower variance = more stable
    emotional_growth_score = Column(Float, default=0.0)  # Progress indicator
    
    # Therapeutic metrics
    recommendations_completed = Column(Integer, default=0)
    recommendations_completion_rate = Column(Float, default=0.0)
    therapeutic_engagement_score = Column(Float, default=0.0)
    
    # Progress indicators
    crisis_episodes = Column(Integer, default=0)
    breakthrough_moments = Column(Integer, default=0)
    overall_progress_score = Column(Float, default=0.0)  # Composite score
    
    # Calculated at
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress_metrics")
    
    def __repr__(self):
        return f"<UserProgressMetrics(id={self.id}, user_id={self.user_id}, period='{self.period_type}')>"
