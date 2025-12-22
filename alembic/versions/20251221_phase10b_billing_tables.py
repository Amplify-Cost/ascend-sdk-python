"""Phase 10B: Stripe Billing Tables

Revision ID: phase10b_billing
Revises: c10d8fe3d900
Create Date: 2025-12-21

Creates billing infrastructure tables:
- usage_events: High-throughput usage event tracking
- usage_aggregates: Pre-computed usage summaries
- spend_limits: Financial kill-switch configuration
- spend_limit_events: Audit trail for spend changes
- billing_records: Monthly billing summaries
- stripe_webhook_events: Webhook deduplication
- stripe_sync_log: API interaction audit
- subscription_tiers: Tier configuration reference

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase10b_billing'
down_revision = 'val_fix_001_multi_signal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # USAGE EVENTS - High-throughput usage tracking
    # ==========================================================================
    op.create_table(
        'usage_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_cost', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('billing_period', sa.String(7), nullable=False),
        sa.Column('stripe_reported', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('stripe_usage_record_id', sa.String(255), nullable=True),
        sa.Column('stripe_reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_usage_events_organization_id', 'usage_events', ['organization_id'])
    op.create_index('ix_usage_events_event_type', 'usage_events', ['event_type'])
    op.create_index('ix_usage_events_timestamp', 'usage_events', ['timestamp'])
    op.create_index('ix_usage_events_billing_period', 'usage_events', ['billing_period'])
    op.create_index('ix_usage_events_stripe_reported', 'usage_events', ['stripe_reported'])
    op.create_index(
        'ix_usage_events_org_period_reported',
        'usage_events',
        ['organization_id', 'billing_period', 'stripe_reported']
    )
    op.create_index(
        'ix_usage_events_org_type_period',
        'usage_events',
        ['organization_id', 'event_type', 'billing_period']
    )

    # ==========================================================================
    # USAGE AGGREGATES - Pre-computed summaries
    # ==========================================================================
    op.create_table(
        'usage_aggregates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('billing_period', sa.String(7), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('total_quantity', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('event_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('included_quantity', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('overage_quantity', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('overage_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_event_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_aggregated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'billing_period', 'event_type', name='uq_usage_aggregate_org_period_type')
    )
    op.create_index('ix_usage_aggregates_org_period', 'usage_aggregates', ['organization_id', 'billing_period'])

    # ==========================================================================
    # SPEND LIMITS - Financial kill-switch
    # ==========================================================================
    op.create_table(
        'spend_limits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('monthly_limit', sa.Float(), nullable=False),
        sa.Column('warning_threshold_percent', sa.Float(), nullable=False, server_default='80.0'),
        sa.Column('hard_limit_action', sa.String(50), nullable=False, server_default="'block'"),
        sa.Column('current_spend', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default="'active'"),
        sa.Column('limit_enforced', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('warning_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warning_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('warning_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warning_acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('kill_switch_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('kill_switch_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('kill_switch_triggered_by', sa.String(100), nullable=True),
        sa.Column('kill_switch_reason', sa.Text(), nullable=True),
        sa.Column('kill_switch_released', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('kill_switch_released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('kill_switch_released_by', sa.Integer(), nullable=True),
        sa.Column('release_reason', sa.Text(), nullable=True),
        sa.Column('current_billing_period', sa.String(7), nullable=True),
        sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warning_acknowledged_by'], ['users.id']),
        sa.ForeignKeyConstraint(['kill_switch_released_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spend_limits_organization_id', 'spend_limits', ['organization_id'], unique=True)

    # ==========================================================================
    # SPEND LIMIT EVENTS - Audit trail
    # ==========================================================================
    op.create_table(
        'spend_limit_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('previous_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spend_limit_events_organization_id', 'spend_limit_events', ['organization_id'])
    op.create_index('ix_spend_limit_events_event_type', 'spend_limit_events', ['event_type'])
    op.create_index('ix_spend_limit_events_org_created', 'spend_limit_events', ['organization_id', 'created_at'])

    # ==========================================================================
    # BILLING RECORDS - Monthly summaries
    # ==========================================================================
    op.create_table(
        'billing_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('billing_period', sa.String(7), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('base_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('usage_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('overage_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('usage_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True),
        sa.Column('stripe_invoice_url', sa.Text(), nullable=True),
        sa.Column('stripe_invoice_pdf', sa.Text(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default="'pending'"),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'billing_period', name='uq_billing_record_org_period')
    )
    op.create_index('ix_billing_records_organization_id', 'billing_records', ['organization_id'])
    op.create_index('ix_billing_records_org_period', 'billing_records', ['organization_id', 'billing_period'])
    op.create_index('ix_billing_records_status', 'billing_records', ['status'])
    op.create_index('ix_billing_records_stripe_invoice_id', 'billing_records', ['stripe_invoice_id'], unique=True)

    # ==========================================================================
    # STRIPE WEBHOOK EVENTS - Idempotency
    # ==========================================================================
    op.create_table(
        'stripe_webhook_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stripe_event_id', sa.String(255), nullable=False),
        sa.Column('stripe_event_type', sa.String(100), nullable=False),
        sa.Column('stripe_api_version', sa.String(50), nullable=True),
        sa.Column('event_data', postgresql.JSONB(), nullable=False),
        sa.Column('livemode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(50), nullable=False, server_default="'received'"),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('billing_record_id', sa.Integer(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['billing_record_id'], ['billing_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stripe_webhook_events_stripe_event_id', 'stripe_webhook_events', ['stripe_event_id'], unique=True)
    op.create_index('ix_stripe_webhook_events_stripe_event_type', 'stripe_webhook_events', ['stripe_event_type'])
    op.create_index('ix_stripe_webhook_events_organization_id', 'stripe_webhook_events', ['organization_id'])
    op.create_index('ix_stripe_webhook_events_type_status', 'stripe_webhook_events', ['stripe_event_type', 'status'])
    op.create_index('ix_stripe_webhook_events_received', 'stripe_webhook_events', ['received_at'])

    # ==========================================================================
    # STRIPE SYNC LOG - API audit
    # ==========================================================================
    op.create_table(
        'stripe_sync_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('operation', sa.String(100), nullable=False),
        sa.Column('stripe_object_type', sa.String(50), nullable=True),
        sa.Column('stripe_object_id', sa.String(255), nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stripe_sync_log_organization_id', 'stripe_sync_log', ['organization_id'])
    op.create_index('ix_stripe_sync_log_operation', 'stripe_sync_log', ['operation'])
    op.create_index('ix_stripe_sync_log_stripe_object_id', 'stripe_sync_log', ['stripe_object_id'])
    op.create_index('ix_stripe_sync_log_idempotency_key', 'stripe_sync_log', ['idempotency_key'])
    op.create_index('ix_stripe_sync_log_created_at', 'stripe_sync_log', ['created_at'])
    op.create_index('ix_stripe_sync_log_org_created', 'stripe_sync_log', ['organization_id', 'created_at'])
    op.create_index('ix_stripe_sync_log_operation_success', 'stripe_sync_log', ['operation', 'success'])

    # ==========================================================================
    # SUBSCRIPTION TIERS - Update existing table with Stripe fields
    # ==========================================================================
    # subscription_tiers table already exists, add Stripe columns if missing
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='subscription_tiers' AND column_name='stripe_product_id') THEN
                ALTER TABLE subscription_tiers ADD COLUMN stripe_product_id VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='subscription_tiers' AND column_name='stripe_price_id') THEN
                ALTER TABLE subscription_tiers ADD COLUMN stripe_price_id VARCHAR(255);
            END IF;
        END $$;
    """)

    # Update pilot tier with Stripe IDs
    op.execute("""
        UPDATE subscription_tiers
        SET stripe_product_id = 'prod_TddRiHRooPx0T0',
            stripe_price_id = 'price_1SgMAyECPjy5KubvAI2DsdEk'
        WHERE name = 'pilot';
    """)


def downgrade() -> None:
    # Don't drop subscription_tiers - it existed before this migration
    # Just remove the Stripe columns we added
    op.execute("""
        ALTER TABLE subscription_tiers
        DROP COLUMN IF EXISTS stripe_product_id,
        DROP COLUMN IF EXISTS stripe_price_id;
    """)
    op.drop_table('stripe_sync_log')
    op.drop_table('stripe_webhook_events')
    op.drop_table('billing_records')
    op.drop_table('spend_limit_events')
    op.drop_table('spend_limits')
    op.drop_table('usage_aggregates')
    op.drop_table('usage_events')
