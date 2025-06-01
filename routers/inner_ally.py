"""
Inner Ally Agent router for persona management and widget interactions.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database import get_db
from routers.auth import get_current_active_user
from models.user import User, UserPreferences
from models.user_memory import (
    UserMemory, PersonalTrigger, CopingPreference,
    SupportivePhrase, ConversationPattern
)
from models.agent_persona import (
    AgentPersona, UserPersonaCustomization,
    MicroCheckIn, WidgetInteraction
)
from schemas.agent_persona import (
    QuickChatRequest, QuickChatResponse, PersonaPreview,
    WidgetSettings, InnerAllyStatus, MicroCheckInCreate,
    MicroCheckInResponse, WidgetInteractionCreate, WidgetInteractionResponse
)
from schemas.user_memory import PersonalizationSummary
from services.inner_ally import InnerAllyAgent
from services.ai_chat import AIChat

router = APIRouter(prefix="/inner-ally", tags=["inner-ally"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=InnerAllyStatus)
async def get_inner_ally_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current status of the Inner Ally agent."""
    try:
        inner_ally = InnerAllyAgent()

        # Get user preferences
        user_prefs = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        # Get recent interactions
        recent_interaction = db.query(WidgetInteraction).filter(
            WidgetInteraction.user_id == current_user.id
        ).order_by(desc(WidgetInteraction.created_at)).first()

        total_interactions = db.query(WidgetInteraction).filter(
            WidgetInteraction.user_id == current_user.id
        ).count()

        # Get next check-in time
        last_checkin = db.query(MicroCheckIn).filter(
            MicroCheckIn.user_id == current_user.id
        ).order_by(desc(MicroCheckIn.created_at)).first()

        next_checkin = None
        if user_prefs and user_prefs.micro_checkin_frequency:
            if last_checkin:
                next_checkin = last_checkin.created_at + timedelta(hours=user_prefs.micro_checkin_frequency)
            else:
                next_checkin = datetime.now() + timedelta(hours=user_prefs.micro_checkin_frequency)

        # Get available interventions based on user's coping preferences
        coping_strategies = db.query(CopingPreference).filter(
            CopingPreference.user_id == current_user.id
        ).filter(CopingPreference.effectiveness_rating >= 3.0).all()

        available_interventions = [strategy.strategy_name for strategy in coping_strategies[:5]]

        return InnerAllyStatus(
            is_active=user_prefs.widget_enabled if user_prefs else True,
            current_persona=user_prefs.agent_persona if user_prefs else "gentle_mentor",
            last_interaction=recent_interaction.created_at if recent_interaction else None,
            total_interactions=total_interactions,
            recent_mood_trend="stable",  # This would be calculated from recent check-ins
            available_interventions=available_interventions,
            next_check_in=next_checkin
        )

    except Exception as e:
        logger.error(f"Error getting Inner Ally status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Inner Ally status"
        )


@router.get("/personas", response_model=List[PersonaPreview])
async def get_available_personas(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available personas for the user."""
    try:
        inner_ally = InnerAllyAgent()
        personas = []

        for key, persona_data in inner_ally.default_personas.items():
            personas.append(PersonaPreview(
                persona_key=key,
                display_name=persona_data["display_name"],
                description=persona_data["description"],
                sample_responses=[
                    "I understand how you're feeling right now.",
                    "Let's explore this together.",
                    "You're taking an important step by sharing this."
                ],
                best_for=[
                    "Deep emotional exploration",
                    "Gentle guidance",
                    "Supportive conversations"
                ],
                communication_style_summary=f"{persona_data['empathy_level']} empathy, {persona_data['directness_level']} approach"
            ))

        return personas

    except Exception as e:
        logger.error(f"Error getting personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available personas"
        )


@router.post("/quick-chat", response_model=QuickChatResponse)
async def quick_chat(
    chat_request: QuickChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle quick chat requests from the Calm Companion widget."""
    try:
        inner_ally = InnerAllyAgent()
        ai_chat = AIChat()

        # Log widget interaction
        interaction = WidgetInteraction(
            user_id=current_user.id,
            interaction_type="quick_chat",
            widget_state="expanded",
            emotional_state=chat_request.emotional_state
        )
        db.add(interaction)

        # Get user's persona and longitudinal context
        persona = inner_ally.get_user_persona(current_user.id, db)
        context = inner_ally.get_longitudinal_context(current_user.id, db)

        # Generate AI response with persona and context
        ai_response_data = await ai_chat.chat(
            user_message=chat_request.message,
            user_id=current_user.id,
            db=db,
            conversation_id=None,  # Quick chats don't create conversations
            emotion_analysis=None
        )

        # Determine if follow-up is needed
        follow_up_recommended = chat_request.urgency_level in ["high", "crisis"]
        escalation_needed = chat_request.urgency_level == "crisis"

        # Get supportive phrases from user's memory
        supportive_phrases = db.query(SupportivePhrase).filter(
            SupportivePhrase.user_id == current_user.id
        ).filter(SupportivePhrase.is_favorite == True).limit(3).all()

        phrase_texts = [phrase.phrase_text for phrase in supportive_phrases]
        if not phrase_texts:
            phrase_texts = [
                "You are stronger than you know",
                "This feeling will pass",
                "You're not alone in this"
            ]

        db.commit()

        return QuickChatResponse(
            response=ai_response_data["response"],
            intervention_suggested=None,  # Could suggest based on context
            follow_up_recommended=follow_up_recommended,
            escalation_needed=escalation_needed,
            estimated_duration=30,  # 30 seconds for quick chat
            supportive_phrases=phrase_texts
        )

    except Exception as e:
        logger.error(f"Error in quick chat: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process quick chat"
        )


@router.post("/quick-chat/stream")
async def quick_chat_stream(
    chat_request: QuickChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stream quick chat responses from the Calm Companion widget."""

    async def generate_stream():
        try:
            inner_ally = InnerAllyAgent()
            ai_chat = AIChat()

            # Log widget interaction
            interaction = WidgetInteraction(
                user_id=current_user.id,
                interaction_type="quick_chat_stream",
                widget_state="expanded",
                emotional_state=chat_request.emotional_state
            )
            db.add(interaction)
            db.commit()

            # Get user's persona and longitudinal context
            persona = inner_ally.get_user_persona(current_user.id, db)
            context = inner_ally.get_longitudinal_context(current_user.id, db)

            # Send initial metadata
            yield f"data: {json.dumps({'type': 'metadata', 'content': '', 'persona': persona})}\n\n"

            # Stream AI response
            full_response = ""
            async for chunk in ai_chat.chat_stream(
                user_message=chat_request.message,
                user_id=current_user.id,
                db=db,
                conversation_id=None,  # Quick chats don't create conversations
                emotion_analysis=None
            ):
                yield f"data: {json.dumps(chunk)}\n\n"

                # Collect full response for additional processing
                if chunk.get("type") == "response_chunk" and chunk.get("content"):
                    full_response += chunk["content"]
                elif chunk.get("type") == "response_complete":
                    full_response = chunk.get("metadata", {}).get("full_response", full_response)

            # Send completion with supportive phrases
            supportive_phrases = db.query(SupportivePhrase).filter(
                SupportivePhrase.user_id == current_user.id
            ).filter(SupportivePhrase.is_favorite == True).limit(3).all()

            phrase_texts = [phrase.phrase_text for phrase in supportive_phrases]
            if not phrase_texts:
                phrase_texts = [
                    "You are stronger than you know",
                    "This feeling will pass",
                    "You're not alone in this"
                ]

            yield f"data: {json.dumps({'type': 'supportive_phrases', 'content': phrase_texts})}\n\n"
            yield f"data: {json.dumps({'type': 'stream_complete'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error in quick chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/micro-checkin", response_model=MicroCheckInResponse)
async def create_micro_checkin(
    checkin_data: MicroCheckInCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a micro check-in session."""
    try:
        inner_ally = InnerAllyAgent()

        # Determine time context
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_context = "morning"
        elif 12 <= current_hour < 17:
            time_context = "afternoon"
        elif 17 <= current_hour < 21:
            time_context = "evening"
        else:
            time_context = "night"

        # Create micro check-in record
        checkin = MicroCheckIn(
            user_id=current_user.id,
            trigger_type=checkin_data.trigger_type,
            mood_rating=checkin_data.mood_rating,
            stress_level=checkin_data.stress_level,
            user_response=checkin_data.user_response,
            location_context=checkin_data.location_context,
            time_context=time_context,
            emotional_context=checkin_data.emotional_context,
            ai_response="",  # Will be filled below
            follow_up_needed=False,
            escalation_triggered=False
        )

        # Generate appropriate AI response based on mood/stress levels
        if checkin_data.mood_rating and checkin_data.mood_rating <= 3:
            ai_response = "I notice you're having a tough time right now. Remember that difficult feelings are temporary, and you have the strength to get through this."
            checkin.follow_up_needed = True
        elif checkin_data.stress_level and checkin_data.stress_level >= 8:
            ai_response = "It sounds like you're feeling quite stressed. Let's take a moment to breathe together. Try taking three deep breaths with me."
            checkin.follow_up_needed = True
        else:
            ai_response = "Thank you for checking in. I'm here with you, and I appreciate you taking a moment to connect with yourself."

        checkin.ai_response = ai_response
        checkin.completed_at = datetime.now()

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return MicroCheckInResponse(
            id=checkin.id,
            user_id=checkin.user_id,
            trigger_type=checkin.trigger_type,
            mood_rating=checkin.mood_rating,
            stress_level=checkin.stress_level,
            user_response=checkin.user_response,
            location_context=checkin.location_context,
            time_context=checkin.time_context,
            emotional_context=checkin.emotional_context,
            ai_response=checkin.ai_response,
            intervention_suggested=None,
            was_helpful=None,
            follow_up_needed=checkin.follow_up_needed,
            escalation_triggered=checkin.escalation_triggered,
            duration_seconds=None,
            created_at=checkin.created_at,
            completed_at=checkin.completed_at
        )

    except Exception as e:
        logger.error(f"Error creating micro check-in: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create micro check-in"
        )


@router.get("/personalization-summary", response_model=PersonalizationSummary)
async def get_personalization_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a summary of the user's personalization data."""
    try:
        # Get memory counts
        total_memories = db.query(UserMemory).filter(
            UserMemory.user_id == current_user.id
        ).count()

        active_triggers = db.query(PersonalTrigger).filter(
            and_(
                PersonalTrigger.user_id == current_user.id,
                PersonalTrigger.is_active == True
            )
        ).count()

        # Get preferred coping strategies
        coping_strategies = db.query(CopingPreference).filter(
            CopingPreference.user_id == current_user.id
        ).filter(CopingPreference.effectiveness_rating >= 3.0).limit(5).all()

        preferred_strategies = [strategy.strategy_name for strategy in coping_strategies]

        # Get favorite phrases
        favorite_phrases = db.query(SupportivePhrase).filter(
            and_(
                SupportivePhrase.user_id == current_user.id,
                SupportivePhrase.is_favorite == True
            )
        ).limit(5).all()

        favorite_phrase_texts = [phrase.phrase_text for phrase in favorite_phrases]

        # Get conversation preferences
        patterns = db.query(ConversationPattern).filter(
            and_(
                ConversationPattern.user_id == current_user.id,
                ConversationPattern.is_active == True
            )
        ).all()

        conversation_preferences = {
            pattern.pattern_type: pattern.pattern_description
            for pattern in patterns
        }

        return PersonalizationSummary(
            total_memories=total_memories,
            active_triggers=active_triggers,
            preferred_coping_strategies=preferred_strategies,
            favorite_phrases=favorite_phrase_texts,
            conversation_preferences=conversation_preferences,
            recent_insights=[]  # Would be populated with actual insights
        )

    except Exception as e:
        logger.error(f"Error getting personalization summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personalization summary"
        )


@router.post("/widget-interaction")
async def log_widget_interaction(
    interaction_data: WidgetInteractionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Log widget interaction for analytics."""
    try:
        interaction = WidgetInteraction(
            user_id=current_user.id,
            interaction_type=interaction_data.interaction_type,
            widget_state=interaction_data.widget_state,
            page_context=interaction_data.page_context,
            emotional_state=interaction_data.emotional_state
        )

        db.add(interaction)
        db.commit()

        return {"status": "logged"}

    except Exception as e:
        logger.error(f"Error logging widget interaction: {e}")
        db.rollback()
        # Don't raise error for logging failures
        return {"status": "failed"}
