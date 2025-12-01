"""merge_agent_registry_with_sec025_email

Revision ID: 08f9e6ba9d35
Revises: 20251130_sec025_email, 20251201_agent_registry
Create Date: 2025-12-01 12:53:51.143053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08f9e6ba9d35'
down_revision: Union[str, None] = ('20251130_sec025_email', '20251201_agent_registry')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
