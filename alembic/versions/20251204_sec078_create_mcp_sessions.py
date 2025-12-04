"""SEC-078: Create MCP Sessions Table

Creates the mcp_sessions table required for SEC-077 governance improvements.
This table tracks active MCP client sessions for enterprise session management.

Compliance: SOC 2 CC6.1, NIST IA-4, GDPR Art. 5, PCI-DSS 8.1
Author: Ascend Platform Engineering

Revision ID: sec078_mcp_sessions
Revises: sec076_diagnostics
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = 'sec078_mcp_sessions'
down_revision = 'sec076_diagnostics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    SEC-078: Create mcp_sessions table for MCP session tracking.

    Features:
    - UUID primary keys for distributed systems
    - Multi-tenant isolation via organization_id
    - Session lifecycle management
    - Activity metrics tracking
    - Security token hashing
    """

    op.create_table(
        'mcp_sessions',
        # Primary Key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        # Multi-Tenant Isolation (SEC-074)
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=True, index=True),

        # Session Identity
        sa.Column('session_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('client_id', sa.String(100), nullable=False, index=True),
        sa.Column('server_id', sa.String(100), nullable=False, index=True),  # References mcp_servers.server_name (no FK for flexibility)

        # User Context
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('authenticated_at', sa.DateTime(), nullable=True),

        # Session Status
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_activity', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Connection Details
        sa.Column('connection_type', sa.String(50), nullable=True),
        sa.Column('source_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),

        # Activity Metrics
        sa.Column('total_actions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_actions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_actions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bytes_transferred', sa.Integer(), nullable=False, server_default='0'),

        # Security
        sa.Column('auth_token_hash', sa.String(64), nullable=True),
        sa.Column('permissions', JSON(), nullable=True, server_default='[]'),
    )

    # Create indexes for common query patterns
    op.create_index(
        'ix_mcp_sessions_org_status',
        'mcp_sessions',
        ['organization_id', 'status']
    )

    op.create_index(
        'ix_mcp_sessions_server_active',
        'mcp_sessions',
        ['server_id', 'is_active']
    )

    op.create_index(
        'ix_mcp_sessions_user_active',
        'mcp_sessions',
        ['user_id', 'is_active']
    )

    print("SEC-078: Created mcp_sessions table")
    print("  - UUID primary keys for distributed systems")
    print("  - Multi-tenant isolation via organization_id")
    print("  - Session lifecycle tracking")
    print("  - Activity metrics and security token hashing")


def downgrade() -> None:
    """Remove mcp_sessions table."""
    op.drop_index('ix_mcp_sessions_user_active', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_server_active', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_org_status', table_name='mcp_sessions')
    op.drop_table('mcp_sessions')

    print("SEC-078: Dropped mcp_sessions table")
