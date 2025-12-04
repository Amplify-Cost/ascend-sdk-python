"""SEC-074: Merge migration heads

Merges sec071_admin_console and sec074_audit into single head.
This is required because both migrations branched from sec068_autonomous.

Revision ID: sec074_merge
Revises: sec071_admin_console, sec074_audit
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'sec074_merge'
down_revision = ('sec071_admin_console', 'sec074_audit')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge point - no additional changes needed."""
    pass


def downgrade() -> None:
    """Merge point - no additional changes needed."""
    pass
