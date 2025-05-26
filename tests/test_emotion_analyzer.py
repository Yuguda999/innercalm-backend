"""
Tests for emotion analysis functionality.
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from services.emotion_analyzer import EmotionAnalyzer
from models.emotion import EmotionAnalysis, EmotionPattern
from models.user import User


class TestEmotionAnalyzer:
    """Test EmotionAnalyzer functionality."""
    
    def setup_method(self):
        """Set up test instance."""
        self.analyzer = EmotionAnalyzer()
    
    def test_analyze_emotion_basic(self, test_user: User):
        """Test basic emotion analysis."""
        text = "I am feeling very sad and depressed today"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["user_id"] == test_user.id
        assert result["sadness"] > 0.3  # Should detect sadness
        assert result["sentiment_label"] == "negative"
        assert result["sentiment_score"] < 0
        assert result["confidence"] > 0
        assert "sad" in result["keywords"] or "depressed" in result["keywords"]
    
    def test_analyze_emotion_positive(self, test_user: User):
        """Test positive emotion analysis."""
        text = "I am so happy and joyful today! Everything is wonderful!"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["joy"] > 0.3  # Should detect joy
        assert result["sentiment_label"] == "positive"
        assert result["sentiment_score"] > 0
        assert "happy" in result["keywords"] or "joyful" in result["keywords"]
    
    def test_analyze_emotion_anger(self, test_user: User):
        """Test anger emotion analysis."""
        text = "I am so angry and frustrated with this situation!"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["anger"] > 0.3  # Should detect anger
        assert "angry" in result["keywords"] or "frustrated" in result["keywords"]
    
    def test_analyze_emotion_fear(self, test_user: User):
        """Test fear/anxiety emotion analysis."""
        text = "I am scared and anxious about what might happen"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["fear"] > 0.3  # Should detect fear
        assert "scared" in result["keywords"] or "anxious" in result["keywords"]
    
    def test_extract_themes_trauma(self, test_user: User):
        """Test trauma theme extraction."""
        text = "I keep having flashbacks and nightmares about the trauma"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert "trauma_related" in result["themes"]
    
    def test_extract_themes_relationships(self, test_user: User):
        """Test relationship theme extraction."""
        text = "My relationship with my partner is causing me stress"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert "relationships" in result["themes"]
    
    def test_extract_themes_work(self, test_user: User):
        """Test work/career theme extraction."""
        text = "My job is so stressful and my boss is demanding"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert "work_career" in result["themes"]
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        text = "  This   has   extra    spaces!!!   "
        cleaned = self.analyzer._preprocess_text(text)
        
        assert cleaned == "this has extra spaces!"
        assert "  " not in cleaned
    
    def test_detect_emotions_multiple(self, test_user: User):
        """Test detection of multiple emotions."""
        text = "I am sad but also angry about this situation"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["sadness"] > 0
        assert result["anger"] > 0
    
    def test_confidence_calculation(self, test_user: User):
        """Test confidence score calculation."""
        # Clear emotional text should have higher confidence
        clear_text = "I am extremely happy and joyful!"
        clear_result = self.analyzer.analyze_emotion(clear_text, test_user.id)
        
        # Neutral text should have lower confidence
        neutral_text = "The weather is okay today."
        neutral_result = self.analyzer.analyze_emotion(neutral_text, test_user.id)
        
        assert clear_result["confidence"] > neutral_result["confidence"]
    
    def test_detect_patterns_insufficient_data(self, db_session: Session, test_user: User):
        """Test pattern detection with insufficient data."""
        patterns = self.analyzer.detect_patterns(db_session, test_user.id, days=30)
        assert patterns == []  # No patterns with insufficient data
    
    def test_detect_patterns_with_data(self, db_session: Session, test_user: User):
        """Test pattern detection with sufficient data."""
        # Create multiple emotion analyses with recurring sadness
        for i in range(5):
            analysis = EmotionAnalysis(
                user_id=test_user.id,
                joy=0.1,
                sadness=0.8,  # High sadness
                anger=0.2,
                fear=0.3,
                surprise=0.1,
                disgust=0.1,
                sentiment_score=-0.6,
                sentiment_label="negative",
                confidence=0.8,
                analyzed_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(analysis)
        
        db_session.commit()
        
        patterns = self.analyzer.detect_patterns(db_session, test_user.id, days=30)
        
        # Should detect recurring sadness pattern
        assert len(patterns) > 0
        sadness_pattern = next((p for p in patterns if "sadness" in p["pattern_name"]), None)
        assert sadness_pattern is not None
        assert sadness_pattern["frequency"] >= 3  # Should appear in most analyses
    
    def test_empty_text_handling(self, test_user: User):
        """Test handling of empty or whitespace-only text."""
        result = self.analyzer.analyze_emotion("", test_user.id)
        
        assert result["user_id"] == test_user.id
        assert all(result[emotion] == 0.0 for emotion in ["joy", "sadness", "anger", "fear", "surprise", "disgust"])
        assert result["sentiment_score"] == 0.0
        assert result["keywords"] == []
    
    def test_special_characters_handling(self, test_user: User):
        """Test handling of text with special characters."""
        text = "I'm feeling @#$% terrible!!! 😢😢😢"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        # Should still detect negative sentiment despite special characters
        assert result["sentiment_label"] == "negative"
        assert "terrible" in result["keywords"]
    
    def test_long_text_handling(self, test_user: User):
        """Test handling of very long text."""
        long_text = "I am sad. " * 100  # Very repetitive long text
        result = self.analyzer.analyze_emotion(long_text, test_user.id)
        
        assert result["sadness"] > 0.5  # Should still detect sadness
        assert result["sentiment_label"] == "negative"
    
    def test_mixed_emotions_text(self, test_user: User):
        """Test text with mixed emotions."""
        text = "I'm happy about the promotion but scared about the new responsibilities"
        result = self.analyzer.analyze_emotion(text, test_user.id)
        
        assert result["joy"] > 0  # Should detect some happiness
        assert result["fear"] > 0  # Should detect some fear
        # Sentiment might be neutral due to mixed emotions
