"""
Community router for peer circles and reflection chains.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.community import (
    SharedWoundGroup, PeerCircle, CircleMembership, CircleMessage,
    ReflectionChain, ReflectionEntry, UserClusterProfile
)
from schemas.community import (
    SharedWoundGroupCreate, SharedWoundGroupUpdate, SharedWoundGroupResponse,
    PeerCircleCreate, PeerCircleUpdate, PeerCircleResponse,
    CircleMembershipCreate, CircleMembershipUpdate, CircleMembershipResponse,
    CircleMessageCreate, CircleMessageUpdate, CircleMessageResponse,
    CircleMessageReplyCreate, MessageSupportCreate,
    ReflectionChainCreate, ReflectionChainUpdate, ReflectionChainResponse,
    ReflectionEntryCreate, ReflectionEntryUpdate, ReflectionEntryResponse,
    UserClusterProfileResponse, CommunityDashboardResponse, ClusteringRequest, ClusteringResponse
)
from services.community_service import CommunityService
from services.clustering_service import ClusteringService
from services.ai_group_manager import ai_group_manager
from services.scheduler import scheduler
from services.content_moderation import moderation_service
from services.notification_service import notification_service

router = APIRouter(prefix="/community", tags=["community"])
logger = logging.getLogger(__name__)

community_service = CommunityService()
clustering_service = ClusteringService()


@router.get("/dashboard", response_model=CommunityDashboardResponse)
async def get_community_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get community dashboard with available groups, user circles, and reflections."""
    try:
        # Get available groups
        available_groups = await community_service.get_available_groups_for_user(
            db, current_user.id
        )

        # Get user's circles
        user_circles = await community_service.get_user_circles(db, current_user.id)

        # Get recent reflections
        recent_reflections = await community_service.get_reflection_entries(
            db, chain_id=None, user_id=current_user.id, limit=5
        )

        # Get suggested chains
        suggested_chains = await community_service.get_reflection_chains_for_user(
            db, current_user.id
        )

        # Get user cluster profile
        user_cluster_profile = db.query(UserClusterProfile).filter(
            UserClusterProfile.user_id == current_user.id
        ).first()

        return CommunityDashboardResponse(
            available_groups=[SharedWoundGroupResponse.model_validate(g) for g in available_groups],
            user_circles=[PeerCircleResponse.model_validate(c) for c in user_circles],
            recent_reflections=[ReflectionEntryResponse.model_validate(r) for r in recent_reflections],
            suggested_chains=[ReflectionChainResponse.model_validate(c) for c in suggested_chains],
            user_cluster_profile=UserClusterProfileResponse.model_validate(user_cluster_profile) if user_cluster_profile else None
        )

    except Exception as e:
        logger.error(f"Error getting community dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load community dashboard"
        )


# Shared Wound Groups
@router.get("/groups", response_model=List[SharedWoundGroupResponse])
async def get_available_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get shared wound groups available to the current user."""
    try:
        groups = await community_service.get_available_groups_for_user(db, current_user.id)
        return [SharedWoundGroupResponse.model_validate(g) for g in groups]

    except Exception as e:
        logger.error(f"Error getting available groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load available groups"
        )


@router.post("/ai-management/run")
async def run_ai_group_management(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Run AI group management cycle (admin/system use)."""
    try:
        # In production, this should be restricted to admin users
        results = await scheduler.run_ai_management_now()
        return {
            "message": "AI group management completed successfully",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error running AI group management: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run AI group management"
        )


@router.get("/ai-management/status")
async def get_ai_management_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of AI-managed groups."""
    try:
        # Get AI-managed groups statistics
        total_groups = db.query(SharedWoundGroup).filter(
            SharedWoundGroup.ai_generated == True
        ).count()

        active_groups = db.query(SharedWoundGroup).filter(
            and_(
                SharedWoundGroup.ai_generated == True,
                SharedWoundGroup.is_active == True
            )
        ).count()

        # Get groups needing review
        review_cutoff = datetime.utcnow()
        groups_needing_review = db.query(SharedWoundGroup).filter(
            and_(
                SharedWoundGroup.ai_generated == True,
                SharedWoundGroup.is_active == True,
                or_(
                    SharedWoundGroup.next_ai_review <= review_cutoff,
                    SharedWoundGroup.next_ai_review.is_(None)
                )
            )
        ).count()

        # Get average metrics
        avg_metrics = db.query(
            func.avg(SharedWoundGroup.confidence_score),
            func.avg(SharedWoundGroup.activity_score),
            func.avg(SharedWoundGroup.cohesion_score),
            func.avg(SharedWoundGroup.member_count)
        ).filter(
            and_(
                SharedWoundGroup.ai_generated == True,
                SharedWoundGroup.is_active == True
            )
        ).first()

        # Get scheduler status
        scheduler_status = scheduler.get_status()

        return {
            "total_ai_groups": total_groups,
            "active_groups": active_groups,
            "groups_needing_review": groups_needing_review,
            "average_confidence": float(avg_metrics[0] or 0),
            "average_activity": float(avg_metrics[1] or 0),
            "average_cohesion": float(avg_metrics[2] or 0),
            "average_member_count": float(avg_metrics[3] or 0),
            "ai_management_enabled": True,
            "scheduler": scheduler_status
        }

    except Exception as e:
        logger.error(f"Error getting AI management status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI management status"
        )


# Peer Circles
@router.get("/circles", response_model=List[PeerCircleResponse])
async def get_user_circles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get peer circles the user is a member of."""
    try:
        circles = await community_service.get_user_circles(db, current_user.id)
        return [PeerCircleResponse.model_validate(c) for c in circles]

    except Exception as e:
        logger.error(f"Error getting user circles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load user circles"
        )


@router.post("/circles", response_model=PeerCircleResponse)
async def create_peer_circle(
    circle_data: PeerCircleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new peer circle."""
    try:
        circle = await community_service.create_peer_circle(
            db, circle_data.model_dump(), current_user.id
        )
        return PeerCircleResponse.model_validate(circle)

    except Exception as e:
        logger.error(f"Error creating peer circle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create peer circle"
        )


@router.get("/circles/{circle_id}", response_model=PeerCircleResponse)
async def get_peer_circle(
    circle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific peer circle."""
    try:
        circle = await community_service.get_peer_circle_details(
            db, current_user.id, circle_id
        )
        return PeerCircleResponse.model_validate(circle)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting peer circle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load peer circle"
        )


@router.get("/circles/{circle_id}/members", response_model=List[CircleMembershipResponse])
async def get_circle_members(
    circle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get members of a specific peer circle."""
    try:
        members = await community_service.get_circle_members(
            db, current_user.id, circle_id
        )
        return [CircleMembershipResponse.model_validate(m) for m in members]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting circle members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load circle members"
        )


@router.post("/circles/{circle_id}/join", response_model=CircleMembershipResponse)
async def join_peer_circle(
    circle_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Join a peer circle."""
    try:
        membership = await community_service.join_peer_circle(
            db, current_user.id, circle_id
        )
        return CircleMembershipResponse.model_validate(membership)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error joining peer circle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join peer circle"
        )


# Circle Messages
@router.get("/circles/{circle_id}/messages", response_model=List[CircleMessageResponse])
async def get_circle_messages(
    circle_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages from a peer circle."""
    try:
        messages = await community_service.get_circle_messages(
            db, current_user.id, circle_id, limit, offset
        )
        return [CircleMessageResponse.model_validate(m) for m in messages]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting circle messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load circle messages"
        )


@router.post("/circles/{circle_id}/messages", response_model=CircleMessageResponse)
async def send_circle_message(
    circle_id: int,
    message_data: CircleMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to a peer circle with content moderation."""
    try:
        # Moderate content before sending
        moderation_result = await moderation_service.moderate_content(
            message_data.content, current_user.id, "circle_message"
        )

        # Handle crisis detection
        if moderation_result["auto_action"] == "crisis_alert":
            crisis_resources = await moderation_service.handle_crisis_alert(
                message_data.content, current_user.id, db, "circle_message"
            )
            if crisis_resources:
                await notification_service.send_crisis_alert(
                    db, current_user.id, crisis_resources
                )

        # Block inappropriate content
        if not moderation_result["approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message blocked due to: {', '.join(moderation_result['flags'])}"
            )

        # Send message if approved
        message = await community_service.send_circle_message(
            db, current_user.id, circle_id, message_data.content, message_data.message_type
        )

        # Store moderation metadata
        if hasattr(message, 'moderation_flags'):
            message.moderation_flags = moderation_result["flags"]
            message.moderation_score = moderation_result["confidence_scores"]
            db.commit()

        return CircleMessageResponse.model_validate(message)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending circle message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.post("/messages/{message_id}/support")
async def support_message(
    message_id: int,
    support_data: MessageSupportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add support to a circle message."""
    try:
        support = await community_service.support_message(
            db, current_user.id, message_id, support_data.support_type
        )
        return {"message": "Support added successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error supporting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add support"
        )


# Reflection Chains
@router.get("/reflection-chains", response_model=List[ReflectionChainResponse])
async def get_reflection_chains(
    healing_module: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get reflection chains relevant to the user."""
    try:
        chains = await community_service.get_reflection_chains_for_user(
            db, current_user.id, healing_module
        )
        return [ReflectionChainResponse.model_validate(c) for c in chains]

    except Exception as e:
        logger.error(f"Error getting reflection chains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load reflection chains"
        )


@router.post("/reflection-chains", response_model=ReflectionChainResponse)
async def create_reflection_chain(
    chain_data: ReflectionChainCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new reflection chain."""
    try:
        chain = await community_service.create_reflection_chain(
            db, chain_data.model_dump()
        )
        return ReflectionChainResponse.model_validate(chain)

    except Exception as e:
        logger.error(f"Error creating reflection chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reflection chain"
        )


@router.get("/reflection-chains/{chain_id}/entries", response_model=List[ReflectionEntryResponse])
async def get_reflection_entries(
    chain_id: int,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get entries from a reflection chain."""
    try:
        entries = await community_service.get_reflection_entries(
            db, chain_id, current_user.id, limit
        )
        return [ReflectionEntryResponse.model_validate(e) for e in entries]

    except Exception as e:
        logger.error(f"Error getting reflection entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load reflection entries"
        )


@router.post("/reflection-entries", response_model=ReflectionEntryResponse)
async def add_reflection_entry(
    entry_data: ReflectionEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add an entry to a reflection chain."""
    try:
        entry = await community_service.add_reflection_entry(
            db, current_user.id, entry_data.model_dump()
        )
        return ReflectionEntryResponse.model_validate(entry)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding reflection entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add reflection entry"
        )


# Clustering
@router.post("/clustering/update", response_model=ClusteringResponse)
async def update_user_clustering(
    request: ClusteringRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user clustering profile and get group suggestions."""
    try:
        user_id = request.user_id or current_user.id

        # Update cluster profile
        profile = await clustering_service.update_user_cluster_profile(
            db, user_id, request.force_recluster
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for clustering"
            )

        # Get suggested groups
        matches = await clustering_service.find_matching_groups(db, user_id)
        suggested_groups = [group for group, similarity in matches]

        return ClusteringResponse(
            user_id=user_id,
            suggested_groups=[SharedWoundGroupResponse.model_validate(g) for g in suggested_groups],
            cluster_confidence=profile.cluster_confidence or 0.0,
            cluster_profile=UserClusterProfileResponse.model_validate(profile)
        )

    except Exception as e:
        logger.error(f"Error updating user clustering: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update clustering"
        )


@router.get("/groups/{group_id}/circles", response_model=List[PeerCircleResponse])
async def get_group_circles(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get peer circles in a shared wound group."""
    try:
        circles = await clustering_service.suggest_peer_circles(
            db, current_user.id, group_id
        )
        return [PeerCircleResponse.model_validate(c) for c in circles]

    except Exception as e:
        logger.error(f"Error getting group circles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load group circles"
        )
