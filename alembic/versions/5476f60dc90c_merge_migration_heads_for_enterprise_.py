"""merge_migration_heads_for_enterprise_policy

Revision ID: 5476f60dc90c
Revises: 001, be858bdecce8
Create Date: 2025-09-08 09:15:37.717439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5476f60dc90c'
down_revision: Union[str, None] = ('001', 'be858bdecce8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
