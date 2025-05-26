"""
Test configuration and fixtures for InnerCalm tests.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db, Base
from models.user import User
from services.auth_service import AuthService
from config import settings

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Import all models to ensure they're registered
    from models import user, conversation, emotion, recommendation

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user(db_session: Session, test_user_data: dict) -> User:
    """Create a test user."""
    from schemas.user import UserCreate
    user_create = UserCreate(**test_user_data)
    return AuthService.create_user(db_session, user_create)


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_conversation_data():
    """Test conversation data."""
    return {
        "title": "Test Conversation"
    }


@pytest.fixture
def test_message_data():
    """Test message data."""
    return {
        "message": "I'm feeling really sad today and don't know what to do."
    }


@pytest.fixture
def test_emotion_analysis_data():
    """Test emotion analysis data."""
    return {
        "joy": 0.1,
        "sadness": 0.8,
        "anger": 0.2,
        "fear": 0.3,
        "surprise": 0.1,
        "disgust": 0.1,
        "sentiment_score": -0.6,
        "sentiment_label": "negative",
        "themes": ["sadness", "emotional_distress"],
        "keywords": ["sad", "feeling", "today"],
        "confidence": 0.85
    }


@pytest.fixture
def test_recommendation_data():
    """Test recommendation data."""
    return {
        "type": "breathing_exercise",
        "title": "Test Breathing Exercise",
        "description": "A test breathing exercise for relaxation",
        "instructions": "1. Breathe in\n2. Hold\n3. Breathe out",
        "target_emotions": ["sadness", "anxiety"],
        "difficulty_level": 1,
        "estimated_duration": 10
    }
