"""
Agentic reframe session service using LangGraph for AI-guided cognitive reframing and self-compassion exercises.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from models.trauma_mapping import LifeEvent, TraumaMapping, ReframeSession, ReframeSessionStatus
from config import settings

logger = logging.getLogger(__name__)


class ReframeSessionState(TypedDict):
    """State for the agentic reframe session workflow."""
    messages: Annotated[List, add_messages]
    user_id: int
    session_id: int
    life_event: Dict[str, Any]
    trauma_mapping: Optional[Dict[str, Any]]
    current_phase: str  # exploration, reframing, integration
    original_narrative: str
    reframed_narrative: Optional[str]
    techniques_used: List[str]
    insights_gained: List[str]
    breakthrough_moments: List[str]
    emotional_shift: Dict[str, float]
    progress_percentage: float
    ai_guidance: List[Dict[str, Any]]
    compassion_exercises: List[Dict[str, Any]]
    session_context: Dict[str, Any]


class ReframeSessionService:
    """Agentic service for managing cognitive reframing sessions using LangGraph."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7  # Balanced creativity and consistency
        )
        self.workflow = self._create_reframe_workflow()

        # Cognitive reframing techniques
        self.reframing_techniques = {
            "cognitive_restructuring": {
                "name": "Cognitive Restructuring",
                "description": "Identifying and challenging negative thought patterns",
                "prompts": [
                    "What evidence supports this thought?",
                    "What evidence contradicts this thought?",
                    "How would you advise a friend in this situation?",
                    "What would be a more balanced way to think about this?"
                ]
            },
            "perspective_taking": {
                "name": "Perspective Taking",
                "description": "Viewing the situation from different angles",
                "prompts": [
                    "How might this look from another person's perspective?",
                    "What would you think about this in 5 years?",
                    "How has this experience contributed to your growth?",
                    "What strengths did you show during this difficult time?"
                ]
            },
            "self_compassion": {
                "name": "Self-Compassion",
                "description": "Treating yourself with kindness and understanding",
                "prompts": [
                    "What would you say to comfort a friend going through this?",
                    "How can you show yourself the same kindness?",
                    "What does your inner wise, compassionate voice say?",
                    "How is this experience part of the shared human experience?"
                ]
            },
            "meaning_making": {
                "name": "Meaning Making",
                "description": "Finding purpose and growth in difficult experiences",
                "prompts": [
                    "What have you learned from this experience?",
                    "How has this made you stronger or wiser?",
                    "What values became important to you through this?",
                    "How might this experience help you help others?"
                ]
            }
        }

        # Self-compassion exercises
        self.compassion_exercises = {
            "loving_kindness": {
                "name": "Loving-Kindness Meditation",
                "duration": 10,
                "instructions": [
                    "Place your hand on your heart",
                    "Take three deep breaths",
                    "Repeat: 'May I be kind to myself'",
                    "Repeat: 'May I give myself the compassion I need'",
                    "Repeat: 'May I be strong and patient'"
                ]
            },
            "self_forgiveness": {
                "name": "Self-Forgiveness Practice",
                "duration": 15,
                "instructions": [
                    "Acknowledge what happened without judgment",
                    "Recognize your humanity and imperfection",
                    "Offer yourself forgiveness",
                    "Commit to learning and growth",
                    "Release the burden of self-blame"
                ]
            },
            "inner_child_healing": {
                "name": "Inner Child Healing",
                "duration": 20,
                "instructions": [
                    "Visualize yourself at the age when this happened",
                    "Imagine comforting that younger version of yourself",
                    "Tell them what they needed to hear",
                    "Offer protection and understanding",
                    "Integrate this healing into your present self"
                ]
            }
        }

    def _create_reframe_workflow(self) -> StateGraph:
        """Create the agentic reframe session workflow using LangGraph."""
        workflow = StateGraph(ReframeSessionState)

        # Add workflow nodes
        workflow.add_node("initialize_session", self._initialize_session)
        workflow.add_node("exploration_phase", self._exploration_phase)
        workflow.add_node("analyze_narrative", self._analyze_narrative)
        workflow.add_node("select_techniques", self._select_techniques)
        workflow.add_node("reframing_phase", self._reframing_phase)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("integration_phase", self._integration_phase)
        workflow.add_node("compassion_phase", self._compassion_exercises)
        workflow.add_node("validate_progress", self._validate_progress)
        workflow.add_node("finalize_session", self._finalize_session)

        # Define workflow edges
        workflow.set_entry_point("initialize_session")
        workflow.add_edge("initialize_session", "exploration_phase")
        workflow.add_edge("exploration_phase", "analyze_narrative")
        workflow.add_edge("analyze_narrative", "select_techniques")
        workflow.add_edge("select_techniques", "reframing_phase")
        workflow.add_edge("reframing_phase", "generate_insights")
        workflow.add_edge("generate_insights", "integration_phase")
        workflow.add_edge("integration_phase", "compassion_phase")
        workflow.add_edge("compassion_phase", "validate_progress")
        workflow.add_edge("validate_progress", "finalize_session")
        workflow.add_edge("finalize_session", END)

        return workflow.compile()

    def _initialize_session(self, state: ReframeSessionState) -> ReframeSessionState:
        """Initialize the reframe session."""
        try:
            state["current_phase"] = "initialization"
            state["progress_percentage"] = 0.0
            state["insights_gained"] = []
            state["breakthrough_moments"] = []
            state["emotional_shift"] = {}
            state["ai_guidance"] = []
            state["compassion_exercises"] = []
            state["techniques_used"] = []

            # Set up session context
            state["session_context"] = {
                "start_time": datetime.now().isoformat(),
                "trauma_severity": state["life_event"].get("trauma_severity", 0),
                "event_type": state["life_event"].get("event_type", "unknown"),
                "is_resolved": state["life_event"].get("is_resolved", False)
            }

            logger.info(f"Initialized reframe session {state['session_id']} for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            return state

    def _exploration_phase(self, state: ReframeSessionState) -> ReframeSessionState:
        """Conduct the exploration phase using AI guidance."""
        try:
            state["current_phase"] = "exploration"

            # Generate AI-guided exploration prompts
            system_prompt = """
            You are a compassionate trauma therapist beginning an exploration phase.
            Your goal is to help the person safely explore their experience and current narrative.

            Create gentle, open-ended questions that:
            1. Help them share their story safely
            2. Explore current thoughts and feelings
            3. Identify patterns and beliefs
            4. Assess emotional readiness for reframing
            5. Build rapport and trust

            Be trauma-informed, gentle, and validating.
            """

            life_event = state["life_event"]
            original_narrative = state["original_narrative"]

            user_prompt = f"""
            Life Event: {life_event.get('title', 'Unknown event')}
            Description: {life_event.get('description', 'No description')}
            Trauma Severity: {life_event.get('trauma_severity', 0)}/10
            Original Narrative: {original_narrative}

            Generate 3-4 gentle exploration questions in JSON format:
            {{
                "exploration_questions": [list of questions],
                "validation_message": "supportive message",
                "safety_check": "question to assess emotional safety"
            }}
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse and store exploration guidance
            try:
                import json
                exploration_result = json.loads(response.content)
                state["ai_guidance"].append({
                    "phase": "exploration",
                    "guidance": exploration_result,
                    "timestamp": datetime.now().isoformat()
                })
                state["progress_percentage"] = 15.0
            except json.JSONDecodeError:
                # Fallback exploration
                state["ai_guidance"].append({
                    "phase": "exploration",
                    "guidance": {
                        "exploration_questions": [
                            "Can you tell me more about how this experience affected you?",
                            "What thoughts or feelings come up when you think about this?",
                            "How do you make sense of what happened?"
                        ],
                        "validation_message": "Thank you for sharing this with me. Your experience matters.",
                        "safety_check": "How are you feeling right now as we explore this?"
                    },
                    "timestamp": datetime.now().isoformat()
                })
                state["progress_percentage"] = 10.0

            logger.info(f"Completed exploration phase for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error in exploration phase: {e}")
            return state

    async def create_guided_session(
        self,
        db: Session,
        user_id: int,
        life_event: LifeEvent,
        trauma_mapping: Optional[TraumaMapping] = None
    ) -> Dict[str, Any]:
        """Create an AI-guided reframing session for a specific life event."""
        try:
            # Analyze the event to determine appropriate techniques
            recommended_techniques = self._recommend_techniques(life_event, trauma_mapping)

            # Generate AI prompts for the session
            ai_prompts = await self._generate_ai_prompts(life_event, recommended_techniques)

            # Create session structure
            session_plan = {
                "session_title": f"Reframing: {life_event.title}",
                "estimated_duration": 45,
                "techniques": recommended_techniques,
                "ai_prompts": ai_prompts,
                "exercises": self._select_compassion_exercises(life_event),
                "phases": [
                    {
                        "name": "Exploration",
                        "duration": 15,
                        "description": "Understanding the current narrative and emotional impact"
                    },
                    {
                        "name": "Reframing",
                        "duration": 20,
                        "description": "Guided cognitive restructuring and perspective shifts"
                    },
                    {
                        "name": "Integration",
                        "duration": 10,
                        "description": "Self-compassion and meaning-making exercises"
                    }
                ]
            }

            return session_plan

        except Exception as e:
            logger.error(f"Error creating guided session: {e}")
            raise

    def _recommend_techniques(
        self,
        life_event: LifeEvent,
        trauma_mapping: Optional[TraumaMapping] = None
    ) -> List[str]:
        """Recommend appropriate reframing techniques based on the event and trauma mapping."""
        techniques = []

        # Base recommendations on trauma severity
        if life_event.trauma_severity > 7:
            techniques.extend(["self_compassion", "perspective_taking"])
        elif life_event.trauma_severity > 4:
            techniques.extend(["cognitive_restructuring", "self_compassion"])
        else:
            techniques.extend(["perspective_taking", "meaning_making"])

        # Add techniques based on trauma mapping insights
        if trauma_mapping:
            if trauma_mapping.healing_stage == "denial":
                techniques.append("cognitive_restructuring")
            elif trauma_mapping.healing_stage == "anger":
                techniques.append("self_compassion")
            elif trauma_mapping.healing_stage == "depression":
                techniques.extend(["self_compassion", "meaning_making"])
            elif trauma_mapping.healing_stage in ["bargaining", "acceptance"]:
                techniques.append("meaning_making")

        # Remove duplicates and limit to 3 techniques
        return list(set(techniques))[:3]

    async def _generate_ai_prompts(
        self,
        life_event: LifeEvent,
        techniques: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate AI-guided prompts for the reframing session."""
        try:
            # Create context for AI prompt generation
            context = f"""
            Life Event: {life_event.title}
            Description: {life_event.description or 'No description provided'}
            Emotional Impact: {life_event.emotional_impact_score}/10
            Trauma Severity: {life_event.trauma_severity}/10
            Event Type: {life_event.event_type.value}
            Category: {life_event.category.value}
            """

            prompts = []

            for technique in techniques:
                if technique in self.reframing_techniques:
                    technique_info = self.reframing_techniques[technique]

                    # Generate personalized prompts using AI
                    ai_prompt = await self._generate_reframe_prompts(
                        context,
                        technique_info["name"],
                        technique_info["description"]
                    )

                    prompts.append({
                        "technique": technique,
                        "technique_name": technique_info["name"],
                        "ai_generated_prompts": ai_prompt,
                        "standard_prompts": technique_info["prompts"]
                    })

            return prompts

        except Exception as e:
            logger.error(f"Error generating AI prompts: {e}")
            # Fallback to standard prompts
            return [
                {
                    "technique": technique,
                    "technique_name": self.reframing_techniques[technique]["name"],
                    "ai_generated_prompts": [],
                    "standard_prompts": self.reframing_techniques[technique]["prompts"]
                }
                for technique in techniques if technique in self.reframing_techniques
            ]

    def _select_compassion_exercises(self, life_event: LifeEvent) -> List[Dict[str, Any]]:
        """Select appropriate self-compassion exercises based on the life event."""
        exercises = []

        # Select exercises based on event characteristics
        if life_event.trauma_severity > 6:
            exercises.append(self.compassion_exercises["inner_child_healing"])
            exercises.append(self.compassion_exercises["self_forgiveness"])
        elif life_event.trauma_severity > 3:
            exercises.append(self.compassion_exercises["loving_kindness"])
            exercises.append(self.compassion_exercises["self_forgiveness"])
        else:
            exercises.append(self.compassion_exercises["loving_kindness"])

        return exercises

    async def process_session_response(
        self,
        db: Session,
        session: ReframeSession,
        user_response: str,
        current_phase: str
    ) -> Dict[str, Any]:
        """Process user response and provide AI guidance."""
        try:
            # Analyze the user's response
            analysis = await self._analyze_reframe_response(
                user_response,
                current_phase,
                session.original_narrative
            )

            # Generate follow-up prompts or guidance
            guidance = await self._generate_follow_up_guidance(
                session,
                user_response,
                analysis,
                current_phase
            )

            # Update session progress
            progress_update = self._calculate_progress_update(session, analysis)

            return {
                "analysis": analysis,
                "guidance": guidance,
                "progress_update": progress_update,
                "next_prompts": guidance.get("next_prompts", []),
                "insights": analysis.get("insights", []),
                "emotional_shift": analysis.get("emotional_shift", {})
            }

        except Exception as e:
            logger.error(f"Error processing session response: {e}")
            raise

    async def _generate_follow_up_guidance(
        self,
        session: ReframeSession,
        user_response: str,
        analysis: Dict[str, Any],
        current_phase: str
    ) -> Dict[str, Any]:
        """Generate follow-up guidance based on user's response."""
        try:
            # Use AI to generate personalized follow-up
            guidance = await self._generate_ai_follow_up_guidance(
                session.original_narrative,
                user_response,
                analysis,
                current_phase
            )

            return guidance

        except Exception as e:
            logger.error(f"Error generating follow-up guidance: {e}")
            # Fallback guidance
            return {
                "message": "Thank you for sharing. Let's continue exploring this together.",
                "next_prompts": ["How does this new perspective feel to you?"],
                "encouragement": "You're doing great work in examining this experience."
            }

    def _calculate_progress_update(
        self,
        session: ReframeSession,
        analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate progress update based on session analysis."""
        # Base progress on various factors
        insight_score = len(analysis.get("insights", [])) * 10
        emotional_shift_score = analysis.get("emotional_shift_magnitude", 0) * 20
        engagement_score = min(len(analysis.get("response_analysis", {}).get("content", "")), 500) / 5

        # Calculate overall progress increment
        progress_increment = min((insight_score + emotional_shift_score + engagement_score) / 3, 25)

        new_progress = min(session.progress_percentage + progress_increment, 100)

        return {
            "previous_progress": session.progress_percentage,
            "new_progress": new_progress,
            "increment": progress_increment,
            "factors": {
                "insights": insight_score,
                "emotional_shift": emotional_shift_score,
                "engagement": engagement_score
            }
        }

    async def complete_session(
        self,
        db: Session,
        session: ReframeSession
    ) -> Dict[str, Any]:
        """Complete a reframing session and generate final insights."""
        try:
            # Generate session summary
            summary = await self._generate_session_summary(
                session.original_narrative,
                session.reframed_narrative or "",
                session.insights_gained or [],
                session.breakthrough_moments or []
            )

            # Calculate final outcomes
            outcomes = {
                "session_completed": True,
                "final_progress": session.progress_percentage,
                "insights_count": len(session.insights_gained or []),
                "breakthrough_moments": len(session.breakthrough_moments or []),
                "emotional_shift_achieved": session.emotional_shift is not None,
                "reframing_successful": session.reframed_narrative is not None,
                "summary": summary
            }

            # Update session status
            session.status = ReframeSessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()

            db.commit()

            return outcomes

        except Exception as e:
            logger.error(f"Error completing session: {e}")
            raise

    async def _generate_reframe_prompts(
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
                import json
                prompts = json.loads(response.content)
                return prompts if isinstance(prompts, list) else []
            except json.JSONDecodeError:
                # Fallback: split by lines and clean up
                lines = response.content.strip().split('\n')
                return [line.strip('- ').strip() for line in lines if line.strip()]

        except Exception as e:
            logger.error(f"Error generating reframe prompts: {e}")
            return []

    async def _analyze_reframe_response(
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
                import json
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

    async def _generate_ai_follow_up_guidance(
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
                import json
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

    async def _generate_session_summary(
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
                import json
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

    def _analyze_narrative(self, state: ReframeSessionState) -> ReframeSessionState:
        """Analyze the original narrative for patterns and themes."""
        try:
            state["current_phase"] = "narrative_analysis"

            # Simple analysis of the narrative
            narrative = state["original_narrative"]

            # Basic pattern detection
            negative_words = ["hurt", "pain", "trauma", "sad", "angry", "fear", "alone", "helpless"]
            positive_words = ["strong", "resilient", "hope", "love", "support", "growth", "learn"]

            negative_count = sum(1 for word in negative_words if word.lower() in narrative.lower())
            positive_count = sum(1 for word in positive_words if word.lower() in narrative.lower())

            # Store analysis in session context
            state["session_context"]["narrative_analysis"] = {
                "negative_indicators": negative_count,
                "positive_indicators": positive_count,
                "narrative_length": len(narrative),
                "emotional_tone": "negative" if negative_count > positive_count else "balanced"
            }

            state["progress_percentage"] = 25.0
            logger.info(f"Analyzed narrative for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error analyzing narrative: {e}")
            return state

    def _select_techniques(self, state: ReframeSessionState) -> ReframeSessionState:
        """Select appropriate reframing techniques based on analysis."""
        try:
            state["current_phase"] = "technique_selection"

            # Get trauma severity from life event
            trauma_severity = state["life_event"].get("trauma_severity", 0)

            # Select techniques based on severity and analysis
            techniques = []
            if trauma_severity > 7:
                techniques = ["self_compassion", "perspective_taking"]
            elif trauma_severity > 4:
                techniques = ["cognitive_restructuring", "self_compassion"]
            else:
                techniques = ["perspective_taking", "meaning_making"]

            state["techniques_used"] = techniques
            state["progress_percentage"] = 35.0

            logger.info(f"Selected techniques for session {state['session_id']}: {techniques}")
            return state

        except Exception as e:
            logger.error(f"Error selecting techniques: {e}")
            return state

    def _reframing_phase(self, state: ReframeSessionState) -> ReframeSessionState:
        """Conduct the reframing phase."""
        try:
            state["current_phase"] = "reframing"
            state["progress_percentage"] = 50.0

            # Add reframing guidance to AI guidance
            state["ai_guidance"].append({
                "phase": "reframing",
                "guidance": {
                    "message": "Now let's work on reframing your experience with new perspectives.",
                    "techniques": state["techniques_used"],
                    "focus": "cognitive restructuring and perspective shifts"
                },
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Entered reframing phase for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error in reframing phase: {e}")
            return state

    def _integration_phase(self, state: ReframeSessionState) -> ReframeSessionState:
        """Conduct the integration phase."""
        try:
            state["current_phase"] = "integration"
            state["progress_percentage"] = 75.0

            # Add integration guidance
            state["ai_guidance"].append({
                "phase": "integration",
                "guidance": {
                    "message": "Let's integrate these new insights and practice self-compassion.",
                    "focus": "meaning-making and self-compassion",
                    "exercises": [ex["name"] for ex in state["compassion_exercises"]]
                },
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Entered integration phase for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error in integration phase: {e}")
            return state

    def _compassion_exercises(self, state: ReframeSessionState) -> ReframeSessionState:
        """Guide through self-compassion exercises."""
        try:
            state["current_phase"] = "compassion_exercises"
            state["progress_percentage"] = 85.0

            # Select appropriate exercises based on trauma severity
            trauma_severity = state["life_event"].get("trauma_severity", 0)

            exercises = []
            if trauma_severity > 6:
                exercises.append(self.compassion_exercises["inner_child_healing"])
                exercises.append(self.compassion_exercises["self_forgiveness"])
            elif trauma_severity > 3:
                exercises.append(self.compassion_exercises["loving_kindness"])
                exercises.append(self.compassion_exercises["self_forgiveness"])
            else:
                exercises.append(self.compassion_exercises["loving_kindness"])

            state["compassion_exercises"] = exercises

            logger.info(f"Selected compassion exercises for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error in compassion exercises: {e}")
            return state

    def _validate_progress(self, state: ReframeSessionState) -> ReframeSessionState:
        """Validate session progress and outcomes."""
        try:
            state["current_phase"] = "validation"

            # Calculate final progress
            insights_count = len(state["insights_gained"])
            breakthroughs_count = len(state["breakthrough_moments"])

            # Validate completion criteria
            completion_score = 0
            if insights_count > 0:
                completion_score += 30
            if breakthroughs_count > 0:
                completion_score += 30
            if state["reframed_narrative"]:
                completion_score += 40

            state["progress_percentage"] = min(completion_score, 95.0)

            # Store validation results
            state["session_context"]["validation"] = {
                "completion_score": completion_score,
                "insights_count": insights_count,
                "breakthroughs_count": breakthroughs_count,
                "has_reframed_narrative": bool(state["reframed_narrative"]),
                "validation_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Validated progress for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error validating progress: {e}")
            return state

    def _finalize_session(self, state: ReframeSessionState) -> ReframeSessionState:
        """Finalize the reframing session."""
        try:
            state["current_phase"] = "finalized"
            state["progress_percentage"] = 100.0

            # Create final session summary
            final_summary = {
                "session_completed": True,
                "total_insights": len(state["insights_gained"]),
                "total_breakthroughs": len(state["breakthrough_moments"]),
                "techniques_used": state["techniques_used"],
                "exercises_completed": len(state["compassion_exercises"]),
                "final_progress": state["progress_percentage"],
                "completion_timestamp": datetime.now().isoformat()
            }

            state["session_context"]["final_summary"] = final_summary

            logger.info(f"Finalized session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error finalizing session: {e}")
            return state

    def _generate_insights(self, state: ReframeSessionState) -> ReframeSessionState:
        """Generate insights from the reframing process."""
        try:
            state["current_phase"] = "insight_generation"
            state["progress_percentage"] = 60.0

            # Generate insights based on the session progress
            insights = []

            # Check if user has engaged with reframing
            if len(state["ai_guidance"]) > 1:
                insights.append("You've shown openness to exploring new perspectives")

            # Check trauma severity and add appropriate insights
            trauma_severity = state["life_event"].get("trauma_severity", 0)
            if trauma_severity > 5:
                insights.append("Recognizing the impact of this experience is an important step in healing")

            # Add technique-specific insights
            for technique in state["techniques_used"]:
                if technique == "self_compassion":
                    insights.append("Practicing self-compassion can transform your relationship with difficult experiences")
                elif technique == "cognitive_restructuring":
                    insights.append("Challenging negative thought patterns opens space for new possibilities")
                elif technique == "perspective_taking":
                    insights.append("Viewing experiences from different angles reveals hidden strengths and growth")
                elif technique == "meaning_making":
                    insights.append("Finding meaning in difficult experiences can be a source of resilience and wisdom")

            # Add general healing insights
            insights.append("Your willingness to engage in this process demonstrates courage and commitment to healing")

            state["insights_gained"].extend(insights)

            logger.info(f"Generated insights for session {state['session_id']}")
            return state

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return state