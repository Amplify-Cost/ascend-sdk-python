"""create_agent_actions_table

Revision ID: $(date +%s)
Revises: 
Create Date: $(date)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '$(date +%s)'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('agent_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True, default='medium'),
        sa.Column('risk_score', sa.Float(), nullable=True, default=50.0),
        sa.Column('status', sa.String(20), nullable=True, default='pending'),
        sa.Column('approved', sa.Boolean(), nullable=True, default=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tool_name', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_actions_agent_id', 'agent_actions', ['agent_id'])
    op.create_index('ix_agent_actions_action_type', 'agent_actions', ['action_type'])
    op.create_index('ix_agent_actions_status', 'agent_actions', ['status'])

def downgrade():
    op.drop_index('ix_agent_actions_status', table_name='agent_actions')
    op.drop_index('ix_agent_actions_action_type', table_name='agent_actions')
    op.drop_index('ix_agent_actions_agent_id', table_name='agent_actions')
    op.drop_table('agent_actions')
