"""
Pydantic schemas for agent persona and widget interactions.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentPersonaBase(BaseModel):
    """Base schema for agent personas."""
    persona_key: str = Field(..., description="Unique key for the persona")
    display_name: str = Field(..., description="Display name for the persona")
    description: str = Field(..., description="Description of the persona")
    communication_style: Dict[str, Any] = Field(..., description="Communication style configuration")
    therapeutic_approach: str = Field(..., description="Primary therapeutic approach")
    response_patterns: Dict[str, Any] = Field(..., description="Response pattern configuration")
    empathy_level: str = Field(default="high", pattern="^(low|medium|high|very_high)$")
    directness_level: str = Field(default="gentle", pattern="^(direct|gentle|very_gentle)$")
    formality_level: str = Field(default="casual", pattern="^(formal|casual|very_casual)$")
    preferred_interventions: Optional[List[str]] = None
    crisis_response_style: Optional[Dict[str, Any]] = None


class AgentPersonaCreate(AgentPersonaBase):
    """Schema for creating agent personas."""
    pass


class AgentPersonaUpdate(BaseModel):
    """Schema for updating agent personas."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    communication_style: Optional[Dict[str, Any]] = None
    therapeutic_approach: Optional[str] = None
    response_patterns: Optional[Dict[str, Any]] = None
    empathy_level: Optional[str] = Field(None, pattern="^(low|medium|high|very_high)$")
    directness_level: Optional[str] = Field(None, pattern="^(direct|gentle|very_gentle)$")
    formality_level: Optional[str] = Field(None, pattern="^(formal|casual|very_casual)$")
    preferred_interventions: Optional[List[str]] = None
    crisis_response_style: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentPersonaResponse(AgentPersonaBase):
    """Schema for agent persona response."""
    id: int
    is_system_persona: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPersonaCustomizationBase(BaseModel):
    """Base schema for user persona customizations."""
    persona_id: int = Field(..., description="ID of the base persona")
    custom_name: Optional[str] = None
    custom_description: Optional[str] = None
    custom_communication_style: Optional[Dict[str, Any]] = None
    custom_response_patterns: Optional[Dict[str, Any]] = None
    favorite_phrases: Optional[List[str]] = None
    avoid_phrases: Optional[List[str]] = None
    custom_affirmations: Optional[List[str]] = None


class UserPersonaCustomizationCreate(UserPersonaCustomizationBase):
    """Schema for creating user persona customizations."""
    pass


class UserPersonaCustomizationUpdate(BaseModel):
    """Schema for updating user persona customizations."""
    custom_name: Optional[str] = None
    custom_description: Optional[str] = None
    custom_communication_style: Optional[Dict[str, Any]] = None
    custom_response_patterns: Optional[Dict[str, Any]] = None
    favorite_phrases: Optional[List[str]] = None
    avoid_phrases: Optional[List[str]] = None
    custom_affirmations: Optional[List[str]] = None
    is_active: Optional[bool] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)


class UserPersonaCustomizationResponse(UserPersonaCustomizationBase):
    """Schema for user persona customization response."""
    id: int
    user_id: int
    is_active: bool
    usage_count: int
    last_used: Optional[datetime] = None
    effectiveness_rating: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MicroCheckInBase(BaseModel):
    """Base schema for micro check-ins."""
    trigger_type: str = Field(..., pattern="^(scheduled|user_initiated|crisis_detected)$")
    mood_rating: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    user_response: Optional[str] = None
    location_context: Optional[str] = None
    time_context: str = Field(..., pattern="^(morning|afternoon|evening|night)$")
    emotional_context: Optional[Dict[str, Any]] = None


class MicroCheckInCreate(MicroCheckInBase):
    """Schema for creating micro check-ins."""
    pass


class MicroCheckInUpdate(BaseModel):
    """Schema for updating micro check-ins."""
    mood_rating: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    user_response: Optional[str] = None
    ai_response: Optional[str] = None
    intervention_suggested: Optional[str] = None
    was_helpful: Optional[bool] = None
    follow_up_needed: Optional[bool] = None
    duration_seconds: Optional[int] = None


class MicroCheckInResponse(MicroCheckInBase):
    """Schema for micro check-in response."""
    id: int
    user_id: int
    ai_response: str
    intervention_suggested: Optional[str] = None
    was_helpful: Optional[bool] = None
    follow_up_needed: bool
    escalation_triggered: bool
    duration_seconds: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WidgetInteractionBase(BaseModel):
    """Base schema for widget interactions."""
    interaction_type: str = Field(..., pattern="^(summon|dismiss|quick_chat|sos|settings)$")
    widget_state: str = Field(..., pattern="^(minimized|expanded|floating|docked)$")
    page_context: Optional[str] = None
    emotional_state: Optional[str] = None


class WidgetInteractionCreate(WidgetInteractionBase):
    """Schema for creating widget interactions."""
    pass


class WidgetInteractionUpdate(BaseModel):
    """Schema for updating widget interactions."""
    action_taken: Optional[str] = None
    duration_seconds: Optional[int] = None


class WidgetInteractionResponse(WidgetInteractionBase):
    """Schema for widget interaction response."""
    id: int
    user_id: int
    action_taken: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuickChatRequest(BaseModel):
    """Schema for quick chat requests from the widget."""
    message: str = Field(..., max_length=500, description="Quick message for 30-second interaction")
    emotional_state: Optional[str] = None
    urgency_level: str = Field(default="normal", pattern="^(low|normal|high|crisis)$")
    context: Optional[Dict[str, Any]] = None


class QuickChatResponse(BaseModel):
    """Schema for quick chat responses."""
    response: str
    intervention_suggested: Optional[str] = None
    follow_up_recommended: bool
    escalation_needed: bool
    estimated_duration: int  # seconds
    supportive_phrases: List[str]


class PersonaPreview(BaseModel):
    """Schema for persona preview."""
    persona_key: str
    display_name: str
    description: str
    sample_responses: List[str]
    best_for: List[str]
    communication_style_summary: str


class WidgetSettings(BaseModel):
    """Schema for widget settings."""
    enabled: bool = True
    position: str = Field(default="bottom-right", pattern="^(bottom-right|bottom-left|top-right|top-left)$")
    auto_minimize: bool = True
    check_in_frequency: int = Field(default=4, ge=1, le=24)  # hours
    crisis_mode_enabled: bool = True
    notification_sounds: bool = True
    theme: str = Field(default="auto", pattern="^(light|dark|auto)$")


class InnerAllyStatus(BaseModel):
    """Schema for Inner Ally status."""
    is_active: bool
    current_persona: str
    last_interaction: Optional[datetime] = None
    total_interactions: int
    recent_mood_trend: str
    available_interventions: List[str]
    next_check_in: Optional[datetime] = None
