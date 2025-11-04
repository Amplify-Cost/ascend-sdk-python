"""add_policy_evaluations_table

Revision ID: b8ebd7cdcb8b
Revises: 389a4795ec57
Create Date: 2025-11-04 16:56:51.751338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b8ebd7cdcb8b'
down_revision: Union[str, None] = '389a4795ec57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create policy_evaluations table
    op.create_table(
        'policy_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('principal', sa.String(length=512), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=512), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('evaluation_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('policies_triggered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('matched_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['enterprise_policies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for query performance
    op.create_index('idx_policy_evaluations_evaluated_at', 'policy_evaluations', ['evaluated_at'], unique=False)
    op.create_index('idx_policy_evaluations_policy_id', 'policy_evaluations', ['policy_id'], unique=False)
    op.create_index('idx_policy_evaluations_user_id', 'policy_evaluations', ['user_id'], unique=False)
    op.create_index('idx_policy_evaluations_decision', 'policy_evaluations', ['decision'], unique=False)
    op.create_index('idx_policy_evaluations_action', 'policy_evaluations', ['action'], unique=False)
    op.create_index('idx_policy_evaluations_allowed', 'policy_evaluations', ['allowed'], unique=False)

    # Create GIN index for JSONB columns (PostgreSQL-specific)
    op.execute('CREATE INDEX idx_policy_evaluations_policies_triggered ON policy_evaluations USING GIN (policies_triggered)')
    op.execute('CREATE INDEX idx_policy_evaluations_context ON policy_evaluations USING GIN (context)')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.execute('DROP INDEX IF EXISTS idx_policy_evaluations_context')
    op.execute('DROP INDEX IF EXISTS idx_policy_evaluations_policies_triggered')
    op.drop_index('idx_policy_evaluations_allowed', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_action', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_decision', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_user_id', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_policy_id', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_evaluated_at', table_name='policy_evaluations')

    # Drop table
    op.drop_table('policy_evaluations')
