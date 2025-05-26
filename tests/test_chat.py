"""
Tests for chat functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, patch

from models.user import User
from models.conversation import Conversation, Message


class TestChatEndpoints:
    """Test chat API endpoints."""
    
    @patch('routers.chat.ai_chat.chat')
    @patch('routers.chat.emotion_analyzer.analyze_emotion')
    def test_send_message_new_conversation(
        self, 
        mock_emotion_analyzer, 
        mock_ai_chat,
        client: TestClient, 
        auth_headers: dict, 
        test_message_data: dict,
        test_emotion_analysis_data: dict
    ):
        """Test sending a message in a new conversation."""
        # Mock the emotion analyzer
        mock_emotion_analyzer.return_value = test_emotion_analysis_data
        
        # Mock the AI chat response
        mock_ai_chat.return_value = {
            "response": "I understand you're feeling sad. Would you like to talk about what's causing these feelings?",
            "therapeutic_approach": "person_centered",
            "response_tone": "empathetic",
            "conversation_id": 1
        }
        
        response = client.post(
            "/chat/",
            json=test_message_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "ai_response" in data
        assert "conversation_id" in data
        assert "emotion_analysis" in data
        
        assert data["message"]["content"] == test_message_data["message"]
        assert data["message"]["is_user_message"] is True
        assert data["ai_response"]["is_user_message"] is False
        assert data["emotion_analysis"]["sentiment_label"] == "negative"
    
    @patch('routers.chat.ai_chat.chat')
    @patch('routers.chat.emotion_analyzer.analyze_emotion')
    def test_send_message_existing_conversation(
        self,
        mock_emotion_analyzer,
        mock_ai_chat,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        test_emotion_analysis_data: dict
    ):
        """Test sending a message in an existing conversation."""
        # Create existing conversation
        conversation = Conversation(
            user_id=test_user.id,
            title="Existing Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Mock responses
        mock_emotion_analyzer.return_value = test_emotion_analysis_data
        mock_ai_chat.return_value = {
            "response": "Thank you for sharing more. How are you feeling now?",
            "therapeutic_approach": "person_centered",
            "response_tone": "empathetic",
            "conversation_id": conversation.id
        }
        
        response = client.post(
            "/chat/",
            json={
                "message": "I'm still feeling down",
                "conversation_id": conversation.id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation.id
    
    def test_send_message_invalid_conversation(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test sending a message to non-existent conversation."""
        response = client.post(
            "/chat/",
            json={
                "message": "Hello",
                "conversation_id": 999  # Non-existent
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_conversations(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test getting user's conversations."""
        # Create test conversations
        for i in range(3):
            conversation = Conversation(
                user_id=test_user.id,
                title=f"Test Conversation {i+1}"
            )
            db_session.add(conversation)
        
        db_session.commit()
        
        response = client.get("/chat/conversations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("title" in conv for conv in data)
        assert all("id" in conv for conv in data)
    
    def test_get_conversations_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test conversation pagination."""
        # Create many conversations
        for i in range(25):
            conversation = Conversation(
                user_id=test_user.id,
                title=f"Conversation {i+1}"
            )
            db_session.add(conversation)
        
        db_session.commit()
        
        # Test first page
        response = client.get(
            "/chat/conversations?limit=10&offset=0",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 10
        
        # Test second page
        response = client.get(
            "/chat/conversations?limit=10&offset=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 10
    
    def test_get_specific_conversation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test getting a specific conversation with messages."""
        # Create conversation with messages
        conversation = Conversation(
            user_id=test_user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Add messages
        user_message = Message(
            conversation_id=conversation.id,
            content="Hello",
            is_user_message=True
        )
        ai_message = Message(
            conversation_id=conversation.id,
            content="Hi there! How can I help?",
            is_user_message=False
        )
        db_session.add_all([user_message, ai_message])
        db_session.commit()
        
        response = client.get(
            f"/chat/conversations/{conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation.id
        assert data["title"] == "Test Conversation"
        assert len(data["messages"]) == 2
    
    def test_get_conversation_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent conversation."""
        response = client.get(
            "/chat/conversations/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_conversation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test deleting a conversation."""
        conversation = Conversation(
            user_id=test_user.id,
            title="To Delete"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        response = client.delete(
            f"/chat/conversations/{conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]
        
        # Verify conversation is marked as inactive
        db_session.refresh(conversation)
        assert conversation.is_active is False
    
    def test_delete_conversation_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent conversation."""
        response = client.delete(
            "/chat/conversations/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_send_empty_message(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test sending empty message."""
        response = client.post(
            "/chat/",
            json={"message": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_send_very_long_message(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test sending very long message."""
        long_message = "A" * 6000  # Exceeds 5000 char limit
        
        response = client.post(
            "/chat/",
            json={"message": long_message},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing chat endpoints without authentication."""
        response = client.post(
            "/chat/",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 401
        
        response = client.get("/chat/conversations")
        assert response.status_code == 401
