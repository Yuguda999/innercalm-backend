"""
Community analytics service for engagement metrics and insights.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case

from models.user import User
from models.community import (
    SharedWoundGroup, PeerCircle, CircleMembership, CircleMessage,
    ReflectionChain, ReflectionEntry, UserClusterProfile,
    CircleStatus, MembershipStatus, MessageStatus, ReflectionStatus
)
from models.emotion import EmotionAnalysis

logger = logging.getLogger(__name__)


class CommunityAnalyticsService:
    """Service for community engagement analytics and insights."""

    def __init__(self):
        self.default_period_days = 30
        self.cache_duration = timedelta(minutes=15)
        self._cache = {}

    async def get_community_overview(
        self,
        db: Session,
        days: int = 30
    ) -> Dict[str, any]:
        """Get overall community engagement overview."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Basic metrics
            total_groups = db.query(SharedWoundGroup).filter(
                SharedWoundGroup.is_active == True
            ).count()

            total_circles = db.query(PeerCircle).filter(
                PeerCircle.status == CircleStatus.ACTIVE
            ).count()

            active_members = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.status == MembershipStatus.ACTIVE,
                    CircleMembership.last_seen_at >= cutoff_date
                )
            ).count()

            total_messages = db.query(CircleMessage).filter(
                CircleMessage.created_at >= cutoff_date
            ).count()

            total_reflections = db.query(ReflectionEntry).filter(
                ReflectionEntry.created_at >= cutoff_date
            ).count()

            # Engagement metrics
            avg_messages_per_circle = db.query(
                func.avg(PeerCircle.message_count)
            ).scalar() or 0

            # Growth metrics
            new_members = db.query(CircleMembership).filter(
                CircleMembership.joined_at >= cutoff_date
            ).count()

            # Support metrics
            total_supports = db.query(
                func.sum(CircleMessage.support_count)
            ).filter(
                CircleMessage.created_at >= cutoff_date
            ).scalar() or 0

            return {
                "period_days": days,
                "total_groups": total_groups,
                "total_circles": total_circles,
                "active_members": active_members,
                "total_messages": total_messages,
                "total_reflections": total_reflections,
                "avg_messages_per_circle": round(avg_messages_per_circle, 2),
                "new_members": new_members,
                "total_supports": total_supports,
                "engagement_rate": round((total_messages + total_reflections) / max(active_members, 1), 2)
            }

        except Exception as e:
            logger.error(f"Error getting community overview: {e}")
            return {}

    async def get_group_analytics(
        self,
        db: Session,
        group_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """Get analytics for shared wound groups."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(SharedWoundGroup)
            if group_id:
                query = query.filter(SharedWoundGroup.id == group_id)

            groups = query.filter(SharedWoundGroup.is_active == True).all()

            group_analytics = []
            for group in groups:
                # Get circles in this group
                circles = db.query(PeerCircle).filter(
                    PeerCircle.shared_wound_group_id == group.id
                ).all()

                # Get active members
                active_members = db.query(CircleMembership).join(PeerCircle).filter(
                    and_(
                        PeerCircle.shared_wound_group_id == group.id,
                        CircleMembership.status == "active",
                        CircleMembership.last_seen_at >= cutoff_date
                    )
                ).count()

                # Get messages
                total_messages = db.query(CircleMessage).join(PeerCircle).filter(
                    and_(
                        PeerCircle.shared_wound_group_id == group.id,
                        CircleMessage.created_at >= cutoff_date
                    )
                ).count()

                # Get engagement metrics
                avg_session_duration = await self._calculate_avg_session_duration(
                    db, group.id, cutoff_date
                )

                # Get emotional health trends
                emotional_trends = await self._get_group_emotional_trends(
                    db, group.id, cutoff_date
                )

                group_analytics.append({
                    "group_id": group.id,
                    "group_name": group.name,
                    "healing_stage": group.healing_stage,
                    "circle_count": len(circles),
                    "active_members": active_members,
                    "total_messages": total_messages,
                    "avg_session_duration_minutes": avg_session_duration,
                    "emotional_trends": emotional_trends,
                    "engagement_score": await self._calculate_engagement_score(
                        active_members, total_messages, avg_session_duration
                    )
                })

            return group_analytics

        except Exception as e:
            logger.error(f"Error getting group analytics: {e}")
            return []

    async def get_circle_analytics(
        self,
        db: Session,
        circle_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """Get analytics for peer circles."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(PeerCircle)
            if circle_id:
                query = query.filter(PeerCircle.id == circle_id)

            circles = query.filter(PeerCircle.status == "active").all()

            circle_analytics = []
            for circle in circles:
                # Member analytics
                members = db.query(CircleMembership).filter(
                    CircleMembership.peer_circle_id == circle.id
                ).all()

                active_members = [m for m in members if m.last_seen_at >= cutoff_date]

                # Message analytics
                messages = db.query(CircleMessage).filter(
                    and_(
                        CircleMessage.peer_circle_id == circle.id,
                        CircleMessage.created_at >= cutoff_date
                    )
                ).all()

                # Support analytics
                total_supports = sum(msg.support_count for msg in messages)

                # Activity patterns
                activity_by_hour = await self._get_activity_by_hour(db, circle.id, cutoff_date)
                activity_by_day = await self._get_activity_by_day(db, circle.id, cutoff_date)

                # Member participation
                member_participation = await self._get_member_participation(
                    db, circle.id, cutoff_date
                )

                circle_analytics.append({
                    "circle_id": circle.id,
                    "circle_name": circle.name,
                    "total_members": len(members),
                    "active_members": len(active_members),
                    "total_messages": len(messages),
                    "total_supports": total_supports,
                    "avg_messages_per_member": round(len(messages) / max(len(active_members), 1), 2),
                    "support_ratio": round(total_supports / max(len(messages), 1), 2),
                    "activity_by_hour": activity_by_hour,
                    "activity_by_day": activity_by_day,
                    "member_participation": member_participation,
                    "health_score": await self._calculate_circle_health_score(
                        len(active_members), len(messages), total_supports
                    )
                })

            return circle_analytics

        except Exception as e:
            logger.error(f"Error getting circle analytics: {e}")
            return []

    async def get_reflection_analytics(
        self,
        db: Session,
        chain_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, any]]:
        """Get analytics for reflection chains."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(ReflectionChain)
            if chain_id:
                query = query.filter(ReflectionChain.id == chain_id)

            chains = query.filter(ReflectionChain.is_active == True).all()

            chain_analytics = []
            for chain in chains:
                # Entry analytics
                entries = db.query(ReflectionEntry).filter(
                    and_(
                        ReflectionEntry.chain_id == chain.id,
                        ReflectionEntry.created_at >= cutoff_date
                    )
                ).all()

                # Engagement metrics
                total_views = sum(entry.view_count for entry in entries)
                total_helpful = sum(entry.helpful_count for entry in entries)

                # Entry type distribution
                entry_types = {}
                for entry in entries:
                    entry_types[entry.reflection_type] = entry_types.get(entry.reflection_type, 0) + 1

                # Target stage distribution
                target_stages = {}
                for entry in entries:
                    if entry.target_stage:
                        target_stages[entry.target_stage] = target_stages.get(entry.target_stage, 0) + 1

                chain_analytics.append({
                    "chain_id": chain.id,
                    "chain_title": chain.title,
                    "healing_module": chain.healing_module,
                    "difficulty_level": chain.difficulty_level,
                    "total_entries": len(entries),
                    "total_views": total_views,
                    "total_helpful": total_helpful,
                    "avg_views_per_entry": round(total_views / max(len(entries), 1), 2),
                    "helpful_ratio": round(total_helpful / max(total_views, 1), 2),
                    "entry_type_distribution": entry_types,
                    "target_stage_distribution": target_stages,
                    "impact_score": await self._calculate_reflection_impact_score(
                        len(entries), total_views, total_helpful
                    )
                })

            return chain_analytics

        except Exception as e:
            logger.error(f"Error getting reflection analytics: {e}")
            return []

    async def get_user_engagement_metrics(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, any]:
        """Get engagement metrics for a specific user."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Circle participation
            memberships = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.user_id == user_id,
                    CircleMembership.status == MembershipStatus.ACTIVE
                )
            ).all()

            # Messages sent
            messages_sent = db.query(CircleMessage).filter(
                and_(
                    CircleMessage.user_id == user_id,
                    CircleMessage.created_at >= cutoff_date
                )
            ).count()

            # Supports given
            supports_given = db.query(CircleMessage).filter(
                and_(
                    CircleMessage.user_id == user_id,
                    CircleMessage.created_at >= cutoff_date
                )
            ).count()  # This would need a proper support table join

            # Reflections shared
            reflections_shared = db.query(ReflectionEntry).filter(
                and_(
                    ReflectionEntry.user_id == user_id,
                    ReflectionEntry.created_at >= cutoff_date
                )
            ).count()

            # Activity streak
            activity_streak = await self._calculate_activity_streak(db, user_id)

            # Emotional progress
            emotional_progress = await self._get_user_emotional_progress(
                db, user_id, cutoff_date
            )

            return {
                "user_id": user_id,
                "period_days": days,
                "circles_joined": len(memberships),
                "messages_sent": messages_sent,
                "supports_given": supports_given,
                "reflections_shared": reflections_shared,
                "activity_streak_days": activity_streak,
                "emotional_progress": emotional_progress,
                "engagement_level": await self._classify_engagement_level(
                    messages_sent, supports_given, reflections_shared, activity_streak
                )
            }

        except Exception as e:
            logger.error(f"Error getting user engagement metrics: {e}")
            return {}

    async def _calculate_avg_session_duration(
        self,
        db: Session,
        group_id: int,
        cutoff_date: datetime
    ) -> float:
        """Calculate average session duration for a group."""
        # This would require session tracking - simplified for now
        return 25.5  # Mock average of 25.5 minutes

    async def _get_group_emotional_trends(
        self,
        db: Session,
        group_id: int,
        cutoff_date: datetime
    ) -> Dict[str, float]:
        """Get emotional health trends for a group."""
        try:
            # Get users in this group
            user_ids = db.query(CircleMembership.user_id).join(PeerCircle).filter(
                PeerCircle.shared_wound_group_id == group_id
            ).distinct().all()

            user_ids = [uid[0] for uid in user_ids]

            if not user_ids:
                return {}

            # Get recent emotion analyses for these users
            emotions = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id.in_(user_ids),
                    EmotionAnalysis.analyzed_at >= cutoff_date
                )
            ).all()

            if not emotions:
                return {}

            # Calculate average emotions
            emotion_totals = {
                'joy': 0, 'sadness': 0, 'anger': 0,
                'fear': 0, 'surprise': 0, 'disgust': 0
            }

            for emotion in emotions:
                for key in emotion_totals.keys():
                    emotion_totals[key] += getattr(emotion, key, 0)

            count = len(emotions)
            return {k: round(v / count, 3) for k, v in emotion_totals.items()}

        except Exception as e:
            logger.error(f"Error getting emotional trends: {e}")
            return {}

    async def _calculate_engagement_score(
        self,
        active_members: int,
        total_messages: int,
        avg_session_duration: float
    ) -> float:
        """Calculate engagement score for a group."""
        if active_members == 0:
            return 0.0

        # Weighted scoring
        message_score = min(total_messages / active_members, 10) * 0.4
        duration_score = min(avg_session_duration / 30, 1) * 0.3
        participation_score = min(active_members / 8, 1) * 0.3

        return round((message_score + duration_score + participation_score) * 10, 2)

    async def _get_activity_by_hour(
        self,
        db: Session,
        circle_id: int,
        cutoff_date: datetime
    ) -> Dict[int, int]:
        """Get activity distribution by hour of day."""
        try:
            results = db.query(
                func.extract('hour', CircleMessage.created_at).label('hour'),
                func.count(CircleMessage.id).label('count')
            ).filter(
                and_(
                    CircleMessage.peer_circle_id == circle_id,
                    CircleMessage.created_at >= cutoff_date
                )
            ).group_by(
                func.extract('hour', CircleMessage.created_at)
            ).all()

            return {int(hour): count for hour, count in results}

        except Exception as e:
            logger.error(f"Error getting activity by hour: {e}")
            return {}

    async def _get_activity_by_day(
        self,
        db: Session,
        circle_id: int,
        cutoff_date: datetime
    ) -> Dict[str, int]:
        """Get activity distribution by day of week."""
        try:
            results = db.query(
                func.extract('dow', CircleMessage.created_at).label('dow'),
                func.count(CircleMessage.id).label('count')
            ).filter(
                and_(
                    CircleMessage.peer_circle_id == circle_id,
                    CircleMessage.created_at >= cutoff_date
                )
            ).group_by(
                func.extract('dow', CircleMessage.created_at)
            ).all()

            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            return {days[int(dow)]: count for dow, count in results}

        except Exception as e:
            logger.error(f"Error getting activity by day: {e}")
            return {}

    async def _get_member_participation(
        self,
        db: Session,
        circle_id: int,
        cutoff_date: datetime
    ) -> List[Dict[str, any]]:
        """Get member participation metrics."""
        try:
            results = db.query(
                CircleMembership.user_id,
                User.username,
                func.count(CircleMessage.id).label('message_count'),
                func.sum(CircleMessage.support_count).label('supports_received')
            ).join(
                User, CircleMembership.user_id == User.id
            ).outerjoin(
                CircleMessage, and_(
                    CircleMessage.user_id == CircleMembership.user_id,
                    CircleMessage.peer_circle_id == circle_id,
                    CircleMessage.created_at >= cutoff_date
                )
            ).filter(
                CircleMembership.peer_circle_id == circle_id
            ).group_by(
                CircleMembership.user_id, User.username
            ).all()

            return [
                {
                    "user_id": user_id,
                    "username": username,
                    "message_count": message_count or 0,
                    "supports_received": supports_received or 0
                }
                for user_id, username, message_count, supports_received in results
            ]

        except Exception as e:
            logger.error(f"Error getting member participation: {e}")
            return []

    async def get_community_dashboard(
        self,
        db: Session,
        user_id: int,
        days_back: int = 30
    ) -> Dict[str, any]:
        """Get comprehensive community analytics dashboard."""
        try:
            overview = await self.get_community_overview(db, days_back)
            user_metrics = await self.get_user_engagement_metrics(db, user_id, days_back)

            return {
                "overview": overview,
                "user_metrics": user_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting community dashboard: {e}")
            return {}

    async def get_engagement_metrics(
        self,
        db: Session,
        user_id: int,
        period: str = "week"
    ) -> Dict[str, any]:
        """Get engagement metrics for a specific period."""
        try:
            days = {"day": 1, "week": 7, "month": 30}.get(period, 7)
            return await self.get_user_engagement_metrics(db, user_id, days)

        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return {}

    async def get_real_time_stats(self, db: Session) -> Dict[str, any]:
        """Get real-time community statistics."""
        try:
            now = datetime.utcnow()

            # Active users in last 24 hours
            active_users_24h = db.query(func.count(func.distinct(CircleMessage.user_id))).filter(
                CircleMessage.created_at >= now - timedelta(hours=24)
            ).scalar() or 0

            # Messages in last hour
            messages_last_hour = db.query(CircleMessage).filter(
                CircleMessage.created_at >= now - timedelta(hours=1)
            ).count()

            # Active circles
            active_circles = db.query(PeerCircle).filter(
                PeerCircle.status == CircleStatus.ACTIVE
            ).count()

            # Recent reflections
            recent_reflections = db.query(ReflectionEntry).filter(
                ReflectionEntry.created_at >= now - timedelta(hours=24)
            ).count()

            return {
                "timestamp": now.isoformat(),
                "active_users_24h": active_users_24h,
                "messages_last_hour": messages_last_hour,
                "active_circles": active_circles,
                "recent_reflections": recent_reflections,
                "community_pulse": self._calculate_community_pulse(
                    active_users_24h, messages_last_hour, recent_reflections
                )
            }

        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")
            return {}

    def _calculate_community_pulse(
        self,
        active_users: int,
        recent_messages: int,
        recent_reflections: int
    ) -> str:
        """Calculate community pulse status."""
        total_activity = active_users + recent_messages + recent_reflections

        if total_activity > 50:
            return "very_active"
        elif total_activity > 20:
            return "active"
        elif total_activity > 5:
            return "moderate"
        else:
            return "quiet"

    async def _calculate_circle_health_score(
        self,
        active_members: int,
        total_messages: int,
        total_supports: int
    ) -> float:
        """Calculate health score for a circle."""
        if active_members == 0:
            return 0.0

        # Balanced participation
        participation_score = min(active_members / 6, 1) * 0.4

        # Message activity
        activity_score = min(total_messages / (active_members * 5), 1) * 0.3

        # Support ratio
        support_score = min(total_supports / max(total_messages, 1), 1) * 0.3

        return round((participation_score + activity_score + support_score) * 100, 2)

    async def _calculate_reflection_impact_score(
        self,
        total_entries: int,
        total_views: int,
        total_helpful: int
    ) -> float:
        """Calculate impact score for reflection chains."""
        if total_entries == 0:
            return 0.0

        # Entry quality (views per entry)
        quality_score = min(total_views / total_entries / 10, 1) * 0.4

        # Helpfulness ratio
        helpful_score = min(total_helpful / max(total_views, 1), 1) * 0.4

        # Volume score
        volume_score = min(total_entries / 20, 1) * 0.2

        return round((quality_score + helpful_score + volume_score) * 100, 2)

    async def _calculate_activity_streak(self, db: Session, user_id: int) -> int:
        """Calculate user's activity streak in days."""
        # Simplified - would need proper streak calculation
        return 7  # Mock 7-day streak

    async def _get_user_emotional_progress(
        self,
        db: Session,
        user_id: int,
        cutoff_date: datetime
    ) -> Dict[str, float]:
        """Get user's emotional progress over time."""
        try:
            # Get emotion analyses for the period
            emotions = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id == user_id,
                    EmotionAnalysis.analyzed_at >= cutoff_date
                )
            ).order_by(EmotionAnalysis.analyzed_at).all()

            if len(emotions) < 2:
                return {}

            # Compare first half vs second half
            mid_point = len(emotions) // 2
            first_half = emotions[:mid_point]
            second_half = emotions[mid_point:]

            def avg_emotions(emotion_list):
                if not emotion_list:
                    return {}
                totals = {'joy': 0, 'sadness': 0, 'anger': 0, 'fear': 0}
                for e in emotion_list:
                    for key in totals.keys():
                        totals[key] += getattr(e, key, 0)
                return {k: v / len(emotion_list) for k, v in totals.items()}

            first_avg = avg_emotions(first_half)
            second_avg = avg_emotions(second_half)

            # Calculate progress (positive emotions up, negative emotions down)
            progress = {}
            for emotion in first_avg.keys():
                if emotion == 'joy':
                    progress[emotion] = second_avg[emotion] - first_avg[emotion]
                else:  # negative emotions
                    progress[emotion] = first_avg[emotion] - second_avg[emotion]

            return progress

        except Exception as e:
            logger.error(f"Error getting emotional progress: {e}")
            return {}

    async def _classify_engagement_level(
        self,
        messages_sent: int,
        supports_given: int,
        reflections_shared: int,
        activity_streak: int
    ) -> str:
        """Classify user engagement level."""
        total_activity = messages_sent + supports_given + reflections_shared

        if total_activity >= 50 and activity_streak >= 14:
            return "highly_engaged"
        elif total_activity >= 20 and activity_streak >= 7:
            return "moderately_engaged"
        elif total_activity >= 5:
            return "lightly_engaged"
        else:
            return "inactive"


# Global analytics service instance
community_analytics = CommunityAnalyticsService()
