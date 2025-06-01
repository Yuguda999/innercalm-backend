"""
Community service for managing peer circles and reflection chains.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

from models.user import User
from models.community import (
    SharedWoundGroup, PeerCircle, CircleMembership, CircleMessage,
    CircleMessageReply, MessageSupport, ReflectionChain, ReflectionEntry,
    UserClusterProfile, CircleStatus, MembershipStatus, MessageStatus, ReflectionStatus
)
from services.clustering_service import ClusteringService

logger = logging.getLogger(__name__)


class CommunityService:
    """Service for managing community features."""

    def __init__(self):
        self.clustering_service = ClusteringService()
        self.max_circles_per_user = 3  # Limit to prevent overwhelming users
        self.message_cooldown_minutes = 1  # Prevent spam

    # Shared Wound Groups
    async def create_shared_wound_group(
        self,
        db: Session,
        group_data: Dict[str, Any]
    ) -> SharedWoundGroup:
        """Create a new shared wound group."""
        try:
            group = SharedWoundGroup(**group_data)
            db.add(group)
            db.commit()
            db.refresh(group)

            logger.info(f"Created shared wound group: {group.name}")
            return group

        except Exception as e:
            logger.error(f"Error creating shared wound group: {e}")
            db.rollback()
            raise

    async def get_available_groups_for_user(
        self,
        db: Session,
        user_id: int
    ) -> List[SharedWoundGroup]:
        """Get shared wound groups available to a user."""
        try:
            # Get user's matching groups
            matches = await self.clustering_service.find_matching_groups(
                db, user_id, limit=10
            )

            available_groups = []
            for group, similarity in matches:
                # Check if user is already in a circle in this group
                existing_membership = db.query(CircleMembership).join(PeerCircle).filter(
                    and_(
                        PeerCircle.shared_wound_group_id == group.id,
                        CircleMembership.user_id == user_id,
                        CircleMembership.status.in_(['active', 'pending'])
                    )
                ).first()

                if not existing_membership:
                    available_groups.append(group)

            return available_groups

        except Exception as e:
            logger.error(f"Error getting available groups for user {user_id}: {e}")
            return []

    # Peer Circles
    async def create_peer_circle(
        self,
        db: Session,
        circle_data: Dict[str, Any],
        creator_id: int
    ) -> PeerCircle:
        """Create a new peer circle."""
        try:
            circle = PeerCircle(**circle_data)
            circle.facilitator_id = creator_id
            db.add(circle)
            db.commit()
            db.refresh(circle)

            # Add creator as first member
            membership = CircleMembership(
                user_id=creator_id,
                peer_circle_id=circle.id,
                status=MembershipStatus.ACTIVE,
                role="facilitator"
            )
            db.add(membership)
            db.commit()

            logger.info(f"Created peer circle: {circle.name}")
            return circle

        except Exception as e:
            logger.error(f"Error creating peer circle: {e}")
            db.rollback()
            raise

    async def join_peer_circle(
        self,
        db: Session,
        user_id: int,
        circle_id: int
    ) -> CircleMembership:
        """Join a peer circle."""
        try:
            # Check if circle exists and has space
            circle = db.query(PeerCircle).filter(PeerCircle.id == circle_id).first()
            if not circle:
                raise ValueError("Circle not found")

            if circle.status != CircleStatus.ACTIVE:
                raise ValueError("Circle is not active")

            # Check current member count
            current_members = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).count()

            if current_members >= circle.max_members:
                raise ValueError("Circle is full")

            # Check if user is already a member
            existing_membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == circle_id
                )
            ).first()

            if existing_membership:
                if existing_membership.status == MembershipStatus.ACTIVE:
                    raise ValueError("Already a member")
                elif existing_membership.status == MembershipStatus.PENDING:
                    raise ValueError("Membership request pending")
                else:
                    # Rejoin
                    existing_membership.status = MembershipStatus.PENDING if circle.requires_invitation else MembershipStatus.ACTIVE
                    existing_membership.joined_at = datetime.utcnow()
                    db.commit()
                    return existing_membership

            # Check user's circle limit
            user_circles = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).count()

            if user_circles >= self.max_circles_per_user:
                raise ValueError(f"Maximum {self.max_circles_per_user} circles allowed")

            # Create membership
            membership = CircleMembership(
                user_id=user_id,
                peer_circle_id=circle_id,
                status=MembershipStatus.PENDING if circle.requires_invitation else MembershipStatus.ACTIVE
            )
            db.add(membership)
            db.commit()
            db.refresh(membership)

            logger.info(f"User {user_id} joined circle {circle_id}")
            return membership

        except Exception as e:
            logger.error(f"Error joining peer circle: {e}")
            db.rollback()
            raise

    async def get_user_circles(
        self,
        db: Session,
        user_id: int
    ) -> List[PeerCircle]:
        """Get peer circles user is a member of."""
        try:
            circles = db.query(PeerCircle).join(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).all()

            return circles

        except Exception as e:
            logger.error(f"Error getting user circles for {user_id}: {e}")
            return []

    async def get_peer_circle_details(
        self,
        db: Session,
        user_id: int,
        circle_id: int
    ) -> PeerCircle:
        """Get details of a specific peer circle."""
        try:
            # First check if user has access to this circle
            membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).first()

            if not membership:
                raise ValueError("Access denied to this circle")

            # Get the circle details
            circle = db.query(PeerCircle).filter(PeerCircle.id == circle_id).first()

            if not circle:
                raise ValueError("Circle not found")

            return circle

        except Exception as e:
            logger.error(f"Error getting circle details for {circle_id}: {e}")
            raise

    async def get_circle_members(
        self,
        db: Session,
        user_id: int,
        circle_id: int
    ) -> List[CircleMembership]:
        """Get members of a specific peer circle."""
        try:
            # First check if user has access to this circle
            user_membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).first()

            if not user_membership:
                raise ValueError("Access denied to this circle")

            # Get all active members with user information
            members = db.query(CircleMembership).join(User).filter(
                and_(
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).all()

            # Populate user_name field for each member
            for member in members:
                if member.user:
                    member.user_name = member.user.full_name or member.user.username

            return members

        except Exception as e:
            logger.error(f"Error getting circle members for {circle_id}: {e}")
            raise

    # Circle Messages
    async def send_circle_message(
        self,
        db: Session,
        user_id: int,
        circle_id: int,
        content: str,
        message_type: str = "text"
    ) -> CircleMessage:
        """Send a message to a peer circle."""
        try:
            # Verify membership
            membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).first()

            if not membership:
                raise ValueError("Not a member of this circle")

            # Check cooldown
            last_message = db.query(CircleMessage).filter(
                and_(
                    CircleMessage.user_id == user_id,
                    CircleMessage.peer_circle_id == circle_id
                )
            ).order_by(desc(CircleMessage.created_at)).first()

            if last_message:
                time_since_last = datetime.utcnow() - last_message.created_at
                if time_since_last.total_seconds() < self.message_cooldown_minutes * 60:
                    raise ValueError("Please wait before sending another message")

            # Create message
            message = CircleMessage(
                peer_circle_id=circle_id,
                user_id=user_id,
                content=content,
                message_type=message_type
            )
            db.add(message)

            # Update circle activity
            circle = db.query(PeerCircle).filter(PeerCircle.id == circle_id).first()
            if circle:
                circle.last_activity_at = datetime.utcnow()
                circle.message_count += 1

            # Update membership activity
            membership.message_count += 1
            membership.last_seen_at = datetime.utcnow()

            db.commit()
            db.refresh(message)

            logger.info(f"Message sent to circle {circle_id} by user {user_id}")
            return message

        except Exception as e:
            logger.error(f"Error sending circle message: {e}")
            db.rollback()
            raise

    async def get_circle_messages(
        self,
        db: Session,
        user_id: int,
        circle_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[CircleMessage]:
        """Get messages from a peer circle."""
        try:
            # Verify membership
            membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).first()

            if not membership:
                raise ValueError("Not a member of this circle")

            # Get messages
            messages = db.query(CircleMessage).filter(
                and_(
                    CircleMessage.peer_circle_id == circle_id,
                    CircleMessage.status == MessageStatus.ACTIVE
                )
            ).order_by(desc(CircleMessage.created_at)).offset(offset).limit(limit).all()

            # Update last seen
            membership.last_seen_at = datetime.utcnow()
            db.commit()

            return messages

        except Exception as e:
            logger.error(f"Error getting circle messages: {e}")
            return []

    async def support_message(
        self,
        db: Session,
        user_id: int,
        message_id: int,
        support_type: str = "heart"
    ) -> MessageSupport:
        """Add support to a circle message."""
        try:
            # Check if message exists and user has access
            message = db.query(CircleMessage).filter(CircleMessage.id == message_id).first()
            if not message:
                raise ValueError("Message not found")

            # Verify membership in circle
            membership = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.peer_circle_id == message.peer_circle_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).first()

            if not membership:
                raise ValueError("Not a member of this circle")

            # Check if already supported
            existing_support = db.query(MessageSupport).filter(
                and_(
                    MessageSupport.user_id == user_id,
                    MessageSupport.message_id == message_id
                )
            ).first()

            if existing_support:
                # Update support type
                existing_support.support_type = support_type
                db.commit()
                return existing_support

            # Create new support
            support = MessageSupport(
                user_id=user_id,
                message_id=message_id,
                support_type=support_type
            )
            db.add(support)

            # Update message support count
            message.support_count += 1

            db.commit()
            db.refresh(support)

            return support

        except Exception as e:
            logger.error(f"Error supporting message: {e}")
            db.rollback()
            raise

    # Reflection Chains
    async def create_reflection_chain(
        self,
        db: Session,
        chain_data: Dict[str, Any]
    ) -> ReflectionChain:
        """Create a new reflection chain."""
        try:
            chain = ReflectionChain(**chain_data)
            db.add(chain)
            db.commit()
            db.refresh(chain)

            logger.info(f"Created reflection chain: {chain.title}")
            return chain

        except Exception as e:
            logger.error(f"Error creating reflection chain: {e}")
            db.rollback()
            raise

    async def add_reflection_entry(
        self,
        db: Session,
        user_id: int,
        entry_data: Dict[str, Any]
    ) -> ReflectionEntry:
        """Add an entry to a reflection chain."""
        try:
            # Check if chain exists and is active
            chain = db.query(ReflectionChain).filter(
                ReflectionChain.id == entry_data['chain_id']
            ).first()

            if not chain or not chain.is_active:
                raise ValueError("Chain not found or inactive")

            # Check entry limit
            current_entries = db.query(ReflectionEntry).filter(
                ReflectionEntry.chain_id == chain.id
            ).count()

            if current_entries >= chain.max_entries:
                raise ValueError("Chain has reached maximum entries")

            # Create entry
            entry = ReflectionEntry(
                user_id=user_id,
                **entry_data
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)

            logger.info(f"Added reflection entry to chain {chain.id}")
            return entry

        except Exception as e:
            logger.error(f"Error adding reflection entry: {e}")
            db.rollback()
            raise

    async def get_reflection_chains_for_user(
        self,
        db: Session,
        user_id: int,
        healing_module: Optional[str] = None
    ) -> List[ReflectionChain]:
        """Get reflection chains relevant to a user."""
        try:
            # Get user's cluster profile for targeting
            user_profile = db.query(UserClusterProfile).filter(
                UserClusterProfile.user_id == user_id
            ).first()

            query = db.query(ReflectionChain).filter(
                ReflectionChain.is_active == True
            )

            if healing_module:
                query = query.filter(ReflectionChain.healing_module == healing_module)

            chains = query.order_by(desc(ReflectionChain.created_at)).limit(10).all()

            return chains

        except Exception as e:
            logger.error(f"Error getting reflection chains for user {user_id}: {e}")
            return []

    async def get_reflection_entries(
        self,
        db: Session,
        chain_id: int,
        user_id: Optional[int] = None,
        limit: int = 20
    ) -> List[ReflectionEntry]:
        """Get entries from a reflection chain."""
        try:
            query = db.query(ReflectionEntry).filter(
                and_(
                    ReflectionEntry.chain_id == chain_id,
                    ReflectionEntry.status == ReflectionStatus.ACTIVE
                )
            )

            # If user provided, get targeted entries
            if user_id:
                user_profile = db.query(UserClusterProfile).filter(
                    UserClusterProfile.user_id == user_id
                ).first()

                if user_profile:
                    # Prioritize entries targeted to user's stage/emotions
                    query = query.filter(
                        or_(
                            ReflectionEntry.target_stage == user_profile.healing_stage,
                            ReflectionEntry.target_stage.is_(None)
                        )
                    )

            entries = query.order_by(desc(ReflectionEntry.created_at)).limit(limit).all()

            # Update view counts
            for entry in entries:
                entry.view_count += 1
            db.commit()

            return entries

        except Exception as e:
            logger.error(f"Error getting reflection entries: {e}")
            return []
