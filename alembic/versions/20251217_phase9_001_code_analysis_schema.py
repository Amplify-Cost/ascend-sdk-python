"""Phase 9: Code Analysis Schema - Option C Enterprise Pattern

Implements CrowdStrike/Palo Alto enterprise pattern:
1. global_code_patterns - Vendor-managed patterns (ASCEND maintains)
2. org_code_analysis_config - Per-org settings and thresholds
3. org_pattern_overrides - Customer can disable/modify with approval
4. org_custom_patterns - Customer can add their own patterns
5. code_pattern_audit_log - Audit trail for all changes

Key design decisions:
- NO hardcoded values in application code
- All thresholds from org_code_analysis_config
- All severity scores from org_code_analysis_config
- Patterns from database, not YAML files
- Respects RegisteredAgent.max_risk_threshold per-agent

Revision ID: phase9_001_code_analysis
Revises: byok_015_legal_waiver
Create Date: 2025-12-17

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase9_001_code_analysis'
down_revision = 'sec_110_auto_resolved'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # TABLE 1: global_code_patterns
    # ========================================================================
    # Vendor-managed patterns maintained by ASCEND (like CrowdStrike signatures)
    # No organization_id - these are global to all tenants
    op.create_table(
        'global_code_patterns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('pattern_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('language', sa.String(20), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('pattern_type', sa.String(20), nullable=False, server_default='regex'),
        sa.Column('pattern_value', sa.Text(), nullable=False),
        sa.Column('pattern_flags', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('cwe_ids', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('mitre_techniques', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('cvss_base_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('cvss_vector', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for common query patterns
    op.create_index('ix_global_code_patterns_language_active', 'global_code_patterns',
                    ['language', 'is_active'])
    op.create_index('ix_global_code_patterns_severity_active', 'global_code_patterns',
                    ['severity', 'is_active'])

    # ========================================================================
    # TABLE 2: org_code_analysis_config
    # ========================================================================
    # Per-organization configuration - NO HARDCODED VALUES
    # All thresholds and severity scores come from here
    op.create_table(
        'org_code_analysis_config',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  unique=True, nullable=False, index=True),

        # Feature toggles
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('mode', sa.String(20), server_default='enforce', nullable=False),  # enforce, monitor, off

        # Per-org severity scores (NOT HARDCODED)
        sa.Column('severity_scores', postgresql.JSONB(), server_default='{"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}'),

        # Per-org thresholds (NOT HARDCODED)
        sa.Column('block_threshold', sa.Integer(), server_default='90', nullable=False),
        sa.Column('escalate_threshold', sa.Integer(), server_default='70', nullable=False),
        sa.Column('alert_threshold', sa.Integer(), server_default='50', nullable=False),

        # CVSS threshold for auto-block
        sa.Column('cvss_block_threshold', sa.Numeric(3, 1), server_default='9.0'),

        # Languages to analyze (empty = all)
        sa.Column('enabled_languages', postgresql.ARRAY(sa.String(20)), server_default='{}'),

        # Categories to analyze (empty = all)
        sa.Column('enabled_categories', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Globally disabled patterns for this org
        sa.Column('disabled_pattern_ids', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Notification settings
        sa.Column('notify_on_block', sa.Boolean(), server_default='true'),
        sa.Column('notify_on_critical', sa.Boolean(), server_default='true'),
        sa.Column('notification_emails', postgresql.ARRAY(sa.String(255)), server_default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # ========================================================================
    # TABLE 3: org_pattern_overrides
    # ========================================================================
    # Customer can disable/modify global patterns for their org
    # Requires approval trail for compliance
    op.create_table(
        'org_pattern_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('pattern_id', sa.String(50), nullable=False, index=True),  # References global_code_patterns.pattern_id

        # Override options
        sa.Column('is_disabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('severity_override', sa.String(20), nullable=True),  # Override global severity
        sa.Column('risk_score_override', sa.Integer(), nullable=True),  # Override calculated risk score

        # Approval trail (required for SOC 2)
        sa.Column('modified_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('modification_reason', sa.Text(), nullable=False),  # Required justification
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_required', sa.Boolean(), server_default='false'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Unique constraint: one override per org per pattern
        sa.UniqueConstraint('organization_id', 'pattern_id', name='uq_org_pattern_override'),
    )

    # ========================================================================
    # TABLE 4: org_custom_patterns
    # ========================================================================
    # Customer can add their own patterns for org-specific risks
    op.create_table(
        'org_custom_patterns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('pattern_id', sa.String(50), nullable=False),  # Customer-defined ID
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('pattern_type', sa.String(20), server_default='regex', nullable=False),
        sa.Column('pattern_value', sa.Text(), nullable=False),
        sa.Column('pattern_flags', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('cwe_ids', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('mitre_techniques', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('cvss_base_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),

        # Creator info
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Unique constraint: pattern_id unique per org
        sa.UniqueConstraint('organization_id', 'pattern_id', name='uq_org_custom_pattern'),
    )

    # ========================================================================
    # TABLE 5: code_pattern_audit_log
    # ========================================================================
    # Immutable audit trail for all pattern changes (SOC 2 requirement)
    op.create_table(
        'code_pattern_audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='SET NULL'),
                  nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),  # Denormalized for audit trail

        # What changed
        sa.Column('action', sa.String(50), nullable=False, index=True),  # created, updated, deleted, disabled, enabled
        sa.Column('resource_type', sa.String(50), nullable=False),  # global_pattern, org_config, org_override, org_custom
        sa.Column('resource_id', sa.String(100), nullable=False),  # pattern_id or config id

        # Change details
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),

        # Request context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),

        # Timestamp (immutable)
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for audit queries
    op.create_index('ix_code_pattern_audit_log_org_created', 'code_pattern_audit_log',
                    ['organization_id', 'created_at'])
    op.create_index('ix_code_pattern_audit_log_action_resource', 'code_pattern_audit_log',
                    ['action', 'resource_type'])


def downgrade():
    op.drop_table('code_pattern_audit_log')
    op.drop_table('org_custom_patterns')
    op.drop_table('org_pattern_overrides')
    op.drop_table('org_code_analysis_config')
    op.drop_table('global_code_patterns')
