"""
Emotion analysis and pattern models.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EmotionAnalysis(Base):
    """Emotion analysis model for storing sentiment analysis results."""
    
    __tablename__ = "emotion_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # Primary emotions with confidence scores
    joy = Column(Float, default=0.0)
    sadness = Column(Float, default=0.0)
    anger = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    
    # Overall sentiment
    sentiment_score = Column(Float, nullable=False)  # -1 to 1
    sentiment_label = Column(String, nullable=False)  # positive, negative, neutral
    
    # Detected themes and keywords
    themes = Column(JSON, nullable=True)  # List of detected themes
    keywords = Column(JSON, nullable=True)  # List of important keywords
    
    # Analysis metadata
    confidence = Column(Float, nullable=False)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emotion_analyses")
    message = relationship("Message", back_populates="emotion_analysis")
    
    def __repr__(self):
        return f"<EmotionAnalysis(id={self.id}, user_id={self.user_id}, sentiment='{self.sentiment_label}')>"


class EmotionPattern(Base):
    """Emotion pattern model for tracking recurring emotional themes."""
    
    __tablename__ = "emotion_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Pattern identification
    pattern_name = Column(String, nullable=False)
    pattern_description = Column(Text, nullable=True)
    
    # Pattern metrics
    frequency = Column(Integer, default=1)  # How often this pattern occurs
    intensity = Column(Float, nullable=False)  # Average intensity of emotions
    
    # Temporal information
    first_detected = Column(DateTime(timezone=True), server_default=func.now())
    last_detected = Column(DateTime(timezone=True), server_default=func.now())
    
    # Pattern data
    triggers = Column(JSON, nullable=True)  # Common triggers for this pattern
    emotions = Column(JSON, nullable=False)  # Emotion distribution
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<EmotionPattern(id={self.id}, user_id={self.user_id}, pattern='{self.pattern_name}')>"
