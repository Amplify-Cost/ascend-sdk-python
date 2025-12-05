"""SEC-082: Merge heads for multi-tenant isolation

Revision ID: a34761a6b6e8
Revises: sec076_multi_tenant, sec077_governance, 20251205_sec082
Create Date: 2025-12-05 00:10:49.503231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a34761a6b6e8'
down_revision: Union[str, None] = ('sec076_multi_tenant', 'sec077_governance', '20251205_sec082')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
