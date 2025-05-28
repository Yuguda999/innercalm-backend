"""
Recommendation engine for personalized healing suggestions.
"""
import logging
from typing import Dict, List, Optional
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.recommendation import Recommendation, RecommendationType
from models.emotion import EmotionAnalysis, EmotionPattern
from models.user import User
from services.svg_generator import SVGGenerator

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating personalized healing recommendations."""

    def __init__(self):
        # Initialize SVG generator
        self.svg_generator = SVGGenerator()

        # Recommendation templates organized by emotion and type
        self.recommendations = {
            "sadness": {
                RecommendationType.BREATHING_EXERCISE: [
                    {
                        "title": "4-7-8 Breathing for Emotional Balance",
                        "description": "A calming breathing technique to help process sadness and find emotional balance.",
                        "instructions": "1. Sit comfortably and close your eyes\n2. Inhale through your nose for 4 counts\n3. Hold your breath for 7 counts\n4. Exhale through your mouth for 8 counts\n5. Repeat 4-6 times\n\nFocus on the rhythm and let each exhale release tension.",
                        "duration": 10
                    }
                ],
                RecommendationType.JOURNALING_PROMPT: [
                    {
                        "title": "Exploring Your Feelings",
                        "description": "A gentle journaling exercise to help you process and understand your sadness.",
                        "instructions": "Take 15-20 minutes to write about:\n\n1. What am I feeling right now, and where do I feel it in my body?\n2. What might have triggered these feelings?\n3. What would I say to a friend experiencing the same thing?\n4. What small act of kindness can I show myself today?\n\nWrite freely without judgment.",
                        "duration": 20
                    }
                ],
                RecommendationType.MINDFULNESS_PRACTICE: [
                    {
                        "title": "Loving-Kindness Meditation",
                        "description": "A meditation practice to cultivate self-compassion during difficult times.",
                        "instructions": "1. Sit quietly and close your eyes\n2. Place your hand on your heart\n3. Repeat these phrases silently:\n   - 'May I be kind to myself'\n   - 'May I give myself the compassion I need'\n   - 'May I be strong and patient'\n   - 'May I accept this moment as it is'\n4. Continue for 10-15 minutes",
                        "duration": 15
                    }
                ]
            },
            "anger": {
                RecommendationType.BREATHING_EXERCISE: [
                    {
                        "title": "Box Breathing for Anger Management",
                        "description": "A structured breathing technique to help calm intense anger and regain control.",
                        "instructions": "1. Sit or stand with your back straight\n2. Inhale for 4 counts\n3. Hold for 4 counts\n4. Exhale for 4 counts\n5. Hold empty for 4 counts\n6. Repeat 8-10 times\n\nVisualize drawing a box with each breath cycle.",
                        "duration": 8
                    }
                ],
                RecommendationType.PHYSICAL_ACTIVITY: [
                    {
                        "title": "Anger Release Movement",
                        "description": "Physical exercises to help channel and release angry energy constructively.",
                        "instructions": "Choose one or more:\n\n1. Vigorous walking for 10-15 minutes\n2. Push-ups or jumping jacks (30 seconds, 3 sets)\n3. Punch a pillow or punching bag\n4. Intense stretching or yoga poses\n5. Dance to energetic music\n\nFocus on releasing the energy, not the anger itself.",
                        "duration": 15
                    }
                ],
                RecommendationType.COGNITIVE_REFRAMING: [
                    {
                        "title": "Anger Thought Challenge",
                        "description": "A cognitive exercise to examine and reframe angry thoughts.",
                        "instructions": "1. Write down the situation that made you angry\n2. List your immediate thoughts about it\n3. Ask yourself:\n   - Is this thought completely true?\n   - What evidence supports/contradicts it?\n   - How might someone else see this?\n   - What would I tell a friend in this situation?\n4. Write a more balanced perspective",
                        "duration": 15
                    }
                ]
            },
            "fear": {
                RecommendationType.BREATHING_EXERCISE: [
                    {
                        "title": "Grounding Breath for Anxiety",
                        "description": "A calming breathing technique to reduce fear and anxiety.",
                        "instructions": "1. Place one hand on chest, one on belly\n2. Breathe slowly through your nose\n3. Feel your belly rise more than your chest\n4. Exhale slowly through pursed lips\n5. Count: 'In-2-3-4, Out-2-3-4-5-6'\n6. Continue for 5-10 minutes\n\nFocus on the sensation of breathing.",
                        "duration": 10
                    }
                ],
                RecommendationType.MINDFULNESS_PRACTICE: [
                    {
                        "title": "5-4-3-2-1 Grounding Technique",
                        "description": "A mindfulness exercise to ground yourself when feeling anxious or fearful.",
                        "instructions": "Notice and name:\n\n5 things you can SEE around you\n4 things you can TOUCH\n3 things you can HEAR\n2 things you can SMELL\n1 thing you can TASTE\n\nTake your time with each sense. This brings you back to the present moment.",
                        "duration": 10
                    }
                ]
            },
            "general": {
                RecommendationType.RELAXATION_TECHNIQUE: [
                    {
                        "title": "Progressive Muscle Relaxation",
                        "description": "A full-body relaxation technique to release physical and emotional tension.",
                        "instructions": "1. Lie down comfortably\n2. Starting with your toes, tense each muscle group for 5 seconds\n3. Release and notice the relaxation\n4. Move up: feet, calves, thighs, abdomen, hands, arms, shoulders, face\n5. End with 2 minutes of deep breathing\n\nFocus on the contrast between tension and relaxation.",
                        "duration": 20
                    }
                ]
            }
        }

    def generate_recommendations(
        self,
        db: Session,
        user_id: int,
        emotion_analysis: Optional[Dict] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Generate personalized recommendations based on user's emotional state.

        Args:
            db: Database session
            user_id: User ID
            emotion_analysis: Current emotion analysis data
            limit: Maximum number of recommendations to generate

        Returns:
            List of recommendation dictionaries
        """
        try:
            recommendations = []

            # Determine target emotions
            target_emotions = self._identify_target_emotions(db, user_id, emotion_analysis)

            # Generate recommendations for each target emotion
            for emotion in target_emotions[:limit]:
                rec = self._create_recommendation(emotion, user_id)
                if rec:
                    recommendations.append(rec)

            # Fill remaining slots with general recommendations if needed
            while len(recommendations) < limit:
                general_rec = self._create_recommendation("general", user_id)
                if general_rec and general_rec not in recommendations:
                    recommendations.append(general_rec)
                else:
                    break

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _identify_target_emotions(
        self,
        db: Session,
        user_id: int,
        emotion_analysis: Optional[Dict]
    ) -> List[str]:
        """Identify which emotions to target with recommendations."""
        target_emotions = []

        # Use current emotion analysis if available
        if emotion_analysis:
            emotions = ["sadness", "anger", "fear", "joy"]
            for emotion in emotions:
                if emotion_analysis.get(emotion, 0) > 0.5:
                    target_emotions.append(emotion)

        # If no strong emotions detected, look at recent patterns
        if not target_emotions:
            recent_analyses = db.query(EmotionAnalysis).filter(
                EmotionAnalysis.user_id == user_id,
                EmotionAnalysis.analyzed_at >= datetime.utcnow() - timedelta(days=7)
            ).all()

            if recent_analyses:
                emotion_averages = {
                    "sadness": sum(a.sadness for a in recent_analyses) / len(recent_analyses),
                    "anger": sum(a.anger for a in recent_analyses) / len(recent_analyses),
                    "fear": sum(a.fear for a in recent_analyses) / len(recent_analyses)
                }

                # Target emotions with highest averages
                sorted_emotions = sorted(emotion_averages.items(), key=lambda x: x[1], reverse=True)
                target_emotions = [emotion for emotion, score in sorted_emotions if score > 0.3]

        # Default to general if no specific emotions identified
        if not target_emotions:
            target_emotions = ["general"]

        return target_emotions

    def _create_recommendation(self, emotion: str, user_id: int) -> Optional[Dict]:
        """Create a recommendation for a specific emotion."""
        try:
            emotion_recs = self.recommendations.get(emotion, {})
            if not emotion_recs:
                return None

            # Randomly select a recommendation type
            rec_type = random.choice(list(emotion_recs.keys()))
            templates = emotion_recs[rec_type]
            template = random.choice(templates)

            # Create base recommendation data
            recommendation_data = {
                "user_id": user_id,
                "type": rec_type,
                "title": template["title"],
                "description": template["description"],
                "instructions": template["instructions"],
                "target_emotions": [emotion] if emotion != "general" else ["stress", "general_wellness"],
                "difficulty_level": 1,  # Default to easy
                "estimated_duration": template.get("duration", 15)
            }

            # Generate SVG illustration
            try:
                svg_data_url = self.svg_generator.generate_svg(recommendation_data)
                recommendation_data["image_url"] = svg_data_url
                recommendation_data["illustration_prompt"] = f"SVG illustration for {template['title']} - {rec_type.value}"
            except Exception as svg_error:
                logger.warning(f"Failed to generate SVG for recommendation: {svg_error}")
                # Continue without SVG - will fall back to default images

            return recommendation_data

        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            return None
