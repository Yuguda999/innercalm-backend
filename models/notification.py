"""
Notification models for push notifications and in-app alerts.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Notification type preferences
    circle_messages = Column(Boolean, default=True)
    message_support = Column(Boolean, default=True)
    circle_invitations = Column(Boolean, default=True)
    reflection_helpful = Column(Boolean, default=True)
    crisis_alerts = Column(Boolean, default=True)
    daily_check_in = Column(Boolean, default=True)
    weekly_summary = Column(Boolean, default=True)
    
    # Delivery preferences
    push_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    in_app_notifications = Column(Boolean, default=True)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class Notification(Base):
    """Notification records."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, default={})
    
    # Delivery status
    is_read = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    delivery_attempts = Column(Integer, default=0)
    
    # Metadata
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(50), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="notifications")


class DeviceToken(Base):
    """Device tokens for push notifications."""
    __tablename__ = "device_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Device information
    token = Column(String(255), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # ios, android, web
    device_id = Column(String(255))
    device_name = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="device_tokens")


class NotificationLog(Base):
    """Log of notification delivery attempts."""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    
    # Delivery details
    delivery_method = Column(String(20), nullable=False)  # push, email, in_app
    status = Column(String(20), nullable=False)  # sent, delivered, failed, bounced
    error_message = Column(Text)
    
    # Provider details
    provider = Column(String(50))  # fcm, apns, web_push, etc.
    provider_response = Column(JSON)
    
    # Timestamps
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    notification = relationship("Notification")
