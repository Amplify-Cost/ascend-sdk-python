"""Enterprise Agent Registry Tables

Revision ID: 20251201_agent_registry
Revises: None
Create Date: 2025-12-01

Creates enterprise-grade agent registration system with:
- RegisteredAgent: Core agent configuration
- AgentVersion: Version history for rollback
- AgentPolicy: Fine-grained access control
- AgentActivityLog: Audit trail
- MCPServerConfig: MCP server governance

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251201_agent_registry'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # REGISTERED_AGENTS TABLE
    # =========================================================================
    op.create_table(
        'registered_agents',
        sa.Column('id', sa.Integer(), nullable=False),

        # Agent Identification
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Agent Classification
        sa.Column('agent_type', sa.String(50), nullable=False, default='supervised'),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),

        # Version Control
        sa.Column('version', sa.String(50), nullable=False, default='1.0.0'),
        sa.Column('version_notes', sa.Text(), nullable=True),

        # Multi-Tenant Isolation
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False, index=True),

        # Risk Configuration
        sa.Column('default_risk_score', sa.Integer(), nullable=False, default=50),
        sa.Column('max_risk_threshold', sa.Integer(), nullable=False, default=80),
        sa.Column('auto_approve_below', sa.Integer(), nullable=False, default=30),
        sa.Column('requires_mfa_above', sa.Integer(), nullable=False, default=70),

        # Capabilities & Permissions (JSONB for PostgreSQL)
        sa.Column('allowed_action_types', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('allowed_resources', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('blocked_resources', postgresql.JSONB(), nullable=True, default=[]),

        # MCP Server Integration
        sa.Column('is_mcp_server', sa.Boolean(), nullable=False, default=False),
        sa.Column('mcp_server_url', sa.String(500), nullable=True),
        sa.Column('mcp_capabilities', postgresql.JSONB(), nullable=True, default={}),

        # Notification Settings
        sa.Column('alert_on_high_risk', sa.Boolean(), nullable=False, default=True),
        sa.Column('alert_recipients', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('webhook_url', sa.String(500), nullable=True),

        # Audit Fields
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),

        # Metadata
        sa.Column('tags', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default={}),

        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_registered_agents_org_status', 'registered_agents', ['organization_id', 'status'])
    op.create_index('ix_registered_agents_agent_type', 'registered_agents', ['agent_type'])

    # Unique constraint: agent_id per organization
    op.create_unique_constraint('uq_agent_org', 'registered_agents', ['agent_id', 'organization_id'])

    # =========================================================================
    # AGENT_VERSIONS TABLE
    # =========================================================================
    op.create_table(
        'agent_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('registered_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('version_notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('config_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_agent_versions_agent', 'agent_versions', ['agent_id'])
    op.create_unique_constraint('uq_agent_version', 'agent_versions', ['agent_id', 'version'])

    # =========================================================================
    # AGENT_POLICIES TABLE
    # =========================================================================
    op.create_table(
        'agent_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('registered_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('policy_name', sa.String(255), nullable=False),
        sa.Column('policy_description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=100),
        sa.Column('conditions', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('policy_action', sa.String(50), nullable=False),
        sa.Column('action_params', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_agent_policies_agent', 'agent_policies', ['agent_id'])
    op.create_index('ix_agent_policies_org', 'agent_policies', ['organization_id'])

    # =========================================================================
    # AGENT_ACTIVITY_LOGS TABLE
    # =========================================================================
    op.create_table(
        'agent_activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('registered_agents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.String(255), nullable=False),
        sa.Column('performed_via', sa.String(50), nullable=True),
        sa.Column('previous_state', postgresql.JSONB(), nullable=True),
        sa.Column('new_state', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_agent_activity_logs_agent', 'agent_activity_logs', ['agent_id'])
    op.create_index('ix_agent_activity_logs_org', 'agent_activity_logs', ['organization_id'])
    op.create_index('ix_agent_activity_logs_timestamp', 'agent_activity_logs', ['timestamp'])

    # =========================================================================
    # MCP_SERVER_CONFIGS TABLE
    # =========================================================================
    op.create_table(
        'mcp_server_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_name', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('server_url', sa.String(500), nullable=True),
        sa.Column('transport_type', sa.String(50), nullable=False, default='stdio'),
        sa.Column('connection_config', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('discovered_tools', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('discovered_prompts', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('discovered_resources', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('last_discovery', sa.DateTime(), nullable=True),
        sa.Column('governance_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('auto_approve_tools', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('blocked_tools', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('tool_risk_overrides', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('health_status', sa.String(50), nullable=False, default='unknown'),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_mcp_server_configs_org', 'mcp_server_configs', ['organization_id'])
    op.create_unique_constraint('uq_mcp_server_org', 'mcp_server_configs', ['server_name', 'organization_id'])


def downgrade():
    op.drop_table('mcp_server_configs')
    op.drop_table('agent_activity_logs')
    op.drop_table('agent_policies')
    op.drop_table('agent_versions')
    op.drop_table('registered_agents')
