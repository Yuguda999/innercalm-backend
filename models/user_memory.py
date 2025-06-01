"""
User memory models for longitudinal memory and personalization.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserMemory(Base):
    """Longitudinal memory for user patterns and preferences."""
    
    __tablename__ = "user_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Memory categories
    memory_type = Column(String, nullable=False)  # trigger, coping_style, supportive_phrase, pattern
    memory_key = Column(String, nullable=False)  # specific identifier
    memory_value = Column(Text, nullable=False)  # the actual memory content
    
    # Effectiveness tracking
    effectiveness_score = Column(Float, default=0.0)  # -1.0 to 1.0
    usage_count = Column(Integer, default=1)
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context information
    context_tags = Column(JSON, nullable=True)  # emotional context, situation type, etc.
    confidence_level = Column(Float, default=0.5)  # how confident we are in this memory
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    def __repr__(self):
        return f"<UserMemory(user_id={self.user_id}, type='{self.memory_type}', key='{self.memory_key}')>"


class PersonalTrigger(Base):
    """Personal triggers identified through conversations."""
    
    __tablename__ = "personal_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trigger information
    trigger_text = Column(Text, nullable=False)  # the trigger phrase or situation
    trigger_category = Column(String, nullable=False)  # emotional, situational, relational, etc.
    intensity_level = Column(Integer, default=5)  # 1-10 scale
    
    # Response patterns
    typical_response = Column(Text, nullable=True)  # how user typically responds
    helpful_interventions = Column(JSON, nullable=True)  # what has helped before
    
    # Tracking
    identified_date = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="personal_triggers")
    
    def __repr__(self):
        return f"<PersonalTrigger(user_id={self.user_id}, category='{self.trigger_category}')>"


class CopingPreference(Base):
    """User's preferred coping strategies and their effectiveness."""
    
    __tablename__ = "coping_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Coping strategy information
    strategy_name = Column(String, nullable=False)
    strategy_description = Column(Text, nullable=False)
    strategy_category = Column(String, nullable=False)  # mindfulness, physical, cognitive, social, etc.
    
    # Effectiveness tracking
    effectiveness_rating = Column(Float, default=0.0)  # user's self-reported effectiveness
    usage_frequency = Column(String, default="rarely")  # rarely, sometimes, often, always
    success_rate = Column(Float, default=0.0)  # calculated success rate
    
    # Context
    best_situations = Column(JSON, nullable=True)  # when this works best
    worst_situations = Column(JSON, nullable=True)  # when this doesn't work
    
    # Personalization
    custom_instructions = Column(Text, nullable=True)  # user's custom way of doing this
    reminder_phrases = Column(JSON, nullable=True)  # phrases that help remember to use this
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="coping_preferences")
    
    def __repr__(self):
        return f"<CopingPreference(user_id={self.user_id}, strategy='{self.strategy_name}')>"


class SupportivePhrase(Base):
    """Supportive phrases that resonate with the user."""
    
    __tablename__ = "supportive_phrases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Phrase information
    phrase_text = Column(Text, nullable=False)
    phrase_category = Column(String, nullable=False)  # affirmation, quote, reminder, etc.
    source = Column(String, nullable=True)  # where it came from (user, AI, book, etc.)
    
    # Effectiveness
    resonance_score = Column(Float, default=0.0)  # how much it resonates with user
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Context
    best_emotions = Column(JSON, nullable=True)  # when this phrase works best
    situation_tags = Column(JSON, nullable=True)  # situations where this helps
    
    # Personalization
    is_favorite = Column(Boolean, default=False)
    custom_variation = Column(Text, nullable=True)  # user's personalized version
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="supportive_phrases")
    
    def __repr__(self):
        return f"<SupportivePhrase(user_id={self.user_id}, category='{self.phrase_category}')>"


class ConversationPattern(Base):
    """Patterns identified in user's conversation style and preferences."""
    
    __tablename__ = "conversation_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Pattern information
    pattern_type = Column(String, nullable=False)  # communication_style, topic_preference, response_preference
    pattern_name = Column(String, nullable=False)
    pattern_description = Column(Text, nullable=False)
    
    # Strength and confidence
    pattern_strength = Column(Float, default=0.0)  # how strong this pattern is
    confidence_level = Column(Float, default=0.0)  # how confident we are
    
    # Evidence
    evidence_count = Column(Integer, default=1)
    first_observed = Column(DateTime(timezone=True), server_default=func.now())
    last_observed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context
    context_data = Column(JSON, nullable=True)  # additional context information
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversation_patterns")
    
    def __repr__(self):
        return f"<ConversationPattern(user_id={self.user_id}, type='{self.pattern_type}')>"
