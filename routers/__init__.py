"""
API routers for InnerCalm application.
"""
from .auth import router as auth_router
from .chat import router as chat_router
from .emotions import router as emotions_router
from .recommendations import router as recommendations_router
from .users import router as users_router
from .analytics import router as analytics_router
from .trauma_mapping import router as trauma_mapping_router
from .inner_ally import router as inner_ally_router
from .professional_bridge import router as professional_bridge_router
from .therapist import router as therapist_router
from .community import router as community_router
from .moderation import router as moderation_router
from .notifications import router as notifications_router

__all__ = [
    "auth_router",
    "chat_router",
    "emotions_router",
    "recommendations_router",
    "users_router",
    "analytics_router",
    "trauma_mapping_router",
    "inner_ally_router",
    "professional_bridge_router",
    "therapist_router",
    "community_router",
    "moderation_router",
    "notifications_router"
]
