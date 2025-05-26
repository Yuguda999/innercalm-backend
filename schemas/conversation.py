"""
Conversation and message-related Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(MessageBase):
    """Schema for message creation."""
    pass


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    conversation_id: int
    is_user_message: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = Field(None, max_length=200)


class ConversationCreate(ConversationBase):
    """Schema for conversation creation."""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    message: MessageResponse
    ai_response: MessageResponse
    conversation_id: int
    emotion_analysis: Optional[dict] = None
