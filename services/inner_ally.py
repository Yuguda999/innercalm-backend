"""
Inner Ally Agent service for personalized AI companion functionality.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.user import User, UserPreferences
from models.user_memory import (
    UserMemory, PersonalTrigger, CopingPreference,
    SupportivePhrase, ConversationPattern
)
from models.agent_persona import (
    AgentPersona, UserPersonaCustomization,
    MicroCheckIn, WidgetInteraction
)
from services.emotion_analyzer import get_emotion_analyzer

logger = logging.getLogger(__name__)


class InnerAllyAgent:
    """
    Personal AI Inner Ally Agent with longitudinal memory and persona customization.
    """

    def __init__(self):
        self.emotion_analyzer = None  # Lazy loaded

        # Default personas configuration
        self.default_personas = {
            "gentle_mentor": {
                "display_name": "Gentle Mentor",
                "description": "A wise, patient guide who offers gentle wisdom and encouragement",
                "communication_style": {
                    "tone": "warm_supportive",
                    "language_patterns": ["I understand", "Let's explore", "You're doing well"],
                    "response_length": "medium",
                    "empathy_expressions": "high"
                },
                "therapeutic_approach": "person_centered",
                "response_patterns": {
                    "validation_frequency": "high",
                    "question_style": "open_ended",
                    "intervention_timing": "gentle"
                },
                "empathy_level": "very_high",
                "directness_level": "very_gentle",
                "formality_level": "casual"
            },
            "warm_friend": {
                "display_name": "Warm Friend",
                "description": "A caring, understanding friend who's always there to listen",
                "communication_style": {
                    "tone": "friendly_casual",
                    "language_patterns": ["I hear you", "That sounds tough", "I'm here for you"],
                    "response_length": "conversational",
                    "empathy_expressions": "very_high"
                },
                "therapeutic_approach": "supportive",
                "response_patterns": {
                    "validation_frequency": "very_high",
                    "question_style": "curious_caring",
                    "intervention_timing": "responsive"
                },
                "empathy_level": "very_high",
                "directness_level": "gentle",
                "formality_level": "very_casual"
            },
            "wise_elder": {
                "display_name": "Wise Elder",
                "description": "A thoughtful, experienced guide with deep wisdom and perspective",
                "communication_style": {
                    "tone": "thoughtful_reflective",
                    "language_patterns": ["In my experience", "Consider this", "Wisdom suggests"],
                    "response_length": "thoughtful",
                    "empathy_expressions": "medium"
                },
                "therapeutic_approach": "wisdom_based",
                "response_patterns": {
                    "validation_frequency": "medium",
                    "question_style": "reflective",
                    "intervention_timing": "considered"
                },
                "empathy_level": "high",
                "directness_level": "gentle",
                "formality_level": "casual"
            }
        }

    async def initialize_user_memory(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Initialize memory system for a new user."""
        try:
            # Check if user already has memory initialized
            existing_memory = db.query(UserMemory).filter(
                UserMemory.user_id == user_id
            ).first()

            if existing_memory:
                return {"status": "already_initialized", "memory_count": self._get_memory_count(user_id, db)}

            # Create initial memory entries
            initial_memories = [
                UserMemory(
                    user_id=user_id,
                    memory_type="system",
                    memory_key="initialization",
                    memory_value="User memory system initialized",
                    confidence_level=1.0
                )
            ]

            for memory in initial_memories:
                db.add(memory)

            db.commit()

            return {
                "status": "initialized",
                "memory_count": len(initial_memories),
                "message": "Inner Ally memory system ready"
            }

        except Exception as e:
            logger.error(f"Error initializing user memory: {e}")
            db.rollback()
            return {"status": "error", "message": str(e)}

    def get_user_persona(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get the user's current persona configuration."""
        try:
            user_prefs = db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()

            if not user_prefs:
                # Return default persona
                return self.default_personas["gentle_mentor"]

            persona_key = user_prefs.agent_persona

            if persona_key == "custom":
                # Get custom persona
                custom_persona = db.query(UserPersonaCustomization).filter(
                    and_(
                        UserPersonaCustomization.user_id == user_id,
                        UserPersonaCustomization.is_active == True
                    )
                ).first()

                if custom_persona:
                    return self._build_custom_persona(custom_persona, user_prefs)
                else:
                    # Fallback to default if custom not found
                    return self.default_personas["gentle_mentor"]
            else:
                # Get predefined persona with any customizations
                base_persona = self.default_personas.get(persona_key, self.default_personas["gentle_mentor"])

                # Apply user customizations if any
                customization = db.query(UserPersonaCustomization).filter(
                    and_(
                        UserPersonaCustomization.user_id == user_id,
                        UserPersonaCustomization.is_active == True
                    )
                ).first()

                if customization:
                    return self._apply_customizations(base_persona, customization, user_prefs)

                return base_persona

        except Exception as e:
            logger.error(f"Error getting user persona: {e}")
            return self.default_personas["gentle_mentor"]

    def get_longitudinal_context(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get longitudinal memory context for personalized responses."""
        try:
            context = {
                "personal_triggers": [],
                "effective_coping_strategies": [],
                "resonant_phrases": [],
                "conversation_patterns": [],
                "recent_insights": []
            }

            # Get active personal triggers
            triggers = db.query(PersonalTrigger).filter(
                and_(
                    PersonalTrigger.user_id == user_id,
                    PersonalTrigger.is_active == True
                )
            ).order_by(desc(PersonalTrigger.last_triggered)).limit(5).all()

            context["personal_triggers"] = [
                {
                    "text": trigger.trigger_text,
                    "category": trigger.trigger_category,
                    "intensity": trigger.intensity_level,
                    "helpful_interventions": json.loads(trigger.helpful_interventions) if trigger.helpful_interventions else []
                }
                for trigger in triggers
            ]

            # Get effective coping strategies
            coping_strategies = db.query(CopingPreference).filter(
                CopingPreference.user_id == user_id
            ).filter(
                CopingPreference.effectiveness_rating >= 3.0
            ).order_by(desc(CopingPreference.effectiveness_rating)).limit(5).all()

            context["effective_coping_strategies"] = [
                {
                    "name": strategy.strategy_name,
                    "description": strategy.strategy_description,
                    "category": strategy.strategy_category,
                    "effectiveness": strategy.effectiveness_rating,
                    "custom_instructions": strategy.custom_instructions
                }
                for strategy in coping_strategies
            ]

            # Get resonant supportive phrases
            phrases = db.query(SupportivePhrase).filter(
                SupportivePhrase.user_id == user_id
            ).filter(
                SupportivePhrase.resonance_score >= 3.0
            ).order_by(desc(SupportivePhrase.resonance_score)).limit(5).all()

            context["resonant_phrases"] = [
                {
                    "text": phrase.phrase_text,
                    "category": phrase.phrase_category,
                    "resonance": phrase.resonance_score,
                    "best_emotions": json.loads(phrase.best_emotions) if phrase.best_emotions else []
                }
                for phrase in phrases
            ]

            # Get conversation patterns
            patterns = db.query(ConversationPattern).filter(
                and_(
                    ConversationPattern.user_id == user_id,
                    ConversationPattern.is_active == True
                )
            ).order_by(desc(ConversationPattern.pattern_strength)).limit(3).all()

            context["conversation_patterns"] = [
                {
                    "type": pattern.pattern_type,
                    "name": pattern.pattern_name,
                    "description": pattern.pattern_description,
                    "strength": pattern.pattern_strength
                }
                for pattern in patterns
            ]

            return context

        except Exception as e:
            logger.error(f"Error getting longitudinal context: {e}")
            return {
                "personal_triggers": [],
                "effective_coping_strategies": [],
                "resonant_phrases": [],
                "conversation_patterns": [],
                "recent_insights": []
            }

    def update_memory_from_interaction(
        self,
        user_id: int,
        interaction_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Update user memory based on interaction data."""
        try:
            updates_made = []

            # Extract emotion analysis if available
            emotion_data = interaction_data.get("emotion_analysis", {})
            user_message = interaction_data.get("user_message", "")
            ai_response = interaction_data.get("ai_response", "")
            effectiveness_feedback = interaction_data.get("effectiveness_feedback")

            # Update or create memories based on interaction
            if emotion_data:
                self._update_emotional_patterns(user_id, emotion_data, db)
                updates_made.append("emotional_patterns")

            if user_message:
                self._analyze_and_store_triggers(user_id, user_message, emotion_data, db)
                updates_made.append("trigger_analysis")

            if effectiveness_feedback is not None:
                self._update_strategy_effectiveness(user_id, ai_response, effectiveness_feedback, db)
                updates_made.append("strategy_effectiveness")

            db.commit()

            return {
                "status": "success",
                "updates_made": updates_made,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating memory from interaction: {e}")
            db.rollback()
            return {"status": "error", "message": str(e)}

    def _get_memory_count(self, user_id: int, db: Session) -> int:
        """Get total memory count for user."""
        return db.query(UserMemory).filter(UserMemory.user_id == user_id).count()

    def _build_custom_persona(self, customization: UserPersonaCustomization, user_prefs: UserPreferences) -> Dict[str, Any]:
        """Build custom persona from user customization."""
        return {
            "display_name": customization.custom_name or "Custom Ally",
            "description": customization.custom_description or "Your personalized Inner Ally",
            "communication_style": customization.custom_communication_style or {},
            "response_patterns": customization.custom_response_patterns or {},
            "favorite_phrases": json.loads(customization.favorite_phrases) if customization.favorite_phrases else [],
            "custom_affirmations": json.loads(customization.custom_affirmations) if customization.custom_affirmations else []
        }

    def _apply_customizations(
        self,
        base_persona: Dict[str, Any],
        customization: UserPersonaCustomization,
        user_prefs: UserPreferences
    ) -> Dict[str, Any]:
        """Apply user customizations to base persona."""
        persona = base_persona.copy()

        if customization.custom_name:
            persona["display_name"] = customization.custom_name

        if customization.custom_description:
            persona["description"] = customization.custom_description

        if customization.custom_communication_style:
            persona["communication_style"].update(customization.custom_communication_style)

        if customization.favorite_phrases:
            persona["favorite_phrases"] = json.loads(customization.favorite_phrases)

        if customization.custom_affirmations:
            persona["custom_affirmations"] = json.loads(customization.custom_affirmations)

        return persona

    def _update_emotional_patterns(self, user_id: int, emotion_data: Dict[str, Any], db: Session):
        """Update emotional patterns in memory."""
        # Implementation for updating emotional patterns
        pass

    def _analyze_and_store_triggers(self, user_id: int, message: str, emotion_data: Dict[str, Any], db: Session):
        """Analyze message for triggers and store them."""
        # Implementation for trigger analysis
        pass

    def _update_strategy_effectiveness(self, user_id: int, response: str, effectiveness: float, db: Session):
        """Update strategy effectiveness based on feedback."""
        # Implementation for updating strategy effectiveness
        pass
