"""
Pydantic schemas for community and peer circles functionality.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CircleStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class MembershipStatusEnum(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    LEFT = "left"
    REMOVED = "removed"


class MessageStatusEnum(str, Enum):
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"


class ReflectionStatusEnum(str, Enum):
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"


# Shared Wound Group Schemas
class SharedWoundGroupCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emotional_pattern: Dict[str, Any]
    trauma_themes: Optional[List[str]] = None
    healing_stage: Optional[str] = None
    max_members: int = Field(8, ge=3, le=15)
    requires_approval: bool = True


class SharedWoundGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_members: Optional[int] = Field(None, ge=3, le=15)
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None


class SharedWoundGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    cluster_id: Optional[str]
    ai_generated: bool
    confidence_score: Optional[float]
    emotional_pattern: Dict[str, Any]
    trauma_themes: Optional[List[str]]
    healing_stage: Optional[str]
    member_count: int
    activity_score: float
    cohesion_score: float
    growth_potential: float
    max_members: int
    is_active: bool
    requires_approval: bool
    last_ai_review: Optional[datetime]
    next_ai_review: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    circle_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Peer Circle Schemas
class PeerCircleCreate(BaseModel):
    shared_wound_group_id: int
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_members: int = Field(6, ge=3, le=10)
    is_private: bool = True
    requires_invitation: bool = True


class PeerCircleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[CircleStatusEnum] = None
    max_members: Optional[int] = Field(None, ge=3, le=10)
    is_private: Optional[bool] = None
    requires_invitation: Optional[bool] = None


class PeerCircleResponse(BaseModel):
    id: int
    shared_wound_group_id: int
    name: str
    description: Optional[str]
    status: CircleStatusEnum
    max_members: int
    is_private: bool
    requires_invitation: bool
    facilitator_id: Optional[int]
    professional_moderator_id: Optional[int]
    last_activity_at: datetime
    message_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    member_count: Optional[int] = 0
    user_membership_status: Optional[MembershipStatusEnum] = None

    class Config:
        from_attributes = True


# Circle Membership Schemas
class CircleMembershipCreate(BaseModel):
    peer_circle_id: int
    role: str = "member"


class CircleMembershipUpdate(BaseModel):
    status: Optional[MembershipStatusEnum] = None
    role: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class CircleMembershipResponse(BaseModel):
    id: int
    user_id: int
    peer_circle_id: int
    status: MembershipStatusEnum
    role: str
    joined_at: datetime
    last_seen_at: datetime
    message_count: int
    notifications_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# Circle Message Schemas
class CircleMessageCreate(BaseModel):
    peer_circle_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    message_type: str = "text"


class CircleMessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    status: Optional[MessageStatusEnum] = None


class CircleMessageReplyCreate(BaseModel):
    message_id: int
    content: str = Field(..., min_length=1, max_length=1000)


class CircleMessageReplyResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    content: str
    status: MessageStatusEnum
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class MessageSupportCreate(BaseModel):
    message_id: int
    support_type: str = "heart"


class MessageSupportResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    support_type: str
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class CircleMessageResponse(BaseModel):
    id: int
    peer_circle_id: int
    user_id: int
    content: str
    message_type: str
    status: MessageStatusEnum
    support_count: int
    reply_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: Optional[str] = None
    replies: List[CircleMessageReplyResponse] = []
    supports: List[MessageSupportResponse] = []
    user_has_supported: bool = False

    class Config:
        from_attributes = True


# Reflection Chain Schemas
class ReflectionChainCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    healing_module: str = Field(..., min_length=1, max_length=100)
    difficulty_level: Optional[str] = None
    max_entries: int = Field(50, ge=10, le=200)


class ReflectionChainUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    max_entries: Optional[int] = Field(None, ge=10, le=200)


class ReflectionChainResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    healing_module: str
    difficulty_level: Optional[str]
    is_active: bool
    max_entries: int
    created_at: datetime
    updated_at: Optional[datetime]
    entry_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Reflection Entry Schemas
class ReflectionEntryCreate(BaseModel):
    chain_id: int
    content: str = Field(..., min_length=10, max_length=2000)
    reflection_type: str = "encouragement"
    target_stage: Optional[str] = None
    target_emotions: Optional[List[str]] = None


class ReflectionEntryUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=10, max_length=2000)
    status: Optional[ReflectionStatusEnum] = None


class ReflectionEntryResponse(BaseModel):
    id: int
    chain_id: int
    user_id: int
    content: str
    reflection_type: str
    target_stage: Optional[str]
    target_emotions: Optional[List[str]]
    status: ReflectionStatusEnum
    helpful_count: int
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_name: Optional[str] = None
    is_helpful_to_user: bool = False

    class Config:
        from_attributes = True


# User Cluster Profile Schemas
class UserClusterProfileCreate(BaseModel):
    dominant_emotions: Dict[str, float]
    emotion_intensity: float
    emotion_variability: float
    trauma_themes: Optional[List[str]] = None
    healing_stage: Optional[str] = None
    coping_patterns: Optional[List[str]] = None
    communication_style: Optional[str] = None
    support_preference: Optional[str] = None
    activity_level: Optional[str] = None


class UserClusterProfileUpdate(BaseModel):
    dominant_emotions: Optional[Dict[str, float]] = None
    emotion_intensity: Optional[float] = None
    emotion_variability: Optional[float] = None
    trauma_themes: Optional[List[str]] = None
    healing_stage: Optional[str] = None
    coping_patterns: Optional[List[str]] = None
    communication_style: Optional[str] = None
    support_preference: Optional[str] = None
    activity_level: Optional[str] = None


class UserClusterProfileResponse(BaseModel):
    id: int
    user_id: int
    dominant_emotions: Dict[str, float]
    emotion_intensity: float
    emotion_variability: float
    trauma_themes: Optional[List[str]]
    healing_stage: Optional[str]
    coping_patterns: Optional[List[str]]
    communication_style: Optional[str]
    support_preference: Optional[str]
    activity_level: Optional[str]
    last_clustered_at: Optional[datetime]
    cluster_confidence: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Community Dashboard Schemas
class CommunityDashboardResponse(BaseModel):
    available_groups: List[SharedWoundGroupResponse]
    user_circles: List[PeerCircleResponse]
    recent_reflections: List[ReflectionEntryResponse]
    suggested_chains: List[ReflectionChainResponse]
    user_cluster_profile: Optional[UserClusterProfileResponse]


# Clustering Request Schemas
class ClusteringRequest(BaseModel):
    user_id: Optional[int] = None
    force_recluster: bool = False


class ClusteringResponse(BaseModel):
    user_id: int
    suggested_groups: List[SharedWoundGroupResponse]
    cluster_confidence: float
    cluster_profile: UserClusterProfileResponse
