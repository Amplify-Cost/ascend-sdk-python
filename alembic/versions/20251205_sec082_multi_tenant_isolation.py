"""SEC-082: Add organization_id to tables for multi-tenant isolation

Tables to be modified (IF EXISTS):
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
Revises: sec078_mcp_sessions
Create Date: 2025-12-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20251205_sec082'
down_revision = 'sec078_mcp_sessions'
branch_labels = None
depends_on = None


def table_exists(connection, table_name):
    """Check if a table exists in the database."""
    result = connection.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name)"
    ), {"table_name": table_name})
    return result.scalar()


def column_exists(connection, table_name, column_name):
    """Check if a column exists in a table."""
    result = connection.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = :table_name AND column_name = :column_name)"
    ), {"table_name": table_name, "column_name": column_name})
    return result.scalar()


def upgrade():
    """
    Add organization_id to tables for multi-tenant isolation.

    Strategy: Only modify tables that exist, skip those that don't.
    Since no production data exists, DELETE existing rows before adding NOT NULL columns.
    """
    connection = op.get_bind()

    # Tables with NOT NULL organization_id
    required_tables = [
        'rules',
        'rule_feedbacks',
        'pending_agent_actions',
        'integration_endpoints',
        'cvss_assessments',
        'log_audit_trails',
    ]

    # Tables with nullable organization_id (for global/system entries)
    nullable_tables = [
        'system_configurations',
        'logs',
    ]

    # Process tables with required organization_id
    for table_name in required_tables:
        if not table_exists(connection, table_name):
            print(f"SEC-082: Skipping {table_name} (table does not exist)")
            continue

        if column_exists(connection, table_name, 'organization_id'):
            print(f"SEC-082: Skipping {table_name} (organization_id already exists)")
            continue

        print(f"SEC-082: Adding organization_id to {table_name}")

        # Delete existing data to avoid NOT NULL constraint violation
        connection.execute(text(f"DELETE FROM {table_name}"))

        # Add organization_id column
        op.add_column(table_name,
            sa.Column('organization_id', sa.Integer(), nullable=False)
        )

        # Add foreign key constraint
        op.create_foreign_key(
            f'fk_{table_name}_organization',
            table_name,
            'organizations',
            ['organization_id'],
            ['id']
        )

        # Add index for query performance
        op.create_index(f'ix_{table_name}_organization_id', table_name, ['organization_id'])

    # Process tables with nullable organization_id
    for table_name in nullable_tables:
        if not table_exists(connection, table_name):
            print(f"SEC-082: Skipping {table_name} (table does not exist)")
            continue

        if column_exists(connection, table_name, 'organization_id'):
            print(f"SEC-082: Skipping {table_name} (organization_id already exists)")
            continue

        print(f"SEC-082: Adding nullable organization_id to {table_name}")

        # Delete existing data for clean slate
        connection.execute(text(f"DELETE FROM {table_name}"))

        # Add organization_id column (nullable for system-level entries)
        op.add_column(table_name,
            sa.Column('organization_id', sa.Integer(), nullable=True)
        )

        # Add foreign key constraint
        op.create_foreign_key(
            f'fk_{table_name}_organization',
            table_name,
            'organizations',
            ['organization_id'],
            ['id']
        )

        # Add index for query performance
        op.create_index(f'ix_{table_name}_organization_id', table_name, ['organization_id'])


def downgrade():
    """
    Remove organization_id columns from all tables (if they exist).
    """
    connection = op.get_bind()

    all_tables = [
        'log_audit_trails',
        'logs',
        'system_configurations',
        'cvss_assessments',
        'integration_endpoints',
        'pending_agent_actions',
        'rule_feedbacks',
        'rules',
    ]

    for table_name in all_tables:
        if not table_exists(connection, table_name):
            continue

        if not column_exists(connection, table_name, 'organization_id'):
            continue

        print(f"SEC-082: Removing organization_id from {table_name}")

        try:
            op.drop_index(f'ix_{table_name}_organization_id', table_name=table_name)
        except Exception:
            pass  # Index might not exist

        try:
            op.drop_constraint(f'fk_{table_name}_organization', table_name, type_='foreignkey')
        except Exception:
            pass  # Constraint might not exist

        op.drop_column(table_name, 'organization_id')
