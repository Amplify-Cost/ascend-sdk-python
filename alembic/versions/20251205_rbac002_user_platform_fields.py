"""RBAC-002: Add platform user fields to users table

Adds fields to support platform users (Ascend internal staff):
- scope: 'platform' or 'org' (default='org')
- is_platform_user: Boolean (default=False)
- organization_id: Made nullable for platform users

Validation (enforced at application level):
- is_platform_user=True  → organization_id MUST be NULL, scope='platform'
- is_platform_user=False → organization_id MUST be NOT NULL, scope='org'

All existing users remain as tenant users (scope='org', is_platform_user=False).

Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1

Revision ID: rbac002_user_platform
Revises: a34761a6b6e8
Create Date: 2025-12-05 09:50:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rbac002_user_platform'
down_revision = 'a34761a6b6e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add platform user support fields to users table."""

    # Add scope column (default='org' for existing users)
    op.add_column('users',
        sa.Column('scope', sa.String(20), nullable=False, server_default='org')
    )

    # Add is_platform_user column (default=False for existing users)
    op.add_column('users',
        sa.Column('is_platform_user', sa.Boolean(), nullable=False, server_default='false')
    )

    # Create indexes for efficient filtering
    op.create_index('ix_users_scope', 'users', ['scope'])
    op.create_index('ix_users_is_platform_user', 'users', ['is_platform_user'])

    # Make organization_id nullable for platform users
    # Note: Existing users all have organization_id, this just allows NULL for new platform users
    op.alter_column('users', 'organization_id',
        existing_type=sa.Integer(),
        nullable=True
    )

    # Add partial unique index for platform user emails
    # This ensures platform user emails are unique (where organization_id IS NULL)
    op.execute("""
        CREATE UNIQUE INDEX ix_users_platform_email_unique
        ON users (email)
        WHERE organization_id IS NULL
    """)


def downgrade() -> None:
    """Remove platform user support fields."""

    # Drop partial unique index for platform emails
    op.execute("DROP INDEX IF EXISTS ix_users_platform_email_unique")

    # Drop indexes
    op.drop_index('ix_users_is_platform_user', table_name='users')
    op.drop_index('ix_users_scope', table_name='users')

    # Drop columns
    op.drop_column('users', 'is_platform_user')
    op.drop_column('users', 'scope')

    # Restore organization_id to NOT NULL
    # WARNING: This will fail if any platform users exist with NULL organization_id
    op.alter_column('users', 'organization_id',
        existing_type=sa.Integer(),
        nullable=False
    )
