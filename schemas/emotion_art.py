"""
Pydantic schemas for emotion art generation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.emotion_art import ArtStyle, ArtStatus


class EmotionArtBase(BaseModel):
    """Base schema for emotion art."""
    title: Optional[str] = None
    description: Optional[str] = None
    art_style: ArtStyle = ArtStyle.ABSTRACT


class EmotionArtCreate(EmotionArtBase):
    """Schema for creating emotion art."""
    source_emotion_analysis_id: Optional[int] = None
    source_voice_journal_id: Optional[int] = None
    emotion_snapshot: Dict[str, float] = Field(..., description="Emotion data for art generation")
    complexity_level: int = Field(default=3, ge=1, le=5)
    generation_parameters: Optional[Dict[str, Any]] = None


class EmotionArtUpdate(BaseModel):
    """Schema for updating emotion art."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_shared: Optional[bool] = None


class EmotionArtResponse(EmotionArtBase):
    """Schema for emotion art response."""
    id: int
    user_id: int
    status: ArtStatus
    source_emotion_analysis_id: Optional[int] = None
    source_voice_journal_id: Optional[int] = None
    emotion_snapshot: Dict[str, float]
    svg_content: Optional[str] = None
    svg_data_url: Optional[str] = None
    color_palette: Optional[List[str]] = None
    dominant_emotion: str
    emotional_intensity: float
    complexity_level: int
    generation_seed: Optional[str] = None
    generation_parameters: Optional[Dict[str, Any]] = None
    is_favorite: bool
    is_shared: bool
    view_count: int
    created_at: datetime
    generated_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArtCustomizationBase(BaseModel):
    """Base schema for art customization."""
    customization_type: str = Field(..., description="Type of customization (color, shape, style, composition)")
    new_value: Dict[str, Any] = Field(..., description="New value for the customization")
    description: Optional[str] = None


class ArtCustomizationCreate(ArtCustomizationBase):
    """Schema for creating art customization."""
    emotion_art_id: int
    original_value: Optional[Dict[str, Any]] = None


class ArtCustomizationUpdate(BaseModel):
    """Schema for updating art customization."""
    new_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ArtCustomizationResponse(ArtCustomizationBase):
    """Schema for art customization response."""
    id: int
    emotion_art_id: int
    user_id: int
    original_value: Optional[Dict[str, Any]] = None
    is_active: bool
    applied_at: datetime

    class Config:
        from_attributes = True


class ArtGalleryBase(BaseModel):
    """Base schema for art gallery."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False


class ArtGalleryCreate(ArtGalleryBase):
    """Schema for creating art gallery."""
    art_pieces: Optional[List[int]] = None


class ArtGalleryUpdate(BaseModel):
    """Schema for updating art gallery."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    art_pieces: Optional[List[int]] = None


class ArtGalleryResponse(ArtGalleryBase):
    """Schema for art gallery response."""
    id: int
    user_id: int
    art_pieces: Optional[List[int]] = None
    total_pieces: int
    total_views: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtShareBase(BaseModel):
    """Base schema for art share."""
    share_message: Optional[str] = None
    is_anonymous: bool = False


class ArtShareCreate(ArtShareBase):
    """Schema for creating art share."""
    emotion_art_id: int


class ArtShareUpdate(BaseModel):
    """Schema for updating art share."""
    share_message: Optional[str] = None
    is_anonymous: Optional[bool] = None


class ArtShareResponse(ArtShareBase):
    """Schema for art share response."""
    id: int
    emotion_art_id: int
    user_id: int
    view_count: int
    like_count: int
    comment_count: int
    is_approved: bool
    is_flagged: bool
    shared_at: datetime

    class Config:
        from_attributes = True


class ArtGenerationRequest(BaseModel):
    """Schema for art generation request."""
    emotion_data: Dict[str, float] = Field(..., description="Emotion scores for art generation")
    art_style: ArtStyle = ArtStyle.ABSTRACT
    complexity_level: int = Field(default=3, ge=1, le=5)
    color_preferences: Optional[List[str]] = None
    title: Optional[str] = None
    description: Optional[str] = None
    source_type: str = Field(..., description="Source of emotion data (analysis, voice_journal, manual)")
    source_id: Optional[int] = None


class ArtCustomizationRequest(BaseModel):
    """Schema for art customization request."""
    customization_type: str = Field(..., description="Type of customization")
    parameters: Dict[str, Any] = Field(..., description="Customization parameters")
    preview_only: bool = Field(default=False, description="Whether to only preview changes")


class EmotionArtAnalytics(BaseModel):
    """Schema for emotion art analytics."""
    total_artworks: int
    favorite_count: int
    shared_count: int
    total_views: int
    most_used_styles: List[Dict[str, Any]]
    emotion_distribution: Dict[str, int]
    color_preferences: List[str]
    customization_frequency: Dict[str, int]
    engagement_metrics: Dict[str, float]


class ArtGalleryWithArt(ArtGalleryResponse):
    """Schema for art gallery with embedded art pieces."""
    artworks: List[EmotionArtResponse]
