"""
Pydantic schemas for user memory and personalization.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserMemoryBase(BaseModel):
    """Base schema for user memory."""
    memory_type: str = Field(..., description="Type of memory (trigger, coping_style, supportive_phrase, pattern)")
    memory_key: str = Field(..., description="Specific identifier for the memory")
    memory_value: str = Field(..., description="The actual memory content")
    effectiveness_score: Optional[float] = Field(default=0.0, ge=-1.0, le=1.0)
    context_tags: Optional[Dict[str, Any]] = None
    confidence_level: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class UserMemoryCreate(UserMemoryBase):
    """Schema for creating user memory."""
    pass


class UserMemoryUpdate(BaseModel):
    """Schema for updating user memory."""
    memory_value: Optional[str] = None
    effectiveness_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    context_tags: Optional[Dict[str, Any]] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class UserMemoryResponse(UserMemoryBase):
    """Schema for user memory response."""
    id: int
    user_id: int
    usage_count: int
    last_used: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PersonalTriggerBase(BaseModel):
    """Base schema for personal triggers."""
    trigger_text: str = Field(..., description="The trigger phrase or situation")
    trigger_category: str = Field(..., description="Category of trigger (emotional, situational, etc.)")
    intensity_level: int = Field(default=5, ge=1, le=10)
    typical_response: Optional[str] = None
    helpful_interventions: Optional[List[str]] = None


class PersonalTriggerCreate(PersonalTriggerBase):
    """Schema for creating personal triggers."""
    pass


class PersonalTriggerUpdate(BaseModel):
    """Schema for updating personal triggers."""
    trigger_text: Optional[str] = None
    trigger_category: Optional[str] = None
    intensity_level: Optional[int] = Field(None, ge=1, le=10)
    typical_response: Optional[str] = None
    helpful_interventions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    resolution_notes: Optional[str] = None


class PersonalTriggerResponse(PersonalTriggerBase):
    """Schema for personal trigger response."""
    id: int
    user_id: int
    identified_date: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int
    is_active: bool
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


class CopingPreferenceBase(BaseModel):
    """Base schema for coping preferences."""
    strategy_name: str = Field(..., description="Name of the coping strategy")
    strategy_description: str = Field(..., description="Description of the strategy")
    strategy_category: str = Field(..., description="Category (mindfulness, physical, cognitive, etc.)")
    effectiveness_rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)
    usage_frequency: str = Field(default="rarely", pattern="^(rarely|sometimes|often|always)$")
    best_situations: Optional[List[str]] = None
    worst_situations: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    reminder_phrases: Optional[List[str]] = None


class CopingPreferenceCreate(CopingPreferenceBase):
    """Schema for creating coping preferences."""
    pass


class CopingPreferenceUpdate(BaseModel):
    """Schema for updating coping preferences."""
    strategy_name: Optional[str] = None
    strategy_description: Optional[str] = None
    strategy_category: Optional[str] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    usage_frequency: Optional[str] = Field(None, pattern="^(rarely|sometimes|often|always)$")
    best_situations: Optional[List[str]] = None
    worst_situations: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    reminder_phrases: Optional[List[str]] = None


class CopingPreferenceResponse(CopingPreferenceBase):
    """Schema for coping preference response."""
    id: int
    user_id: int
    success_rate: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportivePhraseBase(BaseModel):
    """Base schema for supportive phrases."""
    phrase_text: str = Field(..., description="The supportive phrase text")
    phrase_category: str = Field(..., description="Category (affirmation, quote, reminder, etc.)")
    source: Optional[str] = None
    resonance_score: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)
    best_emotions: Optional[List[str]] = None
    situation_tags: Optional[List[str]] = None
    is_favorite: bool = False
    custom_variation: Optional[str] = None


class SupportivePhraseCreate(SupportivePhraseBase):
    """Schema for creating supportive phrases."""
    pass


class SupportivePhraseUpdate(BaseModel):
    """Schema for updating supportive phrases."""
    phrase_text: Optional[str] = None
    phrase_category: Optional[str] = None
    source: Optional[str] = None
    resonance_score: Optional[float] = Field(None, ge=0.0, le=5.0)
    best_emotions: Optional[List[str]] = None
    situation_tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    custom_variation: Optional[str] = None


class SupportivePhraseResponse(SupportivePhraseBase):
    """Schema for supportive phrase response."""
    id: int
    user_id: int
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationPatternBase(BaseModel):
    """Base schema for conversation patterns."""
    pattern_type: str = Field(..., description="Type of pattern (communication_style, topic_preference, etc.)")
    pattern_name: str = Field(..., description="Name of the pattern")
    pattern_description: str = Field(..., description="Description of the pattern")
    pattern_strength: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    context_data: Optional[Dict[str, Any]] = None


class ConversationPatternCreate(ConversationPatternBase):
    """Schema for creating conversation patterns."""
    pass


class ConversationPatternUpdate(BaseModel):
    """Schema for updating conversation patterns."""
    pattern_description: Optional[str] = None
    pattern_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConversationPatternResponse(ConversationPatternBase):
    """Schema for conversation pattern response."""
    id: int
    user_id: int
    evidence_count: int
    first_observed: datetime
    last_observed: datetime
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemoryInsight(BaseModel):
    """Schema for memory-based insights."""
    insight_type: str
    insight_text: str
    confidence: float
    supporting_memories: List[str]
    recommendations: List[str]


class PersonalizationSummary(BaseModel):
    """Schema for user personalization summary."""
    total_memories: int
    active_triggers: int
    preferred_coping_strategies: List[str]
    favorite_phrases: List[str]
    conversation_preferences: Dict[str, Any]
    recent_insights: List[MemoryInsight]
