"""
AI Chat service using LangGraph for empathetic conversation flow.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from config import settings
from models.conversation import Conversation, Message
from models.emotion import EmotionAnalysis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """Enhanced state for the chat workflow."""
    messages: Annotated[List, add_messages]
    user_id: int
    conversation_id: Optional[int]
    emotion_context: Optional[Dict]
    response_tone: str
    therapeutic_approach: str
    conversation_memory: Optional[Dict]
    crisis_indicators: List[str]
    session_context: Optional[Dict]
    user_preferences: Optional[Dict]
    conversation_stage: str  # opening, exploration, intervention, closure


class AIChat:
    """Enhanced AI Chat service with sophisticated conversation management."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
            streaming=True
        )
        self.workflow = self._create_workflow()

        # Initialize Inner Ally agent for personalization
        try:
            from services.inner_ally import InnerAllyAgent
            self.inner_ally = InnerAllyAgent()
        except ImportError:
            logger.warning("Inner Ally agent not available")
            self.inner_ally = None

        # Enhanced therapeutic approaches with detailed configurations
        self.therapeutic_approaches = {
            "cognitive_behavioral": {
                "focus": "thought_patterns",
                "techniques": ["cognitive_restructuring", "behavioral_activation"],
                "tone": "collaborative_questioning"
            },
            "mindfulness_based": {
                "focus": "present_moment_awareness",
                "techniques": ["breathing_exercises", "body_scan", "grounding"],
                "tone": "calm_guiding"
            },
            "emotion_regulation": {
                "focus": "emotional_management",
                "techniques": ["distress_tolerance", "emotional_validation"],
                "tone": "validating_supportive"
            },
            "trauma_informed": {
                "focus": "safety_stabilization",
                "techniques": ["grounding", "resource_building", "containment"],
                "tone": "gentle_stabilizing"
            },
            "person_centered": {
                "focus": "self_exploration",
                "techniques": ["active_listening", "reflection", "empathy"],
                "tone": "empathetic_accepting"
            }
        }

        # Crisis indicators for safety monitoring - more specific keywords
        self.crisis_keywords = [
            "suicide", "kill myself", "end it all", "want to die",
            "hurt myself", "self-harm", "cutting", "overdose",
            "end my life", "better off dead", "no point in living"
        ]

        # Conversation memory for context retention
        self.conversation_memory = {}

    def _create_workflow(self) -> StateGraph:
        """Create the enhanced LangGraph workflow for sophisticated conversation management."""
        workflow = StateGraph(ChatState)

        # Add workflow nodes
        workflow.add_node("initialize_session", self._initialize_session)
        workflow.add_node("analyze_context", self._analyze_context)
        workflow.add_node("detect_crisis", self._detect_crisis)
        workflow.add_node("determine_approach", self._determine_approach)
        workflow.add_node("manage_conversation_flow", self._manage_conversation_flow)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("validate_response", self._validate_response)
        workflow.add_node("update_memory", self._update_memory)
        workflow.add_node("crisis_intervention", self._crisis_intervention)

        # Define workflow edges
        workflow.add_edge("initialize_session", "analyze_context")
        workflow.add_edge("analyze_context", "detect_crisis")

        # Conditional routing based on crisis detection
        workflow.add_conditional_edges(
            "detect_crisis",
            self._route_crisis_detection,
            {
                "crisis": "crisis_intervention",
                "normal": "determine_approach"
            }
        )

        workflow.add_edge("crisis_intervention", "update_memory")
        workflow.add_edge("determine_approach", "manage_conversation_flow")
        workflow.add_edge("manage_conversation_flow", "generate_response")
        workflow.add_edge("generate_response", "validate_response")
        workflow.add_edge("validate_response", "update_memory")
        workflow.add_edge("update_memory", END)

        # Set entry point
        workflow.set_entry_point("initialize_session")

        return workflow.compile()

    async def chat(
        self,
        user_message: str,
        user_id: int,
        db: Session,
        conversation_id: Optional[int] = None,
        emotion_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message using the enhanced LangGraph workflow.

        Args:
            user_message: The user's message
            user_id: User ID
            db: Database session
            conversation_id: Optional conversation ID
            emotion_analysis: Optional emotion analysis data

        Returns:
            Dictionary containing the AI response and metadata
        """
        try:
            # Get conversation history
            conversation_history = self._get_conversation_history(db, conversation_id) if conversation_id else []

            # Get user persona and longitudinal context if Inner Ally is available
            user_persona = {}
            longitudinal_context = {}
            if self.inner_ally:
                try:
                    user_persona = self.inner_ally.get_user_persona(user_id, db)
                    longitudinal_context = self.inner_ally.get_longitudinal_context(user_id, db)
                except Exception as e:
                    logger.warning(f"Could not load Inner Ally context: {e}")

            # Prepare enhanced initial state
            initial_state = ChatState(
                messages=conversation_history + [HumanMessage(content=user_message)],
                user_id=user_id,
                conversation_id=conversation_id,
                emotion_context=emotion_analysis or {},
                response_tone="empathetic",
                therapeutic_approach="person_centered",
                conversation_memory=self.conversation_memory.get(str(user_id), {}),
                crisis_indicators=[],
                session_context={
                    "db": db,
                    "timestamp": datetime.now(),
                    "message_count": len(conversation_history) + 1,
                    "user_persona": user_persona,
                    "longitudinal_context": longitudinal_context
                },
                user_preferences={},
                conversation_stage="exploration"
            )

            # Execute the full LangGraph workflow
            final_state = await self.workflow.ainvoke(initial_state)

            # Extract response from final state
            ai_message = final_state["messages"][-1]
            ai_response = ai_message.content if hasattr(ai_message, 'content') else str(ai_message)

            return {
                "response": ai_response,
                "therapeutic_approach": final_state.get("therapeutic_approach", "person_centered"),
                "response_tone": final_state.get("response_tone", "empathetic"),
                "conversation_id": conversation_id,
                "conversation_stage": final_state.get("conversation_stage", "exploration"),
                "crisis_detected": len(final_state.get("crisis_indicators", [])) > 0,
                "session_metadata": {
                    "emotion_context": final_state.get("emotion_context", {}),
                    "conversation_memory": final_state.get("conversation_memory", {})
                }
            }

        except Exception as e:
            logger.error(f"Error in chat workflow: {e}")
            # Fallback to simple response
            try:
                fallback_response = await self._generate_simple_response(
                    user_message, emotion_analysis, conversation_history
                )
                return {
                    "response": fallback_response,
                    "therapeutic_approach": "person_centered",
                    "response_tone": "empathetic",
                    "conversation_id": conversation_id,
                    "crisis_detected": False,
                    "fallback_used": True
                }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return {
                    "response": "I'm here to listen and support you. Could you tell me more about what's on your mind?",
                    "therapeutic_approach": "person_centered",
                    "response_tone": "empathetic",
                    "conversation_id": conversation_id,
                    "crisis_detected": False,
                    "fallback_used": True
                }

    async def chat_stream(
        self,
        user_message: str,
        user_id: int,
        db: Session,
        conversation_id: Optional[int] = None,
        emotion_analysis: Optional[Dict] = None
    ):
        """
        Stream chat response using Server-Sent Events.

        Args:
            user_message: The user's message
            user_id: User ID
            db: Database session
            conversation_id: Optional conversation ID
            emotion_analysis: Optional emotion analysis data

        Yields:
            Streaming response chunks
        """
        try:
            # Get conversation history
            conversation_history = self._get_conversation_history(db, conversation_id) if conversation_id else []

            # Prepare initial state for streaming
            initial_state = ChatState(
                messages=conversation_history + [HumanMessage(content=user_message)],
                user_id=user_id,
                conversation_id=conversation_id,
                emotion_context=emotion_analysis or {},
                response_tone="empathetic",
                therapeutic_approach="person_centered",
                conversation_memory=self.conversation_memory.get(str(user_id), {}),
                crisis_indicators=[],
                session_context={
                    "db": db,
                    "timestamp": datetime.now(),
                    "message_count": len(conversation_history) + 1
                },
                user_preferences={},
                conversation_stage="exploration"
            )

            # Process through workflow up to response generation
            state = self._initialize_session(initial_state)
            state = self._analyze_context(state)
            state = self._detect_crisis(state)

            # Check for crisis and handle appropriately
            if state.get("crisis_indicators", []):
                state = self._crisis_intervention(state)
                # For crisis, send complete response immediately
                yield {
                    "type": "response_chunk",
                    "content": state["messages"][-1].content,
                    "is_complete": True,
                    "metadata": {
                        "therapeutic_approach": state.get("therapeutic_approach", "trauma_informed"),
                        "crisis_detected": True
                    }
                }
                return

            # Continue with normal flow
            state = self._determine_approach(state)
            state = self._manage_conversation_flow(state)

            # Stream the response generation
            async for chunk in self._generate_streaming_response(state):
                yield chunk

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield {
                "type": "error",
                "content": "I'm here to listen and support you. Could you tell me more about what's on your mind?",
                "is_complete": True,
                "metadata": {"error": True}
            }

    async def _generate_streaming_response(self, state: ChatState):
        """Generate streaming response using the LLM."""
        try:
            approach = state["therapeutic_approach"]
            tone = state["response_tone"]

            # Create system prompt
            system_prompt = self._get_system_prompt(approach, tone)

            # Prepare messages for LLM
            messages = [SystemMessage(content=system_prompt)] + state["messages"]

            # Send metadata first
            yield {
                "type": "metadata",
                "content": "",
                "is_complete": False,
                "metadata": {
                    "therapeutic_approach": approach,
                    "response_tone": tone,
                    "conversation_stage": state.get("conversation_stage", "exploration")
                }
            }

            # Stream the response
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield {
                        "type": "response_chunk",
                        "content": chunk.content,
                        "is_complete": False,
                        "metadata": {}
                    }

            # Send completion signal
            yield {
                "type": "response_complete",
                "content": "",
                "is_complete": True,
                "metadata": {
                    "full_response": full_response,
                    "therapeutic_approach": approach,
                    "response_tone": tone
                }
            }

            # Update state with complete response
            state["messages"].append(AIMessage(content=full_response))
            state = self._validate_response(state)
            state = self._update_memory(state)

        except Exception as e:
            logger.error(f"Error in streaming response generation: {e}")
            yield {
                "type": "error",
                "content": "I understand you're going through something difficult. I'm here to listen and support you.",
                "is_complete": True,
                "metadata": {"error": True}
            }

    # Enhanced workflow methods
    def _initialize_session(self, state: ChatState) -> ChatState:
        """Initialize the conversation session with context and preferences."""
        try:
            user_id = str(state["user_id"])

            # Load or initialize conversation memory
            if user_id not in self.conversation_memory:
                self.conversation_memory[user_id] = {
                    "session_count": 0,
                    "dominant_themes": [],
                    "therapeutic_preferences": {},
                    "conversation_patterns": {},
                    "last_session": None
                }

            # Update session info
            self.conversation_memory[user_id]["session_count"] += 1
            self.conversation_memory[user_id]["last_session"] = datetime.now().isoformat()

            # Update state with memory
            state["conversation_memory"] = self.conversation_memory[user_id]

            # Determine conversation stage based on message count
            message_count = state["session_context"]["message_count"]
            if message_count <= 2:
                state["conversation_stage"] = "opening"
            elif message_count <= 10:
                state["conversation_stage"] = "exploration"
            elif message_count <= 20:
                state["conversation_stage"] = "intervention"
            else:
                state["conversation_stage"] = "closure"

            return state

        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            return state

    def _detect_crisis(self, state: ChatState) -> ChatState:
        """Detect crisis indicators in the conversation."""
        try:
            # Get the latest user message
            user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            if not user_messages:
                return state

            latest_message = user_messages[-1].content.lower()

            # Check for crisis keywords
            crisis_indicators = []
            for keyword in self.crisis_keywords:
                if keyword in latest_message:
                    crisis_indicators.append(keyword)

            # Only check for explicit crisis keywords - no emotion-based triggers for normal emotional distress
            # Removed emotion-based crisis detection to avoid false positives with normal sadness/depression

            state["crisis_indicators"] = crisis_indicators
            return state

        except Exception as e:
            logger.error(f"Error detecting crisis: {e}")
            state["crisis_indicators"] = []
            return state

    def _route_crisis_detection(self, state: ChatState) -> str:
        """Route based on crisis detection results."""
        crisis_indicators = state.get("crisis_indicators", [])
        return "crisis" if crisis_indicators else "normal"

    def _crisis_intervention(self, state: ChatState) -> ChatState:
        """Handle crisis intervention with appropriate resources and support."""
        try:
            crisis_indicators = state.get("crisis_indicators", [])

            # Only provide crisis resources for explicit self-harm indicators
            if any(keyword in ["suicide", "kill myself", "hurt myself", "self-harm", "end my life"] for keyword in crisis_indicators):
                crisis_response = """I'm really concerned about what you're sharing with me. Your feelings are valid, and I want you to know that you're not alone in this.

If you're having thoughts of hurting yourself or ending your life, please reach out for immediate help:
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

You deserve support and care. Would you like to talk about what's making you feel this way?"""
            else:
                # For emotional overwhelm, provide supportive response
                crisis_response = """I can hear that you're going through a really difficult time right now. These intense feelings can be overwhelming, and it's completely understandable that you're struggling.

You're not alone in this. Sometimes when emotions feel too big, it can help to take things one moment at a time. Would you like to talk about what's weighing on your heart right now? I'm here to listen and support you."""

            # Add crisis response to messages
            state["messages"].append(AIMessage(content=crisis_response))

            # Update therapeutic approach for crisis
            state["therapeutic_approach"] = "trauma_informed"
            state["response_tone"] = "gentle_stabilizing"

            return state

        except Exception as e:
            logger.error(f"Error in crisis intervention: {e}")
            return state

    def _manage_conversation_flow(self, state: ChatState) -> ChatState:
        """Manage the flow of conversation based on stage and context."""
        try:
            stage = state.get("conversation_stage", "exploration")
            approach_config = self.therapeutic_approaches.get(
                state.get("therapeutic_approach", "person_centered"), {}
            )

            # Adjust approach based on conversation stage
            if stage == "opening":
                # Focus on building rapport and understanding
                state["response_tone"] = "warm_welcoming"
            elif stage == "exploration":
                # Deep listening and exploration
                state["response_tone"] = approach_config.get("tone", "empathetic")
            elif stage == "intervention":
                # Gentle guidance and coping strategies
                state["response_tone"] = "supportive_guiding"
            elif stage == "closure":
                # Summarizing and planning next steps
                state["response_tone"] = "hopeful_summarizing"

            return state

        except Exception as e:
            logger.error(f"Error managing conversation flow: {e}")
            return state

    def _update_memory(self, state: ChatState) -> ChatState:
        """Update conversation memory with insights from the session."""
        try:
            user_id = str(state["user_id"])
            emotion_context = state.get("emotion_context", {})

            if user_id in self.conversation_memory:
                memory = self.conversation_memory[user_id]

                # Update dominant themes
                if emotion_context.get("themes"):
                    for theme in emotion_context["themes"]:
                        if theme not in memory["dominant_themes"]:
                            memory["dominant_themes"].append(theme)

                # Update therapeutic preferences based on what worked
                approach = state.get("therapeutic_approach")
                if approach and approach not in memory["therapeutic_preferences"]:
                    memory["therapeutic_preferences"][approach] = {
                        "used_count": 1,
                        "effectiveness": "unknown"
                    }
                elif approach:
                    memory["therapeutic_preferences"][approach]["used_count"] += 1

                # Update conversation patterns
                stage = state.get("conversation_stage")
                if stage:
                    if stage not in memory["conversation_patterns"]:
                        memory["conversation_patterns"][stage] = 1
                    else:
                        memory["conversation_patterns"][stage] += 1

            return state

        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return state

    def _analyze_context(self, state: ChatState) -> ChatState:
        """Analyze the conversation context and user's emotional state."""
        try:
            # Extract emotion context if available
            emotion_context = state.get("emotion_context", {})

            # Analyze recent message patterns
            recent_messages = state["messages"][-5:]  # Last 5 messages

            # Determine emotional intensity
            if emotion_context:
                dominant_emotions = []
                for emotion in ["sadness", "anger", "fear", "joy"]:
                    if emotion_context.get(emotion, 0) > 0.6:
                        dominant_emotions.append(emotion)

                state["emotion_context"] = {
                    **emotion_context,
                    "dominant_emotions": dominant_emotions,
                    "emotional_intensity": max(emotion_context.get(emotion, 0) for emotion in ["sadness", "anger", "fear"])
                }

            return state

        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return state

    def _determine_approach(self, state: ChatState) -> ChatState:
        """Determine the therapeutic approach based on context."""
        try:
            emotion_context = state.get("emotion_context", {})

            # Determine approach based on dominant emotions
            if emotion_context.get("sadness", 0) > 0.7:
                approach = "cognitive_behavioral"
                tone = "gentle_supportive"
            elif emotion_context.get("fear", 0) > 0.7 or emotion_context.get("themes", []):
                if "trauma_related" in emotion_context.get("themes", []):
                    approach = "trauma_informed"
                    tone = "calm_grounding"
                else:
                    approach = "mindfulness_based"
                    tone = "reassuring"
            elif emotion_context.get("anger", 0) > 0.7:
                approach = "emotion_regulation"
                tone = "validating_calm"
            else:
                approach = "person_centered"
                tone = "empathetic"

            state["therapeutic_approach"] = approach
            state["response_tone"] = tone

            return state

        except Exception as e:
            logger.error(f"Error determining approach: {e}")
            state["therapeutic_approach"] = "person_centered"
            state["response_tone"] = "empathetic"
            return state

    def _generate_response(self, state: ChatState) -> ChatState:
        """Generate an empathetic AI response."""
        try:
            approach = state["therapeutic_approach"]
            tone = state["response_tone"]

            # Create system prompt based on approach
            system_prompt = self._get_system_prompt(approach, tone)

            # Prepare messages for LLM
            messages = [SystemMessage(content=system_prompt)] + state["messages"]

            # Generate response
            response = self.llm.invoke(messages)

            # Add AI response to messages
            state["messages"].append(AIMessage(content=response.content))

            return state

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            fallback_response = "I understand you're going through something difficult. I'm here to listen and support you."
            state["messages"].append(AIMessage(content=fallback_response))
            return state

    def _validate_response(self, state: ChatState) -> ChatState:
        """Validate the AI response for appropriateness and safety."""
        try:
            ai_response = state["messages"][-1].content

            # Only check for explicitly harmful content that encourages self-harm
            harmful_patterns = ["you should hurt yourself", "you should kill yourself", "end your life"]
            if any(pattern in ai_response.lower() for pattern in harmful_patterns):
                # Replace with supportive response
                supportive_response = ("I'm here to support you through this difficult time. Your feelings are valid, and you deserve care and compassion. "
                                     "Would you like to talk about what's weighing on your heart right now?")
                state["messages"][-1] = AIMessage(content=supportive_response)

            return state

        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return state

    def _get_system_prompt(self, approach: str, tone: str) -> str:
        """Get system prompt based on therapeutic approach and tone."""
        base_prompt = """You are InnerCalm, an empathetic AI companion designed to help individuals find peace with themselves through personalized emotional support and healing.

        Your mission is to guide users on their journey to inner peace by:
        - Helping them recognize and understand their emotional patterns
        - Providing personalized healing exercises and coping strategies
        - Offering a safe space for emotional expression and self-discovery
        - Supporting them in building resilience and emotional wellness

        Core principles:
        - Always validate the user's feelings and experiences
        - Use warm, empathetic, and non-judgmental language
        - Ask thoughtful questions that encourage self-reflection
        - Offer practical guidance and healing techniques
        - Help users find their own inner strength and wisdom
        - Provide hope and perspective while honoring their current experience
        - Only suggest professional help for genuine crisis situations

        Remember: You are here to support their journey to inner peace and emotional healing, not to diagnose or provide medical advice.
        """

        approach_prompts = {
            "cognitive_behavioral": """
            Focus on helping the user identify thought patterns and their connection to emotions.
            Gently guide them to examine their thoughts and consider alternative perspectives.
            Use phrases like "What thoughts come to mind when..." or "How might we look at this differently?"
            """,
            "mindfulness_based": """
            Emphasize present-moment awareness and acceptance.
            Guide the user to notice their current experience without judgment.
            Use grounding techniques and encourage mindful observation of thoughts and feelings.
            """,
            "emotion_regulation": """
            Help the user understand and manage intense emotions.
            Validate their feelings while offering coping strategies.
            Focus on emotional awareness and healthy expression.
            """,
            "trauma_informed": """
            Approach with extra sensitivity and care.
            Emphasize safety, choice, and empowerment.
            Avoid pushing for details and respect boundaries.
            Focus on grounding and stabilization.
            """,
            "person_centered": """
            Provide unconditional positive regard and genuine empathy.
            Reflect the user's feelings and help them explore their own solutions.
            Trust in their capacity for growth and self-understanding.
            """
        }

        tone_modifiers = {
            "gentle_supportive": "Use a gentle, nurturing tone. Offer comfort and reassurance.",
            "calm_grounding": "Maintain a calm, steady presence. Focus on safety and grounding.",
            "validating_calm": "Validate their experience while maintaining a calm, stable energy.",
            "reassuring": "Provide reassurance and hope while acknowledging their struggles.",
            "empathetic": "Show deep empathy and understanding for their experience."
        }

        return f"{base_prompt}\n\nApproach: {approach_prompts.get(approach, approach_prompts['person_centered'])}\n\nTone: {tone_modifiers.get(tone, tone_modifiers['empathetic'])}"

    def _get_conversation_history(self, db: Session, conversation_id: int) -> List:
        """Get conversation history for context."""
        try:
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp).limit(settings.max_conversation_history).all()

            history = []
            for msg in messages:
                if msg.is_user_message:
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))

            return history

        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def _generate_simple_response(
        self,
        user_message: str,
        emotion_analysis: Optional[Dict],
        conversation_history: List
    ) -> str:
        """Generate a simple empathetic response using OpenAI."""
        try:
            # Determine therapeutic approach based on emotions
            approach = "person_centered"
            if emotion_analysis:
                if emotion_analysis.get("sadness", 0) > 0.7:
                    approach = "cognitive_behavioral"
                elif emotion_analysis.get("fear", 0) > 0.7:
                    approach = "mindfulness_based"
                elif emotion_analysis.get("anger", 0) > 0.7:
                    approach = "emotion_regulation"

            # Create system prompt
            system_prompt = self._get_system_prompt(approach, "empathetic")

            # Prepare messages
            messages = [SystemMessage(content=system_prompt)]

            # Add conversation history (last 5 messages)
            if conversation_history:
                messages.extend(conversation_history[-5:])

            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # Generate response
            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"Error generating simple response: {e}")
            return "I'm here to listen and support you. Could you tell me more about what's on your mind?"
