"""create_mcp_server_actions_table

🏢 ENTERPRISE MCP GOVERNANCE MIGRATION
Creates mcp_server_actions table for real MCP server monitoring and governance

Features:
- Integer ID for compatibility + UUID for enterprise distributed systems
- Full audit trail and compliance tracking
- Policy fusion integration (Option 4)
- Multi-level approval workflow
- Real-time risk assessment

Aligns with: Palo Alto Networks, Splunk SOAR governance patterns
Engineer: Donald King, OW-kai Enterprise

Revision ID: 4bc19e3883f3
Revises: 79d6be706f83
Create Date: 2025-11-16 17:59:45.675487

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '4bc19e3883f3'
down_revision: Union[str, None] = '79d6be706f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    🏢 ENTERPRISE UPGRADE: Create MCP Server Actions table

    This table tracks ALL MCP server interactions with enterprise governance:
    - Real-time monitoring of MCP server actions
    - Policy-based approval workflows
    - Audit trail for compliance (SOX, HIPAA, PCI-DSS, GDPR)
    - Risk-based authorization
    """

    op.create_table(
        'mcp_server_actions',

        # Primary identification (Integer + UUID hybrid approach)
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('uuid', UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),

        # 🏢 COMPATIBILITY FIELDS (for enterprise_unified_loader.py)
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),  # Maps to mcp_server_name
        sa.Column('action_type', sa.String(100), nullable=False, index=True),  # Maps to verb
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context', JSONB(), nullable=True),  # JSONB parameters

        # MCP Server Identity
        sa.Column('mcp_server_id', sa.String(200), nullable=True, index=True),
        sa.Column('mcp_server_name', sa.String(200), nullable=False),
        sa.Column('mcp_server_version', sa.String(50), nullable=True),

        # MCP Protocol Details
        sa.Column('namespace', sa.String(100), nullable=False, index=True),  # filesystem, database, tools
        sa.Column('verb', sa.String(100), nullable=False, index=True),  # read_file, write_file, execute
        sa.Column('resource', sa.String(500), nullable=False),  # Target resource path

        # Request Details
        sa.Column('request_id', sa.String(100), nullable=False, unique=True),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('client_id', sa.String(100), nullable=False, index=True),

        # Action Parameters
        sa.Column('parameters', JSONB(), nullable=False, server_default='{}'),
        sa.Column('payload_size', sa.Integer(), server_default='0'),

        # Risk Assessment (0-100 scoring)
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('risk_level', sa.String(20), nullable=False, server_default='LOW'),
        sa.Column('risk_factors', JSONB(), server_default='[]'),

        # Governance Status
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approval_level', sa.Integer(), server_default='1'),

        # User Context
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_role', sa.String(100), nullable=True),

        # Policy & Rules
        sa.Column('policy_result', sa.String(50), server_default='EVALUATE'),
        sa.Column('rule_id', sa.String(100), nullable=True, index=True),
        sa.Column('policy_reason', sa.Text(), nullable=True),

        # 🏢 OPTION 4 POLICY FUSION FIELDS
        sa.Column('policy_evaluated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('policy_decision', sa.String(50), nullable=True),
        sa.Column('policy_risk_score', sa.Float(), nullable=True),
        sa.Column('risk_fusion_formula', sa.String(255), nullable=True),

        # Approval Workflow (enterprise_unified_loader compatibility)
        sa.Column('approver_id', sa.String(100), nullable=True, index=True),
        sa.Column('approver_email', sa.String(255), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),

        # Execution Details
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=True),
        sa.Column('execution_result', sa.String(50), nullable=True),
        sa.Column('execution_output', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Security & Compliance
        sa.Column('environment', sa.String(50), server_default='production'),
        sa.Column('data_classification', sa.String(50), server_default='internal'),
        sa.Column('compliance_tags', JSONB(), server_default='[]'),

        # Audit Trail Integration
        sa.Column('audit_trail_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('evidence_pack_id', UUID(as_uuid=True), nullable=True),

        # Network & Context
        sa.Column('source_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('geo_location', sa.String(100), nullable=True),

        # Performance Metrics
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('bytes_transferred', sa.Integer(), nullable=True),
    )

    # Create enterprise performance indexes
    op.create_index('idx_mcp_server_namespace', 'mcp_server_actions', ['mcp_server_id', 'namespace'])
    op.create_index('idx_mcp_risk_level', 'mcp_server_actions', ['risk_level', 'status'])
    op.create_index('idx_mcp_user_time', 'mcp_server_actions', ['user_id', 'created_at'])
    op.create_index('idx_mcp_approval', 'mcp_server_actions', ['status', 'requires_approval'])
    # GIN index for JSON columns (compliance_tags)
    op.execute('CREATE INDEX idx_mcp_compliance ON mcp_server_actions USING GIN (compliance_tags)')
    op.create_index('idx_mcp_session', 'mcp_server_actions', ['session_id', 'created_at'])
    op.create_index('idx_mcp_agent_action_type', 'mcp_server_actions', ['agent_id', 'action_type'])
    op.create_index('idx_mcp_uuid', 'mcp_server_actions', ['uuid'])


def downgrade() -> None:
    """
    🏢 ENTERPRISE DOWNGRADE: Remove MCP Server Actions table
    """
    op.drop_index('idx_mcp_uuid', 'mcp_server_actions')
    op.drop_index('idx_mcp_agent_action_type', 'mcp_server_actions')
    op.drop_index('idx_mcp_session', 'mcp_server_actions')
    op.execute('DROP INDEX IF EXISTS idx_mcp_compliance')  # GIN index
    op.drop_index('idx_mcp_approval', 'mcp_server_actions')
    op.drop_index('idx_mcp_user_time', 'mcp_server_actions')
    op.drop_index('idx_mcp_risk_level', 'mcp_server_actions')
    op.drop_index('idx_mcp_server_namespace', 'mcp_server_actions')
    op.drop_table('mcp_server_actions')
