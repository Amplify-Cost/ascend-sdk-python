"""
OW-kai Enterprise Webhook Models

Banking-Level Security: HMAC-SHA256 signed webhooks with full audit trail
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, HIPAA 164.312

Document ID: OWKAI-INT-001-MODELS
Version: 1.0.0
Date: November 28, 2025
"""

import uuid
import hashlib
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from enum import Enum

from database import Base


class WebhookEventType(str, Enum):
    """
    Supported webhook event types

    Enterprise events for real-time integration with external systems.
    """
    # Agent Action Events
    ACTION_SUBMITTED = "action.submitted"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"

    # Policy Events
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_DELETED = "policy.deleted"
    POLICY_VIOLATED = "policy.violated"

    # Alert Events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_ESCALATED = "alert.escalated"

    # Risk Events
    RISK_THRESHOLD_EXCEEDED = "risk.threshold_exceeded"
    RISK_SCORE_CHANGED = "risk.score_changed"

    # Compliance Events
    COMPLIANCE_REPORT_READY = "compliance.report_ready"
    COMPLIANCE_VIOLATION = "compliance.violation"

    # User Events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_MFA_ENABLED = "user.mfa_enabled"

    # System Events
    SYSTEM_HEALTH_ALERT = "system.health_alert"


class DeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERING = "delivering"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(Base):
    """
    Enterprise Webhook Subscription

    Allows organizations to subscribe to real-time events via HTTP callbacks.

    Security Features:
    - HMAC-SHA256 signature on every delivery
    - TLS 1.3 required for target URLs
    - Rate limiting per organization
    - Full audit trail of deliveries

    Multi-Tenant: Isolated by organization_id
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant isolation (CRITICAL)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Subscription identity
    subscription_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Target configuration
    target_url = Column(String(2048), nullable=False)

    # Security: HMAC signing secret (stored hashed, actual secret returned only on creation)
    secret_key_hash = Column(String(128), nullable=False)  # SHA-512 hash of secret
    secret_key_salt = Column(String(32), nullable=False)   # Salt for hashing

    # Event subscription (array of event types)
    event_types = Column(JSONB, nullable=False, default=list)

    # Optional filters (e.g., only high-risk actions)
    event_filters = Column(JSONB, nullable=True)

    # Custom headers to include in webhook requests
    custom_headers = Column(JSONB, nullable=True)  # Encrypted at rest

    # Retry configuration
    retry_config = Column(JSONB, nullable=False, default=lambda: {
        "max_retries": 5,
        "initial_delay_seconds": 1,
        "max_delay_seconds": 300,
        "backoff_multiplier": 2
    })

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # URL ownership verified

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=100, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    deliveries = relationship("WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_webhook_sub_org_active', 'organization_id', 'is_active'),
        Index('idx_webhook_sub_events', 'event_types', postgresql_using='gin'),
        UniqueConstraint('organization_id', 'name', name='uq_webhook_org_name'),
    )

    def __repr__(self):
        return f"<WebhookSubscription(id={self.id}, name='{self.name}', org={self.organization_id})>"


class WebhookDelivery(Base):
    """
    Webhook Delivery Log (Immutable Audit Trail)

    Records every webhook delivery attempt for compliance and debugging.

    Compliance: SOC 2 CC8.1 - Change Management
    Security: Immutable log with payload hash for integrity verification
    """
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to subscription
    subscription_id = Column(
        Integer,
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event identification
    event_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)

    # Idempotency key for deduplication
    idempotency_key = Column(String(64), nullable=False, index=True)

    # Payload (stored for debugging, PII should be masked)
    payload = Column(JSONB, nullable=False)
    payload_hash = Column(String(64), nullable=False)  # SHA-256 for integrity

    # Delivery details
    target_url = Column(String(2048), nullable=False)
    request_headers = Column(JSONB, nullable=True)

    # Response
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSONB, nullable=True)
    response_body = Column(Text, nullable=True)  # Truncated to 10KB
    response_time_ms = Column(Integer, nullable=True)

    # Delivery status
    delivery_status = Column(
        String(20),
        default=DeliveryStatus.PENDING.value,
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)

    # Retry tracking
    attempt_count = Column(Integer, default=1, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)

    # HMAC signature sent (for debugging, not the secret)
    signature_sent = Column(String(128), nullable=True)

    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")

    # Indexes for performance and querying
    __table_args__ = (
        Index('idx_delivery_org_status', 'organization_id', 'delivery_status'),
        Index('idx_delivery_retry', 'delivery_status', 'next_retry_at'),
        Index('idx_delivery_created', 'organization_id', 'created_at'),
        Index('idx_delivery_event_type', 'organization_id', 'event_type'),
    )

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, event={self.event_type}, status={self.delivery_status})>"

    @staticmethod
    def compute_payload_hash(payload: dict) -> str:
        """
        Compute SHA-256 hash of payload for integrity verification.

        Used for:
        - Audit trail integrity
        - Deduplication
        - Compliance evidence
        """
        import json
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()


class WebhookDeliveryQueue(Base):
    """
    Dead Letter Queue for Failed Webhooks

    Stores permanently failed webhook deliveries for manual review.

    Banking Requirement: No data loss, manual intervention for critical failures
    """
    __tablename__ = "webhook_delivery_queue"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Original delivery reference
    delivery_id = Column(
        Integer,
        ForeignKey("webhook_deliveries.id", ondelete="SET NULL"),
        nullable=True
    )
    subscription_id = Column(
        Integer,
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Event data (preserved for manual retry)
    event_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)

    # Failure information
    failure_reason = Column(Text, nullable=False)
    last_attempt_at = Column(DateTime, nullable=False)
    total_attempts = Column(Integer, nullable=False)

    # Resolution tracking
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_dlq_org_resolved', 'organization_id', 'resolved'),
    )


# Pydantic schemas for API
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime as dt


class WebhookEventTypeSchema(BaseModel):
    """Schema for listing available event types"""
    type: str
    description: str
    payload_schema: str
    category: str


class WebhookSubscriptionCreate(BaseModel):
    """Schema for creating a webhook subscription"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_url: HttpUrl
    event_types: List[str] = Field(..., min_items=1)
    event_filters: Optional[Dict[str, Any]] = None
    custom_headers: Optional[Dict[str, str]] = None
    retry_config: Optional[Dict[str, Any]] = None
    rate_limit_per_minute: Optional[int] = Field(default=100, ge=1, le=1000)

    @validator('event_types')
    def validate_event_types(cls, v):
        valid_types = [e.value for e in WebhookEventType]
        for event_type in v:
            if event_type not in valid_types:
                raise ValueError(f"Invalid event type: {event_type}. Valid types: {valid_types}")
        return v

    @validator('target_url')
    def validate_https(cls, v):
        if not str(v).startswith('https://'):
            raise ValueError("Webhook URL must use HTTPS for security")
        return v


class WebhookSubscriptionUpdate(BaseModel):
    """Schema for updating a webhook subscription"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_url: Optional[HttpUrl] = None
    event_types: Optional[List[str]] = None
    event_filters: Optional[Dict[str, Any]] = None
    custom_headers: Optional[Dict[str, str]] = None
    retry_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)

    @validator('target_url')
    def validate_https(cls, v):
        if v and not str(v).startswith('https://'):
            raise ValueError("Webhook URL must use HTTPS for security")
        return v


class WebhookSubscriptionResponse(BaseModel):
    """Schema for webhook subscription response"""
    id: int
    subscription_id: str
    name: str
    description: Optional[str]
    target_url: str
    event_types: List[str]
    event_filters: Optional[Dict[str, Any]]
    is_active: bool
    is_verified: bool
    rate_limit_per_minute: int
    created_at: dt
    updated_at: dt

    class Config:
        from_attributes = True


class WebhookSubscriptionWithSecret(WebhookSubscriptionResponse):
    """
    Response including the secret key (only returned on creation)

    SECURITY: Secret is only shown ONCE at creation time.
    Customer must store it securely.
    """
    secret_key: str  # Only returned on creation


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery log entry"""
    id: int
    event_id: str
    event_type: str
    delivery_status: str
    attempt_count: int
    response_status: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: dt
    delivered_at: Optional[dt]

    class Config:
        from_attributes = True


class WebhookTestRequest(BaseModel):
    """Schema for testing a webhook"""
    event_type: str = Field(default="action.submitted")
    custom_payload: Optional[Dict[str, Any]] = None


class WebhookTestResponse(BaseModel):
    """Schema for webhook test result"""
    success: bool
    delivery_id: int
    response_status: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    signature_header: str


class WebhookEventListResponse(BaseModel):
    """Schema for listing available events"""
    events: List[WebhookEventTypeSchema]
    total: int


# Event type metadata
WEBHOOK_EVENT_METADATA = {
    WebhookEventType.ACTION_SUBMITTED: {
        "description": "New agent action submitted for authorization",
        "category": "Agent Actions",
        "payload_schema": "ActionSubmittedPayload"
    },
    WebhookEventType.ACTION_APPROVED: {
        "description": "Agent action was approved",
        "category": "Agent Actions",
        "payload_schema": "ActionApprovedPayload"
    },
    WebhookEventType.ACTION_REJECTED: {
        "description": "Agent action was rejected",
        "category": "Agent Actions",
        "payload_schema": "ActionRejectedPayload"
    },
    WebhookEventType.ACTION_EXECUTED: {
        "description": "Agent action execution completed",
        "category": "Agent Actions",
        "payload_schema": "ActionExecutedPayload"
    },
    WebhookEventType.ACTION_FAILED: {
        "description": "Agent action execution failed",
        "category": "Agent Actions",
        "payload_schema": "ActionFailedPayload"
    },
    WebhookEventType.POLICY_CREATED: {
        "description": "New governance policy created",
        "category": "Policies",
        "payload_schema": "PolicyCreatedPayload"
    },
    WebhookEventType.POLICY_UPDATED: {
        "description": "Governance policy was updated",
        "category": "Policies",
        "payload_schema": "PolicyUpdatedPayload"
    },
    WebhookEventType.POLICY_DELETED: {
        "description": "Governance policy was deleted",
        "category": "Policies",
        "payload_schema": "PolicyDeletedPayload"
    },
    WebhookEventType.POLICY_VIOLATED: {
        "description": "Policy violation detected",
        "category": "Policies",
        "payload_schema": "PolicyViolatedPayload"
    },
    WebhookEventType.ALERT_TRIGGERED: {
        "description": "Security alert triggered",
        "category": "Alerts",
        "payload_schema": "AlertTriggeredPayload"
    },
    WebhookEventType.ALERT_RESOLVED: {
        "description": "Security alert resolved",
        "category": "Alerts",
        "payload_schema": "AlertResolvedPayload"
    },
    WebhookEventType.ALERT_ESCALATED: {
        "description": "Security alert escalated",
        "category": "Alerts",
        "payload_schema": "AlertEscalatedPayload"
    },
    WebhookEventType.RISK_THRESHOLD_EXCEEDED: {
        "description": "Risk score exceeded configured threshold",
        "category": "Risk",
        "payload_schema": "RiskThresholdPayload"
    },
    WebhookEventType.RISK_SCORE_CHANGED: {
        "description": "Risk score changed significantly",
        "category": "Risk",
        "payload_schema": "RiskScoreChangedPayload"
    },
    WebhookEventType.COMPLIANCE_REPORT_READY: {
        "description": "Compliance report generation completed",
        "category": "Compliance",
        "payload_schema": "ComplianceReportPayload"
    },
    WebhookEventType.COMPLIANCE_VIOLATION: {
        "description": "Compliance violation detected",
        "category": "Compliance",
        "payload_schema": "ComplianceViolationPayload"
    },
    WebhookEventType.USER_LOGIN: {
        "description": "User logged in",
        "category": "Users",
        "payload_schema": "UserLoginPayload"
    },
    WebhookEventType.USER_LOGOUT: {
        "description": "User logged out",
        "category": "Users",
        "payload_schema": "UserLogoutPayload"
    },
    WebhookEventType.USER_MFA_ENABLED: {
        "description": "User enabled MFA",
        "category": "Users",
        "payload_schema": "UserMFAPayload"
    },
    WebhookEventType.SYSTEM_HEALTH_ALERT: {
        "description": "System health alert triggered",
        "category": "System",
        "payload_schema": "SystemHealthPayload"
    },
}
