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
    # Create agent_actions table (other tables already exist)
    op.create_table('agent_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),  
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('agent_actions')
