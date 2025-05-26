"""
Advanced analytics service for detailed progress tracking and insights generation.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import statistics
import json

from models.analytics import (
    AnalyticsEvent, AnalyticsEventType,
    MoodTrend, MoodTrendType,
    ProgressInsight,
    ConversationAnalytics,
    UserProgressMetrics
)
from models.emotion import EmotionAnalysis
from models.conversation import Conversation, Message
from models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Advanced analytics service for comprehensive user progress tracking."""

    def __init__(self):
        self.insight_generators = {
            "pattern": self._generate_pattern_insights,
            "breakthrough": self._generate_breakthrough_insights,
            "concern": self._generate_concern_insights,
            "recommendation": self._generate_recommendation_insights
        }

    async def track_event(
        self,
        db: Session,
        user_id: int,
        event_type: str,
        event_name: str,
        event_data: Optional[Dict] = None,
        conversation_id: Optional[int] = None,
        emotion_snapshot: Optional[Dict] = None,
        severity: str = "normal"
    ) -> AnalyticsEvent:
        """Track an analytics event."""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                conversation_id=conversation_id,
                event_type=event_type,
                event_name=event_name,
                event_description=f"{event_name} event for user {user_id}",
                event_data=event_data or {},
                emotion_snapshot=emotion_snapshot,
                severity=severity,
                tags=self._generate_event_tags(event_type, event_data)
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            logger.info(f"Tracked analytics event: {event_type} for user {user_id}")
            return event

        except Exception as e:
            logger.error(f"Error tracking analytics event: {e}")
            db.rollback()
            raise

    async def analyze_mood_trends(
        self,
        db: Session,
        user_id: int,
        days_back: int = 30
    ) -> Optional[MoodTrend]:
        """Analyze mood trends for a user over a specified period."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Get emotion analyses for the period
            emotions = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id == user_id,
                    EmotionAnalysis.analyzed_at >= start_date,
                    EmotionAnalysis.analyzed_at <= end_date
                )
            ).order_by(EmotionAnalysis.analyzed_at).all()

            if len(emotions) < 3:  # Need minimum data points
                return None

            # Analyze trends
            trend_analysis = self._analyze_emotion_progression(emotions)

            # Create mood trend record
            mood_trend = MoodTrend(
                user_id=user_id,
                trend_type=trend_analysis["trend_type"],
                trend_strength=trend_analysis["trend_strength"],
                trend_duration_days=days_back,
                dominant_emotion=trend_analysis["dominant_emotion"],
                emotion_stability=trend_analysis["stability"],
                average_sentiment=trend_analysis["average_sentiment"],
                emotion_progression=trend_analysis["progression_data"],
                key_events=trend_analysis["key_events"],
                start_date=start_date,
                end_date=end_date
            )

            db.add(mood_trend)
            db.commit()
            db.refresh(mood_trend)

            return mood_trend

        except Exception as e:
            logger.error(f"Error analyzing mood trends: {e}")
            return None

    async def generate_progress_insights(
        self,
        db: Session,
        user_id: int,
        insight_types: Optional[List[str]] = None
    ) -> List[ProgressInsight]:
        """Generate AI-powered progress insights for a user."""
        try:
            if insight_types is None:
                insight_types = ["pattern", "breakthrough", "concern", "recommendation"]

            insights = []

            for insight_type in insight_types:
                if insight_type in self.insight_generators:
                    generator = self.insight_generators[insight_type]
                    type_insights = await generator(db, user_id)
                    insights.extend(type_insights)

            # Save insights to database
            for insight in insights:
                db.add(insight)

            db.commit()

            logger.info(f"Generated {len(insights)} insights for user {user_id}")
            return insights

        except Exception as e:
            logger.error(f"Error generating progress insights: {e}")
            return []

    async def analyze_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> Optional[ConversationAnalytics]:
        """Analyze a conversation for detailed metrics."""
        try:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                return None

            # Get conversation messages
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp).all()

            if not messages:
                return None

            # Get emotion analyses for this conversation
            emotions = db.query(EmotionAnalysis).filter(
                EmotionAnalysis.message_id.in_([msg.id for msg in messages if msg.is_user_message])
            ).order_by(EmotionAnalysis.analyzed_at).all()

            # Analyze conversation metrics
            analytics = self._analyze_conversation_metrics(conversation, messages, emotions)

            # Create conversation analytics record
            conv_analytics = ConversationAnalytics(
                conversation_id=conversation_id,
                user_id=conversation.user_id,
                **analytics
            )

            db.add(conv_analytics)
            db.commit()
            db.refresh(conv_analytics)

            return conv_analytics

        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return None

    async def calculate_user_progress_metrics(
        self,
        db: Session,
        user_id: int,
        period_type: str = "weekly"
    ) -> Optional[UserProgressMetrics]:
        """Calculate comprehensive progress metrics for a user."""
        try:
            # Determine time period
            end_date = datetime.now()
            if period_type == "daily":
                start_date = end_date - timedelta(days=1)
            elif period_type == "weekly":
                start_date = end_date - timedelta(weeks=1)
            elif period_type == "monthly":
                start_date = end_date - timedelta(days=30)
            else:
                raise ValueError(f"Invalid period_type: {period_type}")

            # Calculate metrics
            metrics = await self._calculate_comprehensive_metrics(
                db, user_id, start_date, end_date, period_type
            )

            logger.info(f"Calculated metrics for user {user_id}: {metrics}")

            # Create progress metrics record
            progress_metrics = UserProgressMetrics(
                user_id=user_id,
                period_type=period_type,
                period_start=start_date,
                period_end=end_date,
                **metrics
            )

            db.add(progress_metrics)
            db.commit()
            db.refresh(progress_metrics)

            return progress_metrics

        except Exception as e:
            logger.error(f"Error calculating progress metrics: {e}")
            return None

    def _analyze_emotion_progression(self, emotions: List[EmotionAnalysis]) -> Dict:
        """Analyze emotion progression to determine trends."""
        try:
            # Extract sentiment scores over time
            sentiment_scores = [e.sentiment_score for e in emotions]

            # Calculate trend
            if len(sentiment_scores) >= 3:
                # Simple linear trend analysis
                x_values = list(range(len(sentiment_scores)))
                trend_slope = self._calculate_trend_slope(x_values, sentiment_scores)

                if trend_slope > 0.1:
                    trend_type = MoodTrendType.IMPROVING.value
                elif trend_slope < -0.1:
                    trend_type = MoodTrendType.DECLINING.value
                else:
                    # Check volatility
                    volatility = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0
                    if volatility > 0.3:
                        trend_type = MoodTrendType.VOLATILE.value
                    else:
                        trend_type = MoodTrendType.STABLE.value

                trend_strength = min(abs(trend_slope), 1.0)
            else:
                trend_type = MoodTrendType.STABLE.value
                trend_strength = 0.0

            # Find dominant emotion
            emotion_totals = {
                "joy": sum(e.joy for e in emotions),
                "sadness": sum(e.sadness for e in emotions),
                "anger": sum(e.anger for e in emotions),
                "fear": sum(e.fear for e in emotions)
            }
            dominant_emotion = max(emotion_totals, key=emotion_totals.get)

            # Calculate stability (inverse of variance)
            stability = 1.0 - (statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0)
            stability = max(0.0, min(1.0, stability))

            # Average sentiment
            average_sentiment = statistics.mean(sentiment_scores)

            # Create progression data
            progression_data = [
                {
                    "timestamp": e.analyzed_at.isoformat(),
                    "sentiment": e.sentiment_score,
                    "emotions": {
                        "joy": e.joy,
                        "sadness": e.sadness,
                        "anger": e.anger,
                        "fear": e.fear
                    }
                }
                for e in emotions
            ]

            # Identify key events (significant emotion spikes)
            key_events = []
            for i, emotion in enumerate(emotions):
                if emotion.sentiment_score < -0.7:
                    key_events.append({
                        "type": "low_mood",
                        "timestamp": emotion.analyzed_at.isoformat(),
                        "sentiment": emotion.sentiment_score
                    })
                elif emotion.sentiment_score > 0.7:
                    key_events.append({
                        "type": "high_mood",
                        "timestamp": emotion.analyzed_at.isoformat(),
                        "sentiment": emotion.sentiment_score
                    })

            return {
                "trend_type": trend_type,
                "trend_strength": trend_strength,
                "dominant_emotion": dominant_emotion,
                "stability": stability,
                "average_sentiment": average_sentiment,
                "progression_data": progression_data,
                "key_events": key_events
            }

        except Exception as e:
            logger.error(f"Error analyzing emotion progression: {e}")
            return {
                "trend_type": MoodTrendType.STABLE.value,
                "trend_strength": 0.0,
                "dominant_emotion": "neutral",
                "stability": 0.5,
                "average_sentiment": 0.0,
                "progression_data": [],
                "key_events": []
            }

    def _calculate_trend_slope(self, x_values: List[int], y_values: List[float]) -> float:
        """Calculate the slope of a trend line."""
        try:
            n = len(x_values)
            if n < 2:
                return 0.0

            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(y_values)

            numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return 0.0

            return numerator / denominator

        except Exception:
            return 0.0

    def _generate_event_tags(self, event_type: str, event_data: Optional[Dict]) -> List[str]:
        """Generate tags for an analytics event."""
        tags = [event_type]

        if event_data:
            if "emotion" in event_data:
                tags.append(f"emotion_{event_data['emotion']}")
            if "severity" in event_data:
                tags.append(f"severity_{event_data['severity']}")
            if "therapeutic_approach" in event_data:
                tags.append(f"approach_{event_data['therapeutic_approach']}")

        return tags

    async def _generate_pattern_insights(self, db: Session, user_id: int) -> List[ProgressInsight]:
        """Generate insights about emotional patterns."""
        insights = []

        try:
            # Get recent emotion analyses
            recent_emotions = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id == user_id,
                    EmotionAnalysis.analyzed_at >= datetime.now() - timedelta(days=14)
                )
            ).order_by(EmotionAnalysis.analyzed_at).all()

            if len(recent_emotions) < 5:
                return insights

            # Analyze patterns
            patterns = self._identify_emotion_patterns(recent_emotions)

            for pattern in patterns:
                insight = ProgressInsight(
                    user_id=user_id,
                    insight_type="pattern",
                    insight_title=pattern["title"],
                    insight_description=pattern["description"],
                    supporting_data=pattern["data"],
                    confidence_score=pattern["confidence"],
                    impact_level=pattern["impact"],
                    is_actionable=pattern["actionable"],
                    suggested_actions=pattern.get("actions", []),
                    data_period_start=datetime.now() - timedelta(days=14),
                    data_period_end=datetime.now()
                )
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating pattern insights: {e}")

        return insights

    async def _generate_breakthrough_insights(self, db: Session, user_id: int) -> List[ProgressInsight]:
        """Generate insights about therapeutic breakthroughs."""
        insights = []

        try:
            # Look for positive mood changes and completed recommendations
            recent_events = db.query(AnalyticsEvent).filter(
                and_(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.event_timestamp >= datetime.now() - timedelta(days=7),
                    AnalyticsEvent.event_type.in_([
                        AnalyticsEventType.MOOD_IMPROVEMENT.value,
                        AnalyticsEventType.THERAPEUTIC_BREAKTHROUGH.value,
                        AnalyticsEventType.RECOMMENDATION_COMPLETED.value
                    ])
                )
            ).all()

            if recent_events:
                insight = ProgressInsight(
                    user_id=user_id,
                    insight_type="breakthrough",
                    insight_title="Recent Progress Detected",
                    insight_description=f"You've shown positive progress with {len(recent_events)} breakthrough moments this week.",
                    supporting_data={"events": [e.event_name for e in recent_events]},
                    confidence_score=0.8,
                    impact_level="high",
                    is_actionable=True,
                    suggested_actions=["Continue with current therapeutic approaches", "Build on recent successes"],
                    data_period_start=datetime.now() - timedelta(days=7),
                    data_period_end=datetime.now()
                )
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating breakthrough insights: {e}")

        return insights

    async def _generate_concern_insights(self, db: Session, user_id: int) -> List[ProgressInsight]:
        """Generate insights about concerning patterns."""
        insights = []

        try:
            # Check for crisis events or declining mood
            crisis_events = db.query(AnalyticsEvent).filter(
                and_(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.event_timestamp >= datetime.now() - timedelta(days=7),
                    AnalyticsEvent.event_type == AnalyticsEventType.CRISIS_DETECTED.value
                )
            ).count()

            if crisis_events > 0:
                insight = ProgressInsight(
                    user_id=user_id,
                    insight_type="concern",
                    insight_title="Crisis Indicators Detected",
                    insight_description=f"We've detected {crisis_events} crisis indicators this week. Your wellbeing is important.",
                    supporting_data={"crisis_count": crisis_events},
                    confidence_score=0.9,
                    impact_level="high",
                    is_actionable=True,
                    suggested_actions=[
                        "Consider reaching out to a mental health professional",
                        "Use crisis resources if needed",
                        "Practice grounding techniques"
                    ],
                    data_period_start=datetime.now() - timedelta(days=7),
                    data_period_end=datetime.now()
                )
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating concern insights: {e}")

        return insights

    async def _generate_recommendation_insights(self, db: Session, user_id: int) -> List[ProgressInsight]:
        """Generate insights about recommendation effectiveness."""
        insights = []

        try:
            # Analyze recommendation completion rates
            total_recs = db.query(Recommendation).filter(
                Recommendation.user_id == user_id
            ).count()

            completed_recs = db.query(Recommendation).filter(
                and_(
                    Recommendation.user_id == user_id,
                    Recommendation.is_completed == True
                )
            ).count()

            if total_recs > 0:
                completion_rate = completed_recs / total_recs

                if completion_rate < 0.3:
                    insight = ProgressInsight(
                        user_id=user_id,
                        insight_type="recommendation",
                        insight_title="Low Recommendation Completion",
                        insight_description=f"You've completed {completion_rate:.1%} of recommendations. Consider trying shorter or different types of activities.",
                        supporting_data={"completion_rate": completion_rate, "total": total_recs, "completed": completed_recs},
                        confidence_score=0.7,
                        impact_level="medium",
                        is_actionable=True,
                        suggested_actions=[
                            "Try shorter, easier recommendations",
                            "Set reminders for recommendation practice",
                            "Choose recommendations that match your interests"
                        ],
                        data_period_start=datetime.now() - timedelta(days=30),
                        data_period_end=datetime.now()
                    )
                    insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating recommendation insights: {e}")

        return insights

    def _identify_emotion_patterns(self, emotions: List[EmotionAnalysis]) -> List[Dict]:
        """Identify patterns in emotion data."""
        patterns = []

        try:
            # Pattern 1: Consistent high sadness
            sadness_scores = [e.sadness for e in emotions]
            if statistics.mean(sadness_scores) > 0.6:
                patterns.append({
                    "title": "Persistent Sadness Pattern",
                    "description": "You've been experiencing consistently high levels of sadness. This might indicate depression symptoms.",
                    "data": {"average_sadness": statistics.mean(sadness_scores)},
                    "confidence": 0.8,
                    "impact": "high",
                    "actionable": True,
                    "actions": ["Consider professional counseling", "Practice mood-lifting activities", "Reach out to support network"]
                })

            # Pattern 2: High emotional volatility
            sentiment_scores = [e.sentiment_score for e in emotions]
            if len(sentiment_scores) > 1:
                volatility = statistics.stdev(sentiment_scores)
                if volatility > 0.4:
                    patterns.append({
                        "title": "Emotional Volatility Pattern",
                        "description": "Your emotions have been quite variable recently. This might indicate stress or instability.",
                        "data": {"volatility": volatility},
                        "confidence": 0.7,
                        "impact": "medium",
                        "actionable": True,
                        "actions": ["Practice emotional regulation techniques", "Maintain consistent routines", "Consider mindfulness practices"]
                    })

            # Pattern 3: Improving trend
            if len(sentiment_scores) >= 5:
                recent_avg = statistics.mean(sentiment_scores[-3:])
                earlier_avg = statistics.mean(sentiment_scores[:3])
                if recent_avg > earlier_avg + 0.2:
                    patterns.append({
                        "title": "Positive Improvement Pattern",
                        "description": "Your mood has been improving recently. Keep up the good work!",
                        "data": {"improvement": recent_avg - earlier_avg},
                        "confidence": 0.8,
                        "impact": "high",
                        "actionable": True,
                        "actions": ["Continue current coping strategies", "Build on recent successes", "Maintain positive habits"]
                    })

        except Exception as e:
            logger.error(f"Error identifying emotion patterns: {e}")

        return patterns

    def _analyze_conversation_metrics(
        self,
        conversation: Conversation,
        messages: List[Message],
        emotions: List[EmotionAnalysis]
    ) -> Dict:
        """Analyze detailed conversation metrics."""
        try:
            # Basic message metrics
            total_messages = len(messages)
            user_messages = len([m for m in messages if m.is_user_message])
            ai_messages = total_messages - user_messages

            # Calculate conversation duration
            if len(messages) >= 2:
                start_time = messages[0].timestamp
                end_time = messages[-1].timestamp
                duration_minutes = (end_time - start_time).total_seconds() / 60
            else:
                duration_minutes = 0.0

            # Emotional journey analysis
            emotion_trajectory = []
            dominant_emotions = {"joy": 0, "sadness": 0, "anger": 0, "fear": 0}

            if emotions:
                for emotion in emotions:
                    emotion_trajectory.append({
                        "timestamp": emotion.analyzed_at.isoformat(),
                        "sentiment": emotion.sentiment_score,
                        "joy": emotion.joy,
                        "sadness": emotion.sadness,
                        "anger": emotion.anger,
                        "fear": emotion.fear
                    })

                    # Accumulate dominant emotions
                    dominant_emotions["joy"] += emotion.joy
                    dominant_emotions["sadness"] += emotion.sadness
                    dominant_emotions["anger"] += emotion.anger
                    dominant_emotions["fear"] += emotion.fear

                # Calculate emotional range (volatility)
                sentiment_scores = [e.sentiment_score for e in emotions]
                emotional_range = max(sentiment_scores) - min(sentiment_scores) if sentiment_scores else 0.0

                # Mood change (first vs last)
                mood_change = sentiment_scores[-1] - sentiment_scores[0] if len(sentiment_scores) >= 2 else 0.0
            else:
                emotional_range = 0.0
                mood_change = 0.0

            # Calculate engagement score based on message length and frequency
            if user_messages > 0:
                user_message_objects = [m for m in messages if m.is_user_message]
                avg_message_length = statistics.mean([len(m.content) for m in user_message_objects])
                engagement_score = min(1.0, (avg_message_length / 100) * (user_messages / 10))
            else:
                engagement_score = 0.0

            # Calculate empathy score based on conversation analysis
            empathy_score = self._calculate_empathy_score(messages)

            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "ai_messages": ai_messages,
                "conversation_duration_minutes": duration_minutes,
                "emotion_trajectory": emotion_trajectory,
                "emotional_range": emotional_range,
                "dominant_emotions": list(dominant_emotions.keys()),
                "therapeutic_approach_used": self._determine_therapeutic_approach(messages),
                "engagement_score": engagement_score,
                "empathy_score": empathy_score,
                "mood_change": mood_change,
                "conversation_start": conversation.created_at,
                "conversation_end": conversation.updated_at,
                "insights_generated": 0,  # Could be calculated
                "recommendations_provided": 0  # Could be calculated
            }

        except Exception as e:
            logger.error(f"Error analyzing conversation metrics: {e}")
            return {}

    async def _calculate_comprehensive_metrics(
        self,
        db: Session,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        period_type: str = "weekly"
    ) -> Dict:
        """Calculate comprehensive progress metrics for a user."""
        try:
            # Engagement metrics
            conversations = db.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= start_date,
                    Conversation.created_at <= end_date
                )
            ).all()

            total_conversations = len(conversations)

            # Debug logging
            logger.info(f"Analytics calculation for user {user_id}: {period_type} period from {start_date} to {end_date}")
            logger.info(f"Found {total_conversations} conversations in period")

            # Get all messages in period
            conversation_ids = [c.id for c in conversations]
            if conversation_ids:
                messages = db.query(Message).filter(
                    and_(
                        Message.conversation_id.in_(conversation_ids),
                        Message.timestamp >= start_date,
                        Message.timestamp <= end_date
                    )
                ).all()

                total_messages = len(messages)

                # Calculate average session duration
                session_durations = []
                for conv in conversations:
                    conv_messages = [m for m in messages if m.conversation_id == conv.id]
                    if len(conv_messages) >= 2:
                        duration = (conv_messages[-1].timestamp - conv_messages[0].timestamp).total_seconds() / 60
                        session_durations.append(duration)

                average_session_duration = statistics.mean(session_durations) if session_durations else 0.0
            else:
                total_messages = 0
                average_session_duration = 0.0

            # Emotional metrics
            emotions = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id == user_id,
                    EmotionAnalysis.analyzed_at >= start_date,
                    EmotionAnalysis.analyzed_at <= end_date
                )
            ).all()

            if emotions:
                sentiment_scores = [e.sentiment_score for e in emotions]
                average_mood_score = statistics.mean(sentiment_scores)
                mood_stability = 1.0 - (statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0)
                mood_stability = max(0.0, min(1.0, mood_stability))

                # Calculate emotional growth (trend)
                if len(sentiment_scores) >= 3:
                    recent_avg = statistics.mean(sentiment_scores[-3:])
                    earlier_avg = statistics.mean(sentiment_scores[:3])
                    emotional_growth_score = max(0.0, min(1.0, (recent_avg - earlier_avg + 1) / 2))
                else:
                    emotional_growth_score = 0.5
            else:
                average_mood_score = 0.0
                mood_stability = 0.5
                emotional_growth_score = 0.5

            # Therapeutic metrics
            recommendations = db.query(Recommendation).filter(
                and_(
                    Recommendation.user_id == user_id,
                    Recommendation.created_at >= start_date,
                    Recommendation.created_at <= end_date
                )
            ).all()

            recommendations_completed = len([r for r in recommendations if r.is_completed])
            recommendations_completion_rate = (
                recommendations_completed / len(recommendations) if recommendations else 0.0
            )

            # Therapeutic engagement score (based on completion rate and variety)
            therapeutic_engagement_score = recommendations_completion_rate

            # Crisis and breakthrough events
            crisis_episodes = db.query(AnalyticsEvent).filter(
                and_(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.event_timestamp >= start_date,
                    AnalyticsEvent.event_timestamp <= end_date,
                    AnalyticsEvent.event_type == AnalyticsEventType.CRISIS_DETECTED.value
                )
            ).count()

            breakthrough_moments = db.query(AnalyticsEvent).filter(
                and_(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.event_timestamp >= start_date,
                    AnalyticsEvent.event_timestamp <= end_date,
                    AnalyticsEvent.event_type.in_([
                        AnalyticsEventType.THERAPEUTIC_BREAKTHROUGH.value,
                        AnalyticsEventType.MOOD_IMPROVEMENT.value
                    ])
                )
            ).count()

            # Calculate overall progress score (composite)
            progress_components = [
                emotional_growth_score * 0.3,
                mood_stability * 0.2,
                therapeutic_engagement_score * 0.2,
                min(1.0, total_conversations / 7) * 0.15,  # Engagement factor
                max(0.0, 1.0 - (crisis_episodes / 7)) * 0.15  # Crisis factor (inverted)
            ]
            overall_progress_score = sum(progress_components)

            # Engagement consistency (how regularly they engage)
            days_in_period = (end_date - start_date).days
            days_with_activity = len(set(c.created_at.date() for c in conversations))
            engagement_consistency = days_with_activity / days_in_period if days_in_period > 0 else 0.0

            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "average_session_duration": average_session_duration,
                "engagement_consistency": engagement_consistency,
                "average_mood_score": average_mood_score,
                "mood_stability": mood_stability,
                "emotional_growth_score": emotional_growth_score,
                "recommendations_completed": recommendations_completed,
                "recommendations_completion_rate": recommendations_completion_rate,
                "therapeutic_engagement_score": therapeutic_engagement_score,
                "crisis_episodes": crisis_episodes,
                "breakthrough_moments": breakthrough_moments,
                "overall_progress_score": overall_progress_score
            }

        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "average_session_duration": 0.0,
                "engagement_consistency": 0.0,
                "average_mood_score": 0.0,
                "mood_stability": 0.5,
                "emotional_growth_score": 0.5,
                "recommendations_completed": 0,
                "recommendations_completion_rate": 0.0,
                "therapeutic_engagement_score": 0.0,
                "crisis_episodes": 0,
                "breakthrough_moments": 0,
                "overall_progress_score": 0.0
            }

    async def calculate_streak_days(self, db: Session, user_id: int) -> int:
        """Calculate the current streak of consecutive days with activity."""
        try:
            # Get all conversation dates for the user, ordered by date descending
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.created_at.desc()).all()

            if not conversations:
                return 0

            # Get unique dates of activity
            activity_dates = sorted(set(
                conv.created_at.date() for conv in conversations
            ), reverse=True)

            if not activity_dates:
                return 0

            # Check if there's activity today or yesterday (to account for timezone differences)
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            # Start counting from the most recent activity
            if activity_dates[0] not in [today, yesterday]:
                return 0

            # Count consecutive days
            streak = 1
            current_date = activity_dates[0]

            for i in range(1, len(activity_dates)):
                expected_date = current_date - timedelta(days=1)
                if activity_dates[i] == expected_date:
                    streak += 1
                    current_date = activity_dates[i]
                else:
                    break

            return streak

        except Exception as e:
            logger.error(f"Error calculating streak days: {e}")
            return 0

    def _calculate_empathy_score(self, messages: List[Message]) -> float:
        """Calculate empathy score based on AI message characteristics."""
        try:
            ai_messages = [m for m in messages if not m.is_user_message]
            if not ai_messages:
                return 0.5

            # Simple heuristic based on message characteristics
            total_score = 0.0
            for message in ai_messages:
                content = message.content.lower()
                score = 0.5  # Base score

                # Positive indicators
                empathy_words = ['understand', 'feel', 'sorry', 'support', 'here for you', 'validate']
                for word in empathy_words:
                    if word in content:
                        score += 0.1

                # Question asking (shows engagement)
                if '?' in content:
                    score += 0.05

                # Length indicates thoughtfulness
                if len(content) > 100:
                    score += 0.05

                total_score += min(1.0, score)

            return total_score / len(ai_messages)

        except Exception as e:
            logger.error(f"Error calculating empathy score: {e}")
            return 0.5

    def _determine_therapeutic_approach(self, messages: List[Message]) -> str:
        """Determine the therapeutic approach used based on conversation content."""
        try:
            ai_messages = [m for m in messages if not m.is_user_message]
            if not ai_messages:
                return "supportive"

            # Analyze AI message content for therapeutic approaches
            content = ' '.join(m.content.lower() for m in ai_messages)

            # Keywords for different approaches
            approaches = {
                "cognitive_behavioral": ["thought", "thinking", "belief", "behavior", "pattern", "challenge"],
                "person_centered": ["feel", "experience", "understand", "accept", "validate"],
                "mindfulness": ["present", "moment", "breath", "awareness", "mindful", "meditation"],
                "solution_focused": ["goal", "solution", "strength", "resource", "progress", "future"],
                "psychodynamic": ["past", "relationship", "childhood", "unconscious", "insight"]
            }

            scores = {}
            for approach, keywords in approaches.items():
                score = sum(1 for keyword in keywords if keyword in content)
                scores[approach] = score

            # Return the approach with the highest score, or default
            if scores:
                return max(scores, key=scores.get) or "person_centered"
            return "person_centered"

        except Exception as e:
            logger.error(f"Error determining therapeutic approach: {e}")
            return "person_centered"

    async def generate_daily_focus(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Generate personalized daily focus based on user's current state and patterns."""
        try:
            # Get recent emotion data (last 3 days)
            recent_emotions = db.query(EmotionAnalysis).filter(
                EmotionAnalysis.user_id == user_id,
                EmotionAnalysis.analyzed_at >= datetime.now() - timedelta(days=3)
            ).order_by(EmotionAnalysis.analyzed_at.desc()).limit(10).all()

            # Get recent recommendations
            recent_recommendations = db.query(Recommendation).filter(
                Recommendation.user_id == user_id,
                Recommendation.created_at >= datetime.now() - timedelta(days=7)
            ).order_by(Recommendation.created_at.desc()).limit(5).all()

            # Analyze current emotional state
            current_state = self._analyze_current_emotional_state(recent_emotions)

            # Generate focus based on emotional state
            focus_data = self._generate_focus_content(current_state, recent_recommendations)

            return {
                "focus_title": focus_data["title"],
                "focus_description": focus_data["description"],
                "focus_quote": focus_data["quote"],
                "focus_activity": focus_data["activity"],
                "emotional_context": current_state,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating daily focus: {e}")
            # Return default focus if generation fails
            return {
                "focus_title": "Mindful Presence",
                "focus_description": "Take a moment to practice mindfulness and connect with your inner self.",
                "focus_quote": "The present moment is the only time over which we have dominion. - Thích Nhất Hạnh",
                "focus_activity": "Try a 5-minute breathing exercise to center yourself.",
                "emotional_context": {"state": "neutral"},
                "generated_at": datetime.now().isoformat()
            }

    def _analyze_current_emotional_state(self, recent_emotions: List[EmotionAnalysis]) -> Dict[str, Any]:
        """Analyze the user's current emotional state from recent data."""
        if not recent_emotions:
            return {"state": "neutral", "dominant_emotion": "neutral", "intensity": 0.5}

        # Calculate average emotions from recent data
        emotion_totals = {
            "joy": 0, "sadness": 0, "anger": 0, "fear": 0,
            "surprise": 0, "disgust": 0, "neutral": 0
        }

        for emotion in recent_emotions:
            emotion_totals["joy"] += emotion.joy
            emotion_totals["sadness"] += emotion.sadness
            emotion_totals["anger"] += emotion.anger
            emotion_totals["fear"] += emotion.fear
            emotion_totals["surprise"] += emotion.surprise
            emotion_totals["disgust"] += emotion.disgust

        # Calculate averages
        count = len(recent_emotions)
        emotion_averages = {k: v / count for k, v in emotion_totals.items()}

        # Find dominant emotion
        dominant_emotion = max(emotion_averages, key=emotion_averages.get)
        intensity = emotion_averages[dominant_emotion]

        # Determine overall state
        if dominant_emotion == "joy" and intensity > 0.6:
            state = "positive"
        elif dominant_emotion in ["sadness", "anger", "fear"] and intensity > 0.6:
            state = "challenging"
        elif intensity < 0.4:
            state = "neutral"
        else:
            state = "mixed"

        return {
            "state": state,
            "dominant_emotion": dominant_emotion,
            "intensity": intensity,
            "emotion_averages": emotion_averages
        }

    def _generate_focus_content(self, emotional_state: Dict[str, Any], recent_recommendations: List) -> Dict[str, str]:
        """Generate personalized focus content based on emotional state."""
        state = emotional_state.get("state", "neutral")
        dominant_emotion = emotional_state.get("dominant_emotion", "neutral")

        # Focus content based on emotional state
        focus_templates = {
            "positive": {
                "title": "Gratitude and Growth",
                "description": "You're in a positive space today. Let's build on this energy and cultivate gratitude.",
                "quote": "Gratitude turns what we have into enough. - Anonymous",
                "activity": "Write down three things you're grateful for and one way you've grown recently."
            },
            "challenging": {
                "sadness": {
                    "title": "Gentle Self-Compassion",
                    "description": "It's okay to feel sad. Today, focus on treating yourself with the same kindness you'd show a good friend.",
                    "quote": "You are allowed to be both a masterpiece and a work in progress simultaneously. - Sophia Bush",
                    "activity": "Practice a loving-kindness meditation or write yourself a compassionate letter."
                },
                "anger": {
                    "title": "Healthy Expression",
                    "description": "Anger can be a signal that something needs attention. Let's channel this energy constructively.",
                    "quote": "Anger is an acid that can do more harm to the vessel in which it is stored than to anything on which it is poured. - Mark Twain",
                    "activity": "Try journaling about what's triggering your anger, or do some physical exercise to release tension."
                },
                "fear": {
                    "title": "Courage and Grounding",
                    "description": "Fear often points to what matters most to us. Today, focus on grounding yourself in the present moment.",
                    "quote": "Courage is not the absence of fear, but action in spite of it. - Mark Twain",
                    "activity": "Practice the 5-4-3-2-1 grounding technique: 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste."
                }
            },
            "neutral": {
                "title": "Mindful Awareness",
                "description": "Today is a good day to cultivate awareness and set positive intentions.",
                "quote": "The present moment is the only time over which we have dominion. - Thích Nhất Hạnh",
                "activity": "Take 10 minutes for mindful breathing or set a positive intention for your day."
            },
            "mixed": {
                "title": "Balance and Acceptance",
                "description": "You're experiencing a mix of emotions today. Let's focus on finding balance and accepting all parts of your experience.",
                "quote": "Life is like a piano. What you get out of it depends on how you play it. - Tom Lehrer",
                "activity": "Try a body scan meditation to acknowledge and accept all your current feelings."
            }
        }

        # Select appropriate content
        if state == "challenging" and dominant_emotion in focus_templates["challenging"]:
            return focus_templates["challenging"][dominant_emotion]
        elif state in focus_templates:
            return focus_templates[state]
        else:
            return focus_templates["neutral"]
