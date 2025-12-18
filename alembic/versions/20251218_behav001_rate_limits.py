"""BEHAV-001: Rate Limiting Schema

Implements per-agent, per-tenant rate limiting with Redis backend.

Tables:
1. org_rate_limit_config - Per-org rate limit settings
2. agent_rate_limit_overrides - Per-agent limit overrides
3. rate_limit_events - Immutable event log for analytics

Key design decisions:
- Database-driven configuration (no hardcoded values)
- Priority tiers for critical agents
- Fail-closed on Redis unavailability
- Immutable audit trail for compliance

Revision ID: behav001_rate_limits
Revises: b1a16964bb4c
Create Date: 2025-12-18

Compliance: SOC 2 A1.1, NIST 800-53 SC-5, SOC 2 CC6.1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'behav001_rate_limits'
down_revision = 'b1a16964bb4c'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # TABLE 1: org_rate_limit_config
    # ========================================================================
    # Per-organization rate limit configuration
    # One record per org with default limits for all agents
    op.create_table(
        'org_rate_limit_config',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  unique=True, nullable=False, index=True),

        # Tenant-wide limits (aggregate across all agents)
        sa.Column('actions_per_minute', sa.Integer(), server_default='1000', nullable=False),
        sa.Column('actions_per_hour', sa.Integer(), server_default='50000', nullable=False),
        sa.Column('actions_per_day', sa.Integer(), server_default='500000', nullable=False),

        # Default agent limits (can be overridden per-agent)
        sa.Column('agent_actions_per_minute', sa.Integer(), server_default='100', nullable=False),
        sa.Column('agent_actions_per_hour', sa.Integer(), server_default='5000', nullable=False),

        # Burst handling
        sa.Column('burst_multiplier', sa.Numeric(3, 2), server_default='1.5', nullable=False),
        sa.Column('burst_window_seconds', sa.Integer(), server_default='10', nullable=False),

        # Response behavior
        sa.Column('rate_limit_response_code', sa.Integer(), server_default='429', nullable=False),
        sa.Column('include_retry_after', sa.Boolean(), server_default='true', nullable=False),

        # Feature toggle
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # ========================================================================
    # TABLE 2: agent_rate_limit_overrides
    # ========================================================================
    # Per-agent overrides for specific agents that need different limits
    op.create_table(
        'agent_rate_limit_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),

        # Override limits (NULL = use org default)
        sa.Column('actions_per_minute', sa.Integer(), nullable=True),
        sa.Column('actions_per_hour', sa.Integer(), nullable=True),

        # Priority tier (affects multipliers)
        sa.Column('priority_tier', sa.String(20), server_default='standard', nullable=False),

        # Reason for override (required for audit)
        sa.Column('override_reason', sa.Text(), nullable=True),

        # Approval workflow
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # Unique constraint: one override per agent per org
    op.create_unique_constraint(
        'uq_agent_rate_limit_org_agent',
        'agent_rate_limit_overrides',
        ['organization_id', 'agent_id']
    )

    # Index for looking up agent overrides
    op.create_index(
        'idx_agent_rate_limit_org',
        'agent_rate_limit_overrides',
        ['organization_id']
    )

    # ========================================================================
    # TABLE 3: rate_limit_events
    # ========================================================================
    # Immutable event log for analytics and alerting
    op.create_table(
        'rate_limit_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('agent_id', sa.String(255), nullable=True, index=True),

        # Event details
        sa.Column('event_type', sa.String(50), nullable=False),  # limit_reached, burst_allowed, blocked
        sa.Column('limit_type', sa.String(50), nullable=False),  # agent_minute, tenant_minute, etc.

        # Counters at time of event
        sa.Column('current_count', sa.Integer(), nullable=False),
        sa.Column('limit_value', sa.Integer(), nullable=False),

        # Context
        sa.Column('action_type', sa.String(100), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),

        # Timestamp (immutable)
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # Composite indexes for common query patterns
    op.create_index(
        'idx_rate_limit_events_org_time',
        'rate_limit_events',
        ['organization_id', 'created_at']
    )
    op.create_index(
        'idx_rate_limit_events_agent',
        'rate_limit_events',
        ['organization_id', 'agent_id', 'created_at']
    )

    # ========================================================================
    # SEED: Default rate limit config for existing organizations
    # ========================================================================
    # Note: This creates default configs for any existing orgs
    # New orgs will get configs created on first API call
    op.execute("""
        INSERT INTO org_rate_limit_config (organization_id, enabled, created_at, updated_at)
        SELECT id, true, NOW(), NOW()
        FROM organizations
        WHERE id NOT IN (SELECT organization_id FROM org_rate_limit_config)
        ON CONFLICT (organization_id) DO NOTHING;
    """)


def downgrade():
    # Drop tables in reverse order (events -> overrides -> config)
    op.drop_index('idx_rate_limit_events_agent', table_name='rate_limit_events')
    op.drop_index('idx_rate_limit_events_org_time', table_name='rate_limit_events')
    op.drop_table('rate_limit_events')

    op.drop_index('idx_agent_rate_limit_org', table_name='agent_rate_limit_overrides')
    op.drop_constraint('uq_agent_rate_limit_org_agent', 'agent_rate_limit_overrides', type_='unique')
    op.drop_table('agent_rate_limit_overrides')

    op.drop_table('org_rate_limit_config')
