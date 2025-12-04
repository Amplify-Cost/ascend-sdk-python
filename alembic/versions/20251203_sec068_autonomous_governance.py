"""SEC-068: Autonomous Agent Governance

Enterprise-grade controls for autonomous AI agents including:
- Rate limiting (per minute/hour/day)
- Budget controls (daily spend limits)
- Session limits (concurrent actions, duration)
- Time window restrictions (business hours only)
- Data classification enforcement
- Auto-suspension triggers
- Anomaly detection baselines

Compliance: SOC 2 CC6.1/CC6.2/CC7.1, NIST AC-3/SI-4, PCI-DSS 7.1
Aligned with: Datadog, Wiz.io, Splunk enterprise patterns

Revision ID: sec068_autonomous
Revises: 20251202_sec050_agent_heartbeat
Create Date: 2025-12-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'sec068_autonomous'
down_revision = 'sec066_metric_audit'  # CR-015: Set proper down_revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add SEC-068 autonomous agent governance columns."""

    # SEC-068: Rate Limiting
    op.add_column('registered_agents', sa.Column('max_actions_per_minute', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('max_actions_per_hour', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('max_actions_per_day', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('current_minute_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('registered_agents', sa.Column('current_hour_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('registered_agents', sa.Column('current_day_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('registered_agents', sa.Column('rate_limit_window_start', sa.DateTime(), nullable=True))

    # SEC-068: Budget Controls
    op.add_column('registered_agents', sa.Column('max_daily_budget_usd', sa.Float(), nullable=True))
    op.add_column('registered_agents', sa.Column('current_daily_spend_usd', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('registered_agents', sa.Column('budget_reset_at', sa.DateTime(), nullable=True))
    op.add_column('registered_agents', sa.Column('budget_alert_threshold_percent', sa.Integer(), server_default='80', nullable=False))
    op.add_column('registered_agents', sa.Column('budget_alert_sent', sa.Boolean(), server_default='false', nullable=False))

    # SEC-068: Session Limits
    op.add_column('registered_agents', sa.Column('max_concurrent_actions', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('current_concurrent_actions', sa.Integer(), server_default='0', nullable=False))
    op.add_column('registered_agents', sa.Column('max_session_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('current_session_start', sa.DateTime(), nullable=True))

    # SEC-068: Time Window Restrictions
    op.add_column('registered_agents', sa.Column('time_window_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('registered_agents', sa.Column('time_window_start', sa.String(5), nullable=True))
    op.add_column('registered_agents', sa.Column('time_window_end', sa.String(5), nullable=True))
    op.add_column('registered_agents', sa.Column('time_window_timezone', sa.String(50), server_default='UTC', nullable=True))
    op.add_column('registered_agents', sa.Column('time_window_days', postgresql.JSONB(), server_default='[]', nullable=True))

    # SEC-068: Data Classification Restrictions
    op.add_column('registered_agents', sa.Column('allowed_data_classifications', postgresql.JSONB(), server_default='[]', nullable=True))
    op.add_column('registered_agents', sa.Column('blocked_data_classifications', postgresql.JSONB(), server_default='[]', nullable=True))

    # SEC-068: Auto-Suspension Triggers
    # CR-015: Default to FALSE to avoid unexpectedly suspending existing agents
    op.add_column('registered_agents', sa.Column('auto_suspend_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('registered_agents', sa.Column('auto_suspend_on_error_rate', sa.Float(), nullable=True))
    op.add_column('registered_agents', sa.Column('auto_suspend_on_offline_minutes', sa.Integer(), nullable=True))
    op.add_column('registered_agents', sa.Column('auto_suspend_on_budget_exceeded', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('registered_agents', sa.Column('auto_suspend_on_rate_exceeded', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('registered_agents', sa.Column('auto_suspended_at', sa.DateTime(), nullable=True))
    op.add_column('registered_agents', sa.Column('auto_suspend_reason', sa.Text(), nullable=True))

    # SEC-068: Anomaly Detection
    op.add_column('registered_agents', sa.Column('anomaly_detection_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('registered_agents', sa.Column('baseline_actions_per_hour', sa.Float(), nullable=True))
    op.add_column('registered_agents', sa.Column('baseline_error_rate', sa.Float(), nullable=True))
    op.add_column('registered_agents', sa.Column('baseline_avg_risk_score', sa.Float(), nullable=True))
    op.add_column('registered_agents', sa.Column('anomaly_threshold_percent', sa.Float(), server_default='50.0', nullable=False))
    op.add_column('registered_agents', sa.Column('last_anomaly_check', sa.DateTime(), nullable=True))
    op.add_column('registered_agents', sa.Column('last_anomaly_detected', sa.DateTime(), nullable=True))
    op.add_column('registered_agents', sa.Column('anomaly_count_24h', sa.Integer(), server_default='0', nullable=False))

    # SEC-068: Autonomous-Specific Thresholds
    op.add_column('registered_agents', sa.Column('autonomous_max_risk_threshold', sa.Integer(), server_default='60', nullable=False))
    op.add_column('registered_agents', sa.Column('autonomous_auto_approve_below', sa.Integer(), server_default='40', nullable=False))
    op.add_column('registered_agents', sa.Column('autonomous_require_dual_approval', sa.Boolean(), server_default='false', nullable=False))

    # CR-003: Autonomous Escalation Path
    op.add_column('registered_agents', sa.Column('autonomous_escalation_webhook_url', sa.String(500), nullable=True))
    op.add_column('registered_agents', sa.Column('autonomous_escalation_email', sa.String(255), nullable=True))
    op.add_column('registered_agents', sa.Column('autonomous_allow_queued_approval', sa.Boolean(), server_default='false', nullable=False))

    # Create index for autonomous agents (common query pattern)
    op.create_index(
        'ix_registered_agents_autonomous',
        'registered_agents',
        ['organization_id', 'agent_type'],
        postgresql_where=sa.text("agent_type = 'autonomous'")
    )


def downgrade() -> None:
    """Remove SEC-068 autonomous agent governance columns."""

    # Drop index
    op.drop_index('ix_registered_agents_autonomous', table_name='registered_agents')

    # CR-003: Autonomous Escalation Path
    op.drop_column('registered_agents', 'autonomous_allow_queued_approval')
    op.drop_column('registered_agents', 'autonomous_escalation_email')
    op.drop_column('registered_agents', 'autonomous_escalation_webhook_url')

    # SEC-068: Autonomous-Specific Thresholds
    op.drop_column('registered_agents', 'autonomous_require_dual_approval')
    op.drop_column('registered_agents', 'autonomous_auto_approve_below')
    op.drop_column('registered_agents', 'autonomous_max_risk_threshold')

    # SEC-068: Anomaly Detection
    op.drop_column('registered_agents', 'anomaly_count_24h')
    op.drop_column('registered_agents', 'last_anomaly_detected')
    op.drop_column('registered_agents', 'last_anomaly_check')
    op.drop_column('registered_agents', 'anomaly_threshold_percent')
    op.drop_column('registered_agents', 'baseline_avg_risk_score')
    op.drop_column('registered_agents', 'baseline_error_rate')
    op.drop_column('registered_agents', 'baseline_actions_per_hour')
    op.drop_column('registered_agents', 'anomaly_detection_enabled')

    # SEC-068: Auto-Suspension Triggers
    op.drop_column('registered_agents', 'auto_suspend_reason')
    op.drop_column('registered_agents', 'auto_suspended_at')
    op.drop_column('registered_agents', 'auto_suspend_on_rate_exceeded')
    op.drop_column('registered_agents', 'auto_suspend_on_budget_exceeded')
    op.drop_column('registered_agents', 'auto_suspend_on_offline_minutes')
    op.drop_column('registered_agents', 'auto_suspend_on_error_rate')
    op.drop_column('registered_agents', 'auto_suspend_enabled')

    # SEC-068: Data Classification Restrictions
    op.drop_column('registered_agents', 'blocked_data_classifications')
    op.drop_column('registered_agents', 'allowed_data_classifications')

    # SEC-068: Time Window Restrictions
    op.drop_column('registered_agents', 'time_window_days')
    op.drop_column('registered_agents', 'time_window_timezone')
    op.drop_column('registered_agents', 'time_window_end')
    op.drop_column('registered_agents', 'time_window_start')
    op.drop_column('registered_agents', 'time_window_enabled')

    # SEC-068: Session Limits
    op.drop_column('registered_agents', 'current_session_start')
    op.drop_column('registered_agents', 'max_session_duration_minutes')
    op.drop_column('registered_agents', 'current_concurrent_actions')
    op.drop_column('registered_agents', 'max_concurrent_actions')

    # SEC-068: Budget Controls
    op.drop_column('registered_agents', 'budget_alert_sent')
    op.drop_column('registered_agents', 'budget_alert_threshold_percent')
    op.drop_column('registered_agents', 'budget_reset_at')
    op.drop_column('registered_agents', 'current_daily_spend_usd')
    op.drop_column('registered_agents', 'max_daily_budget_usd')

    # SEC-068: Rate Limiting
    op.drop_column('registered_agents', 'rate_limit_window_start')
    op.drop_column('registered_agents', 'current_day_count')
    op.drop_column('registered_agents', 'current_hour_count')
    op.drop_column('registered_agents', 'current_minute_count')
    op.drop_column('registered_agents', 'max_actions_per_day')
    op.drop_column('registered_agents', 'max_actions_per_hour')
    op.drop_column('registered_agents', 'max_actions_per_minute')
