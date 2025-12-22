"""
Phase 10B: Stripe Billing Database Models

Enterprise-grade billing models for usage-based pricing with Stripe integration.

Features:
- High-throughput usage event tracking (partitioned by month)
- Financial kill-switch with spend limits
- Billing records with Stripe invoice linking
- Webhook event deduplication

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10B
Date: 2025-12-21
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


# =============================================================================
# ENUMS
# =============================================================================

class UsageEventType(str, enum.Enum):
    """Types of billable usage events"""
    ACTION_EVALUATION = "action_evaluation"
    MCP_SERVER_HOUR = "mcp_server_hour"
    USER_SEAT = "user_seat"
    API_CALL = "api_call"
    STORAGE_GB = "storage_gb"
    WORKFLOW_EXECUTION = "workflow_execution"


class BillingRecordStatus(str, enum.Enum):
    """Status of billing records"""
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class SpendLimitStatus(str, enum.Enum):
    """Status of spend limit enforcement"""
    ACTIVE = "active"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    DISABLED = "disabled"


class WebhookEventStatus(str, enum.Enum):
    """Processing status for Stripe webhook events"""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# =============================================================================
# USAGE EVENTS
# =============================================================================

class UsageEvent(Base):
    """
    Individual usage events aggregated from Redis metering queue.

    Design:
    - Append-only for audit compliance
    - Indexed for fast aggregation by org/period
    - Stripe reporting status tracked
    - Partitioned by billing_period for performance

    Hot path impact: NONE (written by background worker)
    """
    __tablename__ = "usage_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_cost = Column(Float, nullable=True)  # Cost per unit at time of event
    total_cost = Column(Float, nullable=True)  # quantity * unit_cost

    # Timing
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    billing_period = Column(String(7), nullable=False, index=True)  # YYYY-MM

    # Stripe sync tracking
    stripe_reported = Column(Boolean, nullable=False, default=False, index=True)
    stripe_usage_record_id = Column(String(255), nullable=True)
    stripe_reported_at = Column(DateTime(timezone=True), nullable=True)

    # Event Metadata (renamed from 'metadata' - SQLAlchemy reserved attribute)
    event_metadata = Column(JSONB, nullable=True)  # Additional context
    source = Column(String(50), nullable=True)  # redis_batch, manual, migration

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index(
            'ix_usage_events_org_period_reported',
            'organization_id', 'billing_period', 'stripe_reported'
        ),
        Index(
            'ix_usage_events_org_type_period',
            'organization_id', 'event_type', 'billing_period'
        ),
    )

    def __repr__(self):
        return f"<UsageEvent(id={self.id}, org={self.organization_id}, type={self.event_type}, qty={self.quantity})>"


# =============================================================================
# USAGE AGGREGATES
# =============================================================================

class UsageAggregate(Base):
    """
    Pre-computed usage aggregates for fast dashboard queries.

    Updated by background worker every 5 minutes.
    Reduces query complexity for billing dashboard.
    """
    __tablename__ = "usage_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    # Aggregation period
    billing_period = Column(String(7), nullable=False)  # YYYY-MM
    event_type = Column(String(50), nullable=False)

    # Aggregated values
    total_quantity = Column(BigInteger, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    event_count = Column(Integer, nullable=False, default=0)

    # Included vs overage
    included_quantity = Column(BigInteger, nullable=False, default=0)
    overage_quantity = Column(BigInteger, nullable=False, default=0)
    overage_cost = Column(Float, nullable=False, default=0.0)

    # Timestamps
    first_event_at = Column(DateTime(timezone=True), nullable=True)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    last_aggregated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            'organization_id', 'billing_period', 'event_type',
            name='uq_usage_aggregate_org_period_type'
        ),
        Index('ix_usage_aggregates_org_period', 'organization_id', 'billing_period'),
    )

    def __repr__(self):
        return f"<UsageAggregate(org={self.organization_id}, period={self.billing_period}, type={self.event_type})>"


# =============================================================================
# SPEND LIMITS
# =============================================================================

class SpendLimit(Base):
    """
    Financial kill-switch configuration per organization.

    Features:
    - Monthly spend cap enforcement
    - Warning threshold at configurable percentage
    - Automatic kill-switch when limit exceeded
    - Manual override capability with audit trail

    Hot path impact: Redis cached, <0.5ms check
    """
    __tablename__ = "spend_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Limit configuration
    monthly_limit = Column(Float, nullable=False)  # Hard cap in USD
    warning_threshold_percent = Column(Float, nullable=False, default=80.0)
    hard_limit_action = Column(String(50), nullable=False, default="block")  # block, notify, none

    # Current status
    current_spend = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="active")
    limit_enforced = Column(Boolean, nullable=False, default=True)

    # Warning tracking
    warning_sent = Column(Boolean, nullable=False, default=False)
    warning_sent_at = Column(DateTime(timezone=True), nullable=True)
    warning_acknowledged = Column(Boolean, nullable=False, default=False)
    warning_acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Kill-switch state
    kill_switch_triggered = Column(Boolean, nullable=False, default=False)
    kill_switch_triggered_at = Column(DateTime(timezone=True), nullable=True)
    kill_switch_triggered_by = Column(String(100), nullable=True)  # system or user_id
    kill_switch_reason = Column(Text, nullable=True)

    # Manual override
    kill_switch_released = Column(Boolean, nullable=False, default=False)
    kill_switch_released_at = Column(DateTime(timezone=True), nullable=True)
    kill_switch_released_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    release_reason = Column(Text, nullable=True)

    # Billing period tracking
    current_billing_period = Column(String(7), nullable=True)  # YYYY-MM
    last_reset_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self):
        return f"<SpendLimit(org={self.organization_id}, limit=${self.monthly_limit}, current=${self.current_spend})>"

    @property
    def utilization_percent(self) -> float:
        """Calculate current spend as percentage of limit"""
        if self.monthly_limit <= 0:
            return 0.0
        return (self.current_spend / self.monthly_limit) * 100

    @property
    def is_warning_threshold_exceeded(self) -> bool:
        """Check if warning threshold exceeded"""
        return self.utilization_percent >= self.warning_threshold_percent

    @property
    def is_limit_exceeded(self) -> bool:
        """Check if hard limit exceeded"""
        return self.current_spend >= self.monthly_limit


# =============================================================================
# SPEND LIMIT EVENTS (Audit Trail)
# =============================================================================

class SpendLimitEvent(Base):
    """
    Immutable audit trail for spend limit changes.

    Tracks all limit changes, warnings, and kill-switch events.
    Required for SOC 2 compliance.
    """
    __tablename__ = "spend_limit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event type
    event_type = Column(String(50), nullable=False, index=True)
    # Types: limit_set, limit_updated, warning_triggered, warning_acknowledged,
    #        kill_switch_triggered, kill_switch_released, limit_reset

    # Event details
    previous_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)

    # Actor
    triggered_by = Column(String(100), nullable=False)  # system or user_id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamp (immutable)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index('ix_spend_limit_events_org_created', 'organization_id', 'created_at'),
    )

    def __repr__(self):
        return f"<SpendLimitEvent(org={self.organization_id}, type={self.event_type})>"


# =============================================================================
# BILLING RECORDS
# =============================================================================

class BillingRecord(Base):
    """
    Monthly billing summary per organization.

    Linked to Stripe invoices for payment tracking.
    Provides historical billing data for dashboard.
    """
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Billing period
    billing_period = Column(String(7), nullable=False)  # YYYY-MM
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Amounts
    base_amount = Column(Float, nullable=False, default=0.0)  # Subscription base
    usage_amount = Column(Float, nullable=False, default=0.0)  # Usage charges
    overage_amount = Column(Float, nullable=False, default=0.0)  # Overage charges
    discount_amount = Column(Float, nullable=False, default=0.0)  # Discounts applied
    tax_amount = Column(Float, nullable=False, default=0.0)  # Tax
    total_amount = Column(Float, nullable=False, default=0.0)  # Final total

    # Usage breakdown (JSONB for flexibility)
    usage_breakdown = Column(JSONB, nullable=True)
    # Example: {"action_evaluation": {"quantity": 150000, "included": 100000, "overage": 50000, "cost": 250.00}}

    # Stripe integration
    stripe_invoice_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_invoice_url = Column(Text, nullable=True)
    stripe_invoice_pdf = Column(Text, nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")
    paid_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Dunning
    retry_count = Column(Integer, nullable=False, default=0)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            'organization_id', 'billing_period',
            name='uq_billing_record_org_period'
        ),
        Index('ix_billing_records_org_period', 'organization_id', 'billing_period'),
        Index('ix_billing_records_status', 'status'),
    )

    def __repr__(self):
        return f"<BillingRecord(org={self.organization_id}, period={self.billing_period}, total=${self.total_amount})>"


# =============================================================================
# STRIPE WEBHOOK EVENTS
# =============================================================================

class StripeWebhookEvent(Base):
    """
    Stripe webhook event tracking for idempotency.

    Prevents duplicate processing of webhook events.
    Required for reliable Stripe integration.
    """
    __tablename__ = "stripe_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Stripe event identifiers
    stripe_event_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_event_type = Column(String(100), nullable=False, index=True)
    stripe_api_version = Column(String(50), nullable=True)

    # Event data
    event_data = Column(JSONB, nullable=False)
    livemode = Column(Boolean, nullable=False, default=False)

    # Processing status
    status = Column(String(50), nullable=False, default="received")
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Linked resources (after processing)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    billing_record_id = Column(
        Integer,
        ForeignKey("billing_records.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index('ix_stripe_webhook_events_type_status', 'stripe_event_type', 'status'),
        Index('ix_stripe_webhook_events_received', 'received_at'),
    )

    def __repr__(self):
        return f"<StripeWebhookEvent(id={self.stripe_event_id}, type={self.stripe_event_type}, status={self.status})>"


# =============================================================================
# STRIPE SYNC LOG
# =============================================================================

class StripeSyncLog(Base):
    """
    Audit log for all Stripe API interactions.

    Tracks:
    - Customer creation/updates
    - Subscription changes
    - Usage record reporting
    - Invoice operations

    Required for debugging and compliance.
    """
    __tablename__ = "stripe_sync_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Operation details
    operation = Column(String(100), nullable=False, index=True)
    # Operations: create_customer, update_customer, create_subscription,
    #             update_subscription, report_usage, create_invoice, etc.

    stripe_object_type = Column(String(50), nullable=True)  # customer, subscription, invoice
    stripe_object_id = Column(String(255), nullable=True, index=True)

    # Request/Response
    request_data = Column(JSONB, nullable=True)
    response_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Status
    success = Column(Boolean, nullable=False)
    http_status = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Idempotency
    idempotency_key = Column(String(255), nullable=True, index=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    __table_args__ = (
        Index('ix_stripe_sync_log_org_created', 'organization_id', 'created_at'),
        Index('ix_stripe_sync_log_operation', 'operation', 'success'),
    )

    def __repr__(self):
        return f"<StripeSyncLog(op={self.operation}, success={self.success})>"


# =============================================================================
# SUBSCRIPTION TIERS (Reference)
# =============================================================================

class SubscriptionTier(Base):
    """
    Subscription tier configuration.

    Defines included quantities and overage rates per tier.
    Referenced by Organization.subscription_tier.
    """
    __tablename__ = "subscription_tiers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Stripe product/price
    stripe_product_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    monthly_base_price = Column(Float, nullable=False)

    # Included quantities
    included_api_calls = Column(Integer, nullable=False, default=0)
    included_users = Column(Integer, nullable=False, default=0)
    included_mcp_servers = Column(Integer, nullable=False, default=0)
    included_storage_gb = Column(Integer, nullable=False, default=0)

    # Overage rates (per unit above included)
    overage_rate_api_call = Column(Float, nullable=False, default=0.0)
    overage_rate_user = Column(Float, nullable=False, default=0.0)
    overage_rate_mcp_server = Column(Float, nullable=False, default=0.0)
    overage_rate_storage_gb = Column(Float, nullable=False, default=0.0)

    # Features
    features = Column(JSONB, nullable=True)

    # Ordering
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self):
        return f"<SubscriptionTier(name={self.name}, price=${self.monthly_base_price})>"


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

from pydantic import BaseModel, Field
from typing import List


class UsageEventCreate(BaseModel):
    """Schema for creating usage events"""
    event_type: str
    quantity: int = 1
    event_metadata: Optional[Dict[str, Any]] = None


class SpendLimitCreate(BaseModel):
    """Schema for creating spend limits"""
    monthly_limit: float = Field(..., gt=0)
    warning_threshold_percent: float = Field(default=80.0, ge=0, le=100)
    hard_limit_action: str = Field(default="block")
    limit_enforced: bool = True


class SpendLimitUpdate(BaseModel):
    """Schema for updating spend limits"""
    monthly_limit: Optional[float] = Field(None, gt=0)
    warning_threshold_percent: Optional[float] = Field(None, ge=0, le=100)
    hard_limit_action: Optional[str] = None
    limit_enforced: Optional[bool] = None


class SpendCheckResult(BaseModel):
    """Result of spend limit check"""
    allowed: bool
    blocked: bool = False
    current_spend: float
    monthly_limit: float
    utilization_percent: float
    status: str
    warning_triggered: bool = False
    kill_switch_active: bool = False
    message: Optional[str] = None


class UsageSummary(BaseModel):
    """Usage summary for dashboard"""
    billing_period: str
    total_api_calls: int
    included_api_calls: int
    overage_api_calls: int
    total_cost: float
    breakdown: Dict[str, Any]


class BillingRecordResponse(BaseModel):
    """Billing record response"""
    id: int
    billing_period: str
    base_amount: float
    usage_amount: float
    total_amount: float
    status: str
    stripe_invoice_url: Optional[str]
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True
