"""SEC-066: Enterprise Metric Calculation Audit System

Creates the metric_calculation_audit table for SOC 2 compliant
audit trail of all metric calculations.

Compliance:
- SOC 2 AU-6: Audit record review
- SOC 2 AU-7: Audit reduction and report generation
- SOC 2 PI-1: Processing Integrity
- NIST 800-53 AU-6: Audit Review, Analysis, Reporting
- PCI-DSS 10.2: Implement audit trails

Revision ID: sec066_metric_audit
Revises: sec065_exec_briefs
Create Date: 2025-12-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'sec066_metric_audit'
down_revision = 'sec065_exec_briefs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # CREATE METRIC_CALCULATION_AUDIT TABLE
    # Banking-level security with multi-tenant isolation
    # ==========================================================================
    op.create_table(
        'metric_calculation_audit',

        # Primary Key
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),

        # Multi-tenant isolation
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),

        # Calculation identification
        sa.Column('calculation_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('calculation_type', sa.String(50), nullable=False, default='unified_metrics'),

        # Timing
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_hours', sa.Integer(), nullable=False),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),

        # Input tracking (for reproducibility)
        sa.Column('input_data_hash', sa.String(64), nullable=False),
        sa.Column('config_snapshot', postgresql.JSONB(), nullable=False, default={}),

        # Results
        sa.Column('metrics_snapshot', postgresql.JSONB(), nullable=False),

        # Version tracking
        sa.Column('engine_version', sa.String(20), nullable=False),
        sa.Column('cim_version', sa.String(20), nullable=False),

        # Audit metadata
        sa.Column('triggered_by', sa.String(100), nullable=False, default='system'),
        sa.Column('trigger_source', sa.String(50), nullable=False, default='api'),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True),

        # Validation results
        sa.Column('validation_passed', sa.Boolean(), nullable=False, default=True),
        sa.Column('validation_warnings', postgresql.JSONB(), default=[]),
    )

    # ==========================================================================
    # CREATE COMPOSITE INDEXES FOR PERFORMANCE
    # ==========================================================================

    # Fast lookup: Get calculations for org by time (most common audit query)
    op.create_index(
        'ix_metric_audit_org_time',
        'metric_calculation_audit',
        ['organization_id', 'calculated_at']
    )

    # Audit: Find calculations by type
    op.create_index(
        'ix_metric_audit_org_type',
        'metric_calculation_audit',
        ['organization_id', 'calculation_type']
    )

    # Reproducibility: Find by input hash
    op.create_index(
        'ix_metric_audit_input_hash',
        'metric_calculation_audit',
        ['input_data_hash']
    )

    # ==========================================================================
    # CREATE ORG_METRIC_CONFIGS TABLE
    # Organization-specific metric configuration
    # ==========================================================================
    op.create_table(
        'org_metric_configs',

        # Primary Key
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),

        # Multi-tenant isolation (unique per org)
        sa.Column('organization_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, unique=True, index=True),

        # Financial configuration
        sa.Column('cost_per_incident_usd', sa.Float(), nullable=False, default=50000.0),
        sa.Column('hourly_analyst_rate_usd', sa.Float(), nullable=False, default=75.0),

        # Time configuration
        sa.Column('default_analysis_period_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('sla_critical_minutes', sa.Integer(), nullable=False, default=15),
        sa.Column('sla_high_minutes', sa.Integer(), nullable=False, default=30),
        sa.Column('sla_medium_minutes', sa.Integer(), nullable=False, default=60),
        sa.Column('sla_low_minutes', sa.Integer(), nullable=False, default=120),

        # Feature flags
        sa.Column('include_dismissed_in_accuracy', sa.Boolean(), nullable=False, default=False),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )

    # ==========================================================================
    # LOG MIGRATION
    # ==========================================================================
    print("SEC-066: Created metric audit and configuration tables")
    print("  - metric_calculation_audit: SOC 2 AU-6 compliant audit trail")
    print("  - org_metric_configs: Per-organization metric settings")
    print("  - Composite indexes for <100ms query performance")


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_metric_audit_input_hash', table_name='metric_calculation_audit')
    op.drop_index('ix_metric_audit_org_type', table_name='metric_calculation_audit')
    op.drop_index('ix_metric_audit_org_time', table_name='metric_calculation_audit')

    # Drop tables
    op.drop_table('org_metric_configs')
    op.drop_table('metric_calculation_audit')

    print("SEC-066: Dropped metric audit tables")
