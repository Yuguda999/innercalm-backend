"""
Integration tests for enhanced LangGraph workflow and advanced analytics.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.analytics import AnalyticsEvent, AnalyticsEventType
from models.emotion import EmotionAnalysis
from models.conversation import Conversation, Message
from services.analytics_service import AnalyticsService


class TestEnhancedIntegration:
    """Integration tests for enhanced features."""

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service instance."""
        return AnalyticsService()

    @patch('services.ai_chat.ChatOpenAI')
    async def test_full_conversation_with_analytics_tracking(
        self, 
        mock_openai, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user,
        analytics_service
    ):
        """Test complete conversation flow with analytics tracking."""
        # Mock OpenAI responses
        mock_response = Mock()
        mock_response.content = "I understand you're feeling overwhelmed. Let's work through this together."
        mock_openai.return_value.invoke.return_value = mock_response
        
        # Start a conversation
        conversation_data = {
            "message": "I'm feeling really stressed and overwhelmed with work lately"
        }
        
        response = client.post("/chat/", json=conversation_data, headers=auth_headers)
        assert response.status_code == 200
        
        chat_response = response.json()
        conversation_id = chat_response["conversation_id"]
        
        # Verify analytics events were created
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id,
            AnalyticsEvent.conversation_id == conversation_id
        ).all()
        
        assert len(events) > 0
        
        # Should have conversation start event
        start_events = [e for e in events if e.event_type == AnalyticsEventType.CONVERSATION_START.value]
        assert len(start_events) == 1
        
        # Continue the conversation with multiple messages
        follow_up_messages = [
            "I can't sleep at night because I keep thinking about deadlines",
            "Sometimes I feel like I'm not good enough at my job",
            "I've been having panic attacks when I think about going to work"
        ]
        
        for message in follow_up_messages:
            response = client.post("/chat/", json={
                "message": message,
                "conversation_id": conversation_id
            }, headers=auth_headers)
            assert response.status_code == 200
        
        # Check for emotion peak events
        emotion_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id,
            AnalyticsEvent.event_type == AnalyticsEventType.EMOTION_PEAK.value
        ).all()
        
        # Should have detected high emotion levels
        assert len(emotion_events) > 0
        
        # Get analytics dashboard
        dashboard_response = client.get("/analytics/dashboard?days_back=7", headers=auth_headers)
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert dashboard_data["progress_metrics"]["overall_progress_score"] >= 0
        assert len(dashboard_data["recent_events"]) > 0
        assert len(dashboard_data["conversation_summary"]) > 0

    @patch('services.ai_chat.ChatOpenAI')
    async def test_crisis_detection_and_analytics(
        self, 
        mock_openai, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user
    ):
        """Test crisis detection with analytics tracking."""
        # Mock crisis intervention response
        mock_response = Mock()
        mock_response.content = "I'm really concerned about what you're sharing. Please reach out for help."
        mock_openai.return_value.invoke.return_value = mock_response
        
        # Send a message with crisis indicators
        crisis_message = {
            "message": "I don't want to live anymore. I'm thinking about ending it all."
        }
        
        response = client.post("/chat/", json=crisis_message, headers=auth_headers)
        assert response.status_code == 200
        
        chat_response = response.json()
        conversation_id = chat_response["conversation_id"]
        
        # Verify crisis event was tracked
        crisis_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id,
            AnalyticsEvent.event_type == AnalyticsEventType.CRISIS_DETECTED.value
        ).all()
        
        assert len(crisis_events) > 0
        
        crisis_event = crisis_events[0]
        assert crisis_event.severity == "high"
        assert crisis_event.conversation_id == conversation_id
        
        # Check analytics dashboard reflects crisis
        dashboard_response = client.get("/analytics/dashboard", headers=auth_headers)
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert dashboard_data["progress_metrics"]["crisis_episodes"] > 0
        
        # Check that insights are generated about the crisis
        insights_response = client.get("/analytics/insights", headers=auth_headers)
        assert insights_response.status_code == 200
        
        insights = insights_response.json()
        concern_insights = [i for i in insights if i["type"] == "concern"]
        assert len(concern_insights) > 0

    async def test_mood_trend_analysis_over_time(
        self, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user,
        analytics_service
    ):
        """Test mood trend analysis with historical data."""
        # Create historical emotion data showing improvement over time
        base_time = datetime.now() - timedelta(days=14)
        
        for i in range(14):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.1 + (i * 0.05),  # Gradually increasing
                sadness=0.8 - (i * 0.04),  # Gradually decreasing
                anger=0.2,
                fear=0.3 - (i * 0.01),  # Slightly decreasing
                surprise=0.1,
                disgust=0.1,
                sentiment_score=-0.6 + (i * 0.08),  # Improving sentiment
                sentiment_label="negative" if i < 7 else "positive",
                themes=["stress", "anxiety"] if i < 7 else ["hope", "progress"],
                keywords=["difficult", "hard"] if i < 7 else ["better", "improving"],
                confidence=0.8,
                analyzed_at=base_time + timedelta(days=i)
            )
            db.add(emotion)
        
        db.commit()
        
        # Analyze mood trends
        mood_trend = await analytics_service.analyze_mood_trends(db, test_user.id, 14)
        assert mood_trend is not None
        assert mood_trend.trend_type == "improving"
        assert mood_trend.trend_strength > 0.5
        
        # Get mood trends via API
        trends_response = client.get("/analytics/mood-trends?days_back=14", headers=auth_headers)
        assert trends_response.status_code == 200
        
        trends_data = trends_response.json()
        assert trends_data["trend_analysis"]["trend_type"] == "improving"
        assert len(trends_data["emotion_progression"]) == 14
        
        # Generate insights based on the trend
        insights = await analytics_service.generate_progress_insights(db, test_user.id)
        pattern_insights = [i for i in insights if i.insight_type == "pattern"]
        
        # Should detect the improvement pattern
        improvement_insights = [
            i for i in pattern_insights 
            if "improvement" in i.insight_title.lower() or "positive" in i.insight_title.lower()
        ]
        assert len(improvement_insights) > 0

    async def test_conversation_analytics_generation(
        self, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user,
        analytics_service
    ):
        """Test detailed conversation analytics generation."""
        # Create a conversation with messages
        conversation = Conversation(
            user_id=test_user.id,
            title="Test Therapy Session",
            created_at=datetime.now() - timedelta(hours=1)
        )
        db.add(conversation)
        db.commit()
        
        # Create messages with timestamps
        messages_data = [
            ("I'm feeling really anxious about my presentation tomorrow", True),
            ("I understand that presentations can be nerve-wracking. What specifically worries you?", False),
            ("I'm afraid I'll forget what to say and embarrass myself", True),
            ("That's a common fear. Let's work on some strategies to help you feel more confident.", False),
            ("What kind of strategies? I've tried practicing but I still feel nervous", True),
            ("We can try some breathing exercises and positive visualization techniques.", False)
        ]
        
        base_time = conversation.created_at
        for i, (content, is_user) in enumerate(messages_data):
            message = Message(
                conversation_id=conversation.id,
                content=content,
                is_user_message=is_user,
                timestamp=base_time + timedelta(minutes=i*2)
            )
            db.add(message)
        
        db.commit()
        
        # Create emotion analyses for user messages
        user_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.is_user_message == True
        ).all()
        
        emotion_values = [
            {"joy": 0.1, "sadness": 0.2, "anger": 0.1, "fear": 0.8, "sentiment": -0.3},
            {"joy": 0.1, "sadness": 0.3, "anger": 0.2, "fear": 0.7, "sentiment": -0.2},
            {"joy": 0.2, "sadness": 0.2, "anger": 0.1, "fear": 0.6, "sentiment": -0.1}
        ]
        
        for msg, emotions in zip(user_messages, emotion_values):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                message_id=msg.id,
                joy=emotions["joy"],
                sadness=emotions["sadness"],
                anger=emotions["anger"],
                fear=emotions["fear"],
                surprise=0.0,
                disgust=0.0,
                sentiment_score=emotions["sentiment"],
                sentiment_label="negative" if emotions["sentiment"] < 0 else "positive",
                themes=["anxiety", "performance"],
                keywords=["nervous", "afraid"],
                confidence=0.8,
                analyzed_at=msg.timestamp
            )
            db.add(emotion)
        
        db.commit()
        
        # Analyze the conversation
        conv_analytics = await analytics_service.analyze_conversation(db, conversation.id)
        assert conv_analytics is not None
        assert conv_analytics.total_messages == 6
        assert conv_analytics.user_messages == 3
        assert conv_analytics.ai_messages == 3
        assert conv_analytics.engagement_score > 0
        assert len(conv_analytics.emotion_trajectory) == 3
        
        # Get conversation analytics via API
        analytics_response = client.get(
            f"/analytics/conversation-analytics/{conversation.id}", 
            headers=auth_headers
        )
        assert analytics_response.status_code == 200
        
        analytics_data = analytics_response.json()
        assert analytics_data["conversation_id"] == conversation.id
        assert analytics_data["message_metrics"]["total_messages"] == 6
        assert len(analytics_data["emotional_journey"]["emotion_trajectory"]) == 3

    async def test_progress_metrics_calculation(
        self, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user,
        analytics_service
    ):
        """Test comprehensive progress metrics calculation."""
        # Create data for the past week
        base_time = datetime.now() - timedelta(days=7)
        
        # Create conversations
        conversations = []
        for i in range(3):
            conv = Conversation(
                user_id=test_user.id,
                title=f"Session {i+1}",
                created_at=base_time + timedelta(days=i*2)
            )
            db.add(conv)
            conversations.append(conv)
        
        db.commit()
        
        # Create messages for conversations
        total_messages = 0
        for conv in conversations:
            for j in range(4):  # 4 messages per conversation
                message = Message(
                    conversation_id=conv.id,
                    content=f"Message {j+1} in conversation {conv.id}",
                    is_user_message=j % 2 == 0,
                    timestamp=conv.created_at + timedelta(minutes=j*5)
                )
                db.add(message)
                total_messages += 1
        
        db.commit()
        
        # Create emotion analyses showing improvement
        emotions = []
        for i, conv in enumerate(conversations):
            emotion = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.2 + (i * 0.2),  # Improving joy
                sadness=0.6 - (i * 0.15),  # Decreasing sadness
                anger=0.1,
                fear=0.3 - (i * 0.1),  # Decreasing fear
                surprise=0.1,
                disgust=0.0,
                sentiment_score=-0.3 + (i * 0.25),  # Improving sentiment
                sentiment_label="negative" if i == 0 else "positive",
                themes=["progress", "hope"] if i > 0 else ["stress"],
                keywords=["better"] if i > 0 else ["difficult"],
                confidence=0.8,
                analyzed_at=conv.created_at
            )
            db.add(emotion)
            emotions.append(emotion)
        
        db.commit()
        
        # Calculate progress metrics
        metrics = await analytics_service.calculate_user_progress_metrics(
            db, test_user.id, "weekly"
        )
        
        assert metrics is not None
        assert metrics.total_conversations == 3
        assert metrics.total_messages == total_messages
        assert metrics.emotional_growth_score > 0.5  # Should show improvement
        assert metrics.overall_progress_score > 0.5
        
        # Get progress metrics via API
        metrics_response = client.get(
            "/analytics/progress-metrics?period_type=weekly", 
            headers=auth_headers
        )
        assert metrics_response.status_code == 200
        
        metrics_data = metrics_response.json()
        assert metrics_data["engagement_metrics"]["total_conversations"] == 3
        assert metrics_data["emotional_metrics"]["emotional_growth_score"] > 0.5
        assert metrics_data["progress_indicators"]["overall_progress_score"] > 0.5

    async def test_insight_acknowledgment_workflow(
        self, 
        client: TestClient, 
        auth_headers, 
        db: Session, 
        test_user,
        analytics_service
    ):
        """Test the complete insight generation and acknowledgment workflow."""
        # Generate insights
        insights = await analytics_service.generate_progress_insights(db, test_user.id)
        
        if insights:
            insight = insights[0]
            
            # Get insights via API
            insights_response = client.get("/analytics/insights", headers=auth_headers)
            assert insights_response.status_code == 200
            
            insights_data = insights_response.json()
            api_insight = next(i for i in insights_data if i["id"] == insight.id)
            
            assert not api_insight["is_acknowledged"]
            
            # Acknowledge the insight
            ack_response = client.post(
                f"/analytics/insights/{insight.id}/acknowledge",
                json={"feedback": "This insight helped me understand my progress better"},
                headers=auth_headers
            )
            assert ack_response.status_code == 200
            
            # Verify acknowledgment
            insights_response = client.get("/analytics/insights", headers=auth_headers)
            insights_data = insights_response.json()
            api_insight = next(i for i in insights_data if i["id"] == insight.id)
            
            assert api_insight["is_acknowledged"]
            assert api_insight["user_feedback"] == "This insight helped me understand my progress better"
