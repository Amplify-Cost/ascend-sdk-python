"""add_outcome_to_immutable_audit_logs

Revision ID: 20251115_185707
Revises: 389a4795ec57
Create Date: 2025-11-15 18:57:07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251115_185707'
down_revision: Union[str, None] = '389a4795ec57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add outcome column to immutable_audit_logs table."""
    # Add outcome column with a default value for existing rows
    op.execute("""
        ALTER TABLE immutable_audit_logs
        ADD COLUMN IF NOT EXISTS outcome VARCHAR(50) DEFAULT 'SUCCESS' NOT NULL;
    """)

    print("✅ Added outcome column to immutable_audit_logs table")


def downgrade() -> None:
    """Remove outcome column from immutable_audit_logs table."""
    op.execute("""
        ALTER TABLE immutable_audit_logs
        DROP COLUMN IF EXISTS outcome;
    """)

    print("✅ Removed outcome column from immutable_audit_logs table")
