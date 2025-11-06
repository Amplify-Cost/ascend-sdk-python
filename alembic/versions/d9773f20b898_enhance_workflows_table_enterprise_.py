"""enhance_workflows_table_enterprise_features

Revision ID: d9773f20b898
Revises: b8ebd7cdcb8b
Create Date: 2025-11-06 11:37:31.077579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9773f20b898'
down_revision: Union[str, None] = 'b8ebd7cdcb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add enterprise-grade columns to workflows table."""
    # Add new columns
    op.add_column('workflows', sa.Column('owner', sa.String(255), nullable=True))
    op.add_column('workflows', sa.Column('sla_hours', sa.Integer(), default=24, nullable=True))
    op.add_column('workflows', sa.Column('auto_approve_on_timeout', sa.Boolean(), default=False, nullable=True))
    op.add_column('workflows', sa.Column('last_executed', sa.DateTime(), nullable=True))
    op.add_column('workflows', sa.Column('execution_count', sa.Integer(), default=0, nullable=True))
    op.add_column('workflows', sa.Column('success_rate', sa.Float(), default=0.0, nullable=True))
    op.add_column('workflows', sa.Column('avg_completion_time_hours', sa.Float(), nullable=True))
    op.add_column('workflows', sa.Column('compliance_frameworks', sa.JSON(), nullable=True))
    op.add_column('workflows', sa.Column('tags', sa.JSON(), nullable=True))

    # Create indexes for better query performance
    op.create_index('ix_workflows_last_executed', 'workflows', ['last_executed'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove enterprise columns from workflows table."""
    # Drop indexes
    op.drop_index('ix_workflows_last_executed', table_name='workflows')

    # Drop columns in reverse order
    op.drop_column('workflows', 'tags')
    op.drop_column('workflows', 'compliance_frameworks')
    op.drop_column('workflows', 'avg_completion_time_hours')
    op.drop_column('workflows', 'success_rate')
    op.drop_column('workflows', 'execution_count')
    op.drop_column('workflows', 'last_executed')
    op.drop_column('workflows', 'auto_approve_on_timeout')
    op.drop_column('workflows', 'sla_hours')
    op.drop_column('workflows', 'owner')
