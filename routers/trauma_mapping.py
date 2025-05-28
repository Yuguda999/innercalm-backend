"""
Trauma mapping router for life events, trauma analysis, and reframing sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.trauma_mapping import LifeEvent, TraumaMapping, ReframeSession, ReframeSessionStatus
from schemas.trauma_mapping import (
    LifeEventCreate, LifeEventUpdate, LifeEventResponse,
    TraumaMappingCreate, TraumaMappingResponse,
    ReframeSessionCreate, ReframeSessionUpdate, ReframeSessionResponse,
    TimelineAnalysisResponse
)
from services.trauma_mapping_service import TraumaMappingService
from services.reframe_session_service import ReframeSessionService

router = APIRouter(prefix="/trauma-mapping", tags=["trauma-mapping"])

# Initialize services
trauma_mapping_service = TraumaMappingService()
reframe_session_service = ReframeSessionService()


# Life Events Endpoints
@router.post("/life-events", response_model=LifeEventResponse)
async def create_life_event(
    event_data: LifeEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new life event."""
    try:
        life_event = LifeEvent(
            user_id=current_user.id,
            **event_data.model_dump()
        )

        db.add(life_event)
        db.commit()
        db.refresh(life_event)

        return LifeEventResponse.model_validate(life_event)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create life event: {str(e)}"
        )


@router.get("/life-events", response_model=List[LifeEventResponse])
async def get_life_events(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),  # Reduced default limit for faster loading
    offset: int = Query(0, ge=0)
):
    """Get user's life events with pagination for better performance."""
    try:
        # Use index-optimized query
        events = db.query(LifeEvent).filter(
            LifeEvent.user_id == current_user.id
        ).order_by(LifeEvent.event_date.desc()).offset(offset).limit(limit).all()

        return [LifeEventResponse.model_validate(event) for event in events]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get life events: {str(e)}"
        )


@router.get("/life-events/{event_id}", response_model=LifeEventResponse)
async def get_life_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific life event."""
    try:
        event = db.query(LifeEvent).filter(
            LifeEvent.id == event_id,
            LifeEvent.user_id == current_user.id
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Life event not found"
            )

        return LifeEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get life event: {str(e)}"
        )


@router.put("/life-events/{event_id}", response_model=LifeEventResponse)
async def update_life_event(
    event_id: int,
    event_data: LifeEventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a life event."""
    try:
        event = db.query(LifeEvent).filter(
            LifeEvent.id == event_id,
            LifeEvent.user_id == current_user.id
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Life event not found"
            )

        # Update fields
        update_data = event_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        db.commit()
        db.refresh(event)

        return LifeEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update life event: {str(e)}"
        )


@router.delete("/life-events/{event_id}")
async def delete_life_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a life event."""
    try:
        event = db.query(LifeEvent).filter(
            LifeEvent.id == event_id,
            LifeEvent.user_id == current_user.id
        ).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Life event not found"
            )

        db.delete(event)
        db.commit()

        return {"message": "Life event deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete life event: {str(e)}"
        )


# Timeline Analysis Endpoints
@router.get("/timeline-analysis", response_model=TimelineAnalysisResponse)
async def get_timeline_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive timeline analysis."""
    try:
        analysis = await trauma_mapping_service.analyze_timeline_patterns(db, current_user.id)
        return TimelineAnalysisResponse(**analysis)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze timeline: {str(e)}"
        )


# Trauma Mapping Endpoints
@router.post("/trauma-mappings", response_model=TraumaMappingResponse)
async def create_trauma_mapping(
    mapping_data: TraumaMappingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a trauma mapping analysis."""
    try:
        # Verify the life event belongs to the user
        life_event = db.query(LifeEvent).filter(
            LifeEvent.id == mapping_data.life_event_id,
            LifeEvent.user_id == current_user.id
        ).first()

        if not life_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Life event not found"
            )

        trauma_mapping = TraumaMapping(
            user_id=current_user.id,
            **mapping_data.model_dump()
        )

        db.add(trauma_mapping)
        db.commit()
        db.refresh(trauma_mapping)

        return TraumaMappingResponse.model_validate(trauma_mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trauma mapping: {str(e)}"
        )


@router.get("/trauma-mappings", response_model=List[TraumaMappingResponse])
async def get_trauma_mappings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    life_event_id: Optional[int] = Query(None)
):
    """Get user's trauma mappings."""
    try:
        query = db.query(TraumaMapping).filter(
            TraumaMapping.user_id == current_user.id
        )

        if life_event_id:
            query = query.filter(TraumaMapping.life_event_id == life_event_id)

        mappings = query.order_by(TraumaMapping.analyzed_at.desc()).all()

        return [TraumaMappingResponse.model_validate(mapping) for mapping in mappings]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trauma mappings: {str(e)}"
        )


# Reframe Session Endpoints
@router.post("/reframe-sessions", response_model=ReframeSessionResponse)
async def create_reframe_session(
    session_data: ReframeSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new reframe session."""
    try:
        # Verify the life event belongs to the user
        life_event = db.query(LifeEvent).filter(
            LifeEvent.id == session_data.life_event_id,
            LifeEvent.user_id == current_user.id
        ).first()

        if not life_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Life event not found"
            )

        # Create the session
        reframe_session = ReframeSession(
            user_id=current_user.id,
            **session_data.model_dump()
        )

        db.add(reframe_session)
        db.commit()
        db.refresh(reframe_session)

        return ReframeSessionResponse.model_validate(reframe_session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reframe session: {str(e)}"
        )


@router.get("/reframe-sessions", response_model=List[ReframeSessionResponse])
async def get_reframe_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    status_filter: Optional[ReframeSessionStatus] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    """Get user's reframe sessions."""
    try:
        query = db.query(ReframeSession).filter(
            ReframeSession.user_id == current_user.id
        )

        if status_filter:
            query = query.filter(ReframeSession.status == status_filter)

        sessions = query.order_by(ReframeSession.created_at.desc()).limit(limit).all()

        return [ReframeSessionResponse.model_validate(session) for session in sessions]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reframe sessions: {str(e)}"
        )


@router.get("/reframe-sessions/{session_id}", response_model=ReframeSessionResponse)
async def get_reframe_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific reframe session."""
    try:
        session = db.query(ReframeSession).filter(
            ReframeSession.id == session_id,
            ReframeSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reframe session not found"
            )

        return ReframeSessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reframe session: {str(e)}"
        )


@router.put("/reframe-sessions/{session_id}", response_model=ReframeSessionResponse)
async def update_reframe_session(
    session_id: int,
    session_data: ReframeSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a reframe session."""
    try:
        session = db.query(ReframeSession).filter(
            ReframeSession.id == session_id,
            ReframeSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reframe session not found"
            )

        # Update fields
        update_data = session_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)

        # Update timestamps based on status changes
        if session_data.status == ReframeSessionStatus.IN_PROGRESS and not session.started_at:
            session.started_at = datetime.utcnow()
        elif session_data.status == ReframeSessionStatus.COMPLETED and not session.completed_at:
            session.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(session)

        return ReframeSessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update reframe session: {str(e)}"
        )


@router.post("/reframe-sessions/{session_id}/guided-session")
async def start_guided_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start an AI-guided reframing session."""
    try:
        session = db.query(ReframeSession).filter(
            ReframeSession.id == session_id,
            ReframeSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reframe session not found"
            )

        # Get the associated life event
        life_event = db.query(LifeEvent).filter(
            LifeEvent.id == session.life_event_id
        ).first()

        if not life_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated life event not found"
            )

        # Get trauma mapping if available
        trauma_mapping = None
        if session.trauma_mapping_id:
            trauma_mapping = db.query(TraumaMapping).filter(
                TraumaMapping.id == session.trauma_mapping_id
            ).first()

        # Create guided session plan
        session_plan = await reframe_session_service.create_guided_session(
            db, current_user.id, life_event, trauma_mapping
        )

        # Update session status
        session.status = ReframeSessionStatus.IN_PROGRESS
        session.started_at = datetime.utcnow()
        session.ai_prompts = session_plan.get("ai_prompts", [])

        db.commit()

        return {
            "session_plan": session_plan,
            "session_id": session_id,
            "status": "started"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start guided session: {str(e)}"
        )


@router.post("/reframe-sessions/{session_id}/process-response")
async def process_session_response(
    session_id: int,
    response_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process user response during reframing session."""
    try:
        session = db.query(ReframeSession).filter(
            ReframeSession.id == session_id,
            ReframeSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reframe session not found"
            )

        user_response = response_data.get("response", "")
        current_phase = response_data.get("phase", "exploration")

        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response content is required"
            )

        # Process the response
        result = await reframe_session_service.process_session_response(
            db, session, user_response, current_phase
        )

        # Update session with new insights and progress
        if result.get("insights"):
            current_insights = session.insights_gained or []
            session.insights_gained = current_insights + result["insights"]

        if result.get("progress_update"):
            session.progress_percentage = result["progress_update"]["new_progress"]

        if result.get("emotional_shift"):
            session.emotional_shift = result["emotional_shift"]

        db.commit()

        return {
            "guidance": result.get("guidance", {}),
            "analysis": result.get("analysis", {}),
            "progress": result.get("progress_update", {}),
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process session response: {str(e)}"
        )


@router.post("/reframe-sessions/{session_id}/complete")
async def complete_reframe_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete a reframing session."""
    try:
        session = db.query(ReframeSession).filter(
            ReframeSession.id == session_id,
            ReframeSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reframe session not found"
            )

        # Complete the session
        outcomes = await reframe_session_service.complete_session(db, session)

        return {
            "outcomes": outcomes,
            "session_id": session_id,
            "status": "completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete reframe session: {str(e)}"
        )
