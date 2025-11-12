"""add created_by to agent_actions

Revision ID: 20251112_145303
Revises: ff9244bcab1b
Create Date: 2025-11-12 14:53:03

Enterprise Solution: Add created_by column for audit trail compliance
- Adds created_by VARCHAR(255) column to agent_actions table
- Backfills existing records from users.email via user_id foreign key
- Aligns with NIST/SOX enterprise audit requirements
- Matches schema definition in schemas.py:152
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251112_145303'
down_revision = '202511121500'  # Depends on merge migration
branch_labels = None
depends_on = None


def upgrade():
    # Add created_by column (nullable to allow backfill)
    op.add_column('agent_actions',
        sa.Column('created_by', sa.String(255), nullable=True)
    )
    
    # Backfill existing records with user email from users table
    op.execute("""
        UPDATE agent_actions
        SET created_by = users.email
        FROM users
        WHERE agent_actions.user_id = users.id
        AND agent_actions.created_by IS NULL
    """)


def downgrade():
    # Remove created_by column
    op.drop_column('agent_actions', 'created_by')
