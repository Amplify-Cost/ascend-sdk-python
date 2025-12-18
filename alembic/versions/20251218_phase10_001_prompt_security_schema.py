"""Phase 10: Prompt Security Schema

Creates 6 tables for enterprise-grade prompt injection detection
and LLM-to-LLM governance:

1. global_prompt_patterns - Vendor-managed patterns
2. org_prompt_security_config - Per-org configuration
3. org_prompt_pattern_overrides - Customer overrides
4. org_custom_prompt_patterns - Customer custom patterns
5. prompt_security_audit_log - Immutable audit trail
6. llm_chain_audit_log - LLM-to-LLM tracking

Revision ID: phase10_prompt_security_schema
Revises: deep002_python_patterns
Create Date: 2025-12-18

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10, OWASP LLM Top 10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase10_prompt_security_schema'
down_revision = 'deep002_python_patterns'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # TABLE 1: global_prompt_patterns
    # ========================================================================
    op.create_table(
        'global_prompt_patterns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pattern_id', sa.String(50), nullable=False),

        # Classification
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('attack_vector', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),

        # Pattern definition
        sa.Column('pattern_type', sa.String(20), nullable=False, server_default='regex'),
        sa.Column('pattern_value', sa.Text(), nullable=False),
        sa.Column('pattern_flags', sa.String(50), nullable=True),
        sa.Column('applies_to', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Documentation
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('example_attack', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),

        # Compliance mappings
        sa.Column('cwe_ids', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('mitre_techniques', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('nist_controls', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('owasp_llm_top10', postgresql.ARRAY(sa.String(20)), server_default='{}'),

        # CVSS scoring
        sa.Column('cvss_base_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('cvss_vector', sa.String(100), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pattern_id', name='uq_global_prompt_pattern_id')
    )

    # Indexes for global_prompt_patterns
    op.create_index('ix_global_prompt_patterns_pattern_id', 'global_prompt_patterns', ['pattern_id'])
    op.create_index('ix_global_prompt_patterns_category', 'global_prompt_patterns', ['category'])
    op.create_index('ix_global_prompt_patterns_severity', 'global_prompt_patterns', ['severity'])
    op.create_index('ix_global_prompt_patterns_active', 'global_prompt_patterns', ['is_active'])

    # ========================================================================
    # TABLE 2: org_prompt_security_config
    # ========================================================================
    op.create_table(
        'org_prompt_security_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Feature toggles
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mode', sa.String(20), nullable=False, server_default='monitor'),

        # Severity scores (NOT HARDCODED)
        sa.Column('severity_scores', postgresql.JSONB(),
                  server_default='{"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}'),

        # Thresholds
        sa.Column('block_threshold', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('escalate_threshold', sa.Integer(), nullable=False, server_default='70'),
        sa.Column('alert_threshold', sa.Integer(), nullable=False, server_default='50'),

        # Scan settings
        sa.Column('scan_system_prompts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scan_user_prompts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scan_agent_responses', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scan_llm_to_llm', sa.Boolean(), nullable=False, server_default='true'),

        # Encoding detection
        sa.Column('detect_base64', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('detect_unicode_smuggling', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('detect_html_entities', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_decode_depth', sa.Integer(), nullable=False, server_default='3'),

        # LLM-to-LLM governance
        sa.Column('llm_chain_depth_limit', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('require_chain_approval', sa.Boolean(), nullable=False, server_default='false'),

        # Filtering
        sa.Column('enabled_categories', postgresql.ARRAY(sa.String(50)), server_default='{}'),
        sa.Column('disabled_pattern_ids', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Notifications
        sa.Column('notify_on_block', sa.Boolean(), server_default='true'),
        sa.Column('notify_on_critical', sa.Boolean(), server_default='true'),
        sa.Column('notification_emails', postgresql.ARRAY(sa.String(255)), server_default='{}'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', name='uq_org_prompt_security_config')
    )

    op.create_index('ix_org_prompt_security_config_org', 'org_prompt_security_config', ['organization_id'])

    # ========================================================================
    # TABLE 3: org_prompt_pattern_overrides
    # ========================================================================
    op.create_table(
        'org_prompt_pattern_overrides',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.String(50), nullable=False),

        # Override options
        sa.Column('is_disabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('severity_override', sa.String(20), nullable=True),
        sa.Column('risk_score_override', sa.Integer(), nullable=True),

        # Approval trail
        sa.Column('modified_by', sa.Integer(), nullable=False),
        sa.Column('modification_reason', sa.Text(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'pattern_id', name='uq_org_prompt_pattern_override')
    )

    op.create_index('ix_org_prompt_pattern_overrides_org', 'org_prompt_pattern_overrides', ['organization_id'])
    op.create_index('ix_org_prompt_pattern_overrides_pattern', 'org_prompt_pattern_overrides', ['pattern_id'])

    # ========================================================================
    # TABLE 4: org_custom_prompt_patterns
    # ========================================================================
    op.create_table(
        'org_custom_prompt_patterns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.String(50), nullable=False),

        # Classification
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('attack_vector', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),

        # Pattern definition
        sa.Column('pattern_type', sa.String(20), nullable=False, server_default='regex'),
        sa.Column('pattern_value', sa.Text(), nullable=False),
        sa.Column('pattern_flags', sa.String(50), nullable=True),
        sa.Column('applies_to', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Documentation
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),

        # Compliance mappings
        sa.Column('cwe_ids', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('mitre_techniques', postgresql.ARRAY(sa.String(20)), server_default='{}'),
        sa.Column('cvss_base_score', sa.Numeric(3, 1), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Creator info
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'pattern_id', name='uq_org_custom_prompt_pattern')
    )

    op.create_index('ix_org_custom_prompt_patterns_org', 'org_custom_prompt_patterns', ['organization_id'])

    # ========================================================================
    # TABLE 5: prompt_security_audit_log
    # ========================================================================
    op.create_table(
        'prompt_security_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),

        # What happened
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=False),

        # Detection event fields
        sa.Column('agent_action_id', sa.Integer(), nullable=True),
        sa.Column('prompt_type', sa.String(50), nullable=True),
        sa.Column('detected_patterns', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('blocked', sa.Boolean(), nullable=True),

        # Change details
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),

        # Request context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )

    op.create_index('ix_prompt_security_audit_org', 'prompt_security_audit_log', ['organization_id'])
    op.create_index('ix_prompt_security_audit_action', 'prompt_security_audit_log', ['action'])
    op.create_index('ix_prompt_audit_org_action', 'prompt_security_audit_log', ['organization_id', 'action'])
    op.create_index('ix_prompt_audit_created', 'prompt_security_audit_log', ['created_at'])

    # ========================================================================
    # TABLE 6: llm_chain_audit_log
    # ========================================================================
    op.create_table(
        'llm_chain_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Chain identification
        sa.Column('chain_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_chain_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='1'),

        # Source agent
        sa.Column('source_agent_id', sa.String(255), nullable=False),
        sa.Column('source_action_id', sa.Integer(), nullable=True),

        # Target agent
        sa.Column('target_agent_id', sa.String(255), nullable=False),
        sa.Column('target_action_id', sa.Integer(), nullable=True),

        # Content hashes (privacy)
        sa.Column('prompt_content_hash', sa.String(64), nullable=False),
        sa.Column('prompt_length', sa.Integer(), nullable=True),
        sa.Column('response_content_hash', sa.String(64), nullable=True),
        sa.Column('response_length', sa.Integer(), nullable=True),

        # Security analysis
        sa.Column('injection_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('patterns_matched', postgresql.ARRAY(sa.String(50)), server_default='{}'),

        # Governance decision
        sa.Column('status', sa.String(50), nullable=False, server_default="'allowed'"),
        sa.Column('block_reason', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('chain_id', name='uq_llm_chain_id')
    )

    op.create_index('ix_llm_chain_org', 'llm_chain_audit_log', ['organization_id'])
    op.create_index('ix_llm_chain_parent', 'llm_chain_audit_log', ['parent_chain_id'])
    op.create_index('ix_llm_chain_org_status', 'llm_chain_audit_log', ['organization_id', 'status'])
    op.create_index('ix_llm_chain_source', 'llm_chain_audit_log', ['source_agent_id', 'created_at'])
    op.create_index('ix_llm_chain_target', 'llm_chain_audit_log', ['target_agent_id', 'created_at'])

    # ========================================================================
    # Seed default configs for existing organizations
    # ========================================================================
    op.execute("""
        INSERT INTO org_prompt_security_config (organization_id, enabled, mode)
        SELECT id, true, 'monitor'
        FROM organizations
        WHERE NOT EXISTS (
            SELECT 1 FROM org_prompt_security_config
            WHERE org_prompt_security_config.organization_id = organizations.id
        );
    """)


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('llm_chain_audit_log')
    op.drop_table('prompt_security_audit_log')
    op.drop_table('org_custom_prompt_patterns')
    op.drop_table('org_prompt_pattern_overrides')
    op.drop_table('org_prompt_security_config')
    op.drop_table('global_prompt_patterns')
