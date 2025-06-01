"""
Professional Bridge router for therapist matching, scheduling, and practice plans.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.professional_bridge import (
    TherapistProfile, TherapistMatch, Appointment, PracticePlan,
    AppointmentStatus, PracticePlanStatus
)
from schemas.professional_bridge import (
    TherapistProfileResponse, TherapistMatchRequest, TherapistMatchResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    PracticePlanCreate, PracticePlanUpdate, PracticePlanResponse,
    TherapistSearchFilters, MatchingInsights, PracticePlanProgress
)
from services.therapist_matching import TherapistMatchingService
from services.practice_plan import PracticePlanService

router = APIRouter(prefix="/professional-bridge", tags=["professional-bridge"])
logger = logging.getLogger(__name__)


# Therapist Matching Endpoints
@router.post("/find-matches", response_model=List[TherapistMatchResponse])
async def find_therapist_matches(
    request: TherapistMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Find therapist matches based on user's trauma map and preferences."""
    try:
        matching_service = TherapistMatchingService()
        matches = await matching_service.find_matches(db, current_user, request)
        return matches
    except Exception as e:
        logger.error(f"Error finding therapist matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find therapist matches"
        )


@router.get("/matches", response_model=List[TherapistMatchResponse])
async def get_user_matches(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's existing therapist matches."""
    matches = db.query(TherapistMatch).filter(
        TherapistMatch.user_id == current_user.id
    ).order_by(TherapistMatch.compatibility_score.desc()).all()
    
    return matches


@router.patch("/matches/{match_id}/view")
async def mark_match_viewed(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a therapist match as viewed."""
    match = db.query(TherapistMatch).filter(
        TherapistMatch.id == match_id,
        TherapistMatch.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.is_viewed = True
    match.viewed_at = datetime.now()
    db.commit()
    
    return {"message": "Match marked as viewed"}


@router.patch("/matches/{match_id}/contact")
async def mark_match_contacted(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a therapist match as contacted."""
    match = db.query(TherapistMatch).filter(
        TherapistMatch.id == match_id,
        TherapistMatch.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.is_contacted = True
    match.contacted_at = datetime.now()
    db.commit()
    
    return {"message": "Match marked as contacted"}


# Therapist Search Endpoints
@router.get("/therapists", response_model=List[TherapistProfileResponse])
async def search_therapists(
    specialties: Optional[List[str]] = Query(None),
    max_hourly_rate: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    accepts_insurance: Optional[bool] = Query(None),
    years_experience_min: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for therapists with filters."""
    query = db.query(TherapistProfile).filter(
        TherapistProfile.is_active == True,
        TherapistProfile.is_verified == True,
        TherapistProfile.is_accepting_new_clients == True
    )
    
    if specialties:
        # Filter by specialties (JSON array contains any of the specified specialties)
        for specialty in specialties:
            query = query.filter(TherapistProfile.specialties.contains([specialty]))
    
    if max_hourly_rate:
        query = query.filter(TherapistProfile.hourly_rate <= max_hourly_rate)
    
    if min_rating:
        query = query.filter(TherapistProfile.average_rating >= min_rating)
    
    if accepts_insurance is not None:
        query = query.filter(TherapistProfile.accepts_insurance == accepts_insurance)
    
    if years_experience_min:
        query = query.filter(TherapistProfile.years_experience >= years_experience_min)
    
    therapists = query.order_by(TherapistProfile.average_rating.desc()).limit(20).all()
    return therapists


@router.get("/therapists/{therapist_id}", response_model=TherapistProfileResponse)
async def get_therapist_profile(
    therapist_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed therapist profile."""
    therapist = db.query(TherapistProfile).filter(
        TherapistProfile.id == therapist_id,
        TherapistProfile.is_active == True
    ).first()
    
    if not therapist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Therapist not found"
        )
    
    return therapist


# Appointment Management Endpoints
@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new appointment with a therapist."""
    # Verify therapist exists and is available
    therapist = db.query(TherapistProfile).filter(
        TherapistProfile.id == appointment_data.therapist_id,
        TherapistProfile.is_active == True,
        TherapistProfile.is_accepting_new_clients == True
    ).first()
    
    if not therapist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Therapist not found or not accepting new clients"
        )
    
    # Create appointment
    appointment = Appointment(
        user_id=current_user.id,
        therapist_id=appointment_data.therapist_id,
        match_id=appointment_data.match_id,
        scheduled_datetime=appointment_data.scheduled_datetime,
        duration_minutes=appointment_data.duration_minutes,
        session_type=appointment_data.session_type,
        recording_consent=appointment_data.recording_consent,
        cost=therapist.hourly_rate * (appointment_data.duration_minutes / 60),
        status=AppointmentStatus.SCHEDULED
    )
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    logger.info(f"Created appointment {appointment.id} for user {current_user.id}")
    return appointment


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_user_appointments(
    status: Optional[AppointmentStatus] = Query(None),
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's appointments."""
    query = db.query(Appointment).filter(
        Appointment.user_id == current_user.id
    )
    
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(
        Appointment.scheduled_datetime.desc()
    ).limit(limit).all()
    
    return appointments


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific appointment details."""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return appointment


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update appointment details."""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(appointment, field, value)
    
    appointment.updated_at = datetime.now()
    db.commit()
    db.refresh(appointment)
    
    return appointment


# Practice Plan Endpoints
@router.post("/practice-plans", response_model=PracticePlanResponse)
async def create_practice_plan(
    plan_data: PracticePlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a practice plan (typically after a therapy session)."""
    # Verify appointment exists and belongs to user
    appointment = db.query(Appointment).filter(
        Appointment.id == plan_data.appointment_id,
        Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Create practice plan
    practice_plan = PracticePlan(
        user_id=current_user.id,
        appointment_id=plan_data.appointment_id,
        title=plan_data.title,
        description=plan_data.description,
        goals=plan_data.goals,
        daily_tasks=plan_data.daily_tasks,
        weekly_goals=plan_data.weekly_goals,
        exercises=plan_data.exercises,
        start_date=plan_data.start_date,
        end_date=plan_data.end_date,
        reminder_frequency=plan_data.reminder_frequency,
        status=PracticePlanStatus.ACTIVE
    )
    
    db.add(practice_plan)
    db.commit()
    db.refresh(practice_plan)
    
    logger.info(f"Created practice plan {practice_plan.id} for user {current_user.id}")
    return practice_plan


@router.post("/appointments/{appointment_id}/generate-practice-plan", response_model=PracticePlanResponse)
async def generate_practice_plan(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Auto-generate a practice plan based on the therapy session."""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == current_user.id,
        Appointment.status == AppointmentStatus.COMPLETED
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Completed appointment not found"
        )
    
    # Check if practice plan already exists
    existing_plan = db.query(PracticePlan).filter(
        PracticePlan.appointment_id == appointment_id
    ).first()
    
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Practice plan already exists for this appointment"
        )
    
    try:
        practice_plan_service = PracticePlanService()
        practice_plan = await practice_plan_service.generate_practice_plan(
            db, appointment, appointment.session_notes
        )
        return practice_plan
    except Exception as e:
        logger.error(f"Error generating practice plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate practice plan"
        )


@router.get("/practice-plans", response_model=List[PracticePlanResponse])
async def get_practice_plans(
    status: Optional[PracticePlanStatus] = Query(None),
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's practice plans."""
    query = db.query(PracticePlan).filter(
        PracticePlan.user_id == current_user.id
    )
    
    if status:
        query = query.filter(PracticePlan.status == status)
    
    plans = query.order_by(PracticePlan.created_at.desc()).limit(limit).all()
    return plans


@router.get("/practice-plans/{plan_id}", response_model=PracticePlanResponse)
async def get_practice_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific practice plan details."""
    plan = db.query(PracticePlan).filter(
        PracticePlan.id == plan_id,
        PracticePlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice plan not found"
        )
    
    return plan


@router.patch("/practice-plans/{plan_id}", response_model=PracticePlanResponse)
async def update_practice_plan(
    plan_id: int,
    update_data: PracticePlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update practice plan progress and details."""
    plan = db.query(PracticePlan).filter(
        PracticePlan.id == plan_id,
        PracticePlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice plan not found"
        )
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    
    plan.updated_at = datetime.now()
    
    # Auto-complete if completion percentage reaches 100%
    if plan.completion_percentage >= 100.0 and plan.status == PracticePlanStatus.ACTIVE:
        plan.status = PracticePlanStatus.COMPLETED
        plan.completed_at = datetime.now()
    
    db.commit()
    db.refresh(plan)
    
    return plan
