"""
Tests for analytics API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.analytics import (
    AnalyticsEvent, AnalyticsEventType,
    MoodTrend, MoodTrendType,
    ProgressInsight,
    ConversationAnalytics,
    UserProgressMetrics
)
from models.emotion import EmotionAnalysis
from models.conversation import Conversation, Message


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    @pytest.fixture
    def analytics_data(self, db: Session, test_user, test_conversation):
        """Create comprehensive analytics test data."""
        # Create emotion analyses
        emotions = []
        base_time = datetime.now() - timedelta(days=7)
        for i in range(7):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.1 + (i * 0.1),
                sadness=0.7 - (i * 0.08),
                anger=0.2,
                fear=0.3,
                surprise=0.1,
                disgust=0.1,
                sentiment_score=-0.4 + (i * 0.1),
                sentiment_label="negative" if i < 4 else "positive",
                themes=["stress"] if i < 4 else ["hope"],
                keywords=["difficult"] if i < 4 else ["better"],
                confidence=0.8,
                analyzed_at=base_time + timedelta(days=i)
            )
            db.add(emotion)
            emotions.append(emotion)
        
        # Create analytics events
        events = []
        for i in range(3):
            event = AnalyticsEvent(
                user_id=test_user.id,
                conversation_id=test_conversation.id,
                event_type=AnalyticsEventType.CONVERSATION_START.value,
                event_name=f"Test Event {i}",
                event_description=f"Test event description {i}",
                event_data={"test": f"data_{i}"},
                emotion_snapshot={"joy": 0.5, "sadness": 0.3},
                severity="normal",
                event_timestamp=base_time + timedelta(days=i)
            )
            db.add(event)
            events.append(event)
        
        # Create mood trend
        mood_trend = MoodTrend(
            user_id=test_user.id,
            trend_type=MoodTrendType.IMPROVING.value,
            trend_strength=0.7,
            trend_duration_days=7,
            dominant_emotion="joy",
            emotion_stability=0.8,
            average_sentiment=0.2,
            emotion_progression=[
                {"timestamp": (base_time + timedelta(days=i)).isoformat(), "sentiment": -0.4 + (i * 0.1)}
                for i in range(7)
            ],
            key_events=[{"type": "improvement", "timestamp": base_time.isoformat()}],
            start_date=base_time,
            end_date=base_time + timedelta(days=7)
        )
        db.add(mood_trend)
        
        # Create progress insights
        insight = ProgressInsight(
            user_id=test_user.id,
            insight_type="pattern",
            insight_title="Positive Progress Pattern",
            insight_description="You've been showing consistent improvement",
            supporting_data={"improvement_rate": 0.7},
            confidence_score=0.8,
            impact_level="high",
            is_actionable=True,
            suggested_actions=["Continue current practices", "Build on successes"],
            data_period_start=base_time,
            data_period_end=base_time + timedelta(days=7)
        )
        db.add(insight)
        
        # Create conversation analytics
        conv_analytics = ConversationAnalytics(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            total_messages=10,
            user_messages=5,
            ai_messages=5,
            conversation_duration_minutes=30.0,
            emotion_trajectory=[
                {"timestamp": base_time.isoformat(), "sentiment": 0.2}
            ],
            emotional_range=0.5,
            dominant_emotions=["joy", "hope"],
            therapeutic_approach_used="person_centered",
            engagement_score=0.8,
            empathy_score=0.9,
            mood_change=0.3,
            conversation_start=base_time,
            conversation_end=base_time + timedelta(minutes=30)
        )
        db.add(conv_analytics)
        
        # Create progress metrics
        progress_metrics = UserProgressMetrics(
            user_id=test_user.id,
            period_type="weekly",
            period_start=base_time,
            period_end=base_time + timedelta(days=7),
            total_conversations=3,
            total_messages=15,
            average_session_duration=25.0,
            engagement_consistency=0.7,
            average_mood_score=0.2,
            mood_stability=0.8,
            emotional_growth_score=0.7,
            recommendations_completed=2,
            recommendations_completion_rate=0.8,
            therapeutic_engagement_score=0.75,
            crisis_episodes=0,
            breakthrough_moments=2,
            overall_progress_score=0.8
        )
        db.add(progress_metrics)
        
        db.commit()
        
        return {
            "emotions": emotions,
            "events": events,
            "mood_trend": mood_trend,
            "insight": insight,
            "conv_analytics": conv_analytics,
            "progress_metrics": progress_metrics
        }

    def test_get_analytics_dashboard(self, client: TestClient, auth_headers, analytics_data):
        """Test analytics dashboard endpoint."""
        response = client.get("/analytics/dashboard?days_back=30", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "analysis_period_days" in data
        assert "progress_metrics" in data
        assert "mood_trend" in data
        assert "recent_insights" in data
        assert "recent_events" in data
        assert "conversation_summary" in data
        
        # Verify progress metrics structure
        progress = data["progress_metrics"]
        assert "overall_progress_score" in progress
        assert "emotional_growth_score" in progress
        assert "mood_stability" in progress
        assert "engagement_consistency" in progress
        
        # Verify mood trend structure
        if data["mood_trend"]:
            mood = data["mood_trend"]
            assert "trend_type" in mood
            assert "trend_strength" in mood
            assert "dominant_emotion" in mood

    def test_get_mood_trends(self, client: TestClient, auth_headers, analytics_data):
        """Test mood trends endpoint."""
        response = client.get("/analytics/mood-trends?days_back=14", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trend_analysis" in data
        assert "emotion_progression" in data
        assert "key_events" in data
        assert "analysis_period" in data
        
        trend = data["trend_analysis"]
        assert "trend_type" in trend
        assert "trend_strength" in trend
        assert "dominant_emotion" in trend
        assert "emotion_stability" in trend
        assert "average_sentiment" in trend

    def test_get_mood_trends_insufficient_data(self, client: TestClient, auth_headers, db: Session, test_user):
        """Test mood trends with insufficient data."""
        # Clear existing data
        db.query(EmotionAnalysis).filter(EmotionAnalysis.user_id == test_user.id).delete()
        db.commit()
        
        response = client.get("/analytics/mood-trends?days_back=30", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "insufficient data" in data["message"].lower()

    def test_get_progress_insights(self, client: TestClient, auth_headers, analytics_data):
        """Test progress insights endpoint."""
        response = client.get("/analytics/insights?limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        insight = data[0]
        assert "id" in insight
        assert "type" in insight
        assert "title" in insight
        assert "description" in insight
        assert "confidence_score" in insight
        assert "impact_level" in insight
        assert "is_actionable" in insight
        assert "suggested_actions" in insight

    def test_get_progress_insights_filtered(self, client: TestClient, auth_headers, analytics_data):
        """Test progress insights with type filter."""
        response = client.get("/analytics/insights?insight_type=pattern&limit=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for insight in data:
            assert insight["type"] == "pattern"

    def test_acknowledge_insight(self, client: TestClient, auth_headers, analytics_data):
        """Test insight acknowledgment endpoint."""
        insight_id = analytics_data["insight"].id
        
        response = client.post(
            f"/analytics/insights/{insight_id}/acknowledge",
            json={"feedback": "This insight was very helpful"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "insight_id" in data
        assert "acknowledged_at" in data
        assert data["insight_id"] == insight_id

    def test_acknowledge_nonexistent_insight(self, client: TestClient, auth_headers):
        """Test acknowledging non-existent insight."""
        response = client.post(
            "/analytics/insights/99999/acknowledge",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_get_progress_metrics(self, client: TestClient, auth_headers, analytics_data):
        """Test progress metrics endpoint."""
        response = client.get("/analytics/progress-metrics?period_type=weekly", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_info" in data
        assert "engagement_metrics" in data
        assert "emotional_metrics" in data
        assert "therapeutic_metrics" in data
        assert "progress_indicators" in data
        
        # Verify period info
        period = data["period_info"]
        assert period["type"] == "weekly"
        assert "start_date" in period
        assert "end_date" in period
        
        # Verify engagement metrics
        engagement = data["engagement_metrics"]
        assert "total_conversations" in engagement
        assert "total_messages" in engagement
        assert "average_session_duration" in engagement
        
        # Verify emotional metrics
        emotional = data["emotional_metrics"]
        assert "average_mood_score" in emotional
        assert "mood_stability" in emotional
        assert "emotional_growth_score" in emotional

    def test_get_progress_metrics_invalid_period(self, client: TestClient, auth_headers):
        """Test progress metrics with invalid period type."""
        response = client.get("/analytics/progress-metrics?period_type=invalid", headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    def test_get_conversation_analytics(self, client: TestClient, auth_headers, analytics_data, test_conversation):
        """Test conversation analytics endpoint."""
        conversation_id = test_conversation.id
        
        response = client.get(f"/analytics/conversation-analytics/{conversation_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "conversation_id" in data
        assert "message_metrics" in data
        assert "emotional_journey" in data
        assert "therapeutic_analysis" in data
        assert "quality_metrics" in data
        assert "outcomes" in data
        assert "timeline" in data
        
        # Verify message metrics
        messages = data["message_metrics"]
        assert "total_messages" in messages
        assert "user_messages" in messages
        assert "ai_messages" in messages
        
        # Verify emotional journey
        emotional = data["emotional_journey"]
        assert "emotion_trajectory" in emotional
        assert "emotional_range" in emotional
        assert "dominant_emotions" in emotional

    def test_get_conversation_analytics_not_found(self, client: TestClient, auth_headers):
        """Test conversation analytics for non-existent conversation."""
        response = client.get("/analytics/conversation-analytics/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_analytics_dashboard_parameters(self, client: TestClient, auth_headers, analytics_data):
        """Test analytics dashboard with different parameters."""
        # Test with different days_back values
        for days in [7, 14, 30, 90]:
            response = client.get(f"/analytics/dashboard?days_back={days}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_period_days"] == days

    def test_analytics_endpoints_authentication(self, client: TestClient):
        """Test that analytics endpoints require authentication."""
        endpoints = [
            "/analytics/dashboard",
            "/analytics/mood-trends",
            "/analytics/insights",
            "/analytics/progress-metrics",
            "/analytics/conversation-analytics/1"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_analytics_data_isolation(self, client: TestClient, auth_headers, db: Session, analytics_data):
        """Test that users can only access their own analytics data."""
        # Create another user
        from models.user import User
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            full_name="Other User"
        )
        db.add(other_user)
        db.commit()
        
        # Create analytics data for other user
        other_insight = ProgressInsight(
            user_id=other_user.id,
            insight_type="pattern",
            insight_title="Other User Insight",
            insight_description="This should not be visible",
            confidence_score=0.8,
            impact_level="high",
            data_period_start=datetime.now() - timedelta(days=7),
            data_period_end=datetime.now()
        )
        db.add(other_insight)
        db.commit()
        
        # Test that current user doesn't see other user's data
        response = client.get("/analytics/insights", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should not contain other user's insight
        insight_titles = [insight["title"] for insight in data]
        assert "Other User Insight" not in insight_titles

    def test_analytics_error_handling(self, client: TestClient, auth_headers):
        """Test analytics endpoints error handling."""
        # Test with invalid parameters
        response = client.get("/analytics/mood-trends?days_back=0", headers=auth_headers)
        assert response.status_code == 422
        
        response = client.get("/analytics/insights?limit=0", headers=auth_headers)
        assert response.status_code == 422
        
        response = client.get("/analytics/insights?limit=100", headers=auth_headers)
        assert response.status_code == 422
