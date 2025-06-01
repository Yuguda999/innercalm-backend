"""
Voice journaling router for multimodal self-expression.
"""
import os
import tempfile
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.voice_journal import VoiceJournal, VoiceJournalEntry, BreathingExerciseSession, VoiceJournalStatus
from schemas.voice_journal import (
    VoiceJournalCreate, VoiceJournalUpdate, VoiceJournalResponse,
    VoiceJournalEntryResponse, BreathingExerciseSessionCreate,
    BreathingExerciseSessionUpdate, BreathingExerciseSessionResponse,
    RealTimeSentimentUpdate, VoiceJournalAnalytics
)
from services.voice_processing_service import VoiceProcessingService
from services.emotion_analyzer import EmotionAnalyzer

router = APIRouter(prefix="/voice-journal", tags=["voice-journal"])


@router.post("/sessions", response_model=VoiceJournalResponse)
async def create_voice_journal_session(
    journal_data: VoiceJournalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new voice journal session."""
    try:
        journal = VoiceJournal(
            user_id=current_user.id,
            title=journal_data.title,
            description=journal_data.description,
            status=VoiceJournalStatus.RECORDING.value
        )

        db.add(journal)
        db.commit()
        db.refresh(journal)

        return journal

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating voice journal session: {str(e)}"
        )


@router.get("/sessions", response_model=List[VoiceJournalResponse])
async def get_voice_journal_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    status_filter: Optional[VoiceJournalStatus] = None
):
    """Get user's voice journal sessions."""
    try:
        query = db.query(VoiceJournal).filter(
            VoiceJournal.user_id == current_user.id
        )

        if status_filter:
            query = query.filter(VoiceJournal.status == status_filter.value)

        sessions = query.order_by(
            VoiceJournal.created_at.desc()
        ).offset(offset).limit(limit).all()

        return sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving voice journal sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=VoiceJournalResponse)
async def get_voice_journal_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific voice journal session."""
    try:
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving voice journal session: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=VoiceJournalResponse)
async def update_voice_journal_session(
    session_id: int,
    update_data: VoiceJournalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a voice journal session."""
    try:
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(session, field, value)

        db.commit()
        db.refresh(session)

        return session

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating voice journal session: {str(e)}"
        )


@router.post("/sessions/{session_id}/upload-audio")
async def upload_audio_file(
    session_id: int,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process audio file for voice journal session."""
    try:
        # Verify session exists and belongs to user
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Update session status
        session.status = VoiceJournalStatus.PROCESSING.value
        session.audio_file_path = temp_file_path
        session.audio_format = audio_file.content_type.split('/')[-1]
        db.commit()

        # Process audio in background
        voice_service = VoiceProcessingService()
        background_tasks.add_task(
            voice_service.process_audio_file,
            temp_file_path,
            session_id,
            current_user.id,
            db
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Audio file uploaded successfully. Processing started.",
                "session_id": session_id,
                "status": "processing"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up temp file on error
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading audio file: {str(e)}"
        )


@router.get("/sessions/{session_id}/entries", response_model=List[VoiceJournalEntryResponse])
async def get_session_entries(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get entries for a voice journal session."""
    try:
        # Verify session exists and belongs to user
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        entries = db.query(VoiceJournalEntry).filter(
            VoiceJournalEntry.journal_id == session_id
        ).order_by(VoiceJournalEntry.segment_start_time).all()

        return entries

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session entries: {str(e)}"
        )


@router.post("/sessions/{session_id}/real-time-sentiment")
async def update_real_time_sentiment(
    session_id: int,
    sentiment_data: RealTimeSentimentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update real-time sentiment analysis during recording."""
    try:
        # Verify session exists and belongs to user
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        # Update sentiment timeline
        if not session.sentiment_timeline:
            session.sentiment_timeline = []

        session.sentiment_timeline.append({
            "timestamp": sentiment_data.timestamp,
            "emotions": sentiment_data.emotions,
            "sentiment_score": sentiment_data.sentiment_score,
            "emotional_intensity": sentiment_data.emotional_intensity
        })

        # Update emotion spikes if detected
        if sentiment_data.is_spike:
            if not session.emotion_spikes:
                session.emotion_spikes = []

            session.emotion_spikes.append({
                "timestamp": sentiment_data.timestamp,
                "spike_type": sentiment_data.spike_type,
                "intensity": sentiment_data.emotional_intensity,
                "dominant_emotion": max(sentiment_data.emotions, key=sentiment_data.emotions.get)
            })

        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Real-time sentiment updated successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating real-time sentiment: {str(e)}"
        )


@router.post("/breathing-exercises", response_model=BreathingExerciseSessionResponse)
async def create_breathing_exercise_session(
    exercise_data: BreathingExerciseSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new breathing exercise session."""
    try:
        session = BreathingExerciseSession(
            user_id=current_user.id,
            voice_journal_id=exercise_data.voice_journal_id,
            exercise_type=exercise_data.exercise_type,
            exercise_name=exercise_data.exercise_name,
            duration_minutes=exercise_data.duration_minutes,
            pre_session_mood=exercise_data.pre_session_mood
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating breathing exercise session: {str(e)}"
        )


@router.get("/breathing-exercises", response_model=List[BreathingExerciseSessionResponse])
async def get_breathing_exercise_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get user's breathing exercise sessions."""
    try:
        sessions = db.query(BreathingExerciseSession).filter(
            BreathingExerciseSession.user_id == current_user.id
        ).order_by(
            BreathingExerciseSession.started_at.desc()
        ).offset(offset).limit(limit).all()

        return sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving breathing exercise sessions: {str(e)}"
        )


@router.put("/breathing-exercises/{session_id}", response_model=BreathingExerciseSessionResponse)
async def update_breathing_exercise_session(
    session_id: int,
    update_data: BreathingExerciseSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a breathing exercise session."""
    try:
        session = db.query(BreathingExerciseSession).filter(
            BreathingExerciseSession.id == session_id,
            BreathingExerciseSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Breathing exercise session not found"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(session, field, value)

        # Set completion timestamp if marked as completed
        if update_data.completed and not session.completed_at:
            from datetime import datetime
            session.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(session)

        return session

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating breathing exercise session: {str(e)}"
        )


@router.get("/analytics", response_model=VoiceJournalAnalytics)
async def get_voice_journal_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get voice journal analytics for the user."""
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get sessions in date range
        sessions = db.query(VoiceJournal).filter(
            VoiceJournal.user_id == current_user.id,
            VoiceJournal.created_at >= cutoff_date,
            VoiceJournal.status == VoiceJournalStatus.COMPLETED.value
        ).all()

        # Calculate analytics
        total_sessions = len(sessions)
        total_duration = sum(s.audio_duration or 0 for s in sessions)
        average_duration = total_duration / total_sessions if total_sessions > 0 else 0

        # Emotion analysis
        emotion_counts = {}
        emotion_trends = {}
        spike_counts = {"positive": 0, "negative": 0, "mixed": 0}

        for session in sessions:
            if session.overall_sentiment:
                dominant = session.overall_sentiment.get("dominant_emotion", "neutral")
                emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1

            if session.emotion_spikes:
                for spike in session.emotion_spikes:
                    spike_type = spike.get("spike_type", "mixed")
                    spike_counts[spike_type] = spike_counts.get(spike_type, 0) + 1

        # Most common emotions
        most_common_emotions = [
            {"emotion": emotion, "count": count}
            for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Recommended exercises used
        exercise_usage = {}
        for session in sessions:
            if session.recommended_exercises:
                for exercise in session.recommended_exercises:
                    ex_type = exercise.get("type", "unknown")
                    exercise_usage[ex_type] = exercise_usage.get(ex_type, 0) + 1

        recommended_exercises_used = [
            {"exercise_type": ex_type, "usage_count": count}
            for ex_type, count in exercise_usage.items()
        ]

        # Improvement metrics (simplified)
        improvement_metrics = {
            "session_frequency": total_sessions / days if days > 0 else 0,
            "average_emotional_intensity": 0.5,  # Would calculate from actual data
            "completion_rate": 1.0 if total_sessions > 0 else 0.0
        }

        return VoiceJournalAnalytics(
            total_sessions=total_sessions,
            total_duration_minutes=total_duration / 60 if total_duration else 0,
            average_session_duration=average_duration / 60 if average_duration else 0,
            most_common_emotions=most_common_emotions,
            emotion_trends=emotion_trends,
            spike_frequency=spike_counts,
            recommended_exercises_used=recommended_exercises_used,
            improvement_metrics=improvement_metrics
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving voice journal analytics: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_voice_journal_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a voice journal session."""
    try:
        session = db.query(VoiceJournal).filter(
            VoiceJournal.id == session_id,
            VoiceJournal.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice journal session not found"
            )

        # Clean up audio file if it exists
        if session.audio_file_path and os.path.exists(session.audio_file_path):
            try:
                os.unlink(session.audio_file_path)
            except Exception as e:
                # Log but don't fail the deletion
                print(f"Warning: Could not delete audio file {session.audio_file_path}: {e}")

        db.delete(session)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Voice journal session deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting voice journal session: {str(e)}"
        )
