"""merge_phase2_phase3_with_unified

Revision ID: 79d6be706f83
Revises: 20251115_unified, 20251116_trigger
Create Date: 2025-11-15 19:56:33.581268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79d6be706f83'
down_revision: Union[str, None] = ('20251115_unified', '20251116_trigger')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
