"""SEC-046 Phase 2: Add user management columns

Revision ID: 20251202_sec046_p2
Revises: 20251202_sec045
Create Date: 2025-12-02

Banking-Level Security: User suspension, profile, and session management
Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.1, NIST AC-2

SEC-046 Phase 2 columns:
1. User Profile: first_name, last_name, phone, department, job_title, updated_at
2. Suspension: is_suspended, suspended_at, suspended_by, suspension_reason
3. Session: token_version, last_logout, last_active_at
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from typing import Sequence, Union

# revision identifiers
revision: str = '20251202_sec046_p2'
down_revision: Union[str, None] = '20251202_sec045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists (idempotent pattern)"""
    conn = op.get_bind()
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
            AND column_name = '{column_name}'
        )
    """))
    return result.scalar()


def index_exists(index_name: str) -> bool:
    """Check if index exists"""
    conn = op.get_bind()
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname = '{index_name}'
        )
    """))
    return result.scalar()


def upgrade() -> None:
    """
    SEC-046 Phase 2: Add user management columns

    Enterprise Pattern: Idempotent, logged, reversible
    """
    print("=" * 70)
    print("SEC-046 Phase 2: User Management Columns Migration")
    print("=" * 70)

    columns_added = 0

    # ===========================================
    # 1. User Profile Fields
    # ===========================================
    profile_columns = [
        ('first_name', sa.String(100), None),
        ('last_name', sa.String(100), None),
        ('phone', sa.String(20), None),
        ('department', sa.String(100), None),
        ('job_title', sa.String(100), None),
        ('updated_at', sa.DateTime(), None),
    ]

    print("\n[PROFILE] Adding user profile columns...")
    for col_name, col_type, default in profile_columns:
        if not column_exists('users', col_name):
            op.add_column('users', sa.Column(col_name, col_type, nullable=True))
            columns_added += 1
            print(f"  Added: {col_name}")
        else:
            print(f"  Exists: {col_name}")

    # Index for department (common filter)
    if not index_exists('ix_users_department'):
        op.create_index('ix_users_department', 'users', ['department'])
        print("  Index: ix_users_department created")

    # ===========================================
    # 2. Suspension Management Fields
    # ===========================================
    print("\n[SUSPENSION] Adding suspension management columns...")

    if not column_exists('users', 'is_suspended'):
        op.add_column('users',
            sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'))
        columns_added += 1
        print("  Added: is_suspended (default: false)")

    if not column_exists('users', 'suspended_at'):
        op.add_column('users', sa.Column('suspended_at', sa.DateTime(), nullable=True))
        columns_added += 1
        print("  Added: suspended_at")

    if not column_exists('users', 'suspended_by'):
        op.add_column('users', sa.Column('suspended_by', sa.Integer(), nullable=True))
        columns_added += 1
        print("  Added: suspended_by")
        # Foreign key to users.id
        try:
            op.create_foreign_key(
                'fk_users_suspended_by', 'users', 'users',
                ['suspended_by'], ['id']
            )
            print("  FK: fk_users_suspended_by created")
        except Exception as e:
            print(f"  FK: Already exists or skipped: {e}")

    if not column_exists('users', 'suspension_reason'):
        op.add_column('users',
            sa.Column('suspension_reason', sa.String(500), nullable=True))
        columns_added += 1
        print("  Added: suspension_reason")

    # Index for suspended users (filter)
    if not index_exists('ix_users_is_suspended'):
        op.create_index('ix_users_is_suspended', 'users', ['is_suspended'])
        print("  Index: ix_users_is_suspended created")

    # ===========================================
    # 3. Session Management Fields
    # ===========================================
    print("\n[SESSION] Adding session management columns...")

    if not column_exists('users', 'token_version'):
        op.add_column('users',
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))
        columns_added += 1
        print("  Added: token_version (default: 0)")

    if not column_exists('users', 'last_logout'):
        op.add_column('users', sa.Column('last_logout', sa.DateTime(), nullable=True))
        columns_added += 1
        print("  Added: last_logout")

    if not column_exists('users', 'last_active_at'):
        op.add_column('users', sa.Column('last_active_at', sa.DateTime(), nullable=True))
        columns_added += 1
        print("  Added: last_active_at")

    # ===========================================
    # Summary
    # ===========================================
    print("")
    print("=" * 70)
    print(f"SEC-046 Phase 2 MIGRATION COMPLETE: {columns_added} columns added")
    print("=" * 70)
    print("")
    print("FEATURES ENABLED:")
    print("  - User profile management (name, phone, department, title)")
    print("  - User suspension (without delete for compliance)")
    print("  - Force logout (token versioning)")
    print("  - Activity tracking (last_active_at)")
    print("")
    print("COMPLIANCE:")
    print("  SOC 2 CC6.1  - User lifecycle management")
    print("  HIPAA 164.312 - Access controls")
    print("  PCI-DSS 8.1  - User identification")
    print("  NIST AC-2    - Account management")
    print("=" * 70)


def downgrade() -> None:
    """
    SEC-046 Phase 2: Remove user management columns (reversible)
    """
    print("=" * 70)
    print("SEC-046 Phase 2: Rolling back User Management Columns")
    print("=" * 70)

    # Session columns
    for col in ['last_active_at', 'last_logout', 'token_version']:
        if column_exists('users', col):
            op.drop_column('users', col)
            print(f"  Dropped: {col}")

    # Suspension columns
    if column_exists('users', 'suspended_by'):
        try:
            op.drop_constraint('fk_users_suspended_by', 'users', type_='foreignkey')
        except:
            pass

    for col in ['suspension_reason', 'suspended_by', 'suspended_at']:
        if column_exists('users', col):
            op.drop_column('users', col)
            print(f"  Dropped: {col}")

    if column_exists('users', 'is_suspended'):
        if index_exists('ix_users_is_suspended'):
            op.drop_index('ix_users_is_suspended', 'users')
        op.drop_column('users', 'is_suspended')
        print("  Dropped: is_suspended + index")

    # Profile columns
    if index_exists('ix_users_department'):
        op.drop_index('ix_users_department', 'users')

    for col in ['updated_at', 'job_title', 'department', 'phone', 'last_name', 'first_name']:
        if column_exists('users', col):
            op.drop_column('users', col)
            print(f"  Dropped: {col}")

    print("")
    print("=" * 70)
    print("SEC-046 Phase 2 ROLLBACK COMPLETE")
    print("=" * 70)
