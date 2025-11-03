"""add_cvss_integration_schema

Revision ID: 07d1a4d8402b
Revises: 9b855d1e4aef
Create Date: 2025-10-28 10:47:34.018767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07d1a4d8402b'
down_revision: Union[str, None] = '9b855d1e4aef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ARCH-001: Add CVSS v3.1 integration schema

    Changes:
    1. Add 3 CVSS columns to agent_actions table (nullable, backward compatible)
    2. Create cvss_assessments table for detailed metric storage
    """

    # Step 1: Add CVSS columns to agent_actions table
    op.add_column('agent_actions', sa.Column('cvss_score', sa.Float(), nullable=True))
    op.add_column('agent_actions', sa.Column('cvss_severity', sa.String(length=20), nullable=True))
    op.add_column('agent_actions', sa.Column('cvss_vector', sa.String(length=100), nullable=True))

    # Step 2: Create cvss_assessments table for detailed CVSS metrics
    op.create_table(
        'cvss_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),

        # CVSS v3.1 Base Metrics
        sa.Column('attack_vector', sa.String(length=20), nullable=False),
        sa.Column('attack_complexity', sa.String(length=20), nullable=False),
        sa.Column('privileges_required', sa.String(length=20), nullable=False),
        sa.Column('user_interaction', sa.String(length=20), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('confidentiality_impact', sa.String(length=20), nullable=False),
        sa.Column('integrity_impact', sa.String(length=20), nullable=False),
        sa.Column('availability_impact', sa.String(length=20), nullable=False),

        # Calculated Scores
        sa.Column('base_score', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('vector_string', sa.String(length=100), nullable=False),

        # Metadata
        sa.Column('assessed_by', sa.String(length=50), nullable=False, server_default='system'),
        sa.Column('assessed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['action_id'], ['agent_actions.id'], ondelete='CASCADE')
    )

    # Step 3: Create indexes for performance
    op.create_index('ix_cvss_assessments_action_id', 'cvss_assessments', ['action_id'])
    op.create_index('ix_cvss_assessments_severity', 'cvss_assessments', ['severity'])
    op.create_index('ix_cvss_assessments_base_score', 'cvss_assessments', ['base_score'])
    op.create_index('ix_agent_actions_cvss_score', 'agent_actions', ['cvss_score'])
    op.create_index('ix_agent_actions_cvss_severity', 'agent_actions', ['cvss_severity'])


def downgrade() -> None:
    """
    ARCH-001: Rollback CVSS v3.1 integration schema

    Reverts all changes made in upgrade()
    """

    # Drop indexes first
    op.drop_index('ix_agent_actions_cvss_severity', 'agent_actions')
    op.drop_index('ix_agent_actions_cvss_score', 'agent_actions')
    op.drop_index('ix_cvss_assessments_base_score', 'cvss_assessments')
    op.drop_index('ix_cvss_assessments_severity', 'cvss_assessments')
    op.drop_index('ix_cvss_assessments_action_id', 'cvss_assessments')

    # Drop cvss_assessments table
    op.drop_table('cvss_assessments')

    # Drop CVSS columns from agent_actions
    op.drop_column('agent_actions', 'cvss_vector')
    op.drop_column('agent_actions', 'cvss_severity')
    op.drop_column('agent_actions', 'cvss_score')
