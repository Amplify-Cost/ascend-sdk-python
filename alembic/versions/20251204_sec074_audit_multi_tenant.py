"""SEC-074: Multi-Tenant Isolation for Immutable Audit Logs

Enterprise-grade multi-tenant isolation for WORM audit log tables.
Adds organization_id column with foreign key to organizations table.

Critical Security & Compliance Fix:
- CVSS 8.5 High: Cross-tenant audit log visibility vulnerability
- immutable_audit_logs, evidence_packs, audit_integrity_checks lack organization isolation
- Allows Organization A to potentially view Organization B's audit trails and evidence

WORM Compliance Considerations:
- Hash chain integrity preserved (organization_id NOT part of content_hash calculation)
- Existing records retain NULL organization_id for backwards compatibility
- New records MUST include organization_id (enforced at application layer)
- Retention policies remain tenant-scoped

Tables Modified:
- immutable_audit_logs: WORM audit trail with hash chaining
- evidence_packs: Signed evidence packages for legal/compliance
- audit_integrity_checks: Chain integrity verification records

Compliance: SOC 2 CC6.1/AU-6, PCI-DSS 10.2/10.6, HIPAA 164.312, GDPR Art. 30, SOX 802
Aligned with: Banking-level tenant isolation patterns (SEC-007), WORM compliance

Revision ID: sec074_audit
Revises: sec074_mcp
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = 'sec074_audit'
down_revision = 'sec074_mcp'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add organization_id to immutable audit log tables.

    IMPORTANT: These columns are nullable to preserve existing audit records.
    The application layer enforces non-null for new records.
    Hash chains remain valid - organization_id is NOT part of content_hash.
    """

    # ==========================================================================
    # SEC-074: immutable_audit_logs - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'immutable_audit_logs',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_immutable_audit_logs_organization',
        'immutable_audit_logs',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='RESTRICT'  # RESTRICT: Cannot delete org with audit logs (compliance)
    )

    op.create_index(
        'ix_immutable_audit_logs_organization_id',
        'immutable_audit_logs',
        ['organization_id']
    )

    # Composite index: org + timestamp (for time-range queries)
    op.create_index(
        'ix_immutable_audit_logs_org_time',
        'immutable_audit_logs',
        ['organization_id', 'timestamp']
    )

    # Composite index: org + actor (for user activity queries)
    op.create_index(
        'ix_immutable_audit_logs_org_actor',
        'immutable_audit_logs',
        ['organization_id', 'actor_id']
    )

    # Composite index: org + event_type (for filtering by event)
    op.create_index(
        'ix_immutable_audit_logs_org_event',
        'immutable_audit_logs',
        ['organization_id', 'event_type']
    )

    # Composite index: org + risk_level (for high-risk queries)
    op.create_index(
        'ix_immutable_audit_logs_org_risk',
        'immutable_audit_logs',
        ['organization_id', 'risk_level']
    )

    # ==========================================================================
    # SEC-074: evidence_packs - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'evidence_packs',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_evidence_packs_organization',
        'evidence_packs',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='RESTRICT'  # RESTRICT: Cannot delete org with evidence packs
    )

    op.create_index(
        'ix_evidence_packs_organization_id',
        'evidence_packs',
        ['organization_id']
    )

    # Composite index: org + status (for active packs)
    op.create_index(
        'ix_evidence_packs_org_status',
        'evidence_packs',
        ['organization_id', 'status']
    )

    # Composite index: org + legal_hold (for legal compliance)
    op.create_index(
        'ix_evidence_packs_org_legal_hold',
        'evidence_packs',
        ['organization_id', 'legal_hold']
    )

    # ==========================================================================
    # SEC-074: audit_integrity_checks - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'audit_integrity_checks',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_audit_integrity_checks_organization',
        'audit_integrity_checks',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='RESTRICT'  # RESTRICT: Cannot delete org with integrity checks
    )

    op.create_index(
        'ix_audit_integrity_checks_organization_id',
        'audit_integrity_checks',
        ['organization_id']
    )

    # Composite index: org + status (for failed checks)
    op.create_index(
        'ix_audit_integrity_checks_org_status',
        'audit_integrity_checks',
        ['organization_id', 'status']
    )

    # Composite index: org + check_time (for time-based queries)
    op.create_index(
        'ix_audit_integrity_checks_org_time',
        'audit_integrity_checks',
        ['organization_id', 'check_time']
    )


def downgrade() -> None:
    """Remove organization_id from immutable audit log tables.

    WARNING: This downgrade should only be run if absolutely necessary.
    It will remove multi-tenant isolation from audit logs.
    """

    # audit_integrity_checks
    op.drop_index('ix_audit_integrity_checks_org_time', table_name='audit_integrity_checks')
    op.drop_index('ix_audit_integrity_checks_org_status', table_name='audit_integrity_checks')
    op.drop_index('ix_audit_integrity_checks_organization_id', table_name='audit_integrity_checks')
    op.drop_constraint('fk_audit_integrity_checks_organization', 'audit_integrity_checks', type_='foreignkey')
    op.drop_column('audit_integrity_checks', 'organization_id')

    # evidence_packs
    op.drop_index('ix_evidence_packs_org_legal_hold', table_name='evidence_packs')
    op.drop_index('ix_evidence_packs_org_status', table_name='evidence_packs')
    op.drop_index('ix_evidence_packs_organization_id', table_name='evidence_packs')
    op.drop_constraint('fk_evidence_packs_organization', 'evidence_packs', type_='foreignkey')
    op.drop_column('evidence_packs', 'organization_id')

    # immutable_audit_logs
    op.drop_index('ix_immutable_audit_logs_org_risk', table_name='immutable_audit_logs')
    op.drop_index('ix_immutable_audit_logs_org_event', table_name='immutable_audit_logs')
    op.drop_index('ix_immutable_audit_logs_org_actor', table_name='immutable_audit_logs')
    op.drop_index('ix_immutable_audit_logs_org_time', table_name='immutable_audit_logs')
    op.drop_index('ix_immutable_audit_logs_organization_id', table_name='immutable_audit_logs')
    op.drop_constraint('fk_immutable_audit_logs_organization', 'immutable_audit_logs', type_='foreignkey')
    op.drop_column('immutable_audit_logs', 'organization_id')
