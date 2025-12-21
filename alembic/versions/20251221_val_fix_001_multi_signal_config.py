"""VAL-FIX-001: Add Multi-Signal Configuration to Prompt Security

Adds per-organization configuration for multi-signal prompt security scoring.
This reduces false positives on business terminology while maintaining
security for actual injection attempts.

New columns in org_prompt_security_config:
- multi_signal_required: Require 2+ pattern matches for HIGH risk
- single_pattern_max_risk: Max risk score when only 1 pattern matches
- business_context_filter: Enable business terminology pre-filter
- critical_patterns_always_block: Critical patterns bypass multi-signal

Revision ID: val_fix_001_multi_signal
Revises: phase10_seed_prompt_patterns
Create Date: 2025-12-21

Compliance: SOC 2 CC6.1, OWASP LLM01, CWE-77
Rationale: Reduce false positives from 2/5 to 0/5 on clean business prompts
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'val_fix_001_multi_signal'
down_revision = 'phase10_seed_prompt_patterns'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # VAL-FIX-001: Add Multi-Signal Configuration Columns
    # =========================================================================
    # These columns allow per-org tuning of prompt security sensitivity.
    # Banks and regulated industries can adjust thresholds without code changes.
    # =========================================================================

    # Check if columns already exist (idempotent migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('org_prompt_security_config')]

    # Add multi_signal_required column
    if 'multi_signal_required' not in existing_columns:
        op.add_column(
            'org_prompt_security_config',
            sa.Column(
                'multi_signal_required',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true'),
                comment='VAL-FIX-001: Require 2+ pattern matches for HIGH risk (>=80). '
                        'Reduces false positives on business terminology.'
            )
        )

    # Add single_pattern_max_risk column
    if 'single_pattern_max_risk' not in existing_columns:
        op.add_column(
            'org_prompt_security_config',
            sa.Column(
                'single_pattern_max_risk',
                sa.Integer(),
                nullable=False,
                server_default=sa.text('70'),
                comment='VAL-FIX-001: Maximum risk score when only 1 pattern matches '
                        '(if multi_signal_required=True). Default 70 = MEDIUM tier.'
            )
        )

    # Add business_context_filter column
    if 'business_context_filter' not in existing_columns:
        op.add_column(
            'org_prompt_security_config',
            sa.Column(
                'business_context_filter',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true'),
                comment='VAL-FIX-001: Enable pre-filter for common business terminology '
                        'to reduce false positives on reports, analytics, etc.'
            )
        )

    # Add critical_patterns_always_block column
    if 'critical_patterns_always_block' not in existing_columns:
        op.add_column(
            'org_prompt_security_config',
            sa.Column(
                'critical_patterns_always_block',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true'),
                comment='VAL-FIX-001: Critical injection patterns (PROMPT-001, 004, etc.) '
                        'always use full risk score regardless of multi-signal settings. '
                        'WARNING: Setting to False significantly reduces security.'
            )
        )

    # =========================================================================
    # Add check constraints for valid ranges
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_single_pattern_max_risk_range'
            ) THEN
                ALTER TABLE org_prompt_security_config
                ADD CONSTRAINT chk_single_pattern_max_risk_range
                CHECK (single_pattern_max_risk >= 0 AND single_pattern_max_risk <= 100);
            END IF;
        END $$;
    """)

    # =========================================================================
    # Create audit trigger for config changes
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_prompt_security_config_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO prompt_security_audit_log (
                organization_id,
                action,
                resource_type,
                resource_id,
                old_value,
                new_value,
                change_reason,
                created_at
            ) VALUES (
                NEW.organization_id,
                CASE
                    WHEN TG_OP = 'INSERT' THEN 'created'
                    WHEN TG_OP = 'UPDATE' THEN 'updated'
                    ELSE 'unknown'
                END,
                'org_config',
                NEW.id::text,
                CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END,
                row_to_json(NEW),
                'VAL-FIX-001: Multi-signal config change',
                NOW()
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_audit_prompt_security_config ON org_prompt_security_config;

        CREATE TRIGGER trg_audit_prompt_security_config
            AFTER INSERT OR UPDATE ON org_prompt_security_config
            FOR EACH ROW
            EXECUTE FUNCTION audit_prompt_security_config_changes();
    """)

    # =========================================================================
    # Add index for faster lookups
    # =========================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_org_prompt_config_multi_signal
        ON org_prompt_security_config (organization_id, multi_signal_required);
    """)


def downgrade():
    # Remove index
    op.execute("DROP INDEX IF EXISTS idx_org_prompt_config_multi_signal;")

    # Remove trigger
    op.execute("DROP TRIGGER IF EXISTS trg_audit_prompt_security_config ON org_prompt_security_config;")
    op.execute("DROP FUNCTION IF EXISTS audit_prompt_security_config_changes();")

    # Remove constraint
    op.execute("""
        ALTER TABLE org_prompt_security_config
        DROP CONSTRAINT IF EXISTS chk_single_pattern_max_risk_range;
    """)

    # Remove columns (in reverse order)
    op.drop_column('org_prompt_security_config', 'critical_patterns_always_block')
    op.drop_column('org_prompt_security_config', 'business_context_filter')
    op.drop_column('org_prompt_security_config', 'single_pattern_max_risk')
    op.drop_column('org_prompt_security_config', 'multi_signal_required')
