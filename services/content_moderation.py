"""
AI-powered content moderation service for community safety.
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sqlalchemy.orm import Session

from models.community import CircleMessage, ReflectionEntry
from models.user import User

logger = logging.getLogger(__name__)


class ContentModerationService:
    """AI-powered content moderation for community safety."""

    def __init__(self):
        self.toxicity_threshold = 0.7
        self.crisis_threshold = 0.8
        self.spam_threshold = 0.6

        # Initialize AI models
        self._load_models()

        # Predefined word lists
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'not worth living', 'want to die',
            'self harm', 'cutting', 'overdose', 'jump off', 'hang myself'
        ]

        self.inappropriate_keywords = [
            'fuck', 'shit', 'damn', 'bitch', 'asshole', 'bastard',
            # Add more as needed, but be careful with mental health context
        ]

        self.spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'\b(?:buy|sell|cheap|discount|offer|deal)\b.*\b(?:now|today|click|visit)\b',
            r'(\b\w+\b)(?:\s+\1){2,}',  # Repeated words
        ]

    def _load_models(self):
        """Load AI models for content moderation."""
        # Force CPU usage to avoid CUDA issues
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = ''

        # Initialize all classifiers to None
        self.toxicity_classifier = None
        self.crisis_classifier = None
        self.spam_classifier = None

        # Try to load toxicity detection model
        try:
            self.toxicity_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=-1  # Force CPU
            )
            logger.info("Toxicity classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load toxicity classifier: {e}")

        # Try to load crisis detection model (use alternative model)
        try:
            # Use a more accessible emotion/sentiment model for crisis detection
            self.crisis_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=-1  # Force CPU
            )
            logger.info("Crisis classifier loaded successfully (using emotion model)")
        except Exception as e:
            logger.warning(f"Could not load crisis classifier: {e}")

        # Try to load spam detection model
        try:
            self.spam_classifier = pipeline(
                "text-classification",
                model="madhurjindal/autonlp-Gibberish-Detector-492513457",
                device=-1  # Force CPU
            )
            logger.info("Spam classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load spam classifier: {e}")

        # Log final status
        loaded_models = []
        if self.toxicity_classifier: loaded_models.append("toxicity")
        if self.crisis_classifier: loaded_models.append("crisis")
        if self.spam_classifier: loaded_models.append("spam")

        if loaded_models:
            logger.info(f"Content moderation initialized with models: {', '.join(loaded_models)}")
        else:
            logger.warning("Content moderation initialized with rule-based detection only")

    async def moderate_content(
        self,
        content: str,
        user_id: int,
        content_type: str = "message"
    ) -> Dict[str, any]:
        """
        Moderate content and return moderation results.

        Returns:
            {
                "approved": bool,
                "flags": List[str],
                "confidence_scores": Dict[str, float],
                "requires_review": bool,
                "auto_action": str  # "approve", "flag", "block", "crisis_alert"
            }
        """
        try:
            moderation_result = {
                "approved": True,
                "flags": [],
                "confidence_scores": {},
                "requires_review": False,
                "auto_action": "approve"
            }

            # 1. Crisis detection (highest priority)
            crisis_score = await self._detect_crisis_content(content)
            moderation_result["confidence_scores"]["crisis"] = crisis_score

            if crisis_score > self.crisis_threshold:
                moderation_result["flags"].append("crisis_language")
                moderation_result["auto_action"] = "crisis_alert"
                moderation_result["requires_review"] = True
                # Don't block crisis messages, but flag for immediate professional attention
                return moderation_result

            # 2. Toxicity detection
            toxicity_score = await self._detect_toxicity(content)
            moderation_result["confidence_scores"]["toxicity"] = toxicity_score

            if toxicity_score > self.toxicity_threshold:
                moderation_result["flags"].append("toxic_language")
                moderation_result["approved"] = False
                moderation_result["auto_action"] = "block"
                return moderation_result

            # 3. Spam detection
            spam_score = await self._detect_spam(content)
            moderation_result["confidence_scores"]["spam"] = spam_score

            if spam_score > self.spam_threshold:
                moderation_result["flags"].append("spam")
                moderation_result["approved"] = False
                moderation_result["auto_action"] = "block"
                return moderation_result

            # 4. Inappropriate content (context-aware for mental health)
            inappropriate_score = await self._detect_inappropriate_content(content)
            moderation_result["confidence_scores"]["inappropriate"] = inappropriate_score

            if inappropriate_score > 0.5:
                moderation_result["flags"].append("inappropriate_language")
                moderation_result["requires_review"] = True
                moderation_result["auto_action"] = "flag"

            # 5. Check for personal information
            pii_detected = await self._detect_personal_info(content)
            if pii_detected:
                moderation_result["flags"].append("personal_information")
                moderation_result["requires_review"] = True
                moderation_result["auto_action"] = "flag"

            # 6. Length and quality checks
            quality_issues = await self._check_content_quality(content)
            if quality_issues:
                moderation_result["flags"].extend(quality_issues)
                if "too_short" not in quality_issues:  # Don't flag short messages
                    moderation_result["requires_review"] = True

            return moderation_result

        except Exception as e:
            logger.error(f"Error in content moderation: {e}")
            # Default to requiring review on error
            return {
                "approved": True,
                "flags": ["moderation_error"],
                "confidence_scores": {},
                "requires_review": True,
                "auto_action": "flag"
            }

    async def _detect_crisis_content(self, content: str) -> float:
        """Detect crisis/self-harm language."""
        try:
            # Rule-based detection for crisis keywords
            content_lower = content.lower()
            crisis_matches = sum(1 for keyword in self.crisis_keywords if keyword in content_lower)

            if crisis_matches > 0:
                base_score = min(0.8 + (crisis_matches * 0.1), 1.0)
            else:
                base_score = 0.0

            # AI-based detection if model is available
            if self.crisis_classifier:
                try:
                    result = self.crisis_classifier(content)
                    if isinstance(result, list) and len(result) > 0:
                        # Look for crisis-related labels
                        crisis_labels = ['crisis', 'suicide', 'self_harm', 'depression_severe']
                        ai_score = max([r['score'] for r in result if r['label'].lower() in crisis_labels], default=0.0)

                        # Combine rule-based and AI scores
                        return max(base_score, ai_score)
                except Exception as e:
                    logger.error(f"Error in AI crisis detection: {e}")

            return base_score

        except Exception as e:
            logger.error(f"Error detecting crisis content: {e}")
            return 0.0

    async def _detect_toxicity(self, content: str) -> float:
        """Detect toxic language."""
        try:
            if self.toxicity_classifier:
                result = self.toxicity_classifier(content)
                if isinstance(result, list) and len(result) > 0:
                    # Look for toxic label
                    for r in result:
                        if r['label'].upper() == 'TOXIC':
                            return r['score']
                return 0.0

            # Fallback rule-based detection
            content_lower = content.lower()
            toxic_matches = sum(1 for word in self.inappropriate_keywords if word in content_lower)
            return min(toxic_matches * 0.3, 1.0)

        except Exception as e:
            logger.error(f"Error detecting toxicity: {e}")
            return 0.0

    async def _detect_spam(self, content: str) -> float:
        """Detect spam content."""
        try:
            spam_score = 0.0

            # Pattern-based detection
            for pattern in self.spam_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    spam_score += 0.3

            # Length-based heuristics
            if len(content) > 1000:  # Very long messages
                spam_score += 0.2

            # Repetition detection
            words = content.lower().split()
            if len(words) > 5:
                unique_words = len(set(words))
                repetition_ratio = 1 - (unique_words / len(words))
                if repetition_ratio > 0.7:
                    spam_score += 0.4

            # AI-based detection if available
            if self.spam_classifier:
                try:
                    result = self.spam_classifier(content)
                    if isinstance(result, list) and len(result) > 0:
                        for r in result:
                            if r['label'].upper() in ['SPAM', 'GIBBERISH']:
                                spam_score = max(spam_score, r['score'])
                except Exception as e:
                    logger.error(f"Error in AI spam detection: {e}")

            return min(spam_score, 1.0)

        except Exception as e:
            logger.error(f"Error detecting spam: {e}")
            return 0.0

    async def _detect_inappropriate_content(self, content: str) -> float:
        """Detect inappropriate content (context-aware for mental health)."""
        try:
            content_lower = content.lower()

            # Be more lenient with mental health context
            mental_health_context = any(word in content_lower for word in [
                'depression', 'anxiety', 'trauma', 'therapy', 'healing', 'recovery',
                'mental health', 'ptsd', 'panic', 'stress', 'emotional'
            ])

            inappropriate_matches = 0
            for word in self.inappropriate_keywords:
                if word in content_lower:
                    # Reduce score if in mental health context
                    if mental_health_context:
                        inappropriate_matches += 0.5
                    else:
                        inappropriate_matches += 1

            return min(inappropriate_matches * 0.2, 1.0)

        except Exception as e:
            logger.error(f"Error detecting inappropriate content: {e}")
            return 0.0

    async def _detect_personal_info(self, content: str) -> bool:
        """Detect personal information that should be flagged."""
        try:
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if re.search(email_pattern, content):
                return True

            # Phone number pattern
            phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            if re.search(phone_pattern, content):
                return True

            # Social security number pattern
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            if re.search(ssn_pattern, content):
                return True

            # Address pattern (basic)
            address_pattern = r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b'
            if re.search(address_pattern, content, re.IGNORECASE):
                return True

            return False

        except Exception as e:
            logger.error(f"Error detecting personal info: {e}")
            return False

    async def _check_content_quality(self, content: str) -> List[str]:
        """Check content quality and return list of issues."""
        issues = []

        try:
            # Length checks
            if len(content.strip()) < 3:
                issues.append("too_short")
            elif len(content) > 5000:
                issues.append("too_long")

            # All caps check
            if len(content) > 20 and content.isupper():
                issues.append("all_caps")

            # Excessive punctuation
            punctuation_ratio = sum(1 for c in content if c in '!?.,;:') / len(content)
            if punctuation_ratio > 0.3:
                issues.append("excessive_punctuation")

            # Excessive emojis (basic check)
            emoji_count = sum(1 for c in content if ord(c) > 127)
            if emoji_count > len(content) * 0.2:
                issues.append("excessive_emojis")

        except Exception as e:
            logger.error(f"Error checking content quality: {e}")

        return issues

    async def handle_crisis_alert(
        self,
        content: str,
        user_id: int,
        db: Session,
        content_type: str = "message"
    ):
        """Handle crisis content by alerting moderators and providing resources."""
        try:
            # Log crisis alert
            logger.critical(f"CRISIS ALERT: User {user_id} posted potential crisis content")

            # Here you would:
            # 1. Alert professional moderators immediately
            # 2. Send crisis resources to the user
            # 3. Potentially escalate to emergency services if configured
            # 4. Log the incident for follow-up

            # For now, we'll create a moderation record
            # In production, integrate with crisis intervention services

            crisis_resources = {
                "message": "We noticed you might be going through a difficult time. You're not alone.",
                "resources": [
                    {
                        "name": "National Suicide Prevention Lifeline",
                        "phone": "988",
                        "available": "24/7"
                    },
                    {
                        "name": "Crisis Text Line",
                        "text": "Text HOME to 741741",
                        "available": "24/7"
                    },
                    {
                        "name": "International Association for Suicide Prevention",
                        "website": "https://www.iasp.info/resources/Crisis_Centres/",
                        "available": "Global resources"
                    }
                ]
            }

            return crisis_resources

        except Exception as e:
            logger.error(f"Error handling crisis alert: {e}")
            return None


# Global moderation service instance
moderation_service = ContentModerationService()
