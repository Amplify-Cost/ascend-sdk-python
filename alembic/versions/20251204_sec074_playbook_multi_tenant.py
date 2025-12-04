"""SEC-074: Multi-Tenant Isolation for Automation Playbooks

Enterprise-grade multi-tenant isolation for automation playbooks and executions.
Adds organization_id column with foreign key to organizations table.

Critical Security Fix:
- CVSS 9.1 Critical: Cross-tenant data leakage vulnerability
- automation_playbooks and playbook_executions currently lack organization isolation
- Allows Organization A to potentially access/execute Organization B's playbooks

Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312, GDPR Art. 32
Aligned with: Banking-level tenant isolation patterns (SEC-007)

Revision ID: sec074_playbook
Revises: sec068_autonomous
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'sec074_playbook'
down_revision = 'sec068_autonomous'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add organization_id to automation_playbooks and playbook_executions tables."""

    # ==========================================================================
    # SEC-074: automation_playbooks - Multi-Tenant Isolation
    # ==========================================================================

    # Add organization_id column (nullable initially for existing data)
    op.add_column(
        'automation_playbooks',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_automation_playbooks_organization',
        'automation_playbooks',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index for tenant-scoped queries (critical for performance)
    op.create_index(
        'ix_automation_playbooks_organization_id',
        'automation_playbooks',
        ['organization_id']
    )

    # Composite index for common query pattern: org + status
    op.create_index(
        'ix_automation_playbooks_org_status',
        'automation_playbooks',
        ['organization_id', 'status']
    )

    # ==========================================================================
    # SEC-074: playbook_executions - Multi-Tenant Isolation
    # ==========================================================================

    # Add organization_id column (nullable initially for existing data)
    op.add_column(
        'playbook_executions',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_playbook_executions_organization',
        'playbook_executions',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index for tenant-scoped queries
    op.create_index(
        'ix_playbook_executions_organization_id',
        'playbook_executions',
        ['organization_id']
    )

    # Composite index for common query pattern: org + execution_status
    op.create_index(
        'ix_playbook_executions_org_status',
        'playbook_executions',
        ['organization_id', 'execution_status']
    )

    # Composite index for time-based queries: org + created_at
    op.create_index(
        'ix_playbook_executions_org_time',
        'playbook_executions',
        ['organization_id', 'created_at']
    )


def downgrade() -> None:
    """Remove organization_id from automation_playbooks and playbook_executions."""

    # playbook_executions
    op.drop_index('ix_playbook_executions_org_time', table_name='playbook_executions')
    op.drop_index('ix_playbook_executions_org_status', table_name='playbook_executions')
    op.drop_index('ix_playbook_executions_organization_id', table_name='playbook_executions')
    op.drop_constraint('fk_playbook_executions_organization', 'playbook_executions', type_='foreignkey')
    op.drop_column('playbook_executions', 'organization_id')

    # automation_playbooks
    op.drop_index('ix_automation_playbooks_org_status', table_name='automation_playbooks')
    op.drop_index('ix_automation_playbooks_organization_id', table_name='automation_playbooks')
    op.drop_constraint('fk_automation_playbooks_organization', 'automation_playbooks', type_='foreignkey')
    op.drop_column('automation_playbooks', 'organization_id')
