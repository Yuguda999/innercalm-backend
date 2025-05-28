"""
OpenAI service for trauma mapping and reframing functionality.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI-powered trauma mapping and reframing functionality."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7
        )

    async def generate_reframe_prompts(
        self, 
        event_context: str, 
        technique_name: str, 
        technique_description: str
    ) -> List[str]:
        """Generate personalized reframing prompts for a specific life event."""
        try:
            system_prompt = f"""
            You are a compassionate trauma-informed therapist specializing in cognitive reframing.
            Your task is to generate 3-4 personalized, gentle prompts for the {technique_name} technique.
            
            Technique Description: {technique_description}
            
            Guidelines:
            - Be gentle, non-judgmental, and trauma-informed
            - Use "you" language to make it personal
            - Focus on empowerment and self-compassion
            - Avoid re-traumatizing language
            - Make prompts specific to the event context
            - Each prompt should be a thoughtful question or gentle invitation
            
            Return only the prompts as a JSON array of strings.
            """
            
            user_prompt = f"""
            Event Context:
            {event_context}
            
            Generate personalized {technique_name} prompts for this specific situation.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the JSON response
            try:
                prompts = json.loads(response.content)
                return prompts if isinstance(prompts, list) else []
            except json.JSONDecodeError:
                # Fallback: split by lines and clean up
                lines = response.content.strip().split('\n')
                return [line.strip('- ').strip() for line in lines if line.strip()]
                
        except Exception as e:
            logger.error(f"Error generating reframe prompts: {e}")
            return []

    async def analyze_reframe_response(
        self, 
        user_response: str, 
        current_phase: str, 
        original_narrative: str
    ) -> Dict[str, Any]:
        """Analyze user's response during reframing session."""
        try:
            system_prompt = f"""
            You are an expert trauma therapist analyzing a client's response during a {current_phase} phase 
            of cognitive reframing. Provide a comprehensive analysis.
            
            Analyze the response for:
            1. Emotional insights and breakthroughs
            2. Cognitive shifts or new perspectives
            3. Level of engagement and openness
            4. Signs of resistance or avoidance
            5. Progress indicators
            6. Areas needing more exploration
            
            Return your analysis as a JSON object with these keys:
            - insights: array of key insights identified
            - emotional_shift: object with before/after emotional indicators
            - engagement_level: number from 1-10
            - breakthrough_indicators: array of breakthrough signs
            - areas_to_explore: array of areas needing more work
            - progress_indicators: array of positive progress signs
            - emotional_shift_magnitude: number from 0-10 indicating degree of shift
            """
            
            user_prompt = f"""
            Original Narrative: {original_narrative}
            
            Current Phase: {current_phase}
            
            User's Response: {user_response}
            
            Provide detailed analysis of this response.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                analysis = json.loads(response.content)
                return analysis
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "insights": ["User is engaging with the reframing process"],
                    "emotional_shift": {},
                    "engagement_level": 7,
                    "breakthrough_indicators": [],
                    "areas_to_explore": ["Continue exploring this perspective"],
                    "progress_indicators": ["Active participation"],
                    "emotional_shift_magnitude": 3
                }
                
        except Exception as e:
            logger.error(f"Error analyzing reframe response: {e}")
            return {
                "insights": [],
                "emotional_shift": {},
                "engagement_level": 5,
                "breakthrough_indicators": [],
                "areas_to_explore": [],
                "progress_indicators": [],
                "emotional_shift_magnitude": 0
            }

    async def generate_follow_up_guidance(
        self,
        original_narrative: str,
        user_response: str,
        analysis: Dict[str, Any],
        current_phase: str
    ) -> Dict[str, Any]:
        """Generate follow-up guidance based on user's response analysis."""
        try:
            system_prompt = f"""
            You are a compassionate trauma therapist providing follow-up guidance during the {current_phase} 
            phase of cognitive reframing. Based on the analysis, provide supportive next steps.
            
            Guidelines:
            - Be warm, validating, and encouraging
            - Build on insights the user has shared
            - Gently guide toward deeper exploration when appropriate
            - Offer specific next prompts or exercises
            - Acknowledge progress and breakthroughs
            - Be trauma-informed and avoid pushing too hard
            
            Return guidance as JSON with these keys:
            - message: encouraging response to their sharing
            - next_prompts: array of 2-3 follow-up questions/prompts
            - encouragement: specific validation of their progress
            - suggested_exercise: optional self-compassion exercise
            """
            
            user_prompt = f"""
            Original Narrative: {original_narrative}
            
            User's Response: {user_response}
            
            Analysis Results: {json.dumps(analysis, indent=2)}
            
            Current Phase: {current_phase}
            
            Generate supportive follow-up guidance.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                guidance = json.loads(response.content)
                return guidance
            except json.JSONDecodeError:
                # Fallback guidance
                return {
                    "message": "Thank you for sharing that insight. I can see you're really engaging with this process.",
                    "next_prompts": [
                        "How does this new perspective feel in your body?",
                        "What would you tell someone else in a similar situation?"
                    ],
                    "encouragement": "You're showing real courage in exploring this experience.",
                    "suggested_exercise": None
                }
                
        except Exception as e:
            logger.error(f"Error generating follow-up guidance: {e}")
            return {
                "message": "Thank you for sharing. Let's continue exploring this together.",
                "next_prompts": ["How does this feel to you right now?"],
                "encouragement": "You're doing important work here.",
                "suggested_exercise": None
            }

    async def generate_session_summary(
        self,
        original_narrative: str,
        reframed_narrative: str,
        insights_gained: List[str],
        breakthrough_moments: List[str]
    ) -> Dict[str, Any]:
        """Generate a comprehensive session summary."""
        try:
            system_prompt = """
            You are a trauma therapist creating a session summary for a cognitive reframing session.
            Provide a comprehensive, encouraging summary that highlights progress and insights.
            
            Include:
            - Key transformations in perspective
            - Insights and breakthroughs achieved
            - Progress made in healing
            - Strengths and resilience demonstrated
            - Recommendations for continued growth
            
            Return as JSON with these keys:
            - transformation_summary: overview of perspective shifts
            - key_insights: most important insights gained
            - progress_highlights: specific progress made
            - strengths_identified: personal strengths demonstrated
            - next_steps: recommendations for continued healing
            - encouragement_message: uplifting closing message
            """
            
            user_prompt = f"""
            Original Narrative: {original_narrative}
            
            Reframed Narrative: {reframed_narrative}
            
            Insights Gained: {json.dumps(insights_gained)}
            
            Breakthrough Moments: {json.dumps(breakthrough_moments)}
            
            Create a comprehensive session summary.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                summary = json.loads(response.content)
                return summary
            except json.JSONDecodeError:
                # Fallback summary
                return {
                    "transformation_summary": "You've made meaningful progress in reframing this experience.",
                    "key_insights": insights_gained[:3] if insights_gained else ["You showed courage in exploring this experience"],
                    "progress_highlights": ["Engaged openly with the reframing process", "Demonstrated self-awareness"],
                    "strengths_identified": ["Resilience", "Self-reflection", "Openness to growth"],
                    "next_steps": ["Continue practicing self-compassion", "Notice when old patterns arise"],
                    "encouragement_message": "You've done important healing work today. Be gentle with yourself as you integrate these insights."
                }
                
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            return {
                "transformation_summary": "Session completed successfully.",
                "key_insights": insights_gained if insights_gained else [],
                "progress_highlights": ["Participated in reframing session"],
                "strengths_identified": ["Commitment to healing"],
                "next_steps": ["Continue self-reflection"],
                "encouragement_message": "Thank you for your courage in this healing work."
            }

    async def analyze_trauma_patterns(
        self, 
        events_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze trauma patterns across multiple life events."""
        try:
            system_prompt = """
            You are a trauma specialist analyzing patterns across multiple life events.
            Identify recurring themes, triggers, and healing opportunities.
            
            Look for:
            - Recurring themes and patterns
            - Common triggers or circumstances
            - Progression of healing over time
            - Resilience factors and strengths
            - Areas needing focused attention
            - Recommendations for healing approaches
            
            Return analysis as JSON with these keys:
            - recurring_themes: array of identified themes
            - trigger_patterns: array of common triggers
            - healing_progression: assessment of healing over time
            - resilience_factors: identified strengths and resources
            - priority_areas: areas needing immediate attention
            - recommended_approaches: suggested therapeutic approaches
            - overall_assessment: summary of trauma impact and healing potential
            """
            
            user_prompt = f"""
            Life Events Data: {json.dumps(events_data, indent=2)}
            
            Analyze these events for trauma patterns and healing opportunities.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                analysis = json.loads(response.content)
                return analysis
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "recurring_themes": ["Life transitions", "Relationship challenges"],
                    "trigger_patterns": ["Stress", "Loss", "Change"],
                    "healing_progression": "Gradual progress with some setbacks",
                    "resilience_factors": ["Self-awareness", "Seeking help"],
                    "priority_areas": ["Unresolved trauma", "Coping strategies"],
                    "recommended_approaches": ["Trauma-informed therapy", "Self-compassion practices"],
                    "overall_assessment": "Shows potential for healing with appropriate support"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing trauma patterns: {e}")
            return {
                "recurring_themes": [],
                "trigger_patterns": [],
                "healing_progression": "Unable to assess",
                "resilience_factors": [],
                "priority_areas": [],
                "recommended_approaches": [],
                "overall_assessment": "Analysis unavailable"
            }
