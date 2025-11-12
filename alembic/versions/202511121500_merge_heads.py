"""merge migration heads

Revision ID: 202511121500
Revises: d9773f20b898, ff9244bcab1b
Create Date: 2025-11-12 15:00:00

Merges two migration branches:
- d9773f20b898 (workflows enhancement)
- ff9244bcab1b (summary column)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202511121500'
down_revision = ('d9773f20b898', 'ff9244bcab1b')
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration - no changes needed
    pass


def downgrade():
    # Merge migration - no changes needed
    pass
