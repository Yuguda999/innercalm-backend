"""
Community and peer circles models for InnerCalm application.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class CircleStatus(enum.Enum):
    """Status of a peer circle."""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class MembershipStatus(enum.Enum):
    """Status of circle membership."""
    ACTIVE = "active"
    PENDING = "pending"
    LEFT = "left"
    REMOVED = "removed"


class MessageStatus(enum.Enum):
    """Status of circle messages."""
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"


class ReflectionStatus(enum.Enum):
    """Status of reflection chain entries."""
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"


class SharedWoundGroup(Base):
    """AI-managed shared wound groups for clustering users by similar emotional patterns."""

    __tablename__ = "shared_wound_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # AI Management metadata
    cluster_id = Column(String, nullable=True, unique=True)  # AI-generated cluster identifier
    ai_generated = Column(Boolean, default=True)  # Whether this group was AI-created
    confidence_score = Column(Float, nullable=True)  # AI confidence in group coherence

    # Clustering metadata
    emotional_pattern = Column(JSON, nullable=False)  # Dominant emotions and patterns
    trauma_themes = Column(JSON, nullable=True)  # Common trauma themes
    healing_stage = Column(String, nullable=True)  # early, processing, integration, growth

    # Dynamic group metrics
    member_count = Column(Integer, default=0)
    activity_score = Column(Float, default=0.0)  # Engagement level
    cohesion_score = Column(Float, default=0.0)  # How well members connect
    growth_potential = Column(Float, default=0.0)  # Potential for helping members heal

    # Group settings
    max_members = Column(Integer, default=50)  # Larger groups that spawn circles
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)  # AI manages membership

    # AI management timestamps
    last_ai_review = Column(DateTime(timezone=True), nullable=True)
    next_ai_review = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    peer_circles = relationship("PeerCircle", back_populates="shared_wound_group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SharedWoundGroup(id={self.id}, name='{self.name}', ai_generated={self.ai_generated})>"


class PeerCircle(Base):
    """Peer circles for small group support within shared wound groups."""

    __tablename__ = "peer_circles"

    id = Column(Integer, primary_key=True, index=True)
    shared_wound_group_id = Column(Integer, ForeignKey("shared_wound_groups.id"), nullable=False)

    # Circle metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CircleStatus), default=CircleStatus.ACTIVE)

    # Circle settings
    max_members = Column(Integer, default=6)  # Intimate circle size
    is_private = Column(Boolean, default=True)
    requires_invitation = Column(Boolean, default=True)

    # Moderation
    facilitator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional peer facilitator
    professional_moderator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Professional volunteer

    # Activity tracking
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shared_wound_group = relationship("SharedWoundGroup", back_populates="peer_circles")
    facilitator = relationship("User", foreign_keys=[facilitator_id])
    professional_moderator = relationship("User", foreign_keys=[professional_moderator_id])
    memberships = relationship("CircleMembership", back_populates="peer_circle", cascade="all, delete-orphan")
    messages = relationship("CircleMessage", back_populates="peer_circle", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PeerCircle(id={self.id}, name='{self.name}')>"


class CircleMembership(Base):
    """Membership in peer circles."""

    __tablename__ = "circle_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    peer_circle_id = Column(Integer, ForeignKey("peer_circles.id"), nullable=False)

    # Membership details
    status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    role = Column(String, default="member")  # member, facilitator, moderator

    # Activity tracking
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    message_count = Column(Integer, default=0)

    # Preferences
    notifications_enabled = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    peer_circle = relationship("PeerCircle", back_populates="memberships")

    def __repr__(self):
        return f"<CircleMembership(user_id={self.user_id}, circle_id={self.peer_circle_id})>"


class CircleMessage(Base):
    """Messages in peer circles."""

    __tablename__ = "circle_messages"

    id = Column(Integer, primary_key=True, index=True)
    peer_circle_id = Column(Integer, ForeignKey("peer_circles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # text, support, check_in, reflection

    # Moderation
    status = Column(Enum(MessageStatus), default=MessageStatus.ACTIVE)
    flagged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    flagged_reason = Column(String, nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderation_notes = Column(Text, nullable=True)

    # Engagement
    support_count = Column(Integer, default=0)  # Like/heart reactions
    reply_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    peer_circle = relationship("PeerCircle", back_populates="messages")
    user = relationship("User", foreign_keys=[user_id])
    flagged_by_user = relationship("User", foreign_keys=[flagged_by])
    moderated_by_user = relationship("User", foreign_keys=[moderated_by])
    replies = relationship("CircleMessageReply", back_populates="message", cascade="all, delete-orphan")
    supports = relationship("MessageSupport", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CircleMessage(id={self.id}, circle_id={self.peer_circle_id})>"


class CircleMessageReply(Base):
    """Replies to circle messages."""

    __tablename__ = "circle_message_replies"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("circle_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.ACTIVE)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    message = relationship("CircleMessage", back_populates="replies")
    user = relationship("User")

    def __repr__(self):
        return f"<CircleMessageReply(id={self.id}, message_id={self.message_id})>"


class MessageSupport(Base):
    """Support reactions to messages (like hearts/likes)."""

    __tablename__ = "message_supports"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("circle_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    support_type = Column(String, default="heart")  # heart, hug, strength, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("CircleMessage", back_populates="supports")
    user = relationship("User")

    def __repr__(self):
        return f"<MessageSupport(message_id={self.message_id}, user_id={self.user_id})>"


class ReflectionChain(Base):
    """Pay It Forward reflection chains."""

    __tablename__ = "reflection_chains"

    id = Column(Integer, primary_key=True, index=True)

    # Chain metadata
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    healing_module = Column(String, nullable=False)  # Which healing exercise this relates to
    difficulty_level = Column(String, nullable=True)  # beginner, intermediate, advanced

    # Chain settings
    is_active = Column(Boolean, default=True)
    max_entries = Column(Integer, default=50)  # Limit chain length

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    entries = relationship("ReflectionEntry", back_populates="chain", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ReflectionChain(id={self.id}, title='{self.title}')>"


class ReflectionEntry(Base):
    """Individual entries in reflection chains."""

    __tablename__ = "reflection_entries"

    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(Integer, ForeignKey("reflection_chains.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Entry content
    content = Column(Text, nullable=False)
    reflection_type = Column(String, default="encouragement")  # encouragement, insight, tip, story

    # Targeting
    target_stage = Column(String, nullable=True)  # For users at specific healing stages
    target_emotions = Column(JSON, nullable=True)  # For users experiencing specific emotions

    # Moderation
    status = Column(Enum(ReflectionStatus), default=ReflectionStatus.ACTIVE)
    flagged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    flagged_reason = Column(String, nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Engagement
    helpful_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chain = relationship("ReflectionChain", back_populates="entries")
    user = relationship("User", foreign_keys=[user_id])
    flagged_by_user = relationship("User", foreign_keys=[flagged_by])
    moderated_by_user = relationship("User", foreign_keys=[moderated_by])

    def __repr__(self):
        return f"<ReflectionEntry(id={self.id}, chain_id={self.chain_id})>"


class UserClusterProfile(Base):
    """User clustering profile for matching to shared wound groups."""

    __tablename__ = "user_cluster_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Emotional patterns
    dominant_emotions = Column(JSON, nullable=False)  # Top emotions from analysis
    emotion_intensity = Column(Float, nullable=False)  # Average emotional intensity
    emotion_variability = Column(Float, nullable=False)  # Emotional stability measure

    # Trauma patterns
    trauma_themes = Column(JSON, nullable=True)  # Identified trauma themes
    healing_stage = Column(String, nullable=True)  # Current healing stage
    coping_patterns = Column(JSON, nullable=True)  # Preferred coping mechanisms

    # Interaction patterns
    communication_style = Column(String, nullable=True)  # direct, gentle, analytical, etc.
    support_preference = Column(String, nullable=True)  # giving, receiving, balanced
    activity_level = Column(String, nullable=True)  # high, medium, low

    # Clustering metadata
    cluster_vector = Column(JSON, nullable=False)  # Numerical representation for clustering
    last_clustered_at = Column(DateTime(timezone=True), nullable=True)
    cluster_confidence = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UserClusterProfile(user_id={self.user_id}, stage='{self.healing_stage}')>"
