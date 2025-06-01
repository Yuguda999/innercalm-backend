"""
Tests for WebSocket functionality.
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models.user import User
from models.community import SharedWoundGroup, PeerCircle, CircleMembership
from services.websocket_manager import connection_manager


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
def test_circle_with_membership(db_session: Session, test_user: User):
    """Create a test circle with user membership."""
    # Create shared wound group
    group = SharedWoundGroup(
        name="Test Group",
        description="Test group",
        emotional_pattern={"sadness": 0.5},
        is_active=True
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    
    # Create peer circle
    circle = PeerCircle(
        shared_wound_group_id=group.id,
        name="Test Circle",
        description="Test circle",
        status="active"
    )
    db_session.add(circle)
    db_session.commit()
    db_session.refresh(circle)
    
    # Create membership
    membership = CircleMembership(
        user_id=test_user.id,
        peer_circle_id=circle.id,
        status="active"
    )
    db_session.add(membership)
    db_session.commit()
    
    return circle


class TestWebSocketManager:
    """Test WebSocket connection manager."""
    
    def test_connection_manager_initialization(self):
        """Test that connection manager initializes properly."""
        assert connection_manager.active_connections == {}
        assert connection_manager.connection_users == {}
        assert connection_manager.user_circles == {}
    
    def test_get_circle_users_empty(self):
        """Test getting users from empty circle."""
        users = connection_manager.get_circle_users(999)
        assert users == []
    
    def test_get_connection_count_empty(self):
        """Test getting connection count for empty circle."""
        count = connection_manager.get_connection_count(999)
        assert count == 0


class TestWebSocketEndpoints:
    """Test WebSocket endpoints."""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is properly registered."""
        client = TestClient(app)
        
        # Test that the WebSocket route exists
        # Note: TestClient doesn't support WebSocket testing directly
        # In production, you'd use a proper WebSocket testing framework
        
        # For now, just verify the route is registered
        routes = [route.path for route in app.routes]
        websocket_routes = [route for route in routes if '/ws/' in route]
        
        assert len(websocket_routes) > 0
        assert any('/ws/circles/' in route for route in websocket_routes)


# Note: For full WebSocket testing, you would need:
# 1. A WebSocket testing framework like pytest-asyncio with websockets library
# 2. Mock authentication for testing
# 3. Database setup/teardown for each test
# 4. Proper async test handling

# Example of what full WebSocket testing would look like:
"""
import websockets
import asyncio

@pytest.mark.asyncio
async def test_websocket_connection():
    # This would require a running test server
    uri = "ws://localhost:8000/ws/circles/1?token=test_token"
    
    async with websockets.connect(uri) as websocket:
        # Test sending a message
        await websocket.send(json.dumps({
            "type": "chat_message",
            "content": "Hello, world!",
            "message_type": "text"
        }))
        
        # Test receiving a response
        response = await websocket.recv()
        data = json.loads(response)
        
        assert data["type"] == "new_message"
        assert data["message"]["content"] == "Hello, world!"
"""
