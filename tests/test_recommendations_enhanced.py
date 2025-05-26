"""
Enhanced tests for recommendations functionality including modal and detailed view.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from database import get_db
from models.user import User
from models.recommendation import Recommendation, RecommendationType
from routers.auth import create_access_token
import json

client = TestClient(app)

def test_get_recommendation_detail(test_db: Session, test_user: User):
    """Test getting detailed recommendation information."""
    # Create a test recommendation
    recommendation = Recommendation(
        user_id=test_user.id,
        type=RecommendationType.MEDITATION,
        title="Morning Meditation",
        description="A peaceful morning meditation to start your day",
        instructions="Sit comfortably, close your eyes, and focus on your breath for 10 minutes.",
        target_emotions=["stress", "anxiety"],
        difficulty_level=2,
        estimated_duration=10,
        is_completed=False
    )
    test_db.add(recommendation)
    test_db.commit()
    test_db.refresh(recommendation)
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test getting the recommendation
    response = client.get(f"/recommendations/{recommendation.id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == recommendation.id
    assert data["title"] == "Morning Meditation"
    assert data["description"] == "A peaceful morning meditation to start your day"
    assert data["instructions"] == "Sit comfortably, close your eyes, and focus on your breath for 10 minutes."
    assert data["type"] == "meditation"
    assert data["target_emotions"] == ["stress", "anxiety"]
    assert data["difficulty_level"] == 2
    assert data["estimated_duration"] == 10
    assert data["is_completed"] == False


def test_update_recommendation_with_rating(test_db: Session, test_user: User):
    """Test updating recommendation with effectiveness rating."""
    # Create a test recommendation
    recommendation = Recommendation(
        user_id=test_user.id,
        type=RecommendationType.BREATHING,
        title="Deep Breathing Exercise",
        description="A simple breathing exercise for relaxation",
        instructions="Breathe in for 4 counts, hold for 4, breathe out for 4.",
        target_emotions=["stress"],
        difficulty_level=1,
        estimated_duration=5,
        is_completed=False
    )
    test_db.add(recommendation)
    test_db.commit()
    test_db.refresh(recommendation)
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test updating with completion and rating
    update_data = {
        "is_completed": True,
        "effectiveness_rating": 4,
        "notes": "Very helpful for reducing stress"
    }
    
    response = client.patch(
        f"/recommendations/{recommendation.id}", 
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["is_completed"] == True
    assert data["effectiveness_rating"] == 4
    assert data["notes"] == "Very helpful for reducing stress"
    assert data["completed_at"] is not None


def test_get_recommendations_with_ratings(test_db: Session, test_user: User):
    """Test getting recommendations list with effectiveness ratings."""
    # Create test recommendations with different ratings
    recommendations = [
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.MEDITATION,
            title="Meditation 1",
            description="First meditation",
            instructions="Meditate for 10 minutes",
            target_emotions=["stress"],
            difficulty_level=1,
            estimated_duration=10,
            is_completed=True,
            effectiveness_rating=5
        ),
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.JOURNALING,
            title="Journaling 1",
            description="Write about your feelings",
            instructions="Write for 15 minutes about your day",
            target_emotions=["sadness"],
            difficulty_level=2,
            estimated_duration=15,
            is_completed=True,
            effectiveness_rating=3
        ),
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.EXERCISE,
            title="Light Exercise",
            description="A gentle workout",
            instructions="Do 20 minutes of light exercise",
            target_emotions=["depression"],
            difficulty_level=3,
            estimated_duration=20,
            is_completed=False
        )
    ]
    
    for rec in recommendations:
        test_db.add(rec)
    test_db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test getting all recommendations
    response = client.get("/recommendations", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    
    # Check that ratings are included for completed recommendations
    completed_recs = [rec for rec in data if rec["is_completed"]]
    assert len(completed_recs) == 2
    
    for rec in completed_recs:
        assert "effectiveness_rating" in rec
        assert rec["effectiveness_rating"] is not None


def test_recommendation_summary_stats(test_db: Session, test_user: User):
    """Test getting recommendation summary statistics."""
    # Create test recommendations with various states
    recommendations = [
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.MEDITATION,
            title="Meditation 1",
            description="First meditation",
            instructions="Meditate",
            target_emotions=["stress"],
            difficulty_level=1,
            estimated_duration=10,
            is_completed=True,
            effectiveness_rating=5
        ),
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.MEDITATION,
            title="Meditation 2",
            description="Second meditation",
            instructions="Meditate more",
            target_emotions=["anxiety"],
            difficulty_level=2,
            estimated_duration=15,
            is_completed=True,
            effectiveness_rating=4
        ),
        Recommendation(
            user_id=test_user.id,
            type=RecommendationType.JOURNALING,
            title="Journal Entry",
            description="Write about feelings",
            instructions="Write",
            target_emotions=["sadness"],
            difficulty_level=1,
            estimated_duration=20,
            is_completed=False
        )
    ]
    
    for rec in recommendations:
        test_db.add(rec)
    test_db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test getting summary stats
    response = client.get("/recommendations/summary/stats", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_recommendations"] == 3
    assert data["completed_recommendations"] == 2
    assert data["completion_rate"] == 66.67  # 2/3 * 100
    assert data["average_effectiveness"] == 4.5  # (5+4)/2
    assert data["most_effective_type"] == "meditation"
    assert len(data["recent_recommendations"]) == 3


def test_recommendation_not_found(test_db: Session, test_user: User):
    """Test getting non-existent recommendation."""
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.get("/recommendations/999", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_nonexistent_recommendation(test_db: Session, test_user: User):
    """Test updating non-existent recommendation."""
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    update_data = {"is_completed": True}
    response = client.patch("/recommendations/999", headers=headers, json=update_data)
    assert response.status_code == 404


def test_recommendation_authorization(test_db: Session, test_user: User):
    """Test that users can only access their own recommendations."""
    # Create another user
    other_user = User(
        email="other@example.com",
        name="Other User",
        hashed_password="hashed_password"
    )
    test_db.add(other_user)
    test_db.commit()
    test_db.refresh(other_user)
    
    # Create recommendation for other user
    recommendation = Recommendation(
        user_id=other_user.id,
        type=RecommendationType.MEDITATION,
        title="Other's Meditation",
        description="Not accessible",
        instructions="Private",
        target_emotions=["stress"],
        difficulty_level=1,
        estimated_duration=10
    )
    test_db.add(recommendation)
    test_db.commit()
    test_db.refresh(recommendation)
    
    # Try to access with test_user's token
    access_token = create_access_token(data={"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.get(f"/recommendations/{recommendation.id}", headers=headers)
    assert response.status_code == 404  # Should not find it
