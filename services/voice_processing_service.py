"""
Voice processing service for speech-to-text and real-time sentiment analysis.
"""
import os
import io
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    # Fallback for when audio processing libraries are not available
    sr = None
    AudioSegment = None
    split_on_silence = None
    AUDIO_PROCESSING_AVAILABLE = False
import tempfile
import base64

from services.emotion_analyzer import EmotionAnalyzer
from services.openai_service import OpenAIService
from models.voice_journal import VoiceJournal, VoiceJournalEntry, VoiceJournalStatus
from models.emotion import EmotionAnalysis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VoiceProcessingService:
    """Service for processing voice recordings and real-time sentiment analysis."""

    def __init__(self):
        if not AUDIO_PROCESSING_AVAILABLE:
            logger.warning("Audio processing libraries not available. Voice processing will be limited.")
            self.recognizer = None
        else:
            self.recognizer = sr.Recognizer()
            # Configure speech recognition
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.3

        self.emotion_analyzer = EmotionAnalyzer()
        self.openai_service = OpenAIService()

        # Segment processing settings
        self.segment_duration = 5.0  # Process in 5-second segments
        self.overlap_duration = 1.0  # 1-second overlap between segments

    async def process_audio_file(
        self,
        audio_file_path: str,
        journal_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process an uploaded audio file for transcription and sentiment analysis.

        Args:
            audio_file_path: Path to the audio file
            journal_id: ID of the voice journal
            user_id: ID of the user
            db: Database session

        Returns:
            Dictionary containing processing results
        """
        if not AUDIO_PROCESSING_AVAILABLE:
            logger.error("Audio processing libraries not available")
            return {
                "status": "failed",
                "error": "Audio processing libraries not available"
            }

        try:
            # Load and preprocess audio
            audio = AudioSegment.from_file(audio_file_path)

            # Convert to mono and normalize
            audio = audio.set_channels(1)
            audio = audio.normalize()

            # Split audio into segments for processing
            segments = self._split_audio_into_segments(audio)

            # Process each segment
            all_entries = []
            sentiment_timeline = []
            emotion_spikes = []

            for i, segment in enumerate(segments):
                start_time = i * (self.segment_duration - self.overlap_duration)

                # Process segment
                entry_data = await self._process_audio_segment(
                    segment, start_time, journal_id, user_id, db
                )

                if entry_data:
                    all_entries.append(entry_data)

                    # Add to sentiment timeline
                    sentiment_timeline.append({
                        "timestamp": start_time,
                        "emotions": entry_data.get("emotions", {}),
                        "sentiment_score": entry_data.get("sentiment_score", 0.0),
                        "emotional_intensity": entry_data.get("emotional_intensity", 0.0)
                    })

                    # Check for emotional spikes
                    if entry_data.get("is_emotional_spike", False):
                        emotion_spikes.append({
                            "timestamp": start_time,
                            "spike_type": entry_data.get("spike_type"),
                            "intensity": entry_data.get("emotional_intensity", 0.0),
                            "dominant_emotion": self._get_dominant_emotion(entry_data.get("emotions", {})),
                            "text": entry_data.get("transcribed_text", "")
                        })

            # Generate overall analysis
            overall_sentiment = self._calculate_overall_sentiment(all_entries)

            # Generate AI insights and recommendations
            ai_insights = await self._generate_ai_insights(all_entries, overall_sentiment)
            recommended_exercises = await self._recommend_breathing_exercises(
                overall_sentiment, emotion_spikes
            )

            # Update journal with results
            journal = db.query(VoiceJournal).filter(VoiceJournal.id == journal_id).first()
            if journal:
                journal.status = VoiceJournalStatus.COMPLETED.value
                journal.audio_duration = len(audio) / 1000.0  # Convert to seconds
                journal.transcription = self._combine_transcriptions(all_entries)
                journal.sentiment_timeline = sentiment_timeline
                journal.emotion_spikes = emotion_spikes
                journal.overall_sentiment = overall_sentiment
                journal.ai_insights = ai_insights
                journal.recommended_exercises = recommended_exercises
                journal.completed_at = datetime.utcnow()

                if recommended_exercises:
                    journal.breathing_exercise_suggested = recommended_exercises[0].get("type", "calm_breathing")

                db.commit()

            return {
                "status": "completed",
                "total_segments": len(all_entries),
                "total_duration": len(audio) / 1000.0,
                "transcription": journal.transcription,
                "sentiment_timeline": sentiment_timeline,
                "emotion_spikes": emotion_spikes,
                "overall_sentiment": overall_sentiment,
                "ai_insights": ai_insights,
                "recommended_exercises": recommended_exercises
            }

        except Exception as e:
            logger.error(f"Error processing audio file: {e}")

            # Update journal status to failed
            journal = db.query(VoiceJournal).filter(VoiceJournal.id == journal_id).first()
            if journal:
                journal.status = VoiceJournalStatus.FAILED.value
                db.commit()

            raise

    def _split_audio_into_segments(self, audio: AudioSegment) -> List[AudioSegment]:
        """Split audio into overlapping segments for processing."""
        segments = []
        segment_length_ms = int(self.segment_duration * 1000)
        overlap_ms = int(self.overlap_duration * 1000)
        step_ms = segment_length_ms - overlap_ms

        for start_ms in range(0, len(audio), step_ms):
            end_ms = min(start_ms + segment_length_ms, len(audio))
            segment = audio[start_ms:end_ms]

            # Only process segments longer than 1 second
            if len(segment) >= 1000:
                segments.append(segment)

        return segments

    async def _process_audio_segment(
        self,
        segment: AudioSegment,
        start_time: float,
        journal_id: int,
        user_id: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Process a single audio segment."""
        try:
            # Convert segment to WAV for speech recognition
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                segment.export(temp_file.name, format="wav")

                # Transcribe audio
                with sr.AudioFile(temp_file.name) as source:
                    audio_data = self.recognizer.record(source)

                try:
                    text = self.recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    text = ""
                except sr.RequestError as e:
                    logger.warning(f"Speech recognition error: {e}")
                    text = ""

                # Clean up temp file
                os.unlink(temp_file.name)

            if not text.strip():
                return None

            # Analyze emotions in transcribed text
            emotion_analysis = self.emotion_analyzer.analyze_emotion(text, user_id)

            # Determine if this is an emotional spike
            is_spike, spike_type = self._detect_emotional_spike(emotion_analysis)

            # Create journal entry
            entry = VoiceJournalEntry(
                journal_id=journal_id,
                user_id=user_id,
                transcribed_text=text,
                segment_start_time=start_time,
                segment_duration=len(segment) / 1000.0,
                emotions=emotion_analysis,
                sentiment_score=emotion_analysis.get("sentiment_score", 0.0),
                sentiment_label=emotion_analysis.get("sentiment_label", "neutral"),
                emotional_intensity=self._calculate_emotional_intensity(emotion_analysis),
                themes=emotion_analysis.get("themes", []),
                keywords=emotion_analysis.get("keywords", []),
                is_emotional_spike=is_spike,
                spike_type=spike_type,
                analyzed_at=datetime.utcnow()
            )

            db.add(entry)
            db.commit()

            return {
                "entry_id": entry.id,
                "transcribed_text": text,
                "emotions": emotion_analysis,
                "sentiment_score": emotion_analysis.get("sentiment_score", 0.0),
                "sentiment_label": emotion_analysis.get("sentiment_label", "neutral"),
                "emotional_intensity": entry.emotional_intensity,
                "themes": emotion_analysis.get("themes", []),
                "keywords": emotion_analysis.get("keywords", []),
                "is_emotional_spike": is_spike,
                "spike_type": spike_type
            }

        except Exception as e:
            logger.error(f"Error processing audio segment: {e}")
            return None

    def _detect_emotional_spike(self, emotion_analysis: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Detect if this segment contains an emotional spike."""
        emotions = emotion_analysis

        # Calculate emotional intensity
        intensity = max(
            emotions.get("sadness", 0.0),
            emotions.get("anger", 0.0),
            emotions.get("fear", 0.0),
            emotions.get("joy", 0.0)
        )

        # Threshold for emotional spike
        if intensity > 0.7:
            # Determine spike type
            if emotions.get("joy", 0.0) > 0.7:
                return True, "positive"
            elif any(emotions.get(emotion, 0.0) > 0.7 for emotion in ["sadness", "anger", "fear"]):
                return True, "negative"
            else:
                return True, "mixed"

        return False, None

    def _calculate_emotional_intensity(self, emotion_analysis: Dict[str, Any]) -> float:
        """Calculate overall emotional intensity from emotion scores."""
        emotions = emotion_analysis

        # Weight different emotions
        intensity = (
            emotions.get("sadness", 0.0) * 1.0 +
            emotions.get("anger", 0.0) * 1.2 +
            emotions.get("fear", 0.0) * 1.1 +
            emotions.get("joy", 0.0) * 0.8 +
            emotions.get("surprise", 0.0) * 0.6 +
            emotions.get("disgust", 0.0) * 0.9
        )

        return min(intensity, 1.0)

    def _get_dominant_emotion(self, emotions: Dict[str, float]) -> str:
        """Get the dominant emotion from emotion scores."""
        if not emotions:
            return "neutral"

        return max(emotions, key=emotions.get)

    def _combine_transcriptions(self, entries: List[Dict[str, Any]]) -> str:
        """Combine transcriptions from all entries."""
        transcriptions = [
            entry.get("transcribed_text", "").strip()
            for entry in entries
            if entry.get("transcribed_text", "").strip()
        ]

        return " ".join(transcriptions)

    def _calculate_overall_sentiment(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall sentiment from all entries."""
        if not entries:
            return {
                "dominant_emotion": "neutral",
                "average_sentiment": 0.0,
                "emotional_intensity": 0.0,
                "emotion_distribution": {}
            }

        # Aggregate emotions
        emotion_totals = {}
        sentiment_scores = []
        intensities = []

        for entry in entries:
            emotions = entry.get("emotions", {})
            for emotion, score in emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0.0) + score

            sentiment_scores.append(entry.get("sentiment_score", 0.0))
            intensities.append(entry.get("emotional_intensity", 0.0))

        # Calculate averages
        count = len(entries)
        emotion_averages = {k: v / count for k, v in emotion_totals.items()}

        return {
            "dominant_emotion": max(emotion_averages, key=emotion_averages.get) if emotion_averages else "neutral",
            "average_sentiment": sum(sentiment_scores) / count if sentiment_scores else 0.0,
            "emotional_intensity": sum(intensities) / count if intensities else 0.0,
            "emotion_distribution": emotion_averages
        }

    async def _generate_ai_insights(
        self,
        entries: List[Dict[str, Any]],
        overall_sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insights from the voice journal session."""
        try:
            # Prepare context for AI analysis
            transcription = " ".join([
                entry.get("transcribed_text", "")
                for entry in entries
                if entry.get("transcribed_text", "")
            ])

            # Get themes and patterns
            themes = []
            for entry in entries:
                themes.extend(entry.get("themes", []))

            unique_themes = list(set(themes))

            # Generate insights using OpenAI
            prompt = f"""
            Analyze this voice journal session and provide supportive insights:

            Transcription: {transcription}

            Emotional themes detected: {unique_themes}
            Dominant emotion: {overall_sentiment.get('dominant_emotion', 'neutral')}
            Average sentiment: {overall_sentiment.get('average_sentiment', 0.0)}

            Please provide:
            1. Key emotional patterns observed
            2. Supportive insights and validation
            3. Gentle suggestions for emotional processing
            4. Positive affirmations based on the content

            Keep the tone warm, supportive, and non-judgmental.
            """

            response = await self.openai_service.generate_response(prompt)

            return {
                "key_patterns": self._extract_patterns_from_entries(entries),
                "supportive_insights": response,
                "emotional_journey": self._map_emotional_journey(entries),
                "growth_opportunities": self._identify_growth_opportunities(entries, overall_sentiment)
            }

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "key_patterns": [],
                "supportive_insights": "Thank you for sharing your thoughts. Your willingness to express yourself is a positive step in your emotional journey.",
                "emotional_journey": [],
                "growth_opportunities": []
            }

    async def _recommend_breathing_exercises(
        self,
        overall_sentiment: Dict[str, Any],
        emotion_spikes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Recommend breathing exercises based on emotional analysis."""
        recommendations = []

        dominant_emotion = overall_sentiment.get("dominant_emotion", "neutral")
        intensity = overall_sentiment.get("emotional_intensity", 0.0)

        # Recommend based on dominant emotion and intensity
        if dominant_emotion in ["anger", "fear"] or intensity > 0.7:
            recommendations.append({
                "type": "4-7-8",
                "name": "4-7-8 Calming Breath",
                "description": "A powerful technique to reduce anxiety and promote calm",
                "duration_minutes": 5,
                "instructions": [
                    "Inhale through your nose for 4 counts",
                    "Hold your breath for 7 counts",
                    "Exhale through your mouth for 8 counts",
                    "Repeat 4-8 times"
                ],
                "reason": f"Recommended for managing {dominant_emotion} and high emotional intensity"
            })

        if dominant_emotion == "sadness" or overall_sentiment.get("average_sentiment", 0.0) < -0.3:
            recommendations.append({
                "type": "heart_coherence",
                "name": "Heart Coherence Breathing",
                "description": "Gentle breathing to lift mood and create emotional balance",
                "duration_minutes": 8,
                "instructions": [
                    "Breathe slowly and deeply",
                    "Focus on your heart area",
                    "Inhale for 5 counts, exhale for 5 counts",
                    "Think of something you appreciate"
                ],
                "reason": "Recommended for emotional uplift and heart-centered healing"
            })

        if len(emotion_spikes) > 2:
            recommendations.append({
                "type": "box_breathing",
                "name": "Box Breathing for Stability",
                "description": "Creates emotional stability and mental clarity",
                "duration_minutes": 6,
                "instructions": [
                    "Inhale for 4 counts",
                    "Hold for 4 counts",
                    "Exhale for 4 counts",
                    "Hold empty for 4 counts"
                ],
                "reason": "Recommended for emotional regulation after intense feelings"
            })

        # Default gentle breathing if no specific recommendations
        if not recommendations:
            recommendations.append({
                "type": "calm_breathing",
                "name": "Gentle Calm Breathing",
                "description": "Simple, soothing breath work for general well-being",
                "duration_minutes": 5,
                "instructions": [
                    "Breathe naturally and slowly",
                    "Inhale for 4 counts",
                    "Exhale for 6 counts",
                    "Focus on the sensation of breathing"
                ],
                "reason": "A gentle practice for overall emotional well-being"
            })

        return recommendations[:2]  # Return top 2 recommendations

    def _extract_patterns_from_entries(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Extract emotional patterns from journal entries."""
        patterns = []

        # Analyze emotional progression
        if len(entries) >= 3:
            emotions_over_time = [
                entry.get("emotions", {})
                for entry in entries
            ]

            # Check for emotional escalation
            intensities = [
                entry.get("emotional_intensity", 0.0)
                for entry in entries
            ]

            if len(intensities) >= 3:
                if intensities[-1] > intensities[0] + 0.3:
                    patterns.append("Emotional intensity increased during the session")
                elif intensities[-1] < intensities[0] - 0.3:
                    patterns.append("Emotional intensity decreased during the session")

        # Check for recurring themes
        all_themes = []
        for entry in entries:
            all_themes.extend(entry.get("themes", []))

        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        recurring_themes = [
            theme for theme, count in theme_counts.items()
            if count >= 2
        ]

        if recurring_themes:
            patterns.append(f"Recurring themes: {', '.join(recurring_themes)}")

        return patterns

    def _map_emotional_journey(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map the emotional journey throughout the session."""
        journey = []

        for i, entry in enumerate(entries):
            emotions = entry.get("emotions", {})
            dominant = max(emotions, key=emotions.get) if emotions else "neutral"

            journey.append({
                "segment": i + 1,
                "timestamp": entry.get("segment_start_time", 0.0),
                "dominant_emotion": dominant,
                "intensity": entry.get("emotional_intensity", 0.0),
                "key_phrase": entry.get("transcribed_text", "")[:50] + "..." if len(entry.get("transcribed_text", "")) > 50 else entry.get("transcribed_text", "")
            })

        return journey

    def _identify_growth_opportunities(
        self,
        entries: List[Dict[str, Any]],
        overall_sentiment: Dict[str, Any]
    ) -> List[str]:
        """Identify growth opportunities from the session."""
        opportunities = []

        # Check for self-awareness moments
        self_aware_keywords = ["realize", "understand", "notice", "aware", "feel", "think"]
        for entry in entries:
            text = entry.get("transcribed_text", "").lower()
            if any(keyword in text for keyword in self_aware_keywords):
                opportunities.append("Demonstrated self-awareness and emotional insight")
                break

        # Check for emotional processing
        if overall_sentiment.get("emotional_intensity", 0.0) > 0.5:
            opportunities.append("Engaged in meaningful emotional processing")

        # Check for positive emotions
        if overall_sentiment.get("emotion_distribution", {}).get("joy", 0.0) > 0.3:
            opportunities.append("Maintained connection to positive emotions")

        return opportunities
