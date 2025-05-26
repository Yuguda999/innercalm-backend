"""
Recommendation models for personalized healing suggestions.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from database import Base


class RecommendationType(PyEnum):
    """Types of recommendations available."""
    BREATHING_EXERCISE = "breathing_exercise"
    JOURNALING_PROMPT = "journaling_prompt"
    MINDFULNESS_PRACTICE = "mindfulness_practice"
    COGNITIVE_REFRAMING = "cognitive_reframing"
    PHYSICAL_ACTIVITY = "physical_activity"
    RELAXATION_TECHNIQUE = "relaxation_technique"


class Recommendation(Base):
    """Recommendation model for storing personalized healing suggestions."""
    
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Recommendation details
    type = Column(Enum(RecommendationType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    
    # Personalization data
    target_emotions = Column(JSON, nullable=False)  # Emotions this recommendation targets
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    estimated_duration = Column(Integer, nullable=True)  # Duration in minutes
    
    # Recommendation metadata
    is_completed = Column(Boolean, default=False)
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 user rating
    notes = Column(Text, nullable=True)  # User notes about the recommendation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, user_id={self.user_id}, type='{self.type.value}', title='{self.title}')>"
