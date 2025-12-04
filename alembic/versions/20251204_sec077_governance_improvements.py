"""
SEC-077: Enterprise Governance Improvements
- Circuit breaker state for MCP servers
- Session expiration tracking
- Anomaly detection rolling statistics
- Policy priority indexes

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 7.1, GDPR Art. 5
Aligned with: Splunk CIM, Datadog metrics, Wiz.io patterns

Revision ID: sec077_governance
Revises: 20251204_sec076_diagnostics
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'sec077_governance'
down_revision = 'sec076_diagnostics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add enterprise governance improvement columns and indexes.
    All changes are backward compatible (nullable or have defaults).
    """

    # =========================================================================
    # CIRCUIT BREAKER FOR MCP SERVERS (SOC 2 CC7.1, NIST SI-4)
    # =========================================================================
    # Pattern: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    # Prevents cascade failures, enables auto-recovery

    op.add_column('mcp_servers', sa.Column(
        'circuit_state', sa.String(20), nullable=False, server_default='CLOSED',
        comment='Circuit breaker state: CLOSED (healthy), OPEN (blocked), HALF_OPEN (testing)'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_failure_count', sa.Integer(), nullable=False, server_default='0',
        comment='Consecutive failures since last success'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_failure_threshold', sa.Integer(), nullable=False, server_default='5',
        comment='Failures needed to trip circuit open'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_last_failure_at', sa.DateTime(), nullable=True,
        comment='Timestamp of most recent failure'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_opened_at', sa.DateTime(), nullable=True,
        comment='When circuit breaker tripped to OPEN'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_recovery_timeout_seconds', sa.Integer(), nullable=False, server_default='300',
        comment='Seconds before attempting recovery (default 5 min)'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_half_open_success_count', sa.Integer(), nullable=False, server_default='0',
        comment='Successful probes in HALF_OPEN state'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_required_successes', sa.Integer(), nullable=False, server_default='2',
        comment='Successes needed in HALF_OPEN to close circuit'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_last_state_change', sa.DateTime(), nullable=True,
        comment='Timestamp of last state transition'
    ))
    op.add_column('mcp_servers', sa.Column(
        'circuit_total_trips', sa.Integer(), nullable=False, server_default='0',
        comment='Total times circuit has tripped (metrics)'
    ))

    # Circuit breaker index for monitoring queries
    op.create_index(
        'ix_mcp_servers_circuit_state',
        'mcp_servers',
        ['circuit_state', 'organization_id'],
        unique=False
    )

    # =========================================================================
    # SESSION EXPIRATION TRACKING (GDPR Art. 5, NIST IA-4)
    # =========================================================================
    # Enhanced session lifecycle management for compliance

    op.add_column('mcp_sessions', sa.Column(
        'expiration_reason', sa.String(50), nullable=True,
        comment='Why session expired: timeout, manual_logout, security_revoked, admin_terminated'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'auto_renewal_enabled', sa.Boolean(), nullable=False, server_default='false',
        comment='Whether session auto-renews before expiration'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'renewal_count', sa.Integer(), nullable=False, server_default='0',
        comment='Number of times session has been renewed'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'max_renewals', sa.Integer(), nullable=False, server_default='5',
        comment='Maximum allowed renewals before forced expiration'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'last_renewed_at', sa.DateTime(), nullable=True,
        comment='Timestamp of last renewal'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'cleanup_status', sa.String(20), nullable=False, server_default='active',
        comment='Cleanup state: active, pending_cleanup, cleaned'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'cleaned_at', sa.DateTime(), nullable=True,
        comment='When session was cleaned by background job'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'security_flags', postgresql.JSONB(), nullable=True,
        comment='Security-related flags: anomaly_detected, compliance_violation, etc.'
    ))
    op.add_column('mcp_sessions', sa.Column(
        'termination_source', sa.String(50), nullable=True,
        comment='Who terminated: system, admin, user, security_policy'
    ))

    # Session cleanup index for background job efficiency
    op.create_index(
        'ix_mcp_sessions_cleanup',
        'mcp_sessions',
        ['cleanup_status', 'expires_at'],
        unique=False
    )
    op.create_index(
        'ix_mcp_sessions_expiration',
        'mcp_sessions',
        ['status', 'expires_at', 'organization_id'],
        unique=False
    )

    # =========================================================================
    # ANOMALY DETECTION ROLLING STATISTICS (SOC 2 CC7.1, NIST SI-4)
    # =========================================================================
    # Z-score based anomaly detection with rolling windows

    op.add_column('registered_agents', sa.Column(
        'rolling_avg_actions_1h', sa.Float(), nullable=True,
        comment='Exponential moving average of actions per hour (1h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_avg_actions_24h', sa.Float(), nullable=True,
        comment='Simple moving average of actions per hour (24h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_std_actions', sa.Float(), nullable=True,
        comment='Standard deviation of actions per hour'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_avg_error_rate_1h', sa.Float(), nullable=True,
        comment='EMA of error rate (1h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_avg_error_rate_24h', sa.Float(), nullable=True,
        comment='SMA of error rate (24h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_std_error_rate', sa.Float(), nullable=True,
        comment='Standard deviation of error rate'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_avg_risk_1h', sa.Float(), nullable=True,
        comment='EMA of risk score (1h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_avg_risk_24h', sa.Float(), nullable=True,
        comment='SMA of risk score (24h window)'
    ))
    op.add_column('registered_agents', sa.Column(
        'rolling_std_risk', sa.Float(), nullable=True,
        comment='Standard deviation of risk score'
    ))
    op.add_column('registered_agents', sa.Column(
        'anomaly_algorithm', sa.String(30), nullable=False, server_default='zscore',
        comment='Detection algorithm: zscore, iqr, mad, isolation_forest'
    ))
    op.add_column('registered_agents', sa.Column(
        'anomaly_sensitivity', sa.Float(), nullable=False, server_default='2.0',
        comment='Z-score threshold for anomaly (default 2 std devs)'
    ))
    op.add_column('registered_agents', sa.Column(
        'last_baseline_update', sa.DateTime(), nullable=True,
        comment='When baseline statistics were last recalculated'
    ))
    op.add_column('registered_agents', sa.Column(
        'baseline_window_hours', sa.Integer(), nullable=False, server_default='168',
        comment='Hours of data for baseline calculation (default 1 week)'
    ))
    op.add_column('registered_agents', sa.Column(
        'consecutive_anomalies', sa.Integer(), nullable=False, server_default='0',
        comment='Consecutive anomaly detections (for escalation)'
    ))
    op.add_column('registered_agents', sa.Column(
        'anomaly_escalation_threshold', sa.Integer(), nullable=False, server_default='3',
        comment='Consecutive anomalies before escalation'
    ))
    op.add_column('registered_agents', sa.Column(
        'last_anomaly_severity', sa.String(20), nullable=True,
        comment='Severity of last anomaly: low, medium, high, critical'
    ))
    op.add_column('registered_agents', sa.Column(
        'anomaly_auto_suspend', sa.Boolean(), nullable=False, server_default='false',
        comment='Auto-suspend agent on critical anomaly'
    ))

    # Anomaly detection index for monitoring
    op.create_index(
        'ix_agents_anomaly_status',
        'registered_agents',
        ['anomaly_detection_enabled', 'consecutive_anomalies', 'organization_id'],
        unique=False
    )

    # =========================================================================
    # POLICY PRIORITY INDEXES (PCI-DSS 7.1, NIST AC-3)
    # =========================================================================
    # Optimize policy evaluation with priority-based ordering

    # MCP Policy priority index for fast evaluation
    op.create_index(
        'ix_mcp_policies_priority_active',
        'mcp_policies',
        ['organization_id', 'priority', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # Agent Policy priority index
    op.create_index(
        'ix_agent_policies_priority_active',
        'agent_policies',
        ['organization_id', 'priority', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # =========================================================================
    # POLICY CONFLICT DETECTION TABLE
    # =========================================================================
    # Track detected conflicts for audit and resolution

    op.create_table(
        'policy_conflicts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False,
            comment='Type: priority_tie, effect_contradiction, resource_overlap'),
        sa.Column('policy_a_id', sa.String(100), nullable=False),
        sa.Column('policy_a_type', sa.String(30), nullable=False, comment='mcp_policy or agent_policy'),
        sa.Column('policy_b_id', sa.String(100), nullable=False),
        sa.Column('policy_b_type', sa.String(30), nullable=False),
        sa.Column('conflict_details', postgresql.JSONB(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, comment='low, medium, high, critical'),
        sa.Column('resolution_status', sa.String(30), nullable=False, server_default='pending',
            comment='pending, auto_resolved, manually_resolved, ignored'),
        sa.Column('resolution_strategy', sa.String(50), nullable=True,
            comment='first_match, highest_priority, most_restrictive'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),

        sa.Index('ix_policy_conflicts_org_status', 'organization_id', 'resolution_status'),
        sa.Index('ix_policy_conflicts_severity', 'severity', 'detected_at'),
    )

    # =========================================================================
    # CIRCUIT BREAKER AUDIT LOG
    # =========================================================================
    # Immutable log of all circuit state transitions

    op.create_table(
        'circuit_breaker_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('server_id', sa.String(100), nullable=False),
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('previous_state', sa.String(20), nullable=False),
        sa.Column('new_state', sa.String(20), nullable=False),
        sa.Column('trigger_reason', sa.String(100), nullable=False,
            comment='failure_threshold, recovery_timeout, manual_reset, successful_probe'),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(64), nullable=True, comment='Splunk CIM correlation'),

        sa.Index('ix_circuit_events_server', 'server_id', 'event_time'),
        sa.Index('ix_circuit_events_org', 'organization_id', 'event_time'),
    )


def downgrade() -> None:
    """
    Remove all SEC-077 additions.
    Safe rollback - no data loss from original schema.
    """

    # Drop new tables
    op.drop_table('circuit_breaker_events')
    op.drop_table('policy_conflicts')

    # Drop indexes
    op.drop_index('ix_agent_policies_priority_active', table_name='agent_policies')
    op.drop_index('ix_mcp_policies_priority_active', table_name='mcp_policies')
    op.drop_index('ix_agents_anomaly_status', table_name='registered_agents')
    op.drop_index('ix_mcp_sessions_expiration', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_cleanup', table_name='mcp_sessions')
    op.drop_index('ix_mcp_servers_circuit_state', table_name='mcp_servers')

    # Drop anomaly detection columns
    op.drop_column('registered_agents', 'anomaly_auto_suspend')
    op.drop_column('registered_agents', 'last_anomaly_severity')
    op.drop_column('registered_agents', 'anomaly_escalation_threshold')
    op.drop_column('registered_agents', 'consecutive_anomalies')
    op.drop_column('registered_agents', 'baseline_window_hours')
    op.drop_column('registered_agents', 'last_baseline_update')
    op.drop_column('registered_agents', 'anomaly_sensitivity')
    op.drop_column('registered_agents', 'anomaly_algorithm')
    op.drop_column('registered_agents', 'rolling_std_risk')
    op.drop_column('registered_agents', 'rolling_avg_risk_24h')
    op.drop_column('registered_agents', 'rolling_avg_risk_1h')
    op.drop_column('registered_agents', 'rolling_std_error_rate')
    op.drop_column('registered_agents', 'rolling_avg_error_rate_24h')
    op.drop_column('registered_agents', 'rolling_avg_error_rate_1h')
    op.drop_column('registered_agents', 'rolling_std_actions')
    op.drop_column('registered_agents', 'rolling_avg_actions_24h')
    op.drop_column('registered_agents', 'rolling_avg_actions_1h')

    # Drop session tracking columns
    op.drop_column('mcp_sessions', 'termination_source')
    op.drop_column('mcp_sessions', 'security_flags')
    op.drop_column('mcp_sessions', 'cleaned_at')
    op.drop_column('mcp_sessions', 'cleanup_status')
    op.drop_column('mcp_sessions', 'last_renewed_at')
    op.drop_column('mcp_sessions', 'max_renewals')
    op.drop_column('mcp_sessions', 'renewal_count')
    op.drop_column('mcp_sessions', 'auto_renewal_enabled')
    op.drop_column('mcp_sessions', 'expiration_reason')

    # Drop circuit breaker columns
    op.drop_column('mcp_servers', 'circuit_total_trips')
    op.drop_column('mcp_servers', 'circuit_last_state_change')
    op.drop_column('mcp_servers', 'circuit_required_successes')
    op.drop_column('mcp_servers', 'circuit_half_open_success_count')
    op.drop_column('mcp_servers', 'circuit_recovery_timeout_seconds')
    op.drop_column('mcp_servers', 'circuit_opened_at')
    op.drop_column('mcp_servers', 'circuit_last_failure_at')
    op.drop_column('mcp_servers', 'circuit_failure_threshold')
    op.drop_column('mcp_servers', 'circuit_failure_count')
    op.drop_column('mcp_servers', 'circuit_state')
