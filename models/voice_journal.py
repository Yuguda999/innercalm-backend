"""
Voice journaling models for multimodal self-expression.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class VoiceJournalStatus(str, Enum):
    """Status of voice journal entry."""
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceJournal(Base):
    """Voice journal session model."""
    
    __tablename__ = "voice_journals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default=VoiceJournalStatus.RECORDING.value)
    
    # Audio file information
    audio_file_path = Column(String, nullable=True)
    audio_duration = Column(Float, nullable=True)  # Duration in seconds
    audio_format = Column(String, default="webm")
    
    # Transcription and analysis
    transcription = Column(Text, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    
    # Real-time sentiment analysis results
    sentiment_timeline = Column(JSON, nullable=True)  # Time-based sentiment data
    emotion_spikes = Column(JSON, nullable=True)  # Detected emotional peaks
    overall_sentiment = Column(JSON, nullable=True)  # Overall session sentiment
    
    # AI-generated insights and recommendations
    ai_insights = Column(JSON, nullable=True)
    recommended_exercises = Column(JSON, nullable=True)
    breathing_exercise_suggested = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="voice_journals")
    entries = relationship("VoiceJournalEntry", back_populates="journal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VoiceJournal(id={self.id}, user_id={self.user_id}, status='{self.status}')>"


class VoiceJournalEntry(Base):
    """Individual voice journal entry with real-time analysis."""
    
    __tablename__ = "voice_journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("voice_journals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Entry content
    audio_segment_path = Column(String, nullable=True)
    transcribed_text = Column(Text, nullable=True)
    segment_start_time = Column(Float, nullable=False)  # Start time in seconds
    segment_duration = Column(Float, nullable=False)  # Duration in seconds
    
    # Real-time emotion analysis
    emotions = Column(JSON, nullable=True)  # Emotion scores for this segment
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    emotional_intensity = Column(Float, nullable=True)
    
    # Detected themes and keywords for this segment
    themes = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    
    # Flags for significant moments
    is_emotional_spike = Column(Boolean, default=False)
    spike_type = Column(String, nullable=True)  # "positive", "negative", "mixed"
    
    # AI recommendations triggered by this segment
    triggered_recommendations = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    journal = relationship("VoiceJournal", back_populates="entries")
    user = relationship("User")
    
    def __repr__(self):
        return f"<VoiceJournalEntry(id={self.id}, journal_id={self.journal_id}, start_time={self.segment_start_time})>"


class BreathingExerciseSession(Base):
    """Breathing exercise session triggered by voice journal analysis."""
    
    __tablename__ = "breathing_exercise_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voice_journal_id = Column(Integer, ForeignKey("voice_journals.id"), nullable=True)
    
    # Exercise details
    exercise_type = Column(String, nullable=False)  # "4-7-8", "box_breathing", "calm_breathing"
    exercise_name = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Session data
    completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Effectiveness tracking
    pre_session_mood = Column(JSON, nullable=True)
    post_session_mood = Column(JSON, nullable=True)
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    voice_journal = relationship("VoiceJournal")
    
    def __repr__(self):
        return f"<BreathingExerciseSession(id={self.id}, user_id={self.user_id}, type='{self.exercise_type}')>"
