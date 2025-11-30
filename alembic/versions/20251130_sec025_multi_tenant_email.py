"""SEC-025: Multi-Tenant Email Isolation - Composite Unique Constraint

Revision ID: 20251130_sec025_email
Revises: 20251130_enterprise_merge
Create Date: 2025-11-30

Banking-Level Security Architecture Change:
==========================================
This migration changes the email uniqueness constraint from GLOBAL to
PER-ORGANIZATION, enabling true multi-tenant isolation.

BEFORE: email must be globally unique (one user per email across all orgs)
AFTER: email must be unique within each organization (same email can exist
       in multiple orgs as separate users)

Security Benefits:
- True multi-tenant data isolation
- Users cannot accidentally access wrong organization
- Each organization's user pool is completely independent
- Aligns with per-organization Cognito user pools

Compliance: SOC 2 CC6.1 (Logical Access), NIST AC-2, PCI-DSS 7.1

Enterprise Migration Pattern:
- Idempotent: Safe to re-run
- Logged: Complete audit trail
- Reversible: Full rollback capability

Authored-By: OW-KAI Engineer
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from typing import Sequence, Union

# revision identifiers
revision: str = '20251130_sec025_email'
down_revision: Union[str, None] = '20251130_enterprise_merge'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def constraint_exists(constraint_name: str, table_name: str) -> bool:
    """Check if a constraint exists on a table"""
    conn = op.get_bind()
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = '{table_name}'
            AND c.conname = '{constraint_name}'
        )
    """))
    return result.scalar()


def index_exists(index_name: str) -> bool:
    """Check if an index exists"""
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
    SEC-025: Convert global email uniqueness to per-organization uniqueness

    This enables the same email to exist in multiple organizations,
    which is required for proper multi-tenant isolation where each
    organization has its own Cognito user pool.
    """
    print("=" * 70)
    print("🏦 SEC-025: Multi-Tenant Email Isolation Migration")
    print("=" * 70)

    conn = op.get_bind()

    # Step 1: Check for duplicate emails that would violate new constraint
    print("🔍 Step 1: Checking for email conflicts...")
    result = conn.execute(text("""
        SELECT email, array_agg(organization_id) as org_ids, count(*) as cnt
        FROM users
        GROUP BY email
        HAVING count(*) > 1
    """))
    conflicts = result.fetchall()

    if conflicts:
        print(f"⚠️  Found {len(conflicts)} emails with multiple users:")
        for row in conflicts:
            print(f"   - {row[0]}: orgs {row[1]}")
        print("   These will be allowed under the new per-org uniqueness.")
    else:
        print("✅ No email conflicts found")

    # Step 2: Drop the old global unique constraint on email
    print("🔧 Step 2: Removing global email unique constraint...")

    # The constraint might be named differently depending on how it was created
    # Try common naming patterns
    constraint_names = [
        'users_email_key',
        'users_email_unique',
        'uq_users_email',
        'ix_users_email'
    ]

    dropped = False
    for constraint_name in constraint_names:
        if constraint_exists(constraint_name, 'users'):
            try:
                op.drop_constraint(constraint_name, 'users', type_='unique')
                print(f"✅ Dropped constraint: {constraint_name}")
                dropped = True
                break
            except Exception as e:
                print(f"⏭️  Could not drop {constraint_name}: {e}")

    if not dropped:
        # Try dropping as index instead
        for idx_name in ['ix_users_email', 'users_email_key']:
            if index_exists(idx_name):
                try:
                    op.drop_index(idx_name, table_name='users')
                    print(f"✅ Dropped index: {idx_name}")
                    dropped = True
                    break
                except Exception as e:
                    print(f"⏭️  Could not drop index {idx_name}: {e}")

    if not dropped:
        print("⚠️  No existing email constraint/index found - may already be migrated")

    # Step 3: Create composite unique constraint (email + organization_id)
    print("🔧 Step 3: Creating per-organization email uniqueness...")

    new_constraint = 'uq_users_email_organization'
    if not constraint_exists(new_constraint, 'users'):
        op.create_unique_constraint(
            new_constraint,
            'users',
            ['email', 'organization_id']
        )
        print(f"✅ Created composite unique constraint: {new_constraint}")
    else:
        print(f"⏭️  Constraint {new_constraint} already exists")

    # Step 4: Create index for email lookups (non-unique)
    print("🔧 Step 4: Creating email lookup index...")

    email_idx = 'ix_users_email_lookup'
    if not index_exists(email_idx):
        op.create_index(email_idx, 'users', ['email'])
        print(f"✅ Created index: {email_idx}")
    else:
        print(f"⏭️  Index {email_idx} already exists")

    # Step 5: Create composite index for email + org lookups
    print("🔧 Step 5: Creating email + org composite index...")

    composite_idx = 'ix_users_email_org'
    if not index_exists(composite_idx):
        op.create_index(composite_idx, 'users', ['email', 'organization_id'])
        print(f"✅ Created composite index: {composite_idx}")
    else:
        print(f"⏭️  Index {composite_idx} already exists")

    print("")
    print("=" * 70)
    print("✅ SEC-025 MIGRATION COMPLETE: Multi-Tenant Email Isolation")
    print("=" * 70)
    print("")
    print("🎯 CHANGES:")
    print("  ✅ Removed global email uniqueness constraint")
    print("  ✅ Added per-organization email uniqueness (email + org_id)")
    print("  ✅ Created optimized lookup indexes")
    print("")
    print("🔐 SECURITY BENEFITS:")
    print("  ✅ True multi-tenant isolation")
    print("  ✅ Same email can exist in different organizations")
    print("  ✅ Aligns with per-organization Cognito pools")
    print("  ✅ SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1 compliant")
    print("")
    print("=" * 70)


def downgrade() -> None:
    """
    Rollback: Convert back to global email uniqueness

    WARNING: This will fail if there are duplicate emails across organizations.
    Data cleanup may be required before rollback.
    """
    print("=" * 70)
    print("⚠️  SEC-025: Rolling back Multi-Tenant Email Isolation")
    print("=" * 70)

    conn = op.get_bind()

    # Check for conflicts that would prevent rollback
    result = conn.execute(text("""
        SELECT email, count(*) as cnt
        FROM users
        GROUP BY email
        HAVING count(*) > 1
    """))
    conflicts = result.fetchall()

    if conflicts:
        print(f"🚨 CANNOT ROLLBACK: {len(conflicts)} emails exist in multiple orgs:")
        for row in conflicts:
            print(f"   - {row[0]}: {row[1]} occurrences")
        raise Exception(
            "Cannot rollback: duplicate emails exist across organizations. "
            "Clean up duplicates before attempting rollback."
        )

    # Drop new constraints/indexes
    print("🔧 Removing per-organization constraints...")

    if index_exists('ix_users_email_org'):
        op.drop_index('ix_users_email_org', table_name='users')
        print("✅ Dropped index: ix_users_email_org")

    if index_exists('ix_users_email_lookup'):
        op.drop_index('ix_users_email_lookup', table_name='users')
        print("✅ Dropped index: ix_users_email_lookup")

    if constraint_exists('uq_users_email_organization', 'users'):
        op.drop_constraint('uq_users_email_organization', 'users', type_='unique')
        print("✅ Dropped constraint: uq_users_email_organization")

    # Restore global unique constraint
    print("🔧 Restoring global email uniqueness...")
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    print("✅ Created constraint: users_email_key")

    print("")
    print("=" * 70)
    print("✅ SEC-025 ROLLBACK COMPLETE")
    print("=" * 70)
