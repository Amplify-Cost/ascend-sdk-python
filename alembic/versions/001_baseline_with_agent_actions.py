"""baseline with agent_actions table

Revision ID: 001
Revises: 
Create Date: 2025-08-29

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Handle existing agent_actions table by adding missing columns
    try:
        # Try to create table first (for clean installs)
        op.create_table('agent_actions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('agent_id', sa.String(255), nullable=False),
            sa.Column('action_type', sa.String(100), nullable=False),  
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('risk_level', sa.String(20), nullable=True),
            sa.Column('risk_score', sa.Float(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True),
            sa.Column('approved', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        # Table exists, add missing columns
        try:
            op.add_column('agent_actions', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
        except Exception:
            pass  # Column already exists
        try:
            op.add_column('agent_actions', sa.Column('user_id', sa.Integer(), nullable=True))
        except Exception:
            pass  # Column already exists

def downgrade():
    op.drop_table('agent_actions')
