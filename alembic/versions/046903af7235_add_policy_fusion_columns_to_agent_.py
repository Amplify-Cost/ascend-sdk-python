"""add_policy_fusion_columns_to_agent_actions

Revision ID: 046903af7235
Revises: 20251112_145303
Create Date: 2025-11-13 11:05:44.264268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '046903af7235'
down_revision: Union[str, None] = '20251112_145303'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add policy fusion columns for Option 4 Hybrid Layered Architecture."""
    # Add policy evaluation tracking columns
    op.add_column('agent_actions', sa.Column('policy_evaluated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('agent_actions', sa.Column('policy_decision', sa.String(50), nullable=True))
    op.add_column('agent_actions', sa.Column('policy_risk_score', sa.Integer(), nullable=True))
    op.add_column('agent_actions', sa.Column('risk_fusion_formula', sa.Text(), nullable=True))

    # Add index for performance on policy evaluation lookups
    op.create_index('idx_agent_actions_policy_evaluated', 'agent_actions', ['policy_evaluated'])
    op.create_index('idx_agent_actions_policy_decision', 'agent_actions', ['policy_decision'])


def downgrade() -> None:
    """Remove policy fusion columns."""
    # Drop indexes first
    op.drop_index('idx_agent_actions_policy_decision', table_name='agent_actions')
    op.drop_index('idx_agent_actions_policy_evaluated', table_name='agent_actions')

    # Drop columns
    op.drop_column('agent_actions', 'risk_fusion_formula')
    op.drop_column('agent_actions', 'policy_risk_score')
    op.drop_column('agent_actions', 'policy_decision')
    op.drop_column('agent_actions', 'policy_evaluated')
