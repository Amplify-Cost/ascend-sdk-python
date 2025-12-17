"""merge_phase9_with_byok

Revision ID: b1a16964bb4c
Revises: byok_015_legal_waiver, phase9_002_seed_patterns
Create Date: 2025-12-17 16:35:19.798154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a16964bb4c'
down_revision: Union[str, None] = ('byok_015_legal_waiver', 'phase9_002_seed_patterns')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
