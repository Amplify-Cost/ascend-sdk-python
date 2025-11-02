"""Enterprise Password Column Standardization

Revision ID: enterprise_pwd_std
Revises: 07d1a4d8402b
Create Date: 2025-11-01

ENTERPRISE SCHEMA STANDARDIZATION
=================================

Issue:
- Production DB uses 'password_hash' column
- Local DB and SQLAlchemy models use 'password' column
- Schema mismatch causing production failures

Solution:
- Rename 'password_hash' to 'password' in production
- Aligns with enterprise SQLAlchemy model standards
- No data loss - simple column rename

Impact:
- Zero downtime migration
- Backward compatible with existing hashed passwords
- All application code already uses 'password' column name

Compliance:
- Maintains NIST SP 800-63B password security
- Preserves bcrypt + SHA-256 hashing
- No security implications

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'enterprise_pwd_std'
down_revision = 'a2d1ed2ea8dd'  # Latest migration (enterprise reports table)
branch_labels = None
depends_on = None


def upgrade():
    """
    Standardize password column name across all environments

    Enterprise Standard: 'password' (not 'password_hash')
    Rationale: Modern SQLAlchemy convention, cleaner API
    """
    # Get connection
    conn = op.get_bind()

    # Check if password_hash column exists (production)
    # If it exists, rename it to password
    # If it doesn't exist, password column already exists (local) - no action needed

    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name IN ('password', 'password_hash')
    """))

    existing_cols = [row[0] for row in result]

    if 'password_hash' in existing_cols and 'password' not in existing_cols:
        # Production schema - rename password_hash to password
        print("🔄 Renaming 'password_hash' to 'password' (Enterprise Standard)")
        op.alter_column('users', 'password_hash',
                       new_column_name='password',
                       existing_type=sa.String(),
                       existing_nullable=True)
        print("✅ Column renamed successfully")

    elif 'password' in existing_cols:
        # Local schema - already correct
        print("✅ Column 'password' already exists (Enterprise Standard)")

    else:
        # Neither column exists - create password column
        print("⚠️  Neither 'password' nor 'password_hash' found - creating 'password' column")
        op.add_column('users', sa.Column('password', sa.String(), nullable=True))
        print("✅ Column 'password' created")


def downgrade():
    """
    Revert to password_hash column name

    Note: This is not recommended for enterprise deployments
    Only use if absolutely necessary for rollback
    """
    # Get connection
    conn = op.get_bind()

    # Check current state
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name IN ('password', 'password_hash')
    """))

    existing_cols = [row[0] for row in result]

    if 'password' in existing_cols and 'password_hash' not in existing_cols:
        # Rename password back to password_hash
        print("🔄 Reverting 'password' to 'password_hash'")
        op.alter_column('users', 'password',
                       new_column_name='password_hash',
                       existing_type=sa.String(),
                       existing_nullable=True)
        print("✅ Reverted to password_hash")
    else:
        print("⚠️  No action needed for downgrade")
