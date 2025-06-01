"""
Agent persona models for customizable AI personality and behavior.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AgentPersona(Base):
    """Predefined and custom agent personas for the Inner Ally."""
    
    __tablename__ = "agent_personas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Persona identification
    persona_key = Column(String, unique=True, nullable=False)  # gentle_mentor, warm_friend, etc.
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Persona characteristics
    communication_style = Column(JSON, nullable=False)  # tone, language patterns, etc.
    therapeutic_approach = Column(String, nullable=False)  # primary therapeutic approach
    response_patterns = Column(JSON, nullable=False)  # how they typically respond
    
    # Personality traits
    empathy_level = Column(String, default="high")  # low, medium, high, very_high
    directness_level = Column(String, default="gentle")  # direct, gentle, very_gentle
    formality_level = Column(String, default="casual")  # formal, casual, very_casual
    
    # Behavioral preferences
    preferred_interventions = Column(JSON, nullable=True)  # types of interventions they prefer
    crisis_response_style = Column(JSON, nullable=True)  # how they handle crisis situations
    
    # Customization
    is_system_persona = Column(Boolean, default=True)  # system-defined vs user-created
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_customizations = relationship("UserPersonaCustomization", back_populates="persona", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentPersona(key='{self.persona_key}', name='{self.display_name}')>"


class UserPersonaCustomization(Base):
    """User-specific customizations to agent personas."""
    
    __tablename__ = "user_persona_customizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("agent_personas.id"), nullable=False)
    
    # Customization details
    custom_name = Column(String, nullable=True)  # user's custom name for this persona
    custom_description = Column(Text, nullable=True)  # user's custom description
    
    # Behavioral customizations
    custom_communication_style = Column(JSON, nullable=True)  # overrides for communication
    custom_response_patterns = Column(JSON, nullable=True)  # custom response patterns
    
    # Personal touches
    favorite_phrases = Column(JSON, nullable=True)  # phrases this persona should use
    avoid_phrases = Column(JSON, nullable=True)  # phrases to avoid
    custom_affirmations = Column(JSON, nullable=True)  # personalized affirmations
    
    # Usage tracking
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 user rating
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="persona_customizations")
    persona = relationship("AgentPersona", back_populates="user_customizations")
    
    def __repr__(self):
        return f"<UserPersonaCustomization(user_id={self.user_id}, persona_id={self.persona_id})>"


class MicroCheckIn(Base):
    """Quick 30-second check-ins with the Calm Companion widget."""
    
    __tablename__ = "micro_checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Check-in details
    trigger_type = Column(String, nullable=False)  # scheduled, user_initiated, crisis_detected
    mood_rating = Column(Integer, nullable=True)  # 1-10 scale
    stress_level = Column(Integer, nullable=True)  # 1-10 scale
    
    # Quick responses
    user_response = Column(Text, nullable=True)  # brief user input
    ai_response = Column(Text, nullable=False)  # AI's supportive response
    intervention_suggested = Column(String, nullable=True)  # quick intervention suggested
    
    # Context
    location_context = Column(String, nullable=True)  # where they were (if shared)
    time_context = Column(String, nullable=False)  # morning, afternoon, evening, night
    emotional_context = Column(JSON, nullable=True)  # detected emotions
    
    # Outcome
    was_helpful = Column(Boolean, nullable=True)  # user feedback
    follow_up_needed = Column(Boolean, default=False)
    escalation_triggered = Column(Boolean, default=False)
    
    # Duration tracking
    duration_seconds = Column(Integer, nullable=True)  # how long the check-in took
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="micro_checkins")
    
    def __repr__(self):
        return f"<MicroCheckIn(user_id={self.user_id}, trigger='{self.trigger_type}')>"


class WidgetInteraction(Base):
    """Tracking interactions with the Calm Companion widget."""
    
    __tablename__ = "widget_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String, nullable=False)  # summon, dismiss, quick_chat, sos, settings
    widget_state = Column(String, nullable=False)  # minimized, expanded, floating, docked
    
    # Context
    page_context = Column(String, nullable=True)  # which page they were on
    emotional_state = Column(String, nullable=True)  # detected emotional state
    
    # Outcome
    action_taken = Column(String, nullable=True)  # what action resulted from interaction
    duration_seconds = Column(Integer, nullable=True)  # how long interaction lasted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="widget_interactions")
    
    def __repr__(self):
        return f"<WidgetInteraction(user_id={self.user_id}, type='{self.interaction_type}')>"
