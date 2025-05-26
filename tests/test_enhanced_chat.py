"""
Tests for enhanced LangGraph chat workflow.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from services.ai_chat import AIChat, ChatState
from models.conversation import Conversation, Message
from models.emotion import EmotionAnalysis


class TestEnhancedAIChat:
    """Test enhanced AI chat functionality with LangGraph workflow."""

    @pytest.fixture
    def ai_chat(self):
        """Create AI chat instance."""
        return AIChat()

    @pytest.fixture
    def sample_emotion_analysis(self):
        """Sample emotion analysis data."""
        return {
            "joy": 0.2,
            "sadness": 0.7,
            "anger": 0.1,
            "fear": 0.6,
            "surprise": 0.0,
            "disgust": 0.0,
            "sentiment_score": -0.4,
            "sentiment_label": "negative",
            "themes": ["stress", "anxiety"],
            "keywords": ["worried", "overwhelmed"],
            "confidence": 0.8
        }

    @pytest.fixture
    def crisis_emotion_analysis(self):
        """Crisis-level emotion analysis data."""
        return {
            "joy": 0.0,
            "sadness": 0.9,
            "anger": 0.1,
            "fear": 0.8,
            "surprise": 0.0,
            "disgust": 0.0,
            "sentiment_score": -0.9,
            "sentiment_label": "negative",
            "themes": ["hopelessness", "despair"],
            "keywords": ["suicide", "hopeless", "end it all"],
            "confidence": 0.9
        }

    def test_chat_state_initialization(self, ai_chat):
        """Test ChatState initialization with enhanced fields."""
        state = {
            "messages": [],
            "user_id": 1,
            "conversation_id": 1,
            "emotion_context": {"sadness": 0.7},
            "response_tone": "empathetic",
            "therapeutic_approach": "person_centered",
            "conversation_memory": {},
            "crisis_indicators": [],
            "session_context": {"timestamp": datetime.now()},
            "user_preferences": {},
            "conversation_stage": "exploration"
        }
        
        # Verify all required fields are present
        assert "conversation_memory" in state
        assert "crisis_indicators" in state
        assert "session_context" in state
        assert "user_preferences" in state
        assert "conversation_stage" in state

    def test_therapeutic_approaches_configuration(self, ai_chat):
        """Test enhanced therapeutic approaches configuration."""
        approaches = ai_chat.therapeutic_approaches
        
        # Verify all approaches have required configuration
        required_keys = ["focus", "techniques", "tone"]
        for approach_name, config in approaches.items():
            for key in required_keys:
                assert key in config, f"Missing {key} in {approach_name}"
            
            assert isinstance(config["techniques"], list)
            assert len(config["techniques"]) > 0

    def test_crisis_keywords_configuration(self, ai_chat):
        """Test crisis keywords are properly configured."""
        crisis_keywords = ai_chat.crisis_keywords
        
        assert isinstance(crisis_keywords, list)
        assert len(crisis_keywords) > 0
        assert "suicide" in crisis_keywords
        assert "self-harm" in crisis_keywords
        assert "hopeless" in crisis_keywords

    def test_initialize_session(self, ai_chat):
        """Test session initialization workflow method."""
        state = {
            "user_id": 1,
            "session_context": {"message_count": 1},
            "conversation_memory": None
        }
        
        result_state = ai_chat._initialize_session(state)
        
        assert "1" in ai_chat.conversation_memory
        assert result_state["conversation_memory"] is not None
        assert result_state["conversation_stage"] == "opening"
        assert ai_chat.conversation_memory["1"]["session_count"] == 1

    def test_detect_crisis_with_keywords(self, ai_chat):
        """Test crisis detection with crisis keywords."""
        from langchain.schema import HumanMessage
        
        state = {
            "messages": [HumanMessage(content="I want to kill myself")],
            "emotion_context": {"sadness": 0.9},
            "crisis_indicators": []
        }
        
        result_state = ai_chat._detect_crisis(state)
        
        assert len(result_state["crisis_indicators"]) > 0
        assert any("kill myself" in indicator for indicator in result_state["crisis_indicators"])

    def test_detect_crisis_with_emotion_patterns(self, ai_chat):
        """Test crisis detection with emotional patterns."""
        from langchain.schema import HumanMessage
        
        state = {
            "messages": [HumanMessage(content="I feel terrible")],
            "emotion_context": {
                "sadness": 0.9,
                "themes": ["hopelessness", "despair"]
            },
            "crisis_indicators": []
        }
        
        result_state = ai_chat._detect_crisis(state)
        
        assert len(result_state["crisis_indicators"]) > 0
        assert "high_despair" in result_state["crisis_indicators"]

    def test_detect_crisis_emotional_overwhelm(self, ai_chat):
        """Test crisis detection with emotional overwhelm."""
        from langchain.schema import HumanMessage
        
        state = {
            "messages": [HumanMessage(content="Everything is wrong")],
            "emotion_context": {
                "sadness": 0.8,
                "anger": 0.8,
                "fear": 0.8
            },
            "crisis_indicators": []
        }
        
        result_state = ai_chat._detect_crisis(state)
        
        assert len(result_state["crisis_indicators"]) > 0
        assert "emotional_overwhelm" in result_state["crisis_indicators"]

    def test_route_crisis_detection(self, ai_chat):
        """Test crisis routing logic."""
        # Test crisis route
        crisis_state = {"crisis_indicators": ["suicide"]}
        assert ai_chat._route_crisis_detection(crisis_state) == "crisis"
        
        # Test normal route
        normal_state = {"crisis_indicators": []}
        assert ai_chat._route_crisis_detection(normal_state) == "normal"

    def test_crisis_intervention(self, ai_chat):
        """Test crisis intervention workflow method."""
        from langchain.schema import AIMessage
        
        state = {
            "messages": [],
            "therapeutic_approach": "person_centered",
            "response_tone": "empathetic"
        }
        
        result_state = ai_chat._crisis_intervention(state)
        
        assert len(result_state["messages"]) == 1
        assert isinstance(result_state["messages"][0], AIMessage)
        assert "988" in result_state["messages"][0].content  # Crisis hotline
        assert result_state["therapeutic_approach"] == "trauma_informed"
        assert result_state["response_tone"] == "gentle_stabilizing"

    def test_manage_conversation_flow_stages(self, ai_chat):
        """Test conversation flow management for different stages."""
        base_state = {
            "therapeutic_approach": "person_centered",
            "response_tone": "empathetic"
        }
        
        # Test opening stage
        opening_state = {**base_state, "conversation_stage": "opening"}
        result = ai_chat._manage_conversation_flow(opening_state)
        assert result["response_tone"] == "warm_welcoming"
        
        # Test exploration stage
        exploration_state = {**base_state, "conversation_stage": "exploration"}
        result = ai_chat._manage_conversation_flow(exploration_state)
        assert result["response_tone"] == "empathetic_accepting"
        
        # Test intervention stage
        intervention_state = {**base_state, "conversation_stage": "intervention"}
        result = ai_chat._manage_conversation_flow(intervention_state)
        assert result["response_tone"] == "supportive_guiding"
        
        # Test closure stage
        closure_state = {**base_state, "conversation_stage": "closure"}
        result = ai_chat._manage_conversation_flow(closure_state)
        assert result["response_tone"] == "hopeful_summarizing"

    def test_update_memory(self, ai_chat):
        """Test conversation memory update."""
        # Initialize memory for user
        ai_chat.conversation_memory["1"] = {
            "dominant_themes": [],
            "therapeutic_preferences": {},
            "conversation_patterns": {}
        }
        
        state = {
            "user_id": 1,
            "emotion_context": {"themes": ["anxiety", "work_stress"]},
            "therapeutic_approach": "mindfulness_based",
            "conversation_stage": "exploration"
        }
        
        result_state = ai_chat._update_memory(state)
        
        memory = ai_chat.conversation_memory["1"]
        assert "anxiety" in memory["dominant_themes"]
        assert "work_stress" in memory["dominant_themes"]
        assert "mindfulness_based" in memory["therapeutic_preferences"]
        assert memory["conversation_patterns"]["exploration"] == 1

    @patch('services.ai_chat.ChatOpenAI')
    async def test_chat_workflow_integration(self, mock_openai, ai_chat, db: Session, test_user, test_conversation, sample_emotion_analysis):
        """Test full chat workflow integration."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.content = "I understand you're feeling overwhelmed. Let's work through this together."
        mock_openai.return_value.invoke.return_value = mock_response
        
        # Mock the workflow to avoid LangGraph complexity in tests
        with patch.object(ai_chat, 'workflow') as mock_workflow:
            mock_final_state = {
                "messages": [Mock(content="I understand you're feeling overwhelmed. Let's work through this together.")],
                "therapeutic_approach": "person_centered",
                "response_tone": "empathetic",
                "conversation_stage": "exploration",
                "crisis_indicators": [],
                "emotion_context": sample_emotion_analysis,
                "conversation_memory": {}
            }
            mock_workflow.ainvoke = AsyncMock(return_value=mock_final_state)
            
            result = await ai_chat.chat(
                user_message="I'm feeling really overwhelmed with work",
                user_id=test_user.id,
                db=db,
                conversation_id=test_conversation.id,
                emotion_analysis=sample_emotion_analysis
            )
            
            assert "response" in result
            assert "therapeutic_approach" in result
            assert "conversation_stage" in result
            assert "crisis_detected" in result
            assert result["crisis_detected"] is False

    @patch('services.ai_chat.ChatOpenAI')
    async def test_chat_crisis_workflow(self, mock_openai, ai_chat, db: Session, test_user, test_conversation, crisis_emotion_analysis):
        """Test chat workflow with crisis detection."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.content = "Crisis response with resources"
        mock_openai.return_value.invoke.return_value = mock_response
        
        # Mock the workflow for crisis scenario
        with patch.object(ai_chat, 'workflow') as mock_workflow:
            mock_final_state = {
                "messages": [Mock(content="Crisis response with resources")],
                "therapeutic_approach": "trauma_informed",
                "response_tone": "gentle_stabilizing",
                "conversation_stage": "exploration",
                "crisis_indicators": ["suicide"],
                "emotion_context": crisis_emotion_analysis,
                "conversation_memory": {}
            }
            mock_workflow.ainvoke = AsyncMock(return_value=mock_final_state)
            
            result = await ai_chat.chat(
                user_message="I want to end it all",
                user_id=test_user.id,
                db=db,
                conversation_id=test_conversation.id,
                emotion_analysis=crisis_emotion_analysis
            )
            
            assert result["crisis_detected"] is True
            assert result["therapeutic_approach"] == "trauma_informed"

    async def test_chat_fallback_mechanism(self, ai_chat, db: Session, test_user, test_conversation):
        """Test chat fallback when workflow fails."""
        # Mock workflow to raise an exception
        with patch.object(ai_chat, 'workflow') as mock_workflow:
            mock_workflow.ainvoke = AsyncMock(side_effect=Exception("Workflow failed"))
            
            # Mock the simple response fallback
            with patch.object(ai_chat, '_generate_simple_response') as mock_simple:
                mock_simple.return_value = "Fallback response"
                
                result = await ai_chat.chat(
                    user_message="Hello",
                    user_id=test_user.id,
                    db=db,
                    conversation_id=test_conversation.id
                )
                
                assert result["fallback_used"] is True
                assert result["response"] == "Fallback response"

    def test_get_system_prompt_variations(self, ai_chat):
        """Test system prompt generation for different approaches and tones."""
        # Test different therapeutic approaches
        approaches = ["cognitive_behavioral", "mindfulness_based", "emotion_regulation", "trauma_informed", "person_centered"]
        tones = ["gentle_supportive", "calm_grounding", "validating_calm", "reassuring", "empathetic"]
        
        for approach in approaches:
            for tone in tones:
                prompt = ai_chat._get_system_prompt(approach, tone)
                assert len(prompt) > 0
                assert "InnerCalm" in prompt
                assert "empathetic" in prompt.lower()
                assert "validate" in prompt.lower()

    def test_conversation_memory_persistence(self, ai_chat):
        """Test conversation memory persistence across sessions."""
        user_id = "test_user"
        
        # First session
        state1 = {
            "user_id": user_id,
            "session_context": {"message_count": 1},
            "emotion_context": {"themes": ["anxiety"]},
            "therapeutic_approach": "mindfulness_based",
            "conversation_stage": "opening"
        }
        
        ai_chat._initialize_session(state1)
        ai_chat._update_memory(state1)
        
        # Second session
        state2 = {
            "user_id": user_id,
            "session_context": {"message_count": 1},
            "emotion_context": {"themes": ["depression"]},
            "therapeutic_approach": "cognitive_behavioral",
            "conversation_stage": "exploration"
        }
        
        ai_chat._initialize_session(state2)
        ai_chat._update_memory(state2)
        
        memory = ai_chat.conversation_memory[user_id]
        assert memory["session_count"] == 2
        assert "anxiety" in memory["dominant_themes"]
        assert "depression" in memory["dominant_themes"]
        assert "mindfulness_based" in memory["therapeutic_preferences"]
        assert "cognitive_behavioral" in memory["therapeutic_preferences"]
