"""merge_sec_105_migration

Revision ID: c10d8fe3d900
Revises: sec_096_prefix_len, sec_103_agent_control, sec_110_auto_resolved
Create Date: 2025-12-10 19:38:13.146743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c10d8fe3d900'
down_revision: Union[str, None] = ('sec_096_prefix_len', 'sec_103_agent_control', 'sec_110_auto_resolved')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
