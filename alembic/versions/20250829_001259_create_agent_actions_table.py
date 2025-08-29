"""Create agent_actions table for MCP Data Backbone

Revision ID: 001_agent_actions
Revises: 
Create Date: 2025-08-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_agent_actions'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('agent_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('action_type', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True, default='medium'),
        sa.Column('risk_score', sa.Float(), nullable=True, default=50.0),
        sa.Column('status', sa.String(20), nullable=True, default='pending', index=True),
        sa.Column('approved', sa.Boolean(), nullable=True, default=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tool_name', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

def downgrade():
    op.drop_table('agent_actions')
