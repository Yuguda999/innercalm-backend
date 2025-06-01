"""
Therapist management router for therapist dashboard and profile management.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from database import get_db
from routers.auth import get_current_active_user
from models.user import User, UserType
from models.professional_bridge import (
    TherapistProfile, Appointment, PracticePlan,
    AppointmentStatus, PracticePlanStatus
)
from schemas.professional_bridge import (
    TherapistProfileUpdate, TherapistProfileResponse,
    AppointmentResponse, PracticePlanCreate, PracticePlanResponse
)

router = APIRouter(prefix="/therapist", tags=["therapist"])
logger = logging.getLogger(__name__)


def get_current_therapist(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user and verify they are a therapist."""
    if current_user.user_type != UserType.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Therapist account required."
        )
    return current_user


@router.get("/profile", response_model=TherapistProfileResponse)
async def get_therapist_profile(
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db)
):
    """Get therapist's profile information."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        return TherapistProfileResponse.model_validate(profile)
    except Exception as e:
        logger.error(f"Error fetching therapist profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


@router.put("/profile", response_model=TherapistProfileResponse)
async def update_therapist_profile(
    profile_update: TherapistProfileUpdate,
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db)
):
    """Update therapist's profile information."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        # Update profile fields
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        db.commit()
        db.refresh(profile)
        
        return TherapistProfileResponse.model_validate(profile)
    except Exception as e:
        logger.error(f"Error updating therapist profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/dashboard")
async def get_therapist_dashboard(
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db)
):
    """Get therapist dashboard data."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        # Get upcoming appointments
        upcoming_appointments = db.query(Appointment).filter(
            and_(
                Appointment.therapist_id == profile.id,
                Appointment.scheduled_datetime >= datetime.utcnow(),
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        ).order_by(Appointment.scheduled_datetime).limit(5).all()
        
        # Get recent appointments
        recent_appointments = db.query(Appointment).filter(
            and_(
                Appointment.therapist_id == profile.id,
                Appointment.status == AppointmentStatus.COMPLETED
            )
        ).order_by(desc(Appointment.scheduled_datetime)).limit(5).all()
        
        # Get active practice plans
        active_plans = db.query(PracticePlan).join(Appointment).filter(
            and_(
                Appointment.therapist_id == profile.id,
                PracticePlan.status == PracticePlanStatus.ACTIVE
            )
        ).count()
        
        # Calculate statistics
        total_appointments = db.query(Appointment).filter(
            Appointment.therapist_id == profile.id
        ).count()
        
        completed_appointments = db.query(Appointment).filter(
            and_(
                Appointment.therapist_id == profile.id,
                Appointment.status == AppointmentStatus.COMPLETED
            )
        ).count()
        
        # Get average rating
        avg_rating = db.query(func.avg(Appointment.session_rating)).filter(
            and_(
                Appointment.therapist_id == profile.id,
                Appointment.session_rating.isnot(None)
            )
        ).scalar() or 0.0
        
        return {
            "profile": TherapistProfileResponse.model_validate(profile),
            "upcoming_appointments": [
                AppointmentResponse.model_validate(apt) for apt in upcoming_appointments
            ],
            "recent_appointments": [
                AppointmentResponse.model_validate(apt) for apt in recent_appointments
            ],
            "statistics": {
                "total_appointments": total_appointments,
                "completed_appointments": completed_appointments,
                "active_practice_plans": active_plans,
                "average_rating": round(avg_rating, 2),
                "completion_rate": round(
                    (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0, 1
                )
            }
        }
    except Exception as e:
        logger.error(f"Error fetching therapist dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_therapist_appointments(
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by appointment status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get therapist's appointments."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        query = db.query(Appointment).filter(Appointment.therapist_id == profile.id)
        
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        
        appointments = query.order_by(desc(Appointment.scheduled_datetime)).offset(offset).limit(limit).all()
        
        return [AppointmentResponse.model_validate(apt) for apt in appointments]
    except Exception as e:
        logger.error(f"Error fetching therapist appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch appointments"
        )


@router.post("/practice-plans", response_model=PracticePlanResponse)
async def create_practice_plan(
    plan_data: PracticePlanCreate,
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db)
):
    """Create a new practice plan for a client."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        # Verify the appointment belongs to this therapist
        appointment = db.query(Appointment).filter(
            and_(
                Appointment.id == plan_data.appointment_id,
                Appointment.therapist_id == profile.id,
                Appointment.status == AppointmentStatus.COMPLETED
            )
        ).first()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or not completed"
            )
        
        # Create practice plan
        practice_plan = PracticePlan(
            user_id=plan_data.user_id,
            appointment_id=plan_data.appointment_id,
            title=plan_data.title,
            description=plan_data.description,
            goals=plan_data.goals,
            daily_tasks=plan_data.daily_tasks,
            weekly_goals=plan_data.weekly_goals,
            exercises=plan_data.exercises,
            start_date=plan_data.start_date,
            end_date=plan_data.end_date,
            reminder_frequency=plan_data.reminder_frequency
        )
        
        db.add(practice_plan)
        db.commit()
        db.refresh(practice_plan)
        
        return PracticePlanResponse.model_validate(practice_plan)
    except Exception as e:
        logger.error(f"Error creating practice plan: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create practice plan"
        )


@router.get("/practice-plans", response_model=List[PracticePlanResponse])
async def get_therapist_practice_plans(
    current_user: User = Depends(get_current_therapist),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by plan status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get practice plans created by this therapist."""
    try:
        profile = db.query(TherapistProfile).filter(
            TherapistProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapist profile not found"
            )
        
        query = db.query(PracticePlan).join(Appointment).filter(
            Appointment.therapist_id == profile.id
        )
        
        if status_filter:
            query = query.filter(PracticePlan.status == status_filter)
        
        plans = query.order_by(desc(PracticePlan.created_at)).offset(offset).limit(limit).all()
        
        return [PracticePlanResponse.model_validate(plan) for plan in plans]
    except Exception as e:
        logger.error(f"Error fetching practice plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch practice plans"
        )
