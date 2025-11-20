"""merge phase3 versioning with mcp server actions

Revision ID: 56cafdd6712b
Revises: 20251118_164732, 4bc19e3883f3
Create Date: 2025-11-18 17:07:38.968592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56cafdd6712b'
down_revision: Union[str, None] = ('20251118_164732', '4bc19e3883f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
