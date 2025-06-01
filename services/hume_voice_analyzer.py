"""
Hume AI voice emotion analysis service for real-time voice processing.
"""
import asyncio
import logging
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import os

from config import settings

logger = logging.getLogger(__name__)


class HumeVoiceAnalyzer:
    """Service for real-time voice emotion analysis using Hume AI."""

    def __init__(self):
        """Initialize the Hume AI voice analyzer."""
        self.api_key = settings.hume_api_key
        self.base_url = "https://api.hume.ai/v0/batch/jobs"
        self.headers = {
            "X-Hume-Api-Key": self.api_key
        }

        # Emotion mapping from Hume AI to our internal format
        self.emotion_mapping = {
            'Joy': 'joy',
            'Sadness': 'sadness',
            'Anger': 'anger',
            'Fear': 'fear',
            'Surprise': 'surprise',
            'Disgust': 'disgust',
            'Contempt': 'contempt',
            'Excitement': 'excitement',
            'Amusement': 'amusement',
            'Awe': 'awe',
            'Calmness': 'calm',
            'Concentration': 'focused',
            'Confusion': 'confused',
            'Determination': 'determined',
            'Disappointment': 'disappointed',
            'Distress': 'distressed',
            'Embarrassment': 'embarrassed',
            'Empathic_Pain': 'empathic_pain',
            'Entrancement': 'entranced',
            'Envy': 'envious',
            'Guilt': 'guilty',
            'Horror': 'horrified',
            'Interest': 'interested',
            'Love': 'loving',
            'Nostalgia': 'nostalgic',
            'Pain': 'pain',
            'Pride': 'proud',
            'Realization': 'realization',
            'Relief': 'relief',
            'Romance': 'romantic',
            'Satisfaction': 'satisfied',
            'Shame': 'ashamed',
            'Sympathy': 'sympathetic',
            'Tiredness': 'tired',
            'Triumph': 'triumphant'
        }

    async def analyze_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Analyze an audio file for emotion content.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary containing emotion analysis results
        """
        try:
            logger.info(f"Analyzing audio file: {audio_file_path}")

            # Prepare the request data for multipart/form-data
            json_data = {
                "models": {
                    "prosody": {
                        "granularity": "utterance",
                        "identify_speakers": False,
                        "window": {
                            "length": 4,
                            "step": 1
                        }
                    }
                },
                "transcription": {
                    "language": "en",
                    "confidence_threshold": 0.1  # Lower threshold for voice journaling
                }
            }

            # Prepare files for upload
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'json': (None, json.dumps(json_data), 'application/json'),
                    'file': (os.path.basename(audio_file_path), audio_file, 'audio/webm')
                }

                # Submit the job
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    files=files
                )

            if response.status_code != 200:
                logger.error(f"Hume AI job submission failed: {response.status_code} - {response.text}")
                raise Exception(f"Hume AI API error: {response.status_code} - {response.text}")

            job_data = response.json()
            job_id = job_data.get('job_id')

            if not job_id:
                logger.error(f"No job_id in response: {job_data}")
                raise Exception("No job_id returned from Hume AI")

            logger.info(f"Hume AI job submitted: {job_id}")

            # Wait for job completion
            results = await self._wait_for_job_completion(job_id)

            logger.info("Hume AI analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"Error in Hume AI analysis: {e}")
            raise e

    async def analyze_audio_blob(self, audio_blob: bytes) -> Dict[str, Any]:
        """
        Analyze audio blob data for emotion content.

        Args:
            audio_blob: Raw audio data

        Returns:
            Dictionary containing emotion analysis results
        """
        try:
            # Create temporary file for Hume AI processing
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_blob)
                temp_file_path = temp_file.name

            try:
                # Analyze the temporary file
                results = await self.analyze_audio_file(temp_file_path)
                return results
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error analyzing audio blob: {e}")
            raise e

    async def _wait_for_job_completion(self, job_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """Wait for Hume AI job to complete and return results."""
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < max_wait_time:
            try:
                # Check job status
                status_url = f"{self.base_url}/{job_id}"
                response = requests.get(status_url, headers=self.headers)

                if response.status_code != 200:
                    logger.error(f"Failed to check job status: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to check job status: {response.status_code}")

                job_status = response.json()
                status = job_status.get('state', {}).get('status')

                logger.info(f"Job {job_id} status: {status}")

                if status == 'COMPLETED':
                    # Get predictions
                    predictions_url = f"{self.base_url}/{job_id}/predictions"
                    pred_response = requests.get(predictions_url, headers=self.headers)

                    if pred_response.status_code == 200:
                        predictions = pred_response.json()
                        return self._process_hume_results(predictions)
                    else:
                        logger.error(f"Failed to get predictions: {pred_response.status_code} - {pred_response.text}")
                        raise Exception(f"Failed to get predictions: {pred_response.status_code}")

                elif status == 'FAILED':
                    error_message = job_status.get('state', {}).get('message', 'Unknown error')
                    logger.error(f"Hume AI job failed: {error_message}")
                    raise Exception(f"Hume AI job failed: {error_message}")

                # Wait before checking again
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Error waiting for job completion: {e}")
                raise e

        logger.error("Job completion timeout")
        raise Exception("Job completion timeout")

    def _process_hume_results(self, predictions_data) -> Dict[str, Any]:
        """Process Hume AI job results into our format."""
        try:
            # Extract predictions from API response
            predictions = predictions_data

            # Debug: Log the structure of the response
            logger.info(f"Hume AI response structure: {type(predictions)}")
            logger.info(f"Predictions data keys: {list(predictions.keys()) if isinstance(predictions, dict) else 'Not a dict'}")
            if isinstance(predictions, list) and len(predictions) > 0:
                logger.info(f"First prediction keys: {list(predictions[0].keys()) if isinstance(predictions[0], dict) else 'Not a dict'}")

            if not predictions:
                raise Exception("Empty predictions response from Hume AI")

            # Get prosody predictions (voice emotion analysis)
            prosody_predictions = []

            # Handle the actual Hume AI response format
            for item in predictions:
                if 'results' in item:
                    results = item['results']

                    # Check for errors first
                    if 'errors' in results and results['errors']:
                        error_messages = [error.get('message', 'Unknown error') for error in results['errors']]
                        error_text = '; '.join(error_messages)

                        # Handle specific transcript confidence error with user-friendly message
                        if 'transcript confidence' in error_text and 'below threshold' in error_text:
                            raise Exception("Please speak more clearly and loudly. Hume AI needs clear speech to analyze emotions accurately. Try recording again with better audio quality.")
                        else:
                            raise Exception(f"Hume AI processing errors: {error_text}")

                    # Get predictions
                    if 'predictions' in results:
                        for prediction in results['predictions']:
                            if 'models' in prediction and 'prosody' in prediction['models']:
                                prosody_data = prediction['models']['prosody']
                                if 'grouped_predictions' in prosody_data:
                                    prosody_predictions.extend(prosody_data['grouped_predictions'])

            if not prosody_predictions:
                raise Exception("No prosody predictions found in Hume AI response")

            # Aggregate emotions across all segments
            emotion_totals = {}
            total_segments = 0
            emotion_timeline = []
            emotion_spikes = []

            for group in prosody_predictions:
                if 'predictions' in group:
                    for prediction in group['predictions']:
                        total_segments += 1
                        segment_emotions = {}

                        # Process emotions for this segment
                        if 'emotions' in prediction:
                            for emotion in prediction['emotions']:
                                hume_name = emotion.get('name', '')
                                our_name = self.emotion_mapping.get(hume_name, hume_name.lower())
                                score = emotion.get('score', 0)

                                segment_emotions[our_name] = score

                                if our_name not in emotion_totals:
                                    emotion_totals[our_name] = 0
                                emotion_totals[our_name] += score

                        # Add to timeline
                        time_info = prediction.get('time', {})
                        begin_time = time_info.get('begin', 0)

                        emotion_timeline.append({
                            'time': begin_time,
                            'emotions': segment_emotions,
                            'dominant_emotion': max(segment_emotions, key=segment_emotions.get) if segment_emotions else 'neutral'
                        })

                        # Detect emotion spikes (high intensity emotions)
                        max_emotion = max(segment_emotions.values()) if segment_emotions else 0
                        if max_emotion > 0.7:  # Threshold for emotion spike
                            dominant = max(segment_emotions, key=segment_emotions.get)
                            emotion_spikes.append({
                                'time': begin_time,
                                'emotion': dominant,
                                'intensity': max_emotion,
                                'type': 'positive' if dominant in ['joy', 'excitement', 'amusement', 'love', 'pride', 'triumph'] else 'negative'
                            })

            # Calculate averages
            if total_segments > 0:
                for emotion in emotion_totals:
                    emotion_totals[emotion] /= total_segments

            # Determine overall sentiment
            positive_emotions = ['joy', 'excitement', 'amusement', 'love', 'pride', 'triumph', 'satisfaction', 'relief']
            negative_emotions = ['sadness', 'anger', 'fear', 'disgust', 'distress', 'disappointment', 'guilt', 'shame']

            positive_score = sum(emotion_totals.get(e, 0) for e in positive_emotions)
            negative_score = sum(emotion_totals.get(e, 0) for e in negative_emotions)
            sentiment_score = positive_score - negative_score

            # Find dominant emotion
            dominant_emotion = max(emotion_totals, key=emotion_totals.get) if emotion_totals else 'neutral'
            emotional_intensity = max(emotion_totals.values()) if emotion_totals else 0

            return {
                'overall_sentiment': {
                    'dominant_emotion': dominant_emotion,
                    'emotional_intensity': emotional_intensity,
                    'sentiment_score': sentiment_score,
                    'confidence': min(emotional_intensity * 1.2, 1.0)  # Scale confidence
                },
                'emotions': emotion_totals,
                'emotion_spikes': emotion_spikes,
                'emotion_timeline': emotion_timeline,
                'analysis_metadata': {
                    'total_segments': total_segments,
                    'analysis_duration': emotion_timeline[-1]['time'] if emotion_timeline else 0,
                    'provider': 'hume_ai'
                }
            }

        except Exception as e:
            logger.error(f"Error processing Hume AI results: {e}")
            raise e


# Global instance
_hume_analyzer = None

def get_hume_voice_analyzer() -> HumeVoiceAnalyzer:
    """Get or create the global Hume voice analyzer instance."""
    global _hume_analyzer
    if _hume_analyzer is None:
        _hume_analyzer = HumeVoiceAnalyzer()
    return _hume_analyzer
