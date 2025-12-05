"""SEC-082: Add organization_id to 8 tables for multi-tenant isolation

Tables modified:
- rules: Add organization_id (Integer, NOT NULL)
- rule_feedbacks: Add organization_id (Integer, NOT NULL)
- pending_agent_actions: Add organization_id (Integer, NOT NULL)
- integration_endpoints: Add organization_id (Integer, NOT NULL)
- cvss_assessments: Add organization_id (Integer, NOT NULL)
- system_configurations: Add organization_id (Integer, nullable for global config)
- logs: Add organization_id (Integer, nullable for system logs)
- log_audit_trails: Add organization_id (Integer, NOT NULL)

Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 7.1

Revision ID: 20251205_sec082
Revises: 20251204_sec078
Create Date: 2025-12-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251205_sec082'
down_revision = '20251204_sec078'  # Latest migration from sec078_create_mcp_sessions
branch_labels = None
depends_on = None


def upgrade():
    """
    Add organization_id to 8 tables for multi-tenant isolation.

    Strategy: Since no production data exists, DELETE existing rows
    before adding NOT NULL columns to avoid constraint violations.
    """

    # =========================================================================
    # 1. rules table - Full tenant isolation
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM rule_feedbacks")  # Must delete child records first
    op.execute("DELETE FROM rules")

    # Add organization_id column
    op.add_column('rules',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_rules_organization',
        'rules',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index for query performance
    op.create_index('ix_rules_organization_id', 'rules', ['organization_id'])

    # =========================================================================
    # 2. rule_feedbacks table - Full tenant isolation
    # =========================================================================
    # Add organization_id column (rules already deleted above)
    op.add_column('rule_feedbacks',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_rule_feedbacks_organization',
        'rule_feedbacks',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_rule_feedbacks_organization_id', 'rule_feedbacks', ['organization_id'])

    # =========================================================================
    # 3. pending_agent_actions table - Full tenant isolation
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM pending_agent_actions")

    # Add organization_id column
    op.add_column('pending_agent_actions',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_pending_agent_actions_organization',
        'pending_agent_actions',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_pending_agent_actions_organization_id', 'pending_agent_actions', ['organization_id'])

    # =========================================================================
    # 4. integration_endpoints table - Full tenant isolation
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM integration_endpoints")

    # Add organization_id column
    op.add_column('integration_endpoints',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_integration_endpoints_organization',
        'integration_endpoints',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_integration_endpoints_organization_id', 'integration_endpoints', ['organization_id'])

    # =========================================================================
    # 5. cvss_assessments table - Full tenant isolation
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM cvss_assessments")

    # Add organization_id column
    op.add_column('cvss_assessments',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_cvss_assessments_organization',
        'cvss_assessments',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_cvss_assessments_organization_id', 'cvss_assessments', ['organization_id'])

    # =========================================================================
    # 6. system_configurations table - Nullable for global config
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM system_configurations")

    # Add organization_id column (nullable for global system config)
    op.add_column('system_configurations',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_system_configurations_organization',
        'system_configurations',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_system_configurations_organization_id', 'system_configurations', ['organization_id'])

    # =========================================================================
    # 7. logs table - Nullable for system logs
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM logs")

    # Add organization_id column (nullable for system-level logs)
    op.add_column('logs',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_logs_organization',
        'logs',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_logs_organization_id', 'logs', ['organization_id'])

    # =========================================================================
    # 8. log_audit_trails table - Full tenant isolation
    # =========================================================================
    # Delete existing test data
    op.execute("DELETE FROM log_audit_trails")

    # Add organization_id column
    op.add_column('log_audit_trails',
        sa.Column('organization_id', sa.Integer(), nullable=False)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_log_audit_trails_organization',
        'log_audit_trails',
        'organizations',
        ['organization_id'],
        ['id']
    )

    # Add index
    op.create_index('ix_log_audit_trails_organization_id', 'log_audit_trails', ['organization_id'])


def downgrade():
    """
    Remove organization_id columns from all 8 tables.
    """

    # Remove in reverse order
    op.drop_index('ix_log_audit_trails_organization_id', table_name='log_audit_trails')
    op.drop_constraint('fk_log_audit_trails_organization', 'log_audit_trails', type_='foreignkey')
    op.drop_column('log_audit_trails', 'organization_id')

    op.drop_index('ix_logs_organization_id', table_name='logs')
    op.drop_constraint('fk_logs_organization', 'logs', type_='foreignkey')
    op.drop_column('logs', 'organization_id')

    op.drop_index('ix_system_configurations_organization_id', table_name='system_configurations')
    op.drop_constraint('fk_system_configurations_organization', 'system_configurations', type_='foreignkey')
    op.drop_column('system_configurations', 'organization_id')

    op.drop_index('ix_cvss_assessments_organization_id', table_name='cvss_assessments')
    op.drop_constraint('fk_cvss_assessments_organization', 'cvss_assessments', type_='foreignkey')
    op.drop_column('cvss_assessments', 'organization_id')

    op.drop_index('ix_integration_endpoints_organization_id', table_name='integration_endpoints')
    op.drop_constraint('fk_integration_endpoints_organization', 'integration_endpoints', type_='foreignkey')
    op.drop_column('integration_endpoints', 'organization_id')

    op.drop_index('ix_pending_agent_actions_organization_id', table_name='pending_agent_actions')
    op.drop_constraint('fk_pending_agent_actions_organization', 'pending_agent_actions', type_='foreignkey')
    op.drop_column('pending_agent_actions', 'organization_id')

    op.drop_index('ix_rule_feedbacks_organization_id', table_name='rule_feedbacks')
    op.drop_constraint('fk_rule_feedbacks_organization', 'rule_feedbacks', type_='foreignkey')
    op.drop_column('rule_feedbacks', 'organization_id')

    op.drop_index('ix_rules_organization_id', table_name='rules')
    op.drop_constraint('fk_rules_organization', 'rules', type_='foreignkey')
    op.drop_column('rules', 'organization_id')
