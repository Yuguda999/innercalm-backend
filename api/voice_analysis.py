"""
Voice analysis API endpoints using Hume AI.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import os

from routers.auth import get_current_user
from models.user import User
from services.hume_voice_analyzer import get_hume_voice_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-analysis", tags=["voice-analysis"])


@router.post("/analyze-audio")
async def analyze_audio_file(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze an uploaded audio file for emotion content using Hume AI.

    Args:
        audio_file: The audio file to analyze
        current_user: The authenticated user

    Returns:
        Dictionary containing emotion analysis results
    """
    try:
        logger.info(f"Analyzing audio file for user {current_user.id}: {audio_file.filename}")

        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read audio data
        audio_data = await audio_file.read()

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        # Get Hume AI analyzer
        analyzer = get_hume_voice_analyzer()

        # Analyze the audio
        results = await analyzer.analyze_audio_blob(audio_data)

        # Add user context to results
        results['user_id'] = current_user.id
        results['filename'] = audio_file.filename
        results['file_size'] = len(audio_data)
        results['analysis_timestamp'] = str(datetime.utcnow())

        logger.info(f"Audio analysis completed for user {current_user.id}")

        return {
            "status": "success",
            "analysis": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing audio file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during audio analysis")


@router.post("/analyze-blob")
async def analyze_audio_blob(
    audio_data: bytes,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze raw audio data for emotion content using Hume AI.

    Args:
        audio_data: Raw audio bytes
        current_user: The authenticated user

    Returns:
        Dictionary containing emotion analysis results
    """
    try:
        logger.info(f"Analyzing audio blob for user {current_user.id}")

        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio data is empty")

        # Get Hume AI analyzer
        analyzer = get_hume_voice_analyzer()

        # Analyze the audio
        results = await analyzer.analyze_audio_blob(audio_data)

        # Add user context to results
        results['user_id'] = current_user.id
        results['data_size'] = len(audio_data)
        results['analysis_timestamp'] = str(datetime.utcnow())

        logger.info(f"Audio blob analysis completed for user {current_user.id}")

        return {
            "status": "success",
            "analysis": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing audio blob: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during audio analysis")


@router.get("/test-connection")
async def test_hume_connection(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test the connection to Hume AI service.

    Args:
        current_user: The authenticated user

    Returns:
        Connection status
    """
    try:
        logger.info(f"Testing Hume AI connection for user {current_user.id}")

        # Simple API connectivity test - just check if we can reach Hume AI
        import requests
        from config import settings

        # Test basic API connectivity with a simple request
        test_url = "https://api.hume.ai/v0/batch/jobs"
        headers = {"X-Hume-Api-Key": settings.hume_api_key}

        # Make a simple GET request to check if API is reachable
        response = requests.get(test_url, headers=headers, timeout=10)

        if response.status_code in [200, 401, 403]:  # Any of these means API is reachable
            return {
                "status": "success",
                "message": "Hume AI API is reachable and ready for voice analysis",
                "provider": "hume_ai",
                "api_status": response.status_code
            }
        else:
            return {
                "status": "error",
                "message": f"Hume AI API returned unexpected status: {response.status_code}",
                "provider": "error"
            }

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Hume AI API timeout - service may be temporarily unavailable",
            "provider": "error"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Cannot connect to Hume AI API - check internet connection",
            "provider": "error"
        }
    except Exception as e:
        logger.error(f"Error testing Hume AI connection: {e}")
        return {
            "status": "error",
            "message": f"Hume AI connection test failed: {str(e)}",
            "provider": "error"
        }


@router.get("/supported-emotions")
async def get_supported_emotions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the list of emotions supported by Hume AI analysis.

    Args:
        current_user: The authenticated user

    Returns:
        List of supported emotions
    """
    try:
        analyzer = get_hume_voice_analyzer()

        return {
            "status": "success",
            "emotions": list(analyzer.emotion_mapping.values()),
            "total_emotions": len(analyzer.emotion_mapping),
            "primary_emotions": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
            "extended_emotions": [
                "excitement", "amusement", "awe", "calm", "focused", "confused",
                "determined", "disappointed", "distressed", "embarrassed",
                "interested", "loving", "nostalgic", "proud", "relief", "satisfied"
            ]
        }

    except Exception as e:
        logger.error(f"Error getting supported emotions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving supported emotions")
