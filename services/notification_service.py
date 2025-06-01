"""
Notification service for push notifications and in-app alerts.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.user import User
from models.community import (
    CircleMembership, CircleMessage, ReflectionEntry, PeerCircle
)
from models.notification import (
    Notification, NotificationPreference, DeviceToken, NotificationLog
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and push alerts."""

    def __init__(self):
        self.notification_types = {
            'new_message': {
                'title': 'New message in {circle_name}',
                'body': '{user_name}: {preview}',
                'priority': 'normal',
                'category': 'circle_activity'
            },
            'message_support': {
                'title': 'Someone supported your message',
                'body': '{user_name} sent you support in {circle_name}',
                'priority': 'low',
                'category': 'engagement'
            },
            'circle_invitation': {
                'title': 'Circle invitation',
                'body': 'You\'ve been invited to join {circle_name}',
                'priority': 'high',
                'category': 'invitation'
            },
            'reflection_helpful': {
                'title': 'Your reflection helped someone',
                'body': 'Someone found your reflection helpful in {chain_title}',
                'priority': 'low',
                'category': 'engagement'
            },
            'crisis_alert': {
                'title': 'Support resources available',
                'body': 'We\'re here to help. Tap for crisis support resources.',
                'priority': 'urgent',
                'category': 'crisis'
            },
            'daily_check_in': {
                'title': 'How are you feeling today?',
                'body': 'Your circle is here to support you',
                'priority': 'low',
                'category': 'wellness'
            },
            'weekly_summary': {
                'title': 'Your weekly community summary',
                'body': 'See your progress and circle activity',
                'priority': 'low',
                'category': 'summary'
            }
        }

    async def send_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
        immediate: bool = False
    ) -> bool:
        """Send a notification to a user."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for notification")
                return False

            # Check user notification preferences
            if not await self._should_send_notification(db, user_id, notification_type):
                logger.info(f"Notification {notification_type} skipped for user {user_id} due to preferences")
                return True

            # Get notification template
            template = self.notification_types.get(notification_type)
            if not template:
                logger.error(f"Unknown notification type: {notification_type}")
                return False

            # Format notification content
            title = template['title'].format(**data)
            body = template['body'].format(**data)

            notification_payload = {
                'title': title,
                'body': body,
                'priority': template['priority'],
                'category': template['category'],
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Send push notification
            success = await self._send_push_notification(user, notification_payload)

            # Store notification in database for history
            await self._store_notification(db, user_id, notification_type, notification_payload)

            logger.info(f"Notification {notification_type} sent to user {user_id}: {success}")
            return success

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    async def send_bulk_notification(
        self,
        db: Session,
        user_ids: List[int],
        notification_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Send notifications to multiple users."""
        results = {"sent": 0, "failed": 0, "skipped": 0}

        for user_id in user_ids:
            try:
                success = await self.send_notification(db, user_id, notification_type, data)
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error sending bulk notification to user {user_id}: {e}")
                results["failed"] += 1

        return results

    async def notify_new_message(
        self,
        db: Session,
        message: CircleMessage,
        exclude_user_id: Optional[int] = None
    ):
        """Notify circle members about a new message."""
        try:
            # Get circle members
            memberships = db.query(CircleMembership).filter(
                and_(
                    CircleMembership.peer_circle_id == message.peer_circle_id,
                    CircleMembership.status == "active",
                    CircleMembership.notifications_enabled == True
                )
            ).all()

            # Get circle and sender info
            circle = db.query(PeerCircle).filter(PeerCircle.id == message.peer_circle_id).first()
            sender = db.query(User).filter(User.id == message.user_id).first()

            if not circle or not sender:
                return

            # Prepare notification data
            preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
            data = {
                'circle_name': circle.name,
                'user_name': sender.full_name or sender.username,
                'preview': preview,
                'circle_id': circle.id,
                'message_id': message.id
            }

            # Send to all members except sender
            user_ids = [
                m.user_id for m in memberships
                if m.user_id != exclude_user_id and m.user_id != message.user_id
            ]

            await self.send_bulk_notification(db, user_ids, 'new_message', data)

        except Exception as e:
            logger.error(f"Error notifying new message: {e}")

    async def notify_message_support(
        self,
        db: Session,
        message: CircleMessage,
        supporter_user_id: int
    ):
        """Notify user when their message receives support."""
        try:
            if message.user_id == supporter_user_id:
                return  # Don't notify self-support

            circle = db.query(PeerCircle).filter(PeerCircle.id == message.peer_circle_id).first()
            supporter = db.query(User).filter(User.id == supporter_user_id).first()

            if not circle or not supporter:
                return

            data = {
                'circle_name': circle.name,
                'user_name': supporter.full_name or supporter.username,
                'circle_id': circle.id,
                'message_id': message.id
            }

            await self.send_notification(db, message.user_id, 'message_support', data)

        except Exception as e:
            logger.error(f"Error notifying message support: {e}")

    async def notify_circle_invitation(
        self,
        db: Session,
        user_id: int,
        circle_id: int,
        inviter_id: int
    ):
        """Notify user about circle invitation."""
        try:
            circle = db.query(PeerCircle).filter(PeerCircle.id == circle_id).first()
            inviter = db.query(User).filter(User.id == inviter_id).first()

            if not circle or not inviter:
                return

            data = {
                'circle_name': circle.name,
                'inviter_name': inviter.full_name or inviter.username,
                'circle_id': circle.id
            }

            await self.send_notification(db, user_id, 'circle_invitation', data)

        except Exception as e:
            logger.error(f"Error notifying circle invitation: {e}")

    async def notify_reflection_helpful(
        self,
        db: Session,
        reflection: ReflectionEntry,
        helper_user_id: int
    ):
        """Notify user when their reflection is marked helpful."""
        try:
            if reflection.user_id == helper_user_id:
                return  # Don't notify self-help

            from models.community import ReflectionChain
            chain = db.query(ReflectionChain).filter(ReflectionChain.id == reflection.chain_id).first()

            if not chain:
                return

            data = {
                'chain_title': chain.title,
                'reflection_id': reflection.id,
                'chain_id': chain.id
            }

            await self.send_notification(db, reflection.user_id, 'reflection_helpful', data)

        except Exception as e:
            logger.error(f"Error notifying reflection helpful: {e}")

    async def send_crisis_alert(
        self,
        db: Session,
        user_id: int,
        crisis_resources: Dict[str, Any]
    ):
        """Send crisis alert with resources."""
        try:
            data = {
                'resources': crisis_resources,
                'urgent': True
            }

            await self.send_notification(db, user_id, 'crisis_alert', data, immediate=True)

        except Exception as e:
            logger.error(f"Error sending crisis alert: {e}")

    async def send_daily_check_in(self, db: Session, user_ids: List[int]):
        """Send daily check-in notifications."""
        try:
            data = {
                'type': 'daily_check_in',
                'timestamp': datetime.utcnow().isoformat()
            }

            await self.send_bulk_notification(db, user_ids, 'daily_check_in', data)

        except Exception as e:
            logger.error(f"Error sending daily check-in: {e}")

    async def send_weekly_summary(
        self,
        db: Session,
        user_id: int,
        summary_data: Dict[str, Any]
    ):
        """Send weekly community summary."""
        try:
            data = {
                'summary': summary_data,
                'week_start': (datetime.utcnow() - timedelta(days=7)).isoformat()
            }

            await self.send_notification(db, user_id, 'weekly_summary', data)

        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")

    async def _should_send_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str
    ) -> bool:
        """Check if notification should be sent based on user preferences."""
        try:
            # Get user notification preferences
            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).first()

            if not prefs:
                # Create default preferences if none exist
                prefs = NotificationPreference(user_id=user_id)
                db.add(prefs)
                db.commit()

            # Check specific notification type preferences
            type_mapping = {
                'new_message': prefs.circle_messages,
                'message_support': prefs.message_support,
                'circle_invitation': prefs.circle_invitations,
                'reflection_helpful': prefs.reflection_helpful,
                'crisis_alert': prefs.crisis_alerts,
                'daily_check_in': prefs.daily_check_in,
                'weekly_summary': prefs.weekly_summary
            }

            if not type_mapping.get(notification_type, True):
                return False

            # Check quiet hours
            if prefs.quiet_hours_enabled:
                current_time = datetime.utcnow().time()
                start_time = datetime.strptime(prefs.quiet_hours_start, "%H:%M").time()
                end_time = datetime.strptime(prefs.quiet_hours_end, "%H:%M").time()

                # Handle quiet hours that span midnight
                if start_time > end_time:
                    in_quiet_hours = current_time >= start_time or current_time <= end_time
                else:
                    in_quiet_hours = start_time <= current_time <= end_time

                if in_quiet_hours:
                    # Only send urgent notifications during quiet hours
                    template = self.notification_types.get(notification_type, {})
                    if template.get('priority') != 'urgent':
                        return False

            # Check notification frequency limits
            recent_notifications = await self._get_recent_notification_count(
                db, user_id, hours=1
            )

            if recent_notifications > 10:  # Max 10 notifications per hour
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking notification preferences: {e}")
            return True  # Default to sending

    async def _send_push_notification(
        self,
        user: User,
        payload: Dict[str, Any]
    ) -> bool:
        """Send push notification to user's devices."""
        try:
            # This would integrate with push notification services like:
            # - Firebase Cloud Messaging (FCM) for mobile
            # - Web Push API for browsers
            # - Apple Push Notification Service (APNs) for iOS

            # For now, we'll simulate the push notification
            logger.info(f"PUSH NOTIFICATION to {user.username}: {payload['title']}")

            # In production, you would:
            # 1. Get user's device tokens from database
            # 2. Send to appropriate push service
            # 3. Handle delivery receipts and failures
            # 4. Update device token status

            return True  # Simulate successful delivery

        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    async def _store_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str,
        payload: Dict[str, Any]
    ):
        """Store notification in database for history."""
        try:
            # Create notification record
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=payload['title'],
                body=payload['body'],
                data=payload.get('data', {}),
                priority=payload['priority'],
                category=payload['category'],
                is_delivered=True,
                delivered_at=datetime.utcnow()
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(f"Stored notification {notification.id} for user {user_id}")
            return notification

        except Exception as e:
            logger.error(f"Error storing notification: {e}")
            db.rollback()
            return None

    async def _get_recent_notification_count(
        self,
        db: Session,
        user_id: int,
        hours: int = 1
    ) -> int:
        """Get count of recent notifications for rate limiting."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= cutoff_time
                )
            ).count()

            return count

        except Exception as e:
            logger.error(f"Error getting recent notification count: {e}")
            return 0

    async def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user's notification history."""
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)

            if unread_only:
                query = query.filter(Notification.is_read == False)

            notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()

            return [
                {
                    "id": notif.id,
                    "type": notif.notification_type,
                    "title": notif.title,
                    "body": notif.body,
                    "data": notif.data,
                    "priority": notif.priority,
                    "category": notif.category,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                    "read_at": notif.read_at.isoformat() if notif.read_at else None
                }
                for notif in notifications
            ]

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    async def mark_notifications_read(
        self,
        db: Session,
        user_id: int,
        notification_ids: List[int]
    ) -> bool:
        """Mark notifications as read."""
        try:
            # Update notification read status
            updated = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids),
                    Notification.is_read == False
                )
            ).update(
                {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                },
                synchronize_session=False
            )

            db.commit()
            logger.info(f"Marked {updated} notifications as read for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error marking notifications as read: {e}")
            db.rollback()
            return False


# Global notification service instance
notification_service = NotificationService()
