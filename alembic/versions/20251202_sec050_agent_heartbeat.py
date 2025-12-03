"""SEC-050: Add agent heartbeat monitoring columns

Enterprise-grade agent health monitoring with heartbeat tracking.
Enables real-time visibility into agent connectivity status.

Features:
- Heartbeat timestamp tracking
- Configurable heartbeat intervals
- Health status enumeration (online/degraded/offline/unknown)
- Consecutive missed heartbeat counter
- Performance metrics tracking

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6

Revision ID: sec050_heartbeat
Revises: 20251202_sec046_pt
Create Date: 2025-12-02

SEC-050: Fixed parent revision to merge into main migration chain (was orphaned from 20251201_agent_registry)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'sec050_heartbeat'
down_revision = '20251202_sec046_pt'  # SEC-050: Fixed - was 20251201_agent_registry (caused branch)
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column already exists in the table (idempotent migration)."""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add heartbeat monitoring columns to registered_agents table.

    SEC-050: Enterprise idempotent migration - safe to re-run
    """

    # SEC-050: Add heartbeat tracking columns (with idempotent checks)
    if not column_exists('registered_agents', 'last_heartbeat'):
        op.add_column(
            'registered_agents',
            sa.Column('last_heartbeat', sa.DateTime(), nullable=True,
                      comment='Timestamp of last heartbeat received from agent')
        )
        print("SEC-050: Added last_heartbeat column")
    else:
        print("SEC-050: last_heartbeat column already exists")

    if not column_exists('registered_agents', 'heartbeat_interval_seconds'):
        op.add_column(
            'registered_agents',
            sa.Column('heartbeat_interval_seconds', sa.Integer(), server_default='60', nullable=False,
                      comment='Expected seconds between heartbeats (default: 60)')
        )
        print("SEC-050: Added heartbeat_interval_seconds column")

    if not column_exists('registered_agents', 'health_status'):
        op.add_column(
            'registered_agents',
            sa.Column('health_status', sa.String(50), server_default='unknown', nullable=False,
                      comment='Current health: online, degraded, offline, unknown')
        )
        print("SEC-050: Added health_status column")

    if not column_exists('registered_agents', 'consecutive_missed_heartbeats'):
        op.add_column(
            'registered_agents',
            sa.Column('consecutive_missed_heartbeats', sa.Integer(), server_default='0', nullable=False,
                      comment='Count of consecutive missed heartbeats')
        )
        print("SEC-050: Added consecutive_missed_heartbeats column")

    # SEC-050: Performance metrics
    if not column_exists('registered_agents', 'avg_response_time_ms'):
        op.add_column(
            'registered_agents',
            sa.Column('avg_response_time_ms', sa.Float(), nullable=True,
                      comment='Average response time in milliseconds')
        )
        print("SEC-050: Added avg_response_time_ms column")

    if not column_exists('registered_agents', 'error_rate_percent'):
        op.add_column(
            'registered_agents',
            sa.Column('error_rate_percent', sa.Float(), server_default='0.0', nullable=False,
                      comment='Error rate percentage over last 24 hours')
        )
        print("SEC-050: Added error_rate_percent column")

    if not column_exists('registered_agents', 'total_requests_24h'):
        op.add_column(
            'registered_agents',
            sa.Column('total_requests_24h', sa.Integer(), server_default='0', nullable=False,
                      comment='Total requests processed in last 24 hours')
        )
        print("SEC-050: Added total_requests_24h column")

    if not column_exists('registered_agents', 'last_error'):
        op.add_column(
            'registered_agents',
            sa.Column('last_error', sa.Text(), nullable=True,
                      comment='Last error message received from agent')
        )
        print("SEC-050: Added last_error column")

    if not column_exists('registered_agents', 'last_error_at'):
        op.add_column(
            'registered_agents',
            sa.Column('last_error_at', sa.DateTime(), nullable=True,
                      comment='Timestamp of last error')
        )
        print("SEC-050: Added last_error_at column")

    # Index for efficient health monitoring queries (idempotent - Alembic handles existing indexes)
    try:
        op.create_index(
            'ix_registered_agents_health',
            'registered_agents',
            ['organization_id', 'health_status'],
            unique=False
        )
        print("SEC-050: Created ix_registered_agents_health index")
    except Exception as e:
        print(f"SEC-050: Index ix_registered_agents_health may already exist: {e}")

    try:
        op.create_index(
            'ix_registered_agents_heartbeat',
            'registered_agents',
            ['organization_id', 'last_heartbeat'],
            unique=False
        )
        print("SEC-050: Created ix_registered_agents_heartbeat index")
    except Exception as e:
        print(f"SEC-050: Index ix_registered_agents_heartbeat may already exist: {e}")

    print("SEC-050: Agent heartbeat monitoring migration completed")


def downgrade() -> None:
    """Remove heartbeat monitoring columns."""

    # Remove indexes
    op.drop_index('ix_registered_agents_heartbeat', table_name='registered_agents')
    op.drop_index('ix_registered_agents_health', table_name='registered_agents')

    # Remove columns
    op.drop_column('registered_agents', 'last_error_at')
    op.drop_column('registered_agents', 'last_error')
    op.drop_column('registered_agents', 'total_requests_24h')
    op.drop_column('registered_agents', 'error_rate_percent')
    op.drop_column('registered_agents', 'avg_response_time_ms')
    op.drop_column('registered_agents', 'consecutive_missed_heartbeats')
    op.drop_column('registered_agents', 'health_status')
    op.drop_column('registered_agents', 'heartbeat_interval_seconds')
    op.drop_column('registered_agents', 'last_heartbeat')

    print("SEC-050: Agent heartbeat monitoring columns removed")
