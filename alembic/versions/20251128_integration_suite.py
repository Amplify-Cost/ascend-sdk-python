"""OW-kai Enterprise Phase 5: Integration Suite Tables

Revision ID: 20251128_integration_suite
Revises: 20251128_compliance_export
Create Date: 2025-11-28 22:00:00.000000

Creates tables for enterprise integration management system:
- integration_registry: Central registry of all integrations
- integration_health_checks: Health monitoring history
- integration_data_flows: Data flow configurations
- data_flow_executions: Execution history
- integration_events: Cross-system event correlation
- integration_metrics: Aggregated performance metrics
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251128_integration_suite'
down_revision: Union[str, None] = '20251128_compliance_export'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================
    # Integration Registry Table
    # ============================================
    op.create_table(
        'integration_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Integration Identity
        sa.Column('integration_type', sa.String(50), nullable=False),
        sa.Column('integration_name', sa.String(200), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Connection Configuration
        sa.Column('endpoint_url', sa.String(500), nullable=True),
        sa.Column('auth_type', sa.String(50), default='none'),
        sa.Column('credentials_encrypted', sa.Text(), nullable=True),

        # Status
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),

        # Health Metrics
        sa.Column('health_status', sa.String(20), default='unknown'),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), default=0),
        sa.Column('uptime_percent_30d', sa.Float(), nullable=True),

        # Configuration
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('retry_config', sa.JSON(), nullable=True),
        sa.Column('rate_limit_config', sa.JSON(), nullable=True),

        # Metadata
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_index('ix_integration_registry_org_id', 'integration_registry', ['organization_id'])
    op.create_index('ix_integration_registry_type', 'integration_registry', ['integration_type'])
    op.create_index('ix_integration_registry_health', 'integration_registry', ['health_status'])
    op.create_index('ix_integration_registry_enabled', 'integration_registry', ['is_enabled'])

    # ============================================
    # Integration Health Checks Table
    # ============================================
    op.create_table(
        'integration_health_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Check Results
        sa.Column('check_type', sa.String(50), default='ping'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        # Error Details
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),

        # Timestamp
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['integration_id'], ['integration_registry.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_health_checks_integration_id', 'integration_health_checks', ['integration_id'])
    op.create_index('ix_health_checks_org_id', 'integration_health_checks', ['organization_id'])
    op.create_index('ix_health_checks_checked_at', 'integration_health_checks', ['checked_at'])

    # ============================================
    # Integration Data Flows Table
    # ============================================
    op.create_table(
        'integration_data_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Flow Identity
        sa.Column('flow_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Source and Destination
        sa.Column('source_integration_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('destination_integration_id', sa.Integer(), nullable=True),
        sa.Column('destination_type', sa.String(50), nullable=False),

        # Data Configuration
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('transformation_rules', sa.JSON(), nullable=True),
        sa.Column('filter_rules', sa.JSON(), nullable=True),

        # Flow Control
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('batch_size', sa.Integer(), default=100),
        sa.Column('batch_interval_seconds', sa.Integer(), default=60),

        # Execution Tracking
        sa.Column('last_execution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution_status', sa.String(20), nullable=True),
        sa.Column('total_records_processed', sa.Integer(), default=0),
        sa.Column('total_errors', sa.Integer(), default=0),

        # Timestamps
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_integration_id'], ['integration_registry.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['destination_integration_id'], ['integration_registry.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_index('ix_data_flows_org_id', 'integration_data_flows', ['organization_id'])
    op.create_index('ix_data_flows_source_id', 'integration_data_flows', ['source_integration_id'])
    op.create_index('ix_data_flows_enabled', 'integration_data_flows', ['is_enabled'])

    # ============================================
    # Data Flow Executions Table
    # ============================================
    op.create_table(
        'data_flow_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_flow_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Execution Details
        sa.Column('execution_id', sa.String(100), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False),

        # Metrics
        sa.Column('records_read', sa.Integer(), default=0),
        sa.Column('records_processed', sa.Integer(), default=0),
        sa.Column('records_failed', sa.Integer(), default=0),
        sa.Column('records_skipped', sa.Integer(), default=0),

        # Performance
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Error Tracking
        sa.Column('errors', sa.JSON(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['data_flow_id'], ['integration_data_flows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_flow_executions_flow_id', 'data_flow_executions', ['data_flow_id'])
    op.create_index('ix_flow_executions_org_id', 'data_flow_executions', ['organization_id'])
    op.create_index('ix_flow_executions_exec_id', 'data_flow_executions', ['execution_id'])
    op.create_index('ix_flow_executions_started_at', 'data_flow_executions', ['started_at'])

    # ============================================
    # Integration Events Table
    # ============================================
    op.create_table(
        'integration_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Event Identity
        sa.Column('event_id', sa.String(100), nullable=False, unique=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),

        # Source
        sa.Column('source_integration_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_system', sa.String(100), nullable=True),

        # Event Details
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), default='info'),

        # Payload
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('payload_hash', sa.String(64), nullable=True),

        # Processing Status
        sa.Column('status', sa.String(20), default='received'),
        sa.Column('processed_by', sa.JSON(), nullable=True),

        # Timestamps
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_integration_id'], ['integration_registry.id'], ondelete='SET NULL'),
    )

    op.create_index('ix_integration_events_org_id', 'integration_events', ['organization_id'])
    op.create_index('ix_integration_events_event_id', 'integration_events', ['event_id'])
    op.create_index('ix_integration_events_correlation_id', 'integration_events', ['correlation_id'])
    op.create_index('ix_integration_events_event_type', 'integration_events', ['event_type'])
    op.create_index('ix_integration_events_event_time', 'integration_events', ['event_time'])
    op.create_index('ix_integration_events_severity', 'integration_events', ['severity'])

    # ============================================
    # Integration Metrics Table
    # ============================================
    op.create_table(
        'integration_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=True),

        # Time Window
        sa.Column('metric_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('granularity', sa.String(20), nullable=False),

        # Volume Metrics
        sa.Column('total_events', sa.Integer(), default=0),
        sa.Column('successful_events', sa.Integer(), default=0),
        sa.Column('failed_events', sa.Integer(), default=0),

        # Performance Metrics
        sa.Column('avg_latency_ms', sa.Float(), nullable=True),
        sa.Column('p95_latency_ms', sa.Float(), nullable=True),
        sa.Column('p99_latency_ms', sa.Float(), nullable=True),
        sa.Column('max_latency_ms', sa.Float(), nullable=True),

        # Reliability Metrics
        sa.Column('uptime_percent', sa.Float(), nullable=True),
        sa.Column('error_rate', sa.Float(), nullable=True),

        # Data Volume
        sa.Column('bytes_processed', sa.Integer(), default=0),

        # Computed at
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integration_id'], ['integration_registry.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_integration_metrics_org_id', 'integration_metrics', ['organization_id'])
    op.create_index('ix_integration_metrics_integration_id', 'integration_metrics', ['integration_id'])
    op.create_index('ix_integration_metrics_date', 'integration_metrics', ['metric_date'])
    op.create_index('ix_integration_metrics_granularity', 'integration_metrics', ['granularity'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_integration_metrics_granularity', table_name='integration_metrics')
    op.drop_index('ix_integration_metrics_date', table_name='integration_metrics')
    op.drop_index('ix_integration_metrics_integration_id', table_name='integration_metrics')
    op.drop_index('ix_integration_metrics_org_id', table_name='integration_metrics')

    op.drop_index('ix_integration_events_severity', table_name='integration_events')
    op.drop_index('ix_integration_events_event_time', table_name='integration_events')
    op.drop_index('ix_integration_events_event_type', table_name='integration_events')
    op.drop_index('ix_integration_events_correlation_id', table_name='integration_events')
    op.drop_index('ix_integration_events_event_id', table_name='integration_events')
    op.drop_index('ix_integration_events_org_id', table_name='integration_events')

    op.drop_index('ix_flow_executions_started_at', table_name='data_flow_executions')
    op.drop_index('ix_flow_executions_exec_id', table_name='data_flow_executions')
    op.drop_index('ix_flow_executions_org_id', table_name='data_flow_executions')
    op.drop_index('ix_flow_executions_flow_id', table_name='data_flow_executions')

    op.drop_index('ix_data_flows_enabled', table_name='integration_data_flows')
    op.drop_index('ix_data_flows_source_id', table_name='integration_data_flows')
    op.drop_index('ix_data_flows_org_id', table_name='integration_data_flows')

    op.drop_index('ix_health_checks_checked_at', table_name='integration_health_checks')
    op.drop_index('ix_health_checks_org_id', table_name='integration_health_checks')
    op.drop_index('ix_health_checks_integration_id', table_name='integration_health_checks')

    op.drop_index('ix_integration_registry_enabled', table_name='integration_registry')
    op.drop_index('ix_integration_registry_health', table_name='integration_registry')
    op.drop_index('ix_integration_registry_type', table_name='integration_registry')
    op.drop_index('ix_integration_registry_org_id', table_name='integration_registry')

    # Drop tables
    op.drop_table('integration_metrics')
    op.drop_table('integration_events')
    op.drop_table('data_flow_executions')
    op.drop_table('integration_data_flows')
    op.drop_table('integration_health_checks')
    op.drop_table('integration_registry')
