"""Enterprise Notification Channels Migration

OW-kai Enterprise Integration Phase 2: Slack/Teams Notification System
Banking-Level Security: Encrypted webhook URLs, audit trails, rate limiting

Purpose: Create notification infrastructure for Slack/Teams integrations
Tables: notification_channels, notification_deliveries, notification_templates
Security: AES-256 encrypted URLs, tenant isolation, complete audit trail
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1

Revision ID: 20251128_notifications
Revises: 20251128_webhooks
Create Date: 2025-11-28 12:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '20251128_notifications'
down_revision: Union[str, Sequence[str], None] = '20251128_webhooks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create notification system tables for enterprise Slack/Teams integrations.

    Tables Created:
    1. notification_channels - Slack/Teams channel configurations
    2. notification_deliveries - Delivery attempt audit trail
    3. notification_templates - Customizable message templates

    Security Features:
    - AES-256 encrypted webhook URLs (never stored plaintext)
    - Multi-tenant isolation via organization_id
    - Complete audit trail for compliance
    - Rate limiting per channel
    - Circuit breaker pattern
    """

    # ========================================
    # Table 1: notification_channels
    # ========================================
    op.create_table(
        'notification_channels',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Channel details
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel_type', sa.String(length=50), nullable=False),  # slack, teams

        # Encrypted webhook storage
        sa.Column('webhook_url_encrypted', sa.Text(), nullable=False),  # AES-256 encrypted
        sa.Column('webhook_url_hash', sa.String(length=64), nullable=False),  # SHA-256 for lookup

        # Slack-specific settings
        sa.Column('slack_channel_name', sa.String(length=255), nullable=True),
        sa.Column('slack_username', sa.String(length=255), nullable=True),
        sa.Column('slack_icon_emoji', sa.String(length=100), nullable=True),

        # Teams-specific settings
        sa.Column('teams_title', sa.String(length=255), nullable=True),

        # Event subscriptions
        sa.Column('subscribed_events', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),

        # Filtering
        sa.Column('min_risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_levels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Rate limiting
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('rate_limit_current_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rate_limit_window_start', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),

        # Metrics
        sa.Column('total_notifications', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_notifications', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_notifications', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_notification_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),

        # Circuit breaker
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
        sa.UniqueConstraint('channel_id'),
    )

    # Indexes for notification_channels
    op.create_index('ix_notification_channels_id', 'notification_channels', ['id'], unique=False)
    op.create_index('ix_notification_channels_organization_id', 'notification_channels', ['organization_id'], unique=False)
    op.create_index('ix_notification_channels_channel_id', 'notification_channels', ['channel_id'], unique=True)
    op.create_index('ix_notification_channels_channel_type', 'notification_channels', ['channel_type'], unique=False)
    op.create_index('ix_notification_channels_is_active', 'notification_channels', ['is_active'], unique=False)
    op.create_index('ix_notification_channels_webhook_url_hash', 'notification_channels', ['webhook_url_hash'], unique=False)
    op.create_index('idx_notification_channels_org_active', 'notification_channels', ['organization_id', 'is_active'],
                   unique=False, postgresql_where=sa.text('is_active = TRUE'))
    # GIN index for subscribed_events JSONB
    op.create_index('idx_notification_channels_events', 'notification_channels', ['subscribed_events'],
                   unique=False, postgresql_using='gin')

    # ========================================
    # Table 2: notification_deliveries
    # ========================================
    op.create_table(
        'notification_deliveries',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Notification identification
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),

        # Message content
        sa.Column('message_title', sa.String(length=500), nullable=False),
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('message_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

        # Related entity
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),

        # Delivery details
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('delivery_status', sa.String(length=50), nullable=False, server_default='pending'),

        # Response tracking
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        # Error tracking
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['channel_id'], ['notification_channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('notification_id'),
    )

    # Indexes for notification_deliveries
    op.create_index('ix_notification_deliveries_id', 'notification_deliveries', ['id'], unique=False)
    op.create_index('ix_notification_deliveries_channel_id', 'notification_deliveries', ['channel_id'], unique=False)
    op.create_index('ix_notification_deliveries_organization_id', 'notification_deliveries', ['organization_id'], unique=False)
    op.create_index('ix_notification_deliveries_notification_id', 'notification_deliveries', ['notification_id'], unique=True)
    op.create_index('ix_notification_deliveries_event_type', 'notification_deliveries', ['event_type'], unique=False)
    op.create_index('ix_notification_deliveries_idempotency_key', 'notification_deliveries', ['idempotency_key'], unique=False)
    op.create_index('ix_notification_deliveries_delivery_status', 'notification_deliveries', ['delivery_status'], unique=False)
    op.create_index('ix_notification_deliveries_created_at', 'notification_deliveries', ['created_at'], unique=False)
    op.create_index('idx_notification_deliveries_ch_status', 'notification_deliveries', ['channel_id', 'delivery_status'], unique=False)
    op.create_index('idx_notification_deliveries_org_created', 'notification_deliveries', ['organization_id', 'created_at'], unique=False)
    op.create_index('idx_notification_deliveries_pending', 'notification_deliveries', ['next_retry_at'],
                   unique=False, postgresql_where=sa.text("delivery_status IN ('pending', 'retrying')"))

    # ========================================
    # Table 3: notification_templates
    # ========================================
    op.create_table(
        'notification_templates',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),  # NULL = system default
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Template details
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('channel_type', sa.String(length=50), nullable=False),  # slack, teams, all
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Templates
        sa.Column('slack_template', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('teams_template', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('plain_text_template', sa.Text(), nullable=False),

        # Variables documentation
        sa.Column('available_variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('template_id'),
    )

    # Indexes for notification_templates
    op.create_index('ix_notification_templates_id', 'notification_templates', ['id'], unique=False)
    op.create_index('ix_notification_templates_organization_id', 'notification_templates', ['organization_id'], unique=False)
    op.create_index('ix_notification_templates_template_id', 'notification_templates', ['template_id'], unique=True)
    op.create_index('ix_notification_templates_event_type', 'notification_templates', ['event_type'], unique=False)
    op.create_index('idx_notification_templates_org_event', 'notification_templates', ['organization_id', 'event_type'], unique=False)


def downgrade() -> None:
    """
    Rollback notification tables (reverse order due to foreign keys)
    """

    # Drop notification_templates
    op.drop_index('idx_notification_templates_org_event', table_name='notification_templates')
    op.drop_index('ix_notification_templates_event_type', table_name='notification_templates')
    op.drop_index('ix_notification_templates_template_id', table_name='notification_templates')
    op.drop_index('ix_notification_templates_organization_id', table_name='notification_templates')
    op.drop_index('ix_notification_templates_id', table_name='notification_templates')
    op.drop_table('notification_templates')

    # Drop notification_deliveries
    op.drop_index('idx_notification_deliveries_pending', table_name='notification_deliveries')
    op.drop_index('idx_notification_deliveries_org_created', table_name='notification_deliveries')
    op.drop_index('idx_notification_deliveries_ch_status', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_created_at', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_delivery_status', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_idempotency_key', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_event_type', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_notification_id', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_organization_id', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_channel_id', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_id', table_name='notification_deliveries')
    op.drop_table('notification_deliveries')

    # Drop notification_channels
    op.drop_index('idx_notification_channels_events', table_name='notification_channels')
    op.drop_index('idx_notification_channels_org_active', table_name='notification_channels')
    op.drop_index('ix_notification_channels_webhook_url_hash', table_name='notification_channels')
    op.drop_index('ix_notification_channels_is_active', table_name='notification_channels')
    op.drop_index('ix_notification_channels_channel_type', table_name='notification_channels')
    op.drop_index('ix_notification_channels_channel_id', table_name='notification_channels')
    op.drop_index('ix_notification_channels_organization_id', table_name='notification_channels')
    op.drop_index('ix_notification_channels_id', table_name='notification_channels')
    op.drop_table('notification_channels')
