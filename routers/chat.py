"""
Chat router for AI conversation functionality.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

logger = logging.getLogger(__name__)

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.conversation import Conversation, Message
from schemas.conversation import (
    ConversationCreate, ConversationResponse,
    ChatRequest, ChatResponse, MessageResponse
)
from services.ai_chat import AIChat
from services.emotion_analyzer import EmotionAnalyzer
from services.analytics_service import AnalyticsService
from models.analytics import AnalyticsEventType

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
ai_chat = AIChat()
emotion_analyzer = EmotionAnalyzer()
analytics_service = AnalyticsService()


@router.post("/", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response."""
    try:
        # Get or create conversation
        conversation = None
        if chat_request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == chat_request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=current_user.id,
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            content=chat_request.message,
            is_user_message=True
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # Analyze emotion in user message
        emotion_analysis = emotion_analyzer.analyze_emotion(
            chat_request.message,
            current_user.id,
            user_message.id
        )

        # Save emotion analysis
        from models.emotion import EmotionAnalysis
        emotion_record = EmotionAnalysis(**emotion_analysis)
        db.add(emotion_record)
        db.commit()

        # Generate AI response
        try:
            ai_response_data = await ai_chat.chat(
                user_message=chat_request.message,
                user_id=current_user.id,
                db=db,
                conversation_id=conversation.id,
                emotion_analysis=emotion_analysis
            )
        except Exception as e:
            # Fallback response if AI chat fails
            ai_response_data = {
                "response": "I'm here to listen and support you. Could you tell me more about what's on your mind?",
                "therapeutic_approach": "person_centered",
                "response_tone": "empathetic",
                "conversation_id": conversation.id
            }

        # Save AI response
        ai_message = Message(
            conversation_id=conversation.id,
            content=ai_response_data["response"],
            is_user_message=False
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)

        # Update conversation timestamp
        conversation.updated_at = user_message.timestamp
        db.commit()

        # Track analytics events
        try:
            # Track conversation start for new conversations
            if len(db.query(Message).filter(Message.conversation_id == conversation.id).all()) <= 2:
                await analytics_service.track_event(
                    db=db,
                    user_id=current_user.id,
                    event_type=AnalyticsEventType.CONVERSATION_START.value,
                    event_name="New Conversation Started",
                    conversation_id=conversation.id,
                    emotion_snapshot=emotion_analysis
                )

            # Track crisis detection if present
            if ai_response_data.get("crisis_detected", False):
                await analytics_service.track_event(
                    db=db,
                    user_id=current_user.id,
                    event_type=AnalyticsEventType.CRISIS_DETECTED.value,
                    event_name="Crisis Indicators Detected",
                    conversation_id=conversation.id,
                    emotion_snapshot=emotion_analysis,
                    severity="high"
                )

            # Track emotion peaks (high intensity emotions)
            dominant_emotions = [
                emotion for emotion in ["joy", "sadness", "anger", "fear"]
                if emotion_analysis.get(emotion, 0) > 0.7
            ]
            if dominant_emotions:
                await analytics_service.track_event(
                    db=db,
                    user_id=current_user.id,
                    event_type=AnalyticsEventType.EMOTION_PEAK.value,
                    event_name=f"High {dominant_emotions[0].title()} Detected",
                    conversation_id=conversation.id,
                    emotion_snapshot=emotion_analysis,
                    event_data={"dominant_emotions": dominant_emotions}
                )

            # Analyze conversation if it's ending (based on certain patterns)
            if len(db.query(Message).filter(Message.conversation_id == conversation.id).all()) >= 10:
                await analytics_service.analyze_conversation(db, conversation.id)

        except Exception as analytics_error:
            # Don't fail the main request if analytics fails
            logger.error(f"Analytics tracking failed: {analytics_error}")

        return ChatResponse(
            message=MessageResponse.model_validate(user_message),
            ai_response=MessageResponse.model_validate(ai_message),
            conversation_id=conversation.id,
            emotion_analysis={
                "sentiment_label": emotion_analysis["sentiment_label"],
                "sentiment_score": emotion_analysis["sentiment_score"],
                "dominant_emotions": [
                    emotion for emotion in ["joy", "sadness", "anger", "fear", "surprise", "disgust"]
                    if emotion_analysis.get(emotion, 0) > 0.5
                ],
                "themes": emotion_analysis.get("themes", [])
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stream AI response for better user experience."""

    async def generate_stream():
        try:
            # Get or create conversation
            conversation = None
            if chat_request.conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == chat_request.conversation_id,
                    Conversation.user_id == current_user.id
                ).first()

                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Conversation not found'})}\n\n"
                    return
            else:
                # Create new conversation
                conversation = Conversation(
                    user_id=current_user.id,
                    title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                content=chat_request.message,
                is_user_message=True
            )
            db.add(user_message)
            db.commit()
            db.refresh(user_message)

            # Analyze emotion in user message
            emotion_analysis = emotion_analyzer.analyze_emotion(
                chat_request.message,
                current_user.id,
                user_message.id
            )

            # Save emotion analysis
            from models.emotion import EmotionAnalysis
            emotion_record = EmotionAnalysis(**emotion_analysis)
            db.add(emotion_record)
            db.commit()

            # Send initial data
            yield f"data: {json.dumps({'type': 'conversation_id', 'content': str(conversation.id)})}\n\n"
            yield f"data: {json.dumps({'type': 'emotion_analysis', 'content': emotion_analysis})}\n\n"

            # Stream AI response
            full_response = ""
            async for chunk in ai_chat.chat_stream(
                user_message=chat_request.message,
                user_id=current_user.id,
                db=db,
                conversation_id=conversation.id,
                emotion_analysis=emotion_analysis
            ):
                yield f"data: {json.dumps(chunk)}\n\n"

                # Collect full response for saving
                if chunk.get("type") == "response_chunk" and chunk.get("content"):
                    full_response += chunk["content"]
                elif chunk.get("type") == "response_complete":
                    full_response = chunk.get("metadata", {}).get("full_response", full_response)

            # Save AI response to database
            if full_response:
                ai_message = Message(
                    conversation_id=conversation.id,
                    content=full_response,
                    is_user_message=False
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)

                # Update conversation timestamp
                conversation.updated_at = user_message.timestamp
                db.commit()

                # Track analytics events (same as regular chat)
                try:
                    if len(db.query(Message).filter(Message.conversation_id == conversation.id).all()) <= 2:
                        await analytics_service.track_event(
                            db=db,
                            user_id=current_user.id,
                            event_type=AnalyticsEventType.CONVERSATION_START.value,
                            event_name="New Conversation Started",
                            conversation_id=conversation.id,
                            emotion_snapshot=emotion_analysis
                        )

                    # Track emotion peaks
                    dominant_emotions = [
                        emotion for emotion in ["joy", "sadness", "anger", "fear"]
                        if emotion_analysis.get(emotion, 0) > 0.7
                    ]
                    if dominant_emotions:
                        await analytics_service.track_event(
                            db=db,
                            user_id=current_user.id,
                            event_type=AnalyticsEventType.EMOTION_PEAK.value,
                            event_name=f"High {dominant_emotions[0].title()} Detected",
                            conversation_id=conversation.id,
                            emotion_snapshot=emotion_analysis,
                            event_data={"dominant_emotions": dominant_emotions}
                        )

                except Exception as analytics_error:
                    logger.error(f"Analytics tracking failed: {analytics_error}")

            yield f"data: {json.dumps({'type': 'stream_complete'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
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


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get user's conversations."""
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit).all()

        return [ConversationResponse.model_validate(conv) for conv in conversations]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with messages."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        return ConversationResponse.model_validate(conversation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        conversation.is_active = False
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )
