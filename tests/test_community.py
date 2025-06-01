"""
Tests for community functionality.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from database import get_db
from models.user import User
from models.community import (
    SharedWoundGroup, PeerCircle, CircleMembership, CircleMessage,
    ReflectionChain, ReflectionEntry, UserClusterProfile
)
from services.community_service import CommunityService
from services.clustering_service import ClusteringService


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_shared_wound_group(db_session: Session):
    """Create a test shared wound group."""
    group = SharedWoundGroup(
        name="Test Support Group",
        description="A test group for healing",
        emotional_pattern={
            "sadness": 0.4,
            "fear": 0.3,
            "anger": 0.2,
            "joy": 0.1
        },
        trauma_themes=["test_trauma"],
        healing_stage="processing",
        max_members=10,
        is_active=True,
        requires_approval=True
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def test_peer_circle(db_session: Session, test_shared_wound_group: SharedWoundGroup):
    """Create a test peer circle."""
    circle = PeerCircle(
        shared_wound_group_id=test_shared_wound_group.id,
        name="Test Circle",
        description="A test peer circle",
        max_members=6,
        is_private=True,
        requires_invitation=True
    )
    db_session.add(circle)
    db_session.commit()
    db_session.refresh(circle)
    return circle


@pytest.fixture
def test_reflection_chain(db_session: Session):
    """Create a test reflection chain."""
    chain = ReflectionChain(
        title="Test Reflection Chain",
        description="A test chain for reflections",
        healing_module="Test Module",
        difficulty_level="beginner",
        is_active=True,
        max_entries=50
    )
    db_session.add(chain)
    db_session.commit()
    db_session.refresh(chain)
    return chain


class TestCommunityService:
    """Test community service functionality."""
    
    def test_create_shared_wound_group(self, db_session: Session):
        """Test creating a shared wound group."""
        service = CommunityService()
        
        group_data = {
            "name": "New Test Group",
            "description": "A new test group",
            "emotional_pattern": {"sadness": 0.5, "fear": 0.3, "anger": 0.2},
            "trauma_themes": ["new_trauma"],
            "healing_stage": "early",
            "max_members": 15,
            "is_active": True,
            "requires_approval": False
        }
        
        # Use asyncio.run for async function
        import asyncio
        group = asyncio.run(service.create_shared_wound_group(db_session, group_data))
        
        assert group.name == "New Test Group"
        assert group.max_members == 15
        assert group.is_active is True
        assert group.requires_approval is False
    
    def test_join_peer_circle(self, db_session: Session, test_user: User, test_peer_circle: PeerCircle):
        """Test joining a peer circle."""
        service = CommunityService()
        
        import asyncio
        membership = asyncio.run(service.join_peer_circle(
            db_session, test_user.id, test_peer_circle.id
        ))
        
        assert membership.user_id == test_user.id
        assert membership.peer_circle_id == test_peer_circle.id
        assert membership.role == "member"
    
    def test_send_circle_message(self, db_session: Session, test_user: User, test_peer_circle: PeerCircle):
        """Test sending a message to a peer circle."""
        service = CommunityService()
        
        # First join the circle
        import asyncio
        membership = asyncio.run(service.join_peer_circle(
            db_session, test_user.id, test_peer_circle.id
        ))
        
        # Update membership status to active
        membership.status = "active"
        db_session.commit()
        
        # Send a message
        message = asyncio.run(service.send_circle_message(
            db_session, test_user.id, test_peer_circle.id, "Hello, this is a test message!"
        ))
        
        assert message.content == "Hello, this is a test message!"
        assert message.user_id == test_user.id
        assert message.peer_circle_id == test_peer_circle.id
    
    def test_add_reflection_entry(self, db_session: Session, test_user: User, test_reflection_chain: ReflectionChain):
        """Test adding a reflection entry."""
        service = CommunityService()
        
        entry_data = {
            "chain_id": test_reflection_chain.id,
            "content": "This is a test reflection about healing and growth.",
            "reflection_type": "encouragement",
            "target_stage": "early"
        }
        
        import asyncio
        entry = asyncio.run(service.add_reflection_entry(
            db_session, test_user.id, entry_data
        ))
        
        assert entry.content == "This is a test reflection about healing and growth."
        assert entry.reflection_type == "encouragement"
        assert entry.target_stage == "early"
        assert entry.user_id == test_user.id


class TestClusteringService:
    """Test clustering service functionality."""
    
    def test_create_cluster_vector(self):
        """Test creating a cluster vector."""
        service = ClusteringService()
        
        emotions = {
            "joy": 0.1,
            "sadness": 0.4,
            "anger": 0.2,
            "fear": 0.3,
            "surprise": 0.0,
            "disgust": 0.0
        }
        
        vector = service._create_cluster_vector(
            emotions=emotions,
            intensity=0.6,
            variability=0.3,
            themes=["trauma", "anxiety"],
            stage="processing",
            coping=["meditation", "therapy"]
        )
        
        assert len(vector) == 10  # 6 emotions + 2 metrics + 4 stage indicators
        assert vector[0] == 0.1  # joy
        assert vector[1] == 0.4  # sadness
        assert vector[6] == 0.6  # intensity
        assert vector[7] == 0.3  # variability
    
    def test_calculate_emotion_similarity(self):
        """Test emotion similarity calculation."""
        service = ClusteringService()
        
        user_emotions = {
            "joy": 0.1,
            "sadness": 0.4,
            "anger": 0.2,
            "fear": 0.3,
            "surprise": 0.0,
            "disgust": 0.0
        }
        
        group_emotions = {
            "joy": 0.15,
            "sadness": 0.35,
            "anger": 0.25,
            "fear": 0.25,
            "surprise": 0.0,
            "disgust": 0.0
        }
        
        similarity = service._calculate_emotion_similarity(user_emotions, group_emotions)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.8  # Should be high similarity
    
    def test_calculate_theme_similarity(self):
        """Test trauma theme similarity calculation."""
        service = ClusteringService()
        
        user_themes = ["childhood_trauma", "anxiety", "depression"]
        group_themes = ["childhood_trauma", "anxiety", "abandonment"]
        
        similarity = service._calculate_theme_similarity(user_themes, group_themes)
        
        # Jaccard similarity: intersection(2) / union(4) = 0.5
        assert similarity == 0.5
    
    def test_are_adjacent_stages(self):
        """Test healing stage adjacency check."""
        service = ClusteringService()
        
        assert service._are_adjacent_stages("early", "processing") is True
        assert service._are_adjacent_stages("processing", "integration") is True
        assert service._are_adjacent_stages("integration", "growth") is True
        assert service._are_adjacent_stages("early", "integration") is False
        assert service._are_adjacent_stages("early", "growth") is False


class TestCommunityAPI:
    """Test community API endpoints."""
    
    def test_get_community_dashboard(self, client: TestClient, test_user: User, auth_headers):
        """Test getting community dashboard."""
        response = client.get("/community/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "available_groups" in data
        assert "user_circles" in data
        assert "recent_reflections" in data
        assert "suggested_chains" in data
        assert isinstance(data["available_groups"], list)
        assert isinstance(data["user_circles"], list)
    
    def test_get_available_groups(self, client: TestClient, test_user: User, auth_headers):
        """Test getting available groups."""
        response = client.get("/community/groups", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_reflection_chains(self, client: TestClient, test_user: User, auth_headers):
        """Test getting reflection chains."""
        response = client.get("/community/reflection-chains", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# Fixtures for testing
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers."""
    # This would normally create a JWT token
    # For testing, we'll use a mock token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def db_session():
    """Create test database session."""
    from database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
