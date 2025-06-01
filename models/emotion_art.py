"""
Emotion art models for generative art based on user's emotional state.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class ArtStyle(str, Enum):
    """Available art styles for emotion portraits."""
    ABSTRACT = "abstract"
    GEOMETRIC = "geometric"
    ORGANIC = "organic"
    MINIMALIST = "minimalist"
    EXPRESSIVE = "expressive"


class ArtStatus(str, Enum):
    """Status of art generation."""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class EmotionArt(Base):
    """Generated emotion art model."""
    
    __tablename__ = "emotion_arts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Art metadata
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    art_style = Column(String, default=ArtStyle.ABSTRACT.value)
    status = Column(String, default=ArtStatus.GENERATING.value)
    
    # Source emotion data
    source_emotion_analysis_id = Column(Integer, ForeignKey("emotion_analyses.id"), nullable=True)
    source_voice_journal_id = Column(Integer, ForeignKey("voice_journals.id"), nullable=True)
    emotion_snapshot = Column(JSON, nullable=False)  # Emotion data used for generation
    
    # Generated art data
    svg_content = Column(Text, nullable=True)  # The actual SVG code
    svg_data_url = Column(Text, nullable=True)  # Base64 encoded data URL
    color_palette = Column(JSON, nullable=True)  # Colors used in the art
    
    # Art characteristics
    dominant_emotion = Column(String, nullable=False)
    emotional_intensity = Column(Float, nullable=False)
    complexity_level = Column(Integer, default=3)  # 1-5 scale
    
    # Generation parameters
    generation_seed = Column(String, nullable=True)  # For reproducibility
    generation_parameters = Column(JSON, nullable=True)
    
    # User interaction
    is_favorite = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_at = Column(DateTime(timezone=True), nullable=True)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="emotion_arts")
    emotion_analysis = relationship("EmotionAnalysis")
    voice_journal = relationship("VoiceJournal")
    customizations = relationship("ArtCustomization", back_populates="emotion_art", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmotionArt(id={self.id}, user_id={self.user_id}, emotion='{self.dominant_emotion}')>"


class ArtCustomization(Base):
    """User customizations applied to emotion art."""
    
    __tablename__ = "art_customizations"
    
    id = Column(Integer, primary_key=True, index=True)
    emotion_art_id = Column(Integer, ForeignKey("emotion_arts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Customization details
    customization_type = Column(String, nullable=False)  # "color", "shape", "style", "composition"
    original_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=False)
    
    # Customization metadata
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    emotion_art = relationship("EmotionArt", back_populates="customizations")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ArtCustomization(id={self.id}, art_id={self.emotion_art_id}, type='{self.customization_type}')>"


class ArtGallery(Base):
    """User's personal art gallery."""
    
    __tablename__ = "art_galleries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Gallery metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Gallery contents (JSON array of emotion_art IDs)
    art_pieces = Column(JSON, nullable=True)
    
    # Gallery statistics
    total_pieces = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<ArtGallery(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


class ArtShare(Base):
    """Shared emotion art with community."""
    
    __tablename__ = "art_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    emotion_art_id = Column(Integer, ForeignKey("emotion_arts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Share details
    share_message = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    
    # Community interaction
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Moderation
    is_approved = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    
    # Timestamps
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    emotion_art = relationship("EmotionArt")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ArtShare(id={self.id}, art_id={self.emotion_art_id}, user_id={self.user_id})>"
