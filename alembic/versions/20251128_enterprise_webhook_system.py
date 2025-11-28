"""Enterprise Webhook Event System Migration

OW-kai Enterprise Integration Phase 1: Webhook Event System
Banking-Level Security: HMAC-SHA256 signatures, audit trails, retry logic

Purpose: Create production-grade webhook infrastructure for real-time event notifications
Tables: webhook_subscriptions, webhook_deliveries, webhook_delivery_queue
Security: SHA-512 hashed secrets, HMAC-SHA256 signatures, tenant isolation
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, NIST 800-63B

Revision ID: 20251128_webhooks
Revises: 20251126_tenant_isolation, 20251127_email_audit
Create Date: 2025-11-28 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '20251128_webhooks'
down_revision: Union[str, Sequence[str], None] = ('20251126_tenant_isolation', '20251127_email_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create webhook event system tables for enterprise integrations

    Tables Created:
    1. webhook_subscriptions - Webhook endpoint registrations
    2. webhook_deliveries - Delivery attempt history (audit trail)
    3. webhook_delivery_queue - Pending/failed delivery queue (DLQ)

    Security Features:
    - SHA-512 hashed secrets (never stores plaintext)
    - HMAC-SHA256 signature generation
    - Multi-tenant isolation via organization_id
    - Complete audit trail for compliance
    - Rate limiting per subscription
    """

    # ========================================
    # Table 1: webhook_subscriptions
    # ========================================
    op.create_table(
        'webhook_subscriptions',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Subscription details
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_url', sa.String(length=2048), nullable=False),

        # Secret storage (NEVER stores plaintext)
        sa.Column('secret_key_hash', sa.String(length=128), nullable=False),  # SHA-512 hash
        sa.Column('secret_key_salt', sa.String(length=32), nullable=False),

        # Event configuration (JSONB array of event types)
        sa.Column('event_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Headers (custom headers for customer systems)
        sa.Column('custom_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Retry configuration
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('retry_interval_seconds', sa.Integer(), nullable=False, server_default='60'),

        # Rate limiting
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('rate_limit_current_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rate_limit_window_start', sa.DateTime(timezone=True), nullable=True),

        # Metrics
        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),

        # Pause/circuit breaker
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_reason', sa.Text(), nullable=True),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.UniqueConstraint('subscription_id'),
    )

    # Indexes for webhook_subscriptions
    op.create_index('ix_webhook_subscriptions_id', 'webhook_subscriptions', ['id'], unique=False)
    op.create_index('ix_webhook_subscriptions_organization_id', 'webhook_subscriptions', ['organization_id'], unique=False)
    op.create_index('ix_webhook_subscriptions_subscription_id', 'webhook_subscriptions', ['subscription_id'], unique=True)
    op.create_index('ix_webhook_subscriptions_is_active', 'webhook_subscriptions', ['is_active'], unique=False)
    op.create_index('ix_webhook_subscriptions_created_at', 'webhook_subscriptions', ['created_at'], unique=False)
    op.create_index('idx_webhook_subs_org_active', 'webhook_subscriptions', ['organization_id', 'is_active'],
                   unique=False, postgresql_where=sa.text('is_active = TRUE'))
    # GIN index for event_types JSONB array containment queries
    op.create_index('idx_webhook_subs_event_types', 'webhook_subscriptions', ['event_types'],
                   unique=False, postgresql_using='gin')

    # ========================================
    # Table 2: webhook_deliveries (Audit trail)
    # ========================================
    op.create_table(
        'webhook_deliveries',
        # Primary identification
        sa.Column('id', sa.BigInteger(), nullable=False),  # BigInteger for high volume
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),  # Denormalized for query performance

        # Event identification
        sa.Column('event_id', sa.String(length=64), nullable=False),  # evt_xxx format
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),

        # Payload (stored for debugging/replay)
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('payload_size_bytes', sa.Integer(), nullable=False),

        # Delivery details
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('delivery_status', sa.String(length=50), nullable=False),  # pending, success, failed, retrying

        # Response tracking
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        # Error tracking
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),

        # Signature (for audit/verification)
        sa.Column('signature', sa.String(length=100), nullable=False),  # sha256=xxx
        sa.Column('timestamp', sa.BigInteger(), nullable=False),  # Unix timestamp used in signature

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    # Indexes for webhook_deliveries
    op.create_index('ix_webhook_deliveries_id', 'webhook_deliveries', ['id'], unique=False)
    op.create_index('ix_webhook_deliveries_subscription_id', 'webhook_deliveries', ['subscription_id'], unique=False)
    op.create_index('ix_webhook_deliveries_organization_id', 'webhook_deliveries', ['organization_id'], unique=False)
    op.create_index('ix_webhook_deliveries_event_id', 'webhook_deliveries', ['event_id'], unique=False)
    op.create_index('ix_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'], unique=False)
    op.create_index('ix_webhook_deliveries_idempotency_key', 'webhook_deliveries', ['idempotency_key'], unique=False)
    op.create_index('ix_webhook_deliveries_delivery_status', 'webhook_deliveries', ['delivery_status'], unique=False)
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'], unique=False)
    op.create_index('ix_webhook_deliveries_next_retry_at', 'webhook_deliveries', ['next_retry_at'], unique=False)
    op.create_index('idx_webhook_deliveries_sub_status', 'webhook_deliveries', ['subscription_id', 'delivery_status'], unique=False)
    op.create_index('idx_webhook_deliveries_org_created', 'webhook_deliveries', ['organization_id', 'created_at'], unique=False)
    op.create_index('idx_webhook_deliveries_pending_retry', 'webhook_deliveries', ['next_retry_at'],
                   unique=False, postgresql_where=sa.text("delivery_status IN ('pending', 'retrying')"))

    # ========================================
    # Table 3: webhook_delivery_queue (DLQ)
    # ========================================
    op.create_table(
        'webhook_delivery_queue',
        # Primary identification
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('original_delivery_id', sa.BigInteger(), nullable=False),

        # Event data
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Queue status
        sa.Column('queue_status', sa.String(length=50), nullable=False, server_default='pending'),  # pending, requeued, abandoned
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries_reached', sa.Boolean(), nullable=False, server_default='false'),

        # Last failure info
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_http_status', sa.Integer(), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Manual intervention
        sa.Column('requeued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requeued_by', sa.Integer(), nullable=True),
        sa.Column('abandoned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('abandoned_by', sa.Integer(), nullable=True),
        sa.Column('abandon_reason', sa.Text(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['original_delivery_id'], ['webhook_deliveries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requeued_by'], ['users.id']),
        sa.ForeignKeyConstraint(['abandoned_by'], ['users.id']),
    )

    # Indexes for webhook_delivery_queue
    op.create_index('ix_webhook_delivery_queue_id', 'webhook_delivery_queue', ['id'], unique=False)
    op.create_index('ix_webhook_delivery_queue_subscription_id', 'webhook_delivery_queue', ['subscription_id'], unique=False)
    op.create_index('ix_webhook_delivery_queue_organization_id', 'webhook_delivery_queue', ['organization_id'], unique=False)
    op.create_index('ix_webhook_delivery_queue_queue_status', 'webhook_delivery_queue', ['queue_status'], unique=False)
    op.create_index('ix_webhook_delivery_queue_created_at', 'webhook_delivery_queue', ['created_at'], unique=False)
    op.create_index('idx_dlq_org_status', 'webhook_delivery_queue', ['organization_id', 'queue_status'], unique=False)
    op.create_index('idx_dlq_pending', 'webhook_delivery_queue', ['queue_status'],
                   unique=False, postgresql_where=sa.text("queue_status = 'pending'"))


def downgrade() -> None:
    """
    Safely rollback webhook tables (reverse order due to foreign keys)
    """

    # Drop webhook_delivery_queue
    op.drop_index('idx_dlq_pending', table_name='webhook_delivery_queue')
    op.drop_index('idx_dlq_org_status', table_name='webhook_delivery_queue')
    op.drop_index('ix_webhook_delivery_queue_created_at', table_name='webhook_delivery_queue')
    op.drop_index('ix_webhook_delivery_queue_queue_status', table_name='webhook_delivery_queue')
    op.drop_index('ix_webhook_delivery_queue_organization_id', table_name='webhook_delivery_queue')
    op.drop_index('ix_webhook_delivery_queue_subscription_id', table_name='webhook_delivery_queue')
    op.drop_index('ix_webhook_delivery_queue_id', table_name='webhook_delivery_queue')
    op.drop_table('webhook_delivery_queue')

    # Drop webhook_deliveries
    op.drop_index('idx_webhook_deliveries_pending_retry', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_org_created', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_sub_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_next_retry_at', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_created_at', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_delivery_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_idempotency_key', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_event_type', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_event_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_organization_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_subscription_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_id', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')

    # Drop webhook_subscriptions
    op.drop_index('idx_webhook_subs_event_types', table_name='webhook_subscriptions')
    op.drop_index('idx_webhook_subs_org_active', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_created_at', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_is_active', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_subscription_id', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_organization_id', table_name='webhook_subscriptions')
    op.drop_index('ix_webhook_subscriptions_id', table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')
