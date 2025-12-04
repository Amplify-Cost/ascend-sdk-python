"""SEC-071: Admin Console - Add Missing Columns (Idempotent)

Adds columns missing from models that admin_console_routes.py references.

NOTE: Most admin console columns were already added by:
- SEC-046 Phase 2: User profile, suspension, session columns
- 20251125: Organization email_domains
- 20251202: AgentAction processing_time_ms

This migration adds ONLY the remaining missing columns:
- User: mfa_enabled (MFA status tracking)
- Organization: owner_user_id (ownership tracking for permission enforcement)

Pattern: Idempotent - checks if column exists before adding.

Compliance:
- SOC 2 CC6.1: MFA tracking for access controls
- NIST IA-2: Multi-factor authentication enforcement
- PCI-DSS 8.3: MFA for administrative access

Revision ID: sec071_admin_console
Revises: sec068_autonomous
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers
revision: str = 'sec071_admin_console'
down_revision: Union[str, None] = 'sec068_autonomous'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """
    Check if column exists (idempotent pattern).

    Banking-Level Security: Uses SQLAlchemy Inspector for injection-safe introspection.
    PCI-DSS 6.5.1 Compliant: No string interpolation in SQL queries.
    """
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def index_exists(index_name: str) -> bool:
    """
    Check if index exists.

    Banking-Level Security: Uses SQLAlchemy Inspector for injection-safe introspection.
    """
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    for table_name in inspector.get_table_names():
        indexes = inspector.get_indexes(table_name)
        if any(idx['name'] == index_name for idx in indexes):
            return True
    return False


def upgrade() -> None:
    """SEC-071: Add missing admin console columns (idempotent)."""
    print("=" * 70)
    print("SEC-071: Admin Console Missing Columns Migration")
    print("=" * 70)

    columns_added = 0

    # ===========================================
    # 1. User: MFA Status Tracking
    # ===========================================
    print("\n[USER] Checking mfa_enabled column...")

    if not column_exists('users', 'mfa_enabled'):
        op.add_column('users',
            sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
        columns_added += 1
        print("  ✅ Added: mfa_enabled (default: false)")
    else:
        print("  ⏭️  Exists: mfa_enabled (skipped)")

    # ===========================================
    # 2. Organization: Owner Tracking
    # ===========================================
    print("\n[ORGANIZATION] Checking owner_user_id column...")

    if not column_exists('organizations', 'owner_user_id'):
        op.add_column('organizations',
            sa.Column('owner_user_id', sa.Integer(), nullable=True))
        columns_added += 1
        print("  ✅ Added: owner_user_id")

        # Add foreign key constraint
        try:
            op.create_foreign_key(
                'fk_organizations_owner_user_id',
                'organizations', 'users',
                ['owner_user_id'], ['id']
            )
            print("  ✅ FK: fk_organizations_owner_user_id created")
        except Exception as e:
            print(f"  ⚠️  FK: Skipped (may already exist): {e}")

        # Add index for faster lookups
        if not index_exists('ix_organizations_owner_user_id'):
            op.create_index('ix_organizations_owner_user_id', 'organizations', ['owner_user_id'])
            print("  ✅ Index: ix_organizations_owner_user_id created")
    else:
        print("  ⏭️  Exists: owner_user_id (skipped)")

    # ===========================================
    # Summary
    # ===========================================
    print("")
    print("=" * 70)
    print(f"SEC-071 MIGRATION COMPLETE: {columns_added} columns added")
    print("=" * 70)

    if columns_added > 0:
        print("")
        print("FEATURES ENABLED:")
        print("  - MFA status tracking for user list display")
        print("  - Organization owner tracking for permission enforcement")
        print("")
        print("COMPLIANCE:")
        print("  SOC 2 CC6.1  - MFA access control tracking")
        print("  NIST IA-2    - Multi-factor authentication")
        print("  PCI-DSS 8.3  - MFA for admin access")
    else:
        print("")
        print("All columns already exist - no changes made.")

    print("=" * 70)


def downgrade() -> None:
    """SEC-071: Remove admin console columns (reversible)."""
    print("=" * 70)
    print("SEC-071: Rolling back Admin Console Columns")
    print("=" * 70)

    # Organization owner_user_id
    if column_exists('organizations', 'owner_user_id'):
        if index_exists('ix_organizations_owner_user_id'):
            op.drop_index('ix_organizations_owner_user_id', table_name='organizations')
            print("  Dropped index: ix_organizations_owner_user_id")

        try:
            op.drop_constraint('fk_organizations_owner_user_id', 'organizations', type_='foreignkey')
            print("  Dropped FK: fk_organizations_owner_user_id")
        except Exception:
            pass

        op.drop_column('organizations', 'owner_user_id')
        print("  Dropped column: owner_user_id")

    # User mfa_enabled
    if column_exists('users', 'mfa_enabled'):
        op.drop_column('users', 'mfa_enabled')
        print("  Dropped column: mfa_enabled")

    print("")
    print("=" * 70)
    print("SEC-071 ROLLBACK COMPLETE")
    print("=" * 70)
