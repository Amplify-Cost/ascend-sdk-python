"""SEC-076: Enterprise Diagnostics Audit System

Creates tables for enterprise-grade diagnostic logging aligned with
Wiz.io, Splunk CIM, and Datadog monitoring patterns.

Tables:
- diagnostic_audit_logs: Immutable audit trail for all diagnostics
- diagnostic_thresholds: Organization-specific alert thresholds

Compliance: SOC 2 CC7.2, PCI-DSS 10.2, HIPAA 164.312, NIST AU-6

Revision ID: sec076_diagnostics
Revises: sec074_merge
Create Date: 2025-12-04

Author: Ascend Engineer
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'sec076_diagnostics'
down_revision = 'sec074_merge'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    SEC-076: Create enterprise diagnostics tables.

    Implements Splunk CIM-compatible diagnostic audit logging
    with multi-tenant isolation and SIEM export support.
    """

    # Create diagnostic_audit_logs table
    op.create_table(
        'diagnostic_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),

        # Distributed tracing correlation ID
        sa.Column('correlation_id', sa.String(64), nullable=False, unique=True, index=True),

        # Multi-tenant isolation (required)
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='RESTRICT'),
                  nullable=False, index=True),

        # Diagnostic classification
        sa.Column('diagnostic_type', sa.String(50), nullable=False, index=True,
                  comment='api_health | database_status | integration_test | full_diagnostic | security_scan'),

        # Execution status
        sa.Column('status', sa.String(20), nullable=False, index=True,
                  comment='success | warning | failure | critical | timeout'),

        # Health scoring (0-100)
        sa.Column('health_score', sa.Float(), nullable=False, default=0.0,
                  comment='Composite health score 0-100'),

        # Severity classification (Splunk-compatible)
        sa.Column('severity', sa.String(20), nullable=False, default='INFO', index=True,
                  comment='INFO | WARNING | ERROR | CRITICAL | EMERGENCY'),

        # Detailed results (JSONB for flexible schema)
        sa.Column('results', JSONB(), nullable=False, server_default='{}',
                  comment='Full diagnostic results with component breakdown'),

        # Component-level health details
        sa.Column('component_details', JSONB(), nullable=True,
                  comment='Individual component statuses: {api: {score: 98, status: healthy}, ...}'),

        # AI-generated remediation suggestions
        sa.Column('remediation_suggestions', JSONB(), nullable=True,
                  comment='Actionable remediation steps: [{priority: 1, action: ..., impact: ...}, ...]'),

        # Execution metadata
        sa.Column('initiated_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, index=True),

        sa.Column('duration_ms', sa.Integer(), nullable=True,
                  comment='Execution duration in milliseconds'),

        # SIEM integration
        sa.Column('siem_export_format', sa.String(30), nullable=True,
                  comment='splunk_cim | datadog_metrics | wiz_json | generic_syslog'),

        sa.Column('siem_exported_at', sa.DateTime(), nullable=True),

        # Request context for debugging
        sa.Column('request_context', JSONB(), nullable=True,
                  comment='Source IP, user agent, request ID for tracing'),

        # Timestamps (immutable audit trail)
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('NOW()'), index=True),
    )

    # Composite indexes for efficient queries
    op.create_index(
        'ix_diagnostic_audit_org_created',
        'diagnostic_audit_logs',
        ['organization_id', 'created_at']
    )

    op.create_index(
        'ix_diagnostic_audit_severity_created',
        'diagnostic_audit_logs',
        ['severity', 'created_at']
    )

    # Create diagnostic_thresholds table
    op.create_table(
        'diagnostic_thresholds',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),

        # Multi-tenant isolation (one config per org)
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, unique=True, index=True),

        # API health thresholds
        sa.Column('api_response_time_warning_ms', sa.Integer(), default=500),
        sa.Column('api_response_time_critical_ms', sa.Integer(), default=2000),
        sa.Column('api_error_rate_warning_pct', sa.Float(), default=1.0),
        sa.Column('api_error_rate_critical_pct', sa.Float(), default=5.0),

        # Database health thresholds
        sa.Column('db_query_time_warning_ms', sa.Integer(), default=100),
        sa.Column('db_query_time_critical_ms', sa.Integer(), default=500),
        sa.Column('db_connection_pool_warning_pct', sa.Float(), default=70.0),
        sa.Column('db_connection_pool_critical_pct', sa.Float(), default=90.0),

        # Overall health score thresholds
        sa.Column('health_score_warning', sa.Float(), default=80.0),
        sa.Column('health_score_critical', sa.Float(), default=60.0),

        # Alerting configuration
        sa.Column('auto_alert_on_critical', sa.Boolean(), default=True),
        sa.Column('alert_cooldown_minutes', sa.Integer(), default=15),

        # Audit timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )

    print("SEC-076: Created diagnostic_audit_logs and diagnostic_thresholds tables")
    print("  - Splunk CIM compatible correlation IDs")
    print("  - Multi-tenant isolation with RESTRICT on delete")
    print("  - SIEM export support (Splunk, Datadog, Wiz)")
    print("  - Organization-specific threshold configuration")


def downgrade() -> None:
    """
    SEC-076: Remove enterprise diagnostics tables.

    WARNING: This will permanently delete all diagnostic audit data.
    """
    # Drop indexes first
    op.drop_index('ix_diagnostic_audit_severity_created', table_name='diagnostic_audit_logs')
    op.drop_index('ix_diagnostic_audit_org_created', table_name='diagnostic_audit_logs')

    # Drop tables
    op.drop_table('diagnostic_thresholds')
    op.drop_table('diagnostic_audit_logs')

    print("SEC-076: Dropped diagnostic_audit_logs and diagnostic_thresholds tables")
