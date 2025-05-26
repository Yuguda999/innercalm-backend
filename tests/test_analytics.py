"""
Tests for analytics functionality.
"""
import pytest
from datetime import datetime, timedelta
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
from services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test analytics service functionality."""

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service instance."""
        return AnalyticsService()

    @pytest.fixture
    def sample_emotions(self, db: Session, test_user):
        """Create sample emotion analyses for testing."""
        emotions = []
        base_time = datetime.now() - timedelta(days=10)
        
        for i in range(10):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.1 + (i * 0.05),  # Gradually increasing joy
                sadness=0.8 - (i * 0.05),  # Gradually decreasing sadness
                anger=0.2,
                fear=0.3,
                surprise=0.1,
                disgust=0.1,
                sentiment_score=-0.5 + (i * 0.1),  # Improving sentiment
                sentiment_label="negative" if i < 5 else "positive",
                themes=["stress", "work"] if i < 5 else ["hope", "progress"],
                keywords=["difficult", "hard"] if i < 5 else ["better", "improving"],
                confidence=0.8,
                analyzed_at=base_time + timedelta(days=i)
            )
            db.add(emotion)
            emotions.append(emotion)
        
        db.commit()
        return emotions

    async def test_track_event(self, analytics_service, db: Session, test_user):
        """Test event tracking functionality."""
        event = await analytics_service.track_event(
            db=db,
            user_id=test_user.id,
            event_type=AnalyticsEventType.CONVERSATION_START.value,
            event_name="Test Conversation Started",
            event_data={"test": "data"},
            emotion_snapshot={"joy": 0.5, "sadness": 0.3},
            severity="normal"
        )
        
        assert event.id is not None
        assert event.user_id == test_user.id
        assert event.event_type == AnalyticsEventType.CONVERSATION_START.value
        assert event.event_name == "Test Conversation Started"
        assert event.event_data == {"test": "data"}
        assert event.emotion_snapshot == {"joy": 0.5, "sadness": 0.3}
        assert event.severity == "normal"

    async def test_analyze_mood_trends(self, analytics_service, db: Session, test_user, sample_emotions):
        """Test mood trend analysis."""
        mood_trend = await analytics_service.analyze_mood_trends(
            db=db,
            user_id=test_user.id,
            days_back=15
        )
        
        assert mood_trend is not None
        assert mood_trend.user_id == test_user.id
        assert mood_trend.trend_type == MoodTrendType.IMPROVING.value
        assert mood_trend.trend_strength > 0
        assert mood_trend.dominant_emotion in ["joy", "sadness", "anger", "fear"]
        assert mood_trend.emotion_stability >= 0
        assert mood_trend.emotion_stability <= 1
        assert len(mood_trend.emotion_progression) > 0

    async def test_analyze_mood_trends_insufficient_data(self, analytics_service, db: Session, test_user):
        """Test mood trend analysis with insufficient data."""
        mood_trend = await analytics_service.analyze_mood_trends(
            db=db,
            user_id=test_user.id,
            days_back=30
        )
        
        assert mood_trend is None

    async def test_generate_progress_insights(self, analytics_service, db: Session, test_user, sample_emotions):
        """Test progress insight generation."""
        insights = await analytics_service.generate_progress_insights(
            db=db,
            user_id=test_user.id,
            insight_types=["pattern", "breakthrough"]
        )
        
        assert isinstance(insights, list)
        # Should generate at least one insight for the improving pattern
        assert len(insights) > 0
        
        for insight in insights:
            assert insight.user_id == test_user.id
            assert insight.insight_type in ["pattern", "breakthrough"]
            assert insight.confidence_score >= 0
            assert insight.confidence_score <= 1
            assert insight.impact_level in ["low", "medium", "high"]

    async def test_analyze_conversation(self, analytics_service, db: Session, test_user, test_conversation):
        """Test conversation analysis."""
        # Create some messages for the conversation
        messages = []
        for i in range(5):
            message = Message(
                conversation_id=test_conversation.id,
                content=f"Test message {i}",
                is_user_message=i % 2 == 0,
                timestamp=datetime.now() - timedelta(minutes=10-i)
            )
            db.add(message)
            messages.append(message)
        
        db.commit()
        
        # Create emotion analyses for user messages
        user_messages = [m for m in messages if m.is_user_message]
        for msg in user_messages:
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                message_id=msg.id,
                joy=0.3,
                sadness=0.4,
                anger=0.1,
                fear=0.2,
                surprise=0.0,
                disgust=0.0,
                sentiment_score=0.1,
                sentiment_label="neutral",
                themes=["general"],
                keywords=["test"],
                confidence=0.8
            )
            db.add(emotion)
        
        db.commit()
        
        analytics = await analytics_service.analyze_conversation(
            db=db,
            conversation_id=test_conversation.id
        )
        
        assert analytics is not None
        assert analytics.conversation_id == test_conversation.id
        assert analytics.user_id == test_user.id
        assert analytics.total_messages == 5
        assert analytics.user_messages == 3
        assert analytics.ai_messages == 2
        assert analytics.engagement_score >= 0
        assert analytics.empathy_score >= 0
        assert len(analytics.emotion_trajectory) > 0

    async def test_calculate_user_progress_metrics(self, analytics_service, db: Session, test_user, sample_emotions):
        """Test user progress metrics calculation."""
        # Create a conversation for engagement metrics
        conversation = Conversation(
            user_id=test_user.id,
            title="Test Conversation",
            created_at=datetime.now() - timedelta(days=3)
        )
        db.add(conversation)
        db.commit()
        
        # Create some messages
        for i in range(5):
            message = Message(
                conversation_id=conversation.id,
                content=f"Test message {i}",
                is_user_message=i % 2 == 0,
                timestamp=datetime.now() - timedelta(days=3, minutes=i)
            )
            db.add(message)
        
        db.commit()
        
        metrics = await analytics_service.calculate_user_progress_metrics(
            db=db,
            user_id=test_user.id,
            period_type="weekly"
        )
        
        assert metrics is not None
        assert metrics.user_id == test_user.id
        assert metrics.period_type == "weekly"
        assert metrics.total_conversations >= 1
        assert metrics.total_messages >= 5
        assert metrics.average_mood_score >= -1
        assert metrics.average_mood_score <= 1
        assert metrics.mood_stability >= 0
        assert metrics.mood_stability <= 1
        assert metrics.overall_progress_score >= 0
        assert metrics.overall_progress_score <= 1

    def test_identify_emotion_patterns(self, analytics_service, sample_emotions):
        """Test emotion pattern identification."""
        patterns = analytics_service._identify_emotion_patterns(sample_emotions)
        
        assert isinstance(patterns, list)
        # Should identify the improving trend pattern
        pattern_titles = [p["title"] for p in patterns]
        assert any("Improvement" in title for title in pattern_titles)
        
        for pattern in patterns:
            assert "title" in pattern
            assert "description" in pattern
            assert "confidence" in pattern
            assert "impact" in pattern
            assert "actionable" in pattern
            assert pattern["confidence"] >= 0
            assert pattern["confidence"] <= 1

    def test_calculate_trend_slope(self, analytics_service):
        """Test trend slope calculation."""
        # Test improving trend
        x_values = [0, 1, 2, 3, 4]
        y_values = [0.0, 0.2, 0.4, 0.6, 0.8]
        slope = analytics_service._calculate_trend_slope(x_values, y_values)
        assert slope > 0
        
        # Test declining trend
        y_values_declining = [0.8, 0.6, 0.4, 0.2, 0.0]
        slope_declining = analytics_service._calculate_trend_slope(x_values, y_values_declining)
        assert slope_declining < 0
        
        # Test flat trend
        y_values_flat = [0.5, 0.5, 0.5, 0.5, 0.5]
        slope_flat = analytics_service._calculate_trend_slope(x_values, y_values_flat)
        assert abs(slope_flat) < 0.01

    def test_generate_event_tags(self, analytics_service):
        """Test event tag generation."""
        event_data = {
            "emotion": "sadness",
            "severity": "high",
            "therapeutic_approach": "cognitive_behavioral"
        }
        
        tags = analytics_service._generate_event_tags("emotion_peak", event_data)
        
        assert "emotion_peak" in tags
        assert "emotion_sadness" in tags
        assert "severity_high" in tags
        assert "approach_cognitive_behavioral" in tags

    async def test_pattern_insights_generation(self, analytics_service, db: Session, test_user):
        """Test pattern-specific insight generation."""
        # Create emotions showing persistent sadness
        base_time = datetime.now() - timedelta(days=14)
        for i in range(10):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.1,
                sadness=0.8,  # Consistently high sadness
                anger=0.1,
                fear=0.1,
                surprise=0.0,
                disgust=0.0,
                sentiment_score=-0.6,
                sentiment_label="negative",
                themes=["depression", "hopelessness"],
                keywords=["sad", "hopeless"],
                confidence=0.8,
                analyzed_at=base_time + timedelta(days=i)
            )
            db.add(emotion)
        
        db.commit()
        
        insights = await analytics_service._generate_pattern_insights(db, test_user.id)
        
        assert len(insights) > 0
        sadness_insights = [i for i in insights if "Sadness" in i.insight_title]
        assert len(sadness_insights) > 0
        
        sadness_insight = sadness_insights[0]
        assert sadness_insight.insight_type == "pattern"
        assert sadness_insight.is_actionable
        assert len(sadness_insight.suggested_actions) > 0
