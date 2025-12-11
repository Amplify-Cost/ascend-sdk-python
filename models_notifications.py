"""
OW-kai Enterprise Notification System Models

Phase 2: Slack/Teams Integration
Banking-Level Security: Encrypted webhook URLs, audit trails, rate limiting

This module defines the database models and Pydantic schemas for the
enterprise notification system supporting Slack and Microsoft Teams.

Document ID: OWKAI-INT-002-MODELS
Version: 1.0.0
Date: November 28, 2025
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator, HttpUrl
import uuid

from database import Base


# ============================================
# Enums
# ============================================

class NotificationChannelType(str, Enum):
    """Supported notification channel types."""
    SLACK = "slack"
    TEAMS = "teams"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationEventType(str, Enum):
    """Events that can trigger notifications.

    Aligned with webhook event types for consistency.
    """
    # Action events
    ACTION_SUBMITTED = "action.submitted"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_ESCALATED = "action.escalated"
    ACTION_PENDING_APPROVAL = "action.pending_approval"

    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_CRITICAL = "alert.critical"

    # Policy events
    POLICY_VIOLATED = "policy.violated"
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_TIMEOUT = "workflow.timeout"
    WORKFLOW_APPROVAL_NEEDED = "workflow.approval_needed"

    # Security events
    SECURITY_MFA_ENABLED = "security.mfa_enabled"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_LOGIN_ANOMALY = "security.login_anomaly"

    # System events
    SYSTEM_HEALTH_WARNING = "system.health_warning"
    SYSTEM_MAINTENANCE = "system.maintenance"

    # Risk events
    RISK_THRESHOLD_EXCEEDED = "risk.threshold_exceeded"
    RISK_CRITICAL_ACTION = "risk.critical_action"

    # Agent control events (SEC-106)
    AGENT_BLOCKED = "agent.blocked"
    AGENT_UNBLOCKED = "agent.unblocked"
    AGENT_SUSPENDED = "agent.suspended"
    AGENT_QUARANTINED = "agent.quarantined"


# ============================================
# SQLAlchemy Models
# ============================================

class NotificationChannel(Base):
    """
    Notification channel configuration (Slack/Teams).

    Stores encrypted webhook URLs and channel-specific settings.
    Multi-tenant isolation via organization_id.
    """
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)

    # Channel details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel_type = Column(String(50), nullable=False)  # slack, teams

    # Webhook configuration (encrypted at rest in production)
    webhook_url_encrypted = Column(Text, nullable=False)  # AES-256 encrypted
    webhook_url_hash = Column(String(64), nullable=False)  # SHA-256 for lookup

    # Channel-specific settings
    slack_channel_name = Column(String(255), nullable=True)  # For Slack: #channel-name
    slack_username = Column(String(255), nullable=True)  # Bot username
    slack_icon_emoji = Column(String(100), nullable=True)  # :robot_face:
    teams_title = Column(String(255), nullable=True)  # Card title for Teams

    # Event subscriptions (JSON array of event types)
    subscribed_events = Column(JSONB, nullable=False, default=list)

    # Filtering
    min_risk_score = Column(Integer, nullable=True)  # Only notify above this score
    risk_levels = Column(JSONB, nullable=True)  # ["critical", "high"]

    # Rate limiting
    rate_limit_per_minute = Column(Integer, nullable=True, default=30)
    rate_limit_current_count = Column(Integer, nullable=False, default=0)
    rate_limit_window_start = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Metrics
    total_notifications = Column(Integer, nullable=False, default=0)
    successful_notifications = Column(Integer, nullable=False, default=0)
    failed_notifications = Column(Integer, nullable=False, default=0)
    last_notification_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)

    # Pause/circuit breaker
    is_paused = Column(Boolean, nullable=False, default=False)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    paused_reason = Column(Text, nullable=True)

    # Audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    deliveries = relationship("NotificationDelivery", back_populates="channel", cascade="all, delete-orphan")


class NotificationDelivery(Base):
    """
    Notification delivery audit trail.

    Records every notification attempt for compliance and debugging.
    """
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification identification
    notification_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False, index=True)

    # Message content
    message_title = Column(String(500), nullable=False)
    message_body = Column(Text, nullable=False)
    message_payload = Column(JSONB, nullable=False)  # Full payload sent

    # Related entity
    related_entity_type = Column(String(50), nullable=True)  # action, alert, policy
    related_entity_id = Column(Integer, nullable=True)

    # Delivery details
    priority = Column(String(20), nullable=False, default="normal")
    attempt_number = Column(Integer, nullable=False, default=1)
    delivery_status = Column(String(50), nullable=False, default="pending", index=True)

    # Response tracking
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    channel = relationship("NotificationChannel", back_populates="deliveries")


class NotificationTemplate(Base):
    """
    Message templates for different event types.

    Allows customization of notification messages per organization.
    """
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = system default

    # Template identification
    template_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False)  # slack, teams, or 'all'

    # Template details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Slack-specific template
    slack_template = Column(JSONB, nullable=True)  # Slack Block Kit JSON

    # Teams-specific template
    teams_template = Column(JSONB, nullable=True)  # Adaptive Card JSON

    # Fallback plain text
    plain_text_template = Column(Text, nullable=False)

    # Variables available (documentation)
    available_variables = Column(JSONB, nullable=True)  # ["action_id", "risk_score", etc.]

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


# ============================================
# Pydantic Schemas - Requests
# ============================================

class NotificationChannelCreate(BaseModel):
    """Schema for creating a notification channel."""
    name: str = Field(..., min_length=1, max_length=255, description="Channel name")
    description: Optional[str] = Field(None, max_length=1000)
    channel_type: NotificationChannelType = Field(..., description="slack or teams")
    webhook_url: str = Field(..., description="Slack/Teams incoming webhook URL")

    # Optional channel settings
    slack_channel_name: Optional[str] = Field(None, max_length=255)
    slack_username: Optional[str] = Field(default="OW-kai Bot", max_length=255)
    slack_icon_emoji: Optional[str] = Field(default=":robot_face:", max_length=100)
    teams_title: Optional[str] = Field(default="OW-kai Alert", max_length=255)

    # Event subscriptions
    subscribed_events: List[NotificationEventType] = Field(
        default_factory=list,
        description="List of events to subscribe to"
    )

    # Filtering
    min_risk_score: Optional[int] = Field(None, ge=0, le=100)
    risk_levels: Optional[List[str]] = Field(None, description="e.g., ['critical', 'high']")

    # Rate limiting
    rate_limit_per_minute: Optional[int] = Field(30, ge=1, le=100)

    @validator('webhook_url')
    def validate_webhook_url(cls, v, values):
        """Validate webhook URL format based on channel type."""
        channel_type = values.get('channel_type')
        if channel_type == NotificationChannelType.SLACK:
            if not v.startswith('https://hooks.slack.com/'):
                raise ValueError('Slack webhook URL must start with https://hooks.slack.com/')
        elif channel_type == NotificationChannelType.TEAMS:
            if not v.startswith('https://') or 'webhook.office.com' not in v:
                raise ValueError('Teams webhook URL must be a valid Office 365 webhook URL')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Security Alerts Channel",
                "description": "Critical security notifications",
                "channel_type": "slack",
                "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
                "slack_channel_name": "#security-alerts",
                "subscribed_events": ["action.rejected", "alert.critical", "security.suspicious_activity"],
                "min_risk_score": 70,
                "risk_levels": ["critical", "high"]
            }
        }


class NotificationChannelUpdate(BaseModel):
    """Schema for updating a notification channel."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    webhook_url: Optional[str] = None  # Will be re-encrypted if changed

    slack_channel_name: Optional[str] = None
    slack_username: Optional[str] = None
    slack_icon_emoji: Optional[str] = None
    teams_title: Optional[str] = None

    subscribed_events: Optional[List[NotificationEventType]] = None
    min_risk_score: Optional[int] = Field(None, ge=0, le=100)
    risk_levels: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=100)

    is_active: Optional[bool] = None


class NotificationTestRequest(BaseModel):
    """Schema for sending a test notification."""
    message: Optional[str] = Field("This is a test notification from OW-kai", max_length=500)


class NotificationSendRequest(BaseModel):
    """Schema for manually sending a notification."""
    event_type: NotificationEventType
    title: str = Field(..., max_length=500)
    message: str = Field(..., max_length=4000)
    priority: NotificationPriority = Field(NotificationPriority.NORMAL)
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# Pydantic Schemas - Responses
# ============================================

class NotificationChannelResponse(BaseModel):
    """Response schema for notification channel."""
    id: int
    channel_id: str
    name: str
    description: Optional[str]
    channel_type: str

    # Settings (webhook URL NOT included for security)
    slack_channel_name: Optional[str]
    slack_username: Optional[str]
    slack_icon_emoji: Optional[str]
    teams_title: Optional[str]

    subscribed_events: List[str]
    min_risk_score: Optional[int]
    risk_levels: Optional[List[str]]
    rate_limit_per_minute: Optional[int]

    is_active: bool
    is_verified: bool
    verified_at: Optional[datetime]

    # Metrics
    total_notifications: int
    successful_notifications: int
    failed_notifications: int
    last_notification_at: Optional[datetime]
    consecutive_failures: int

    is_paused: bool
    paused_reason: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationDeliveryResponse(BaseModel):
    """Response schema for notification delivery."""
    id: int
    notification_id: str
    event_type: str
    message_title: str
    priority: str
    delivery_status: str

    attempt_number: int
    http_status_code: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]

    related_entity_type: Optional[str]
    related_entity_id: Optional[int]

    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationChannelListResponse(BaseModel):
    """Response schema for listing channels."""
    channels: List[NotificationChannelResponse]
    total: int
    page: int
    page_size: int


class NotificationDeliveryListResponse(BaseModel):
    """Response schema for listing deliveries."""
    deliveries: List[NotificationDeliveryResponse]
    total: int
    page: int
    page_size: int


class NotificationMetricsResponse(BaseModel):
    """Aggregated notification metrics."""
    total_channels: int
    active_channels: int
    paused_channels: int

    total_notifications_24h: int
    successful_24h: int
    failed_24h: int
    success_rate_24h: float

    avg_response_time_ms: float

    by_channel_type: Dict[str, Dict[str, int]]  # {"slack": {"total": 100, "success": 95}, ...}
    by_event_type: Dict[str, int]  # {"action.rejected": 50, ...}


class NotificationTestResponse(BaseModel):
    """Response from test notification."""
    success: bool
    message: str
    http_status_code: Optional[int]
    response_time_ms: Optional[int]
    error: Optional[str]


# ============================================
# Event Type Configurations
# ============================================

EVENT_TYPE_CONFIG = {
    # Action events - High priority
    NotificationEventType.ACTION_REJECTED: {
        "priority": NotificationPriority.HIGH,
        "color": "#dc3545",  # Red
        "icon": ":x:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.ACTION_ESCALATED: {
        "priority": NotificationPriority.URGENT,
        "color": "#fd7e14",  # Orange
        "icon": ":warning:",
        "teams_theme_color": "FFA500"
    },
    NotificationEventType.ACTION_PENDING_APPROVAL: {
        "priority": NotificationPriority.HIGH,
        "color": "#ffc107",  # Yellow
        "icon": ":hourglass:",
        "teams_theme_color": "FFFF00"
    },
    NotificationEventType.ACTION_APPROVED: {
        "priority": NotificationPriority.NORMAL,
        "color": "#28a745",  # Green
        "icon": ":white_check_mark:",
        "teams_theme_color": "00FF00"
    },
    NotificationEventType.ACTION_SUBMITTED: {
        "priority": NotificationPriority.LOW,
        "color": "#17a2b8",  # Cyan
        "icon": ":inbox_tray:",
        "teams_theme_color": "00FFFF"
    },

    # Alert events
    NotificationEventType.ALERT_CRITICAL: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",
        "icon": ":rotating_light:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.ALERT_TRIGGERED: {
        "priority": NotificationPriority.HIGH,
        "color": "#fd7e14",
        "icon": ":bell:",
        "teams_theme_color": "FFA500"
    },
    NotificationEventType.ALERT_RESOLVED: {
        "priority": NotificationPriority.NORMAL,
        "color": "#28a745",
        "icon": ":white_check_mark:",
        "teams_theme_color": "00FF00"
    },

    # Security events - Always urgent
    NotificationEventType.SECURITY_SUSPICIOUS_ACTIVITY: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",
        "icon": ":shield:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.SECURITY_LOGIN_ANOMALY: {
        "priority": NotificationPriority.HIGH,
        "color": "#fd7e14",
        "icon": ":lock:",
        "teams_theme_color": "FFA500"
    },

    # Policy events
    NotificationEventType.POLICY_VIOLATED: {
        "priority": NotificationPriority.HIGH,
        "color": "#dc3545",
        "icon": ":no_entry:",
        "teams_theme_color": "FF0000"
    },

    # Risk events
    NotificationEventType.RISK_CRITICAL_ACTION: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",
        "icon": ":warning:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.RISK_THRESHOLD_EXCEEDED: {
        "priority": NotificationPriority.HIGH,
        "color": "#fd7e14",
        "icon": ":chart_with_upwards_trend:",
        "teams_theme_color": "FFA500"
    },

    # Workflow events
    NotificationEventType.WORKFLOW_FAILED: {
        "priority": NotificationPriority.HIGH,
        "color": "#dc3545",
        "icon": ":x:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.WORKFLOW_TIMEOUT: {
        "priority": NotificationPriority.HIGH,
        "color": "#fd7e14",
        "icon": ":alarm_clock:",
        "teams_theme_color": "FFA500"
    },
    NotificationEventType.WORKFLOW_APPROVAL_NEEDED: {
        "priority": NotificationPriority.HIGH,
        "color": "#ffc107",
        "icon": ":hand:",
        "teams_theme_color": "FFFF00"
    },

    # Agent control events (SEC-106) - Always URGENT
    NotificationEventType.AGENT_BLOCKED: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",  # Red
        "icon": ":octagonal_sign:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.AGENT_UNBLOCKED: {
        "priority": NotificationPriority.HIGH,
        "color": "#28a745",  # Green
        "icon": ":white_check_mark:",
        "teams_theme_color": "00FF00"
    },
    NotificationEventType.AGENT_SUSPENDED: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",  # Red
        "icon": ":pause_button:",
        "teams_theme_color": "FF0000"
    },
    NotificationEventType.AGENT_QUARANTINED: {
        "priority": NotificationPriority.URGENT,
        "color": "#dc3545",  # Red
        "icon": ":biohazard:",
        "teams_theme_color": "FF0000"
    },
}

# Default config for unlisted events
DEFAULT_EVENT_CONFIG = {
    "priority": NotificationPriority.NORMAL,
    "color": "#6c757d",  # Gray
    "icon": ":information_source:",
    "teams_theme_color": "808080"
}


def get_event_config(event_type: NotificationEventType) -> dict:
    """Get configuration for an event type."""
    return EVENT_TYPE_CONFIG.get(event_type, DEFAULT_EVENT_CONFIG)
