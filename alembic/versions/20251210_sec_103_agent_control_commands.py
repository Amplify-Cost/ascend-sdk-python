"""SEC-103/104/105: Create agent_control_commands table for kill-switch

Problem:
- No audit trail for agent control commands (kill-switch)
- No way to track BLOCK/UNBLOCK commands sent via SNS/SQS
- Compliance gap for incident response tracking

Solution:
- Create agent_control_commands table
- Track command lifecycle: pending → delivered → acknowledged
- Store SNS message IDs for correlation
- Support per-agent or broadcast (org-wide) commands

Architecture:
- Admin triggers command → Backend publishes to SNS
- SNS fans out to per-org SQS queues (filter policy by org_id)
- SDK agents poll SQS with long-polling
- Commands acknowledged and logged here

Compliance:
- SOC 2 CC6.2: Logical access controls
- NIST IR-4: Incident handling
- HIPAA 164.308(a)(6): Security incident procedures

Revision ID: sec_103_agent_control
Revises: None
Create Date: 2025-12-10

Authored-By: ASCEND Engineering Team
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect

# revision identifiers
revision = 'sec_103_agent_control'
down_revision = None  # Independent branch - merged in c10d8fe3d900
branch_labels = None
depends_on = None


def upgrade():
    """Create agent_control_commands table."""
    # Check if table already exists (idempotent)
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'agent_control_commands' not in existing_tables:
        op.create_table(
            'agent_control_commands',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),

            # Unique command identifier (UUID for SNS deduplication)
            sa.Column('command_id', sa.String(36), nullable=False, unique=True, index=True),

            # Target scope
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
            sa.Column('agent_id', sa.String(255), nullable=True),  # Null = broadcast

            # Command details
            sa.Column('command_type', sa.String(50), nullable=False),  # BLOCK, UNBLOCK, etc.
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('parameters', JSONB, server_default='{}'),

            # Execution tracking
            sa.Column('status', sa.String(50), server_default='pending', nullable=False),
            sa.Column('sns_message_id', sa.String(100), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged_by_agents', JSONB, server_default='[]'),

            # Audit fields
            sa.Column('issued_by', sa.String(255), nullable=False),
            sa.Column('issued_via', sa.String(50), server_default='api', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
        )

        # Create indexes
        op.create_index('ix_agent_control_org', 'agent_control_commands', ['organization_id'])
        op.create_index('ix_agent_control_agent', 'agent_control_commands', ['agent_id'])
        op.create_index('ix_agent_control_command_id', 'agent_control_commands', ['command_id'])
        op.create_index('ix_agent_control_created', 'agent_control_commands', ['created_at'])

        print("SEC-103: Created agent_control_commands table")
    else:
        print("SEC-103: agent_control_commands table already exists, skipping")


def downgrade():
    """Drop agent_control_commands table."""
    op.drop_index('ix_agent_control_created', table_name='agent_control_commands')
    op.drop_index('ix_agent_control_command_id', table_name='agent_control_commands')
    op.drop_index('ix_agent_control_agent', table_name='agent_control_commands')
    op.drop_index('ix_agent_control_org', table_name='agent_control_commands')
    op.drop_table('agent_control_commands')
