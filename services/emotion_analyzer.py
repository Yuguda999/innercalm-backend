"""
Emotion analysis service using a pretrained DistilRoBERTa model.
"""
import logging
from typing import Dict, List, Optional
from transformers import pipeline
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import os
import time
from pathlib import Path

from models.emotion import EmotionAnalysis, EmotionPattern
from config import settings

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """Service for analyzing emotions in text using a pretrained DistilRoBERTa."""

    _instance = None
    _classifier = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmotionAnalyzer, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base", preload: bool = False):
        # Only initialize once
        if self._classifier is not None:
            return

        self.model_name = model_name
        self.model_cache_dir = Path.home() / ".cache" / "innercalm" / "models"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)

        if preload:
            self._load_model()

    def _load_model(self):
        """Load the emotion classification model with caching and progress tracking."""
        if self._classifier is not None:
            return

        try:
            start_time = time.time()
            logger.info(f"Loading emotion classifier: {self.model_name}")
            print(f"🧠 Loading emotion analysis model... (this may take 10-30 seconds on first run)")

            # Set cache directory for model downloads
            os.environ['TRANSFORMERS_CACHE'] = str(self.model_cache_dir)

            # Force CPU usage to avoid CUDA memory issues
            os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable CUDA completely
            print("Device set to use cpu")

            self._classifier = pipeline(
                "text-classification",
                model=self.model_name,
                return_all_scores=True,    # get scores for all labels
                top_k=None,                # include every label in the output
                device=-1                  # Force CPU usage
            )

            load_time = time.time() - start_time
            logger.info(f"✅ Emotion classifier loaded successfully in {load_time:.2f}s (using CPU)")
            print(f"✅ Model loaded in {load_time:.2f} seconds")

        except Exception as e:
            logger.error(f"❌ Failed to load emotion classifier: {e}")
            print(f"❌ Failed to load emotion model: {e}")
            raise

        # Map HF labels to our database fields
        self.label_map = {
            "anger": "anger",
            "disgust": "disgust",
            "fear": "fear",
            "joy": "joy",
            "neutral": "neutral",
            "sadness": "sadness",
            "surprise": "surprise",
        }

        # Trauma and mental health keywords for theme detection - removed common emotional words
        self.trauma_keywords = [
            "trauma", "ptsd", "flashback", "nightmare", "trigger", "abuse", "violence",
            "suicide", "self-harm"
        ]

        # Emotion keywords for pattern detection
        self.emotion_keywords = {
            "joy": ["happy", "joy", "excited", "pleased", "content"],
            "sadness": ["sad", "depressed", "down", "melancholy", "grief"],
            "anger": ["angry", "mad", "furious", "irritated", "rage"],
            "fear": ["afraid", "scared", "anxious", "worried", "panic"],
            "surprise": ["surprised", "shocked", "amazed", "astonished"],
            "disgust": ["disgusted", "revolted", "repulsed", "sick"],
            "neutral": ["neutral", "calm", "okay", "fine"]
        }

    @property
    def classifier(self):
        """Get the classifier, loading it if necessary."""
        if self._classifier is None:
            self._load_model()
        return self._classifier

    def analyze_emotion(self, text: str, user_id: int, message_id: Optional[int] = None) -> Dict:
        """
        Analyze emotions in text via the pretrained model.
        Returns normalized scores for each emotion plus a top label.

        Args:
            text: Text to analyze
            user_id: ID of the user
            message_id: Optional message ID

        Returns:
            Dictionary containing emotion analysis results
        """
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)

            # Get emotion predictions from the model
            raw_scores = self.classifier(cleaned_text)[0]  # pipeline returns list of lists

            # Build a dict of emotion scores
            emotion_scores = {}
            for item in raw_scores:
                label = self.label_map.get(item["label"], item["label"])
                emotion_scores[label] = item["score"]

            # Ensure all expected emotions are present (set to 0 if missing)
            for emotion in ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]:
                if emotion not in emotion_scores:
                    emotion_scores[emotion] = 0.0

            # Determine top emotion and sentiment
            top = max(raw_scores, key=lambda x: x["score"])
            top_emotion = self.label_map.get(top["label"], top["label"])

            # Convert to sentiment label (positive/negative/neutral)
            if top_emotion in ["joy"]:
                sentiment_label = "positive"
                sentiment_score = emotion_scores["joy"]
            elif top_emotion in ["sadness", "anger", "fear", "disgust"]:
                sentiment_label = "negative"
                sentiment_score = -max(emotion_scores["sadness"], emotion_scores["anger"],
                                     emotion_scores["fear"], emotion_scores["disgust"])
            else:
                sentiment_label = "neutral"
                sentiment_score = 0.0

            # Extract themes and keywords
            themes = self._extract_themes(cleaned_text)
            keywords = self._extract_keywords(cleaned_text)

            return {
                "user_id": user_id,
                "message_id": message_id,
                "joy": emotion_scores.get("joy", 0.0),
                "sadness": emotion_scores.get("sadness", 0.0),
                "anger": emotion_scores.get("anger", 0.0),
                "fear": emotion_scores.get("fear", 0.0),
                "surprise": emotion_scores.get("surprise", 0.0),
                "disgust": emotion_scores.get("disgust", 0.0),
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "themes": themes,
                "keywords": keywords,
                "confidence": top["score"]
            }

        except Exception as e:
            logger.error(f"Error analyzing emotion: {e}")
            raise

    def _preprocess_text(self, text: str) -> str:
        """Basic cleanup: collapse whitespace and strip most special chars."""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s.,!?;:\'-]', '', text)
        return text



    def _extract_themes(self, text: str) -> List[str]:
        """Extract themes from text based on keyword patterns."""
        themes = []

        # Check for trauma-related themes
        if any(keyword in text for keyword in self.trauma_keywords):
            themes.append("trauma_related")

        # Check for relationship themes
        relationship_keywords = ["relationship", "family", "friend", "partner", "love", "breakup"]
        if any(keyword in text for keyword in relationship_keywords):
            themes.append("relationships")

        # Check for work/career themes
        work_keywords = ["work", "job", "career", "boss", "colleague", "stress", "deadline"]
        if any(keyword in text for keyword in work_keywords):
            themes.append("work_career")

        # Check for self-esteem themes
        self_esteem_keywords = ["confidence", "self-worth", "insecure", "doubt", "failure"]
        if any(keyword in text for keyword in self_esteem_keywords):
            themes.append("self_esteem")

        return themes

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction based on frequency and importance
        words = text.split()

        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "i", "you", "he", "she", "it", "we", "they", "am", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must"}

        # Clean words by removing punctuation and filtering
        cleaned_keywords = []
        for word in words:
            # Remove punctuation from word
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 3 and clean_word.lower() not in stop_words:
                cleaned_keywords.append(clean_word.lower())

        # Return top 10 most relevant keywords
        return list(set(cleaned_keywords))[:10]



    def detect_patterns(self, db: Session, user_id: int, days: int = 30) -> List[Dict]:
        """
        Detect emotion patterns for a user over a specified period.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze

        Returns:
            List of detected patterns
        """
        try:
            # Get recent emotion analyses
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            analyses = db.query(EmotionAnalysis).filter(
                EmotionAnalysis.user_id == user_id,
                EmotionAnalysis.analyzed_at >= cutoff_date
            ).all()

            if len(analyses) < 3:  # Need minimum data for pattern detection
                return []

            patterns = []

            # Detect recurring high-intensity emotions
            emotion_frequencies = {emotion: 0 for emotion in self.emotion_keywords.keys()}
            total_analyses = len(analyses)

            for analysis in analyses:
                for emotion in emotion_frequencies.keys():
                    score = getattr(analysis, emotion, 0)
                    if score > 0.5:  # High intensity threshold
                        emotion_frequencies[emotion] += 1

            # Identify patterns (emotions occurring in >30% of analyses)
            for emotion, frequency in emotion_frequencies.items():
                if frequency / total_analyses > 0.3:
                    patterns.append({
                        "pattern_name": f"recurring_{emotion}",
                        "pattern_description": f"Recurring {emotion} detected in {frequency}/{total_analyses} recent interactions",
                        "frequency": frequency,
                        "intensity": sum(getattr(a, emotion, 0) for a in analyses) / total_analyses,
                        "emotions": {emotion: frequency / total_analyses}
                    })

            return patterns

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []


# Global instance - lazy loaded
_emotion_analyzer = None

def get_emotion_analyzer(preload: bool = False):
    """Get the global emotion analyzer instance (lazy loaded)."""
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = EmotionAnalyzer(preload=preload)
    return _emotion_analyzer

def preload_emotion_analyzer():
    """Preload the emotion analyzer model for faster first-time usage."""
    logger.info("Preloading emotion analyzer...")
    analyzer = get_emotion_analyzer(preload=True)
    # Trigger model loading by accessing classifier
    _ = analyzer.classifier
    logger.info("Emotion analyzer preloaded successfully")
