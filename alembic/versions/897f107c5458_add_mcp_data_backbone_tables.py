"""add_mcp_data_backbone_tables

Revision ID: 897f107c5458
Revises: de9b00ce321e
Create Date: 2025-08-28 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '897f107c5458'
down_revision: Union[str, None] = 'de9b00ce321e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('agent_actions', sa.Column('policy_id', sa.Text(), nullable=True))
    op.add_column('agent_actions', sa.Column('result', sa.String(), nullable=True))
    op.add_column('agent_actions', sa.Column('metadata', postgresql.JSONB(), nullable=True))
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id SERIAL PRIMARY KEY,
            agent_action_id INTEGER REFERENCES agent_actions(id),
            approver_id INTEGER REFERENCES users(id),
            status TEXT DEFAULT 'pending',
            rationale TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            decided_at TIMESTAMPTZ
        )
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approvals")
    op.drop_column('agent_actions', 'metadata')
    op.drop_column('agent_actions', 'result') 
    op.drop_column('agent_actions', 'policy_id')
