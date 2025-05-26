"""
API routers for InnerCalm application.
"""
from .auth import router as auth_router
from .chat import router as chat_router
from .emotions import router as emotions_router
from .recommendations import router as recommendations_router
from .users import router as users_router
from .analytics import router as analytics_router

__all__ = [
    "auth_router",
    "chat_router",
    "emotions_router",
    "recommendations_router",
    "users_router",
    "analytics_router"
]
