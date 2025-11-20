"""phase2b_fix_idempotent_cognito_integration

Revision ID: 30db27b1ba18
Revises: 4b29c02bbab8
Create Date: 2025-11-20 16:25:50.537749

This migration completes the Phase 2 Cognito integration by creating
only the missing tables. The columns were already added to users table
by a previous partial migration.

This migration is idempotent - safe to run even if some components exist.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '30db27b1ba18'
down_revision: Union[str, None] = '4b29c02bbab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 2B: Complete AWS Cognito Integration (Idempotent Fix)

    Creates only missing components:
    - login_attempts table (if not exists)
    - auth_audit_log table (if not exists)
    - cognito_tokens table (if not exists)
    - RLS policies (if not exist)

    Skips columns that already exist in users table.
    """
    conn = op.get_bind()

    print("📦 Phase 2B: Completing AWS Cognito Integration (Idempotent Fix)")
    print("=" * 70)

    # Helper function to check if table exists
    def table_exists(table_name):
        result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            )
        """))
        return result.scalar()

    # Step 1: Create login_attempts table (brute force detection)
    if not table_exists('login_attempts'):
        print("🚨 Step 1: Creating login_attempts table for brute force detection...")
        op.create_table(
            'login_attempts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 support
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('success', sa.Boolean(), default=False),
            sa.Column('failure_reason', sa.String(255), nullable=True),
            sa.Column('cognito_user_id', sa.String(255), nullable=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('attempted_at', sa.DateTime(), nullable=False, server_default=text('NOW()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.Index('idx_login_attempts_email', 'email'),
            sa.Index('idx_login_attempts_ip', 'ip_address'),
            sa.Index('idx_login_attempts_timestamp', 'attempted_at'),
        )
        print("✅ login_attempts table created")
    else:
        print("⏭️  Step 1: login_attempts table already exists, skipping")

    # Step 2: Create auth_audit_log table (comprehensive compliance logging)
    if not table_exists('auth_audit_log'):
        print("📝 Step 2: Creating auth_audit_log for compliance...")
        op.create_table(
            'auth_audit_log',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('event_type', sa.String(100), nullable=False),  # login, logout, token_refresh, api_key_use
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('cognito_user_id', sa.String(255), nullable=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('api_key_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('success', sa.Boolean(), nullable=False),
            sa.Column('failure_reason', sa.String(255), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Additional context
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=text('NOW()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id']),
            sa.Index('idx_auth_audit_event_type', 'event_type'),
            sa.Index('idx_auth_audit_user_id', 'user_id'),
            sa.Index('idx_auth_audit_org_id', 'organization_id'),
            sa.Index('idx_auth_audit_timestamp', 'timestamp'),
        )
        print("✅ auth_audit_log table created")
    else:
        print("⏭️  Step 2: auth_audit_log table already exists, skipping")

    # Step 3: Create cognito_tokens table (token tracking for revocation)
    if not table_exists('cognito_tokens'):
        print("🎫 Step 3: Creating cognito_tokens table for token management...")
        op.create_table(
            'cognito_tokens',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('cognito_user_id', sa.String(255), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('token_jti', sa.String(255), nullable=False),  # JWT ID claim
            sa.Column('token_type', sa.String(50), nullable=False),  # id, access, refresh
            sa.Column('issued_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('is_revoked', sa.Boolean(), default=False),
            sa.Column('revocation_reason', sa.String(255), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.Index('idx_cognito_tokens_jti', 'token_jti', unique=True),
            sa.Index('idx_cognito_tokens_user', 'user_id'),
            sa.Index('idx_cognito_tokens_revoked', 'is_revoked'),
        )
        print("✅ cognito_tokens table created")
    else:
        print("⏭️  Step 3: cognito_tokens table already exists, skipping")

    # Step 4: Enable RLS on new tables (idempotent)
    print("🔒 Step 4: Enabling Row-Level Security on new tables...")

    # Enable RLS (idempotent - won't error if already enabled)
    if table_exists('login_attempts'):
        op.execute(text("ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY"))
    if table_exists('auth_audit_log'):
        op.execute(text("ALTER TABLE auth_audit_log ENABLE ROW LEVEL SECURITY"))
    if table_exists('cognito_tokens'):
        op.execute(text("ALTER TABLE cognito_tokens ENABLE ROW LEVEL SECURITY"))

    # Helper function to check if policy exists
    def policy_exists(policy_name, table_name):
        result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM pg_policies
                WHERE tablename = '{table_name}'
                AND policyname = '{policy_name}'
            )
        """))
        return result.scalar()

    # Create RLS policies (only if they don't exist)
    if table_exists('login_attempts'):
        if not policy_exists('tenant_isolation_login_attempts', 'login_attempts'):
            op.execute(text("""
                CREATE POLICY tenant_isolation_login_attempts ON login_attempts
                USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
            """))

        if not policy_exists('platform_owner_metadata_login_attempts', 'login_attempts'):
            op.execute(text("""
                CREATE POLICY platform_owner_metadata_login_attempts ON login_attempts
                FOR SELECT
                USING (current_setting('app.current_organization_id', TRUE) = '1')
            """))

    if table_exists('auth_audit_log'):
        if not policy_exists('tenant_isolation_auth_audit_log', 'auth_audit_log'):
            op.execute(text("""
                CREATE POLICY tenant_isolation_auth_audit_log ON auth_audit_log
                USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
            """))

        if not policy_exists('platform_owner_metadata_auth_audit_log', 'auth_audit_log'):
            op.execute(text("""
                CREATE POLICY platform_owner_metadata_auth_audit_log ON auth_audit_log
                FOR SELECT
                USING (current_setting('app.current_organization_id', TRUE) = '1')
            """))

    if table_exists('cognito_tokens'):
        if not policy_exists('tenant_isolation_cognito_tokens', 'cognito_tokens'):
            op.execute(text("""
                CREATE POLICY tenant_isolation_cognito_tokens ON cognito_tokens
                USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
            """))

        if not policy_exists('platform_owner_metadata_cognito_tokens', 'cognito_tokens'):
            op.execute(text("""
                CREATE POLICY platform_owner_metadata_cognito_tokens ON cognito_tokens
                FOR SELECT
                USING (current_setting('app.current_organization_id', TRUE) = '1')
            """))

    print("✅ Row-Level Security enabled on all tables")

    print("")
    print("=" * 70)
    print("✅ PHASE 2B MIGRATION COMPLETE: AWS Cognito Integration Fixed")
    print("=" * 70)
    print("")
    print("🎯 ACCOMPLISHMENTS:")
    print("  ✅ login_attempts table created/verified")
    print("  ✅ auth_audit_log table created/verified")
    print("  ✅ cognito_tokens table created/verified")
    print("  ✅ Row-Level Security enabled on all tables")
    print("  ✅ 6 RLS policies created/verified (tenant isolation + platform owner)")
    print("")
    print("🔐 SECURITY FEATURES:")
    print("  ✅ Brute force detection via login_attempts")
    print("  ✅ Complete auth audit trail for compliance")
    print("  ✅ Token revocation support via cognito_tokens")
    print("  ✅ PostgreSQL RLS enforces multi-tenancy")
    print("")
    print("=" * 70)


def downgrade() -> None:
    """
    Rollback Phase 2B: Remove only the tables created by this migration

    NOTE: This will NOT remove columns from users table as they may have been
    created by the original phase2_add_cognito_integration migration.
    """
    print("⚠️  Rolling back Phase 2B: AWS Cognito Integration Tables")

    # Drop RLS policies first
    op.execute(text("DROP POLICY IF EXISTS tenant_isolation_login_attempts ON login_attempts"))
    op.execute(text("DROP POLICY IF EXISTS platform_owner_metadata_login_attempts ON login_attempts"))
    op.execute(text("DROP POLICY IF EXISTS tenant_isolation_auth_audit_log ON auth_audit_log"))
    op.execute(text("DROP POLICY IF EXISTS platform_owner_metadata_auth_audit_log ON auth_audit_log"))
    op.execute(text("DROP POLICY IF EXISTS tenant_isolation_cognito_tokens ON cognito_tokens"))
    op.execute(text("DROP POLICY IF EXISTS platform_owner_metadata_cognito_tokens ON cognito_tokens"))

    # Drop tables
    op.drop_table('cognito_tokens')
    op.drop_table('auth_audit_log')
    op.drop_table('login_attempts')

    print("✅ Phase 2B rollback complete (tables dropped)")
    print("⚠️  NOTE: Cognito columns in users table were NOT removed (from original migration)")
