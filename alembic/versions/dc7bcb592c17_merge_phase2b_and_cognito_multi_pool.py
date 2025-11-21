"""merge phase2b and cognito multi-pool

Revision ID: dc7bcb592c17
Revises: 30db27b1ba18, d8e9f1a2b3c4
Create Date: 2025-11-21 10:06:24.021503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc7bcb592c17'
down_revision: Union[str, None] = ('30db27b1ba18', 'd8e9f1a2b3c4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
