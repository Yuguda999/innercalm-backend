"""
InnerCalm - AI-Powered Emotional Healing Companion
Main FastAPI application with comprehensive emotional support features.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from database import create_tables, engine
from routers import (
    auth_router,
    chat_router,
    emotions_router,
    recommendations_router,
    users_router,
    analytics_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting InnerCalm API...")
    try:
        # Import all models to ensure they're registered
        from models import user, conversation, emotion, recommendation, analytics

        # Create database tables
        create_tables()
        logger.info("Database tables created successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down InnerCalm API...")
        engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    InnerCalm is an AI-powered emotional healing companion that provides:

    - **Empathetic AI Chat**: Conversational AI that actively listens and responds with empathy
    - **Emotion Analysis**: Advanced sentiment analysis and pattern recognition
    - **Personalized Recommendations**: Custom healing exercises based on emotional patterns
    - **Progress Tracking**: Comprehensive emotional journey analytics

    Built with FastAPI, LangGraph, and OpenAI GPT-4 for therapeutic conversations.
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to InnerCalm API",
        "description": "AI-Powered Emotional Healing Companion",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(emotions_router)
app.include_router(recommendations_router)
app.include_router(users_router)
app.include_router(analytics_router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring."""
    import time
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"Path: {request.url.path}"
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url} - "
            f"Time: {process_time:.3f}s - "
            f"Error: {str(e)}"
        )
        raise


if __name__ == "__main__":
    import time

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
