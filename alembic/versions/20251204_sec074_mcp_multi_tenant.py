"""SEC-074: Multi-Tenant Isolation for MCP Server Governance

Enterprise-grade multi-tenant isolation for MCP server governance tables.
Adds organization_id column with foreign key to organizations table.

Critical Security Fix:
- CVSS 9.1 Critical: Cross-tenant MCP server access vulnerability
- mcp_servers, mcp_server_actions, mcp_sessions, mcp_policies lack organization isolation
- Allows Organization A to potentially register/access Organization B's MCP servers

Tables Modified:
- mcp_servers: MCP server registry
- mcp_server_actions: MCP action audit trail
- mcp_sessions: Active MCP client sessions
- mcp_policies: MCP governance policies

Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312, GDPR Art. 32
Aligned with: Banking-level tenant isolation patterns (SEC-007)

Revision ID: sec074_mcp
Revises: sec074_playbook
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = 'sec074_mcp'
down_revision = 'sec074_playbook'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add organization_id to all MCP governance tables."""

    # ==========================================================================
    # SEC-074: mcp_servers - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'mcp_servers',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_mcp_servers_organization',
        'mcp_servers',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_index(
        'ix_mcp_servers_organization_id',
        'mcp_servers',
        ['organization_id']
    )

    # Composite index: org + active status (common query pattern)
    op.create_index(
        'ix_mcp_servers_org_active',
        'mcp_servers',
        ['organization_id', 'is_active']
    )

    # ==========================================================================
    # SEC-074: mcp_server_actions - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'mcp_server_actions',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_mcp_server_actions_organization',
        'mcp_server_actions',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_index(
        'ix_mcp_server_actions_organization_id',
        'mcp_server_actions',
        ['organization_id']
    )

    # Composite index: org + status (for pending actions query)
    op.create_index(
        'ix_mcp_server_actions_org_status',
        'mcp_server_actions',
        ['organization_id', 'status']
    )

    # Composite index: org + time (for analytics queries)
    op.create_index(
        'ix_mcp_server_actions_org_time',
        'mcp_server_actions',
        ['organization_id', 'created_at']
    )

    # ==========================================================================
    # SEC-074: mcp_sessions - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'mcp_sessions',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_mcp_sessions_organization',
        'mcp_sessions',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_index(
        'ix_mcp_sessions_organization_id',
        'mcp_sessions',
        ['organization_id']
    )

    # Composite index: org + active (for active sessions query)
    op.create_index(
        'ix_mcp_sessions_org_active',
        'mcp_sessions',
        ['organization_id', 'is_active']
    )

    # ==========================================================================
    # SEC-074: mcp_policies - Multi-Tenant Isolation
    # ==========================================================================

    op.add_column(
        'mcp_policies',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_mcp_policies_organization',
        'mcp_policies',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_index(
        'ix_mcp_policies_organization_id',
        'mcp_policies',
        ['organization_id']
    )

    # Composite index: org + active (for policy evaluation)
    op.create_index(
        'ix_mcp_policies_org_active',
        'mcp_policies',
        ['organization_id', 'is_active']
    )

    # Composite index: org + priority (for ordered policy evaluation)
    op.create_index(
        'ix_mcp_policies_org_priority',
        'mcp_policies',
        ['organization_id', 'priority']
    )


def downgrade() -> None:
    """Remove organization_id from all MCP governance tables."""

    # mcp_policies
    op.drop_index('ix_mcp_policies_org_priority', table_name='mcp_policies')
    op.drop_index('ix_mcp_policies_org_active', table_name='mcp_policies')
    op.drop_index('ix_mcp_policies_organization_id', table_name='mcp_policies')
    op.drop_constraint('fk_mcp_policies_organization', 'mcp_policies', type_='foreignkey')
    op.drop_column('mcp_policies', 'organization_id')

    # mcp_sessions
    op.drop_index('ix_mcp_sessions_org_active', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_organization_id', table_name='mcp_sessions')
    op.drop_constraint('fk_mcp_sessions_organization', 'mcp_sessions', type_='foreignkey')
    op.drop_column('mcp_sessions', 'organization_id')

    # mcp_server_actions
    op.drop_index('ix_mcp_server_actions_org_time', table_name='mcp_server_actions')
    op.drop_index('ix_mcp_server_actions_org_status', table_name='mcp_server_actions')
    op.drop_index('ix_mcp_server_actions_organization_id', table_name='mcp_server_actions')
    op.drop_constraint('fk_mcp_server_actions_organization', 'mcp_server_actions', type_='foreignkey')
    op.drop_column('mcp_server_actions', 'organization_id')

    # mcp_servers
    op.drop_index('ix_mcp_servers_org_active', table_name='mcp_servers')
    op.drop_index('ix_mcp_servers_organization_id', table_name='mcp_servers')
    op.drop_constraint('fk_mcp_servers_organization', 'mcp_servers', type_='foreignkey')
    op.drop_column('mcp_servers', 'organization_id')
