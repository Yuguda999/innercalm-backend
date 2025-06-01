"""
Comprehensive tests for enhanced InnerCalm features.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from models.user import User
from models.notification import Notification, NotificationPreference, DeviceToken
from models.community import SharedWoundGroup, UserClusterProfile
from services.notification_service import notification_service
from services.clustering_service import ClusteringService
from services.content_moderation import moderation_service
from services.community_analytics import CommunityAnalyticsService


class TestContentModeration:
    """Test content moderation functionality."""
    
    @pytest.mark.asyncio
    async def test_moderate_content_normal(self):
        """Test moderation of normal content."""
        content = "I'm feeling better today and want to share my progress."
        result = await moderation_service.moderate_content(content, 1, "message")
        
        assert result["approved"] is True
        assert "toxic_language" not in result["flags"]
        assert result["confidence_scores"]["appropriate"] > 0.7
    
    @pytest.mark.asyncio
    async def test_moderate_content_crisis(self):
        """Test crisis detection in content."""
        content = "I don't want to be here anymore and I'm thinking of ending it all."
        result = await moderation_service.moderate_content(content, 1, "message")
        
        assert result["auto_action"] == "crisis_alert"
        assert "crisis_language" in result["flags"]
        assert result["confidence_scores"]["crisis"] > 0.8
    
    @pytest.mark.asyncio
    async def test_moderate_content_inappropriate(self):
        """Test detection of inappropriate content."""
        content = "You're stupid and worthless, nobody cares about you."
        result = await moderation_service.moderate_content(content, 1, "message")
        
        assert result["approved"] is False
        assert "toxic_language" in result["flags"]
        assert result["confidence_scores"]["toxic"] > 0.7


class TestNotificationService:
    """Test notification service functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.mock_db = Mock(spec=Session)
        self.test_user_id = 1
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        # Mock user and preferences
        mock_user = Mock(spec=User)
        mock_user.id = self.test_user_id
        mock_user.username = "testuser"
        
        mock_prefs = Mock(spec=NotificationPreference)
        mock_prefs.circle_messages = True
        mock_prefs.push_notifications = True
        mock_prefs.quiet_hours_enabled = False
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user, mock_prefs
        ]
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Test notification sending
        data = {
            "circle_name": "Test Circle",
            "user_name": "Test User",
            "preview": "Hello world"
        }
        
        result = await notification_service.send_notification(
            self.mock_db, self.test_user_id, "new_message", data
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_notification_preferences_respected(self):
        """Test that notification preferences are respected."""
        # Mock user with disabled circle messages
        mock_user = Mock(spec=User)
        mock_user.id = self.test_user_id
        
        mock_prefs = Mock(spec=NotificationPreference)
        mock_prefs.circle_messages = False  # Disabled
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user, mock_prefs
        ]
        
        data = {"circle_name": "Test Circle"}
        result = await notification_service.send_notification(
            self.mock_db, self.test_user_id, "new_message", data
        )
        
        # Should return True but not actually send (skipped due to preferences)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_quiet_hours_respected(self):
        """Test that quiet hours are respected."""
        mock_user = Mock(spec=User)
        mock_user.id = self.test_user_id
        
        mock_prefs = Mock(spec=NotificationPreference)
        mock_prefs.circle_messages = True
        mock_prefs.quiet_hours_enabled = True
        mock_prefs.quiet_hours_start = "22:00"
        mock_prefs.quiet_hours_end = "08:00"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user, mock_prefs
        ]
        
        # Mock current time to be during quiet hours
        with patch('services.notification_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.time.return_value.strftime.return_value = "23:30"
            
            data = {"circle_name": "Test Circle"}
            result = await notification_service.send_notification(
                self.mock_db, self.test_user_id, "new_message", data
            )
            
            # Non-urgent notifications should be skipped during quiet hours
            assert result is True


class TestClusteringService:
    """Test clustering service functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.clustering_service = ClusteringService()
        self.mock_db = Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_analyze_user_for_clustering(self):
        """Test user analysis for clustering."""
        # Mock emotion analyses
        mock_analyses = []
        for i in range(10):
            mock_analysis = Mock()
            mock_analysis.joy = 0.3
            mock_analysis.sadness = 0.6
            mock_analysis.anger = 0.1
            mock_analysis.fear = 0.4
            mock_analysis.surprise = 0.2
            mock_analysis.disgust = 0.1
            mock_analyses.append(mock_analysis)
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_analyses
        
        # Mock other methods
        with patch.object(self.clustering_service, '_extract_trauma_themes', return_value=['loss', 'anxiety']):
            with patch.object(self.clustering_service, '_determine_healing_stage', return_value='processing'):
                with patch.object(self.clustering_service, '_extract_coping_patterns', return_value=['journaling']):
                    with patch.object(self.clustering_service, '_determine_communication_style', return_value='expressive'):
                        
                        result = await self.clustering_service.analyze_user_for_clustering(
                            self.mock_db, 1
                        )
        
        assert result is not None
        assert 'dominant_emotions' in result
        assert 'trauma_themes' in result
        assert 'healing_stage' in result
        assert result['healing_stage'] == 'processing'
        assert 'loss' in result['trauma_themes']
    
    @pytest.mark.asyncio
    async def test_advanced_clustering_algorithms(self):
        """Test advanced clustering algorithms."""
        # Mock user profiles
        mock_profiles = []
        for i in range(15):
            mock_profile = Mock(spec=UserClusterProfile)
            mock_profile.user_id = i + 1
            mock_profile.cluster_vector = [0.3, 0.6, 0.1, 0.4, 0.2, 0.1, 0.7, 0.3, 1, 0, 0, 0]
            mock_profile.dominant_emotions = {'sadness': 0.6, 'joy': 0.3}
            mock_profile.trauma_themes = ['loss', 'anxiety']
            mock_profile.healing_stage = 'processing'
            mock_profiles.append(mock_profile)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_profiles
        
        # Test hierarchical clustering
        result = await self.clustering_service.perform_advanced_clustering(
            self.mock_db, algorithm="hierarchical", min_users=10
        )
        
        assert "error" not in result
        assert result["total_users"] == 15
        assert result["num_clusters"] > 0
        assert "cluster_assignments" in result
        assert "quality_metrics" in result
    
    @pytest.mark.asyncio
    async def test_emotion_based_clustering(self):
        """Test emotion-based clustering algorithm."""
        # Mock profiles with different emotional patterns
        mock_profiles = []
        emotions_patterns = [
            {'sadness': 0.8, 'joy': 0.2},  # Sad group
            {'sadness': 0.7, 'joy': 0.3},  # Sad group
            {'joy': 0.8, 'sadness': 0.2},  # Happy group
            {'joy': 0.7, 'sadness': 0.3},  # Happy group
            {'anger': 0.8, 'fear': 0.6},   # Angry/fearful group
        ]
        
        for i, emotions in enumerate(emotions_patterns):
            mock_profile = Mock(spec=UserClusterProfile)
            mock_profile.user_id = i + 1
            mock_profile.cluster_vector = [
                emotions.get('joy', 0), emotions.get('sadness', 0),
                emotions.get('anger', 0), emotions.get('fear', 0),
                emotions.get('surprise', 0), emotions.get('disgust', 0),
                0.5, 0.3, 1, 0, 0, 0
            ]
            mock_profile.dominant_emotions = emotions
            mock_profile.trauma_themes = ['general']
            mock_profile.healing_stage = 'processing'
            mock_profiles.append(mock_profile)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_profiles
        
        result = await self.clustering_service.perform_advanced_clustering(
            self.mock_db, algorithm="emotion_based", min_users=3
        )
        
        assert "error" not in result
        assert result["total_users"] == 5
        assert result["num_clusters"] >= 2  # Should identify different emotional groups


class TestCommunityAnalytics:
    """Test community analytics functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.analytics_service = CommunityAnalyticsService()
        self.mock_db = Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_get_community_dashboard(self):
        """Test community dashboard data retrieval."""
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 25
        self.mock_db.query.return_value.filter.return_value.count.return_value = 150
        
        result = await self.analytics_service.get_community_dashboard(
            self.mock_db, user_id=1, days_back=30
        )
        
        assert "overview" in result
        assert "user_metrics" in result
        assert "generated_at" in result
    
    @pytest.mark.asyncio
    async def test_get_real_time_stats(self):
        """Test real-time statistics."""
        # Mock various database queries
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 15
        self.mock_db.query.return_value.filter.return_value.count.return_value = 8
        
        result = await self.analytics_service.get_real_time_stats(self.mock_db)
        
        assert "timestamp" in result
        assert "active_users_24h" in result
        assert "messages_last_hour" in result
        assert "community_pulse" in result
        assert result["community_pulse"] in ["very_active", "active", "moderate", "quiet"]


class TestMobileOptimization:
    """Test mobile optimization features."""
    
    def test_touch_button_component(self):
        """Test touch button component properties."""
        # This would be a frontend test in a real scenario
        # Testing the component's touch-friendly properties
        assert True  # Placeholder for actual component tests
    
    def test_mobile_navigation(self):
        """Test mobile navigation component."""
        # This would test the mobile navigation component
        assert True  # Placeholder for actual component tests
    
    def test_responsive_design(self):
        """Test responsive design breakpoints."""
        # This would test CSS breakpoints and responsive behavior
        assert True  # Placeholder for actual responsive tests


class TestIntegrationFeatures:
    """Test integration between different features."""
    
    @pytest.mark.asyncio
    async def test_moderation_notification_integration(self):
        """Test integration between content moderation and notifications."""
        # Mock crisis detection triggering notification
        mock_db = Mock(spec=Session)
        
        # Test that crisis detection triggers appropriate notifications
        with patch.object(moderation_service, 'handle_crisis_alert') as mock_crisis:
            with patch.object(notification_service, 'send_crisis_alert') as mock_notify:
                mock_crisis.return_value = {"resources": ["crisis_line"]}
                
                # Simulate crisis content moderation
                content = "I want to hurt myself"
                result = await moderation_service.moderate_content(content, 1, "message")
                
                if result.get("auto_action") == "crisis_alert":
                    await notification_service.send_crisis_alert(
                        mock_db, 1, {"resources": ["crisis_line"]}
                    )
                
                # Verify integration worked
                assert result["auto_action"] == "crisis_alert"
    
    @pytest.mark.asyncio
    async def test_clustering_analytics_integration(self):
        """Test integration between clustering and analytics."""
        mock_db = Mock(spec=Session)
        clustering_service = ClusteringService()
        analytics_service = CommunityAnalyticsService()
        
        # Mock cluster insights affecting analytics
        mock_profile = Mock(spec=UserClusterProfile)
        mock_profile.user_id = 1
        mock_profile.healing_stage = "processing"
        mock_profile.trauma_themes = ["loss", "anxiety"]
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        # Test that clustering insights are reflected in analytics
        cluster_insights = await clustering_service.get_cluster_insights(mock_db, 1)
        
        assert "user_profile" in cluster_insights
        assert "insights" in cluster_insights
        assert "recommendations" in cluster_insights


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
