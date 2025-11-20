"""phase2_add_cognito_integration

Revision ID: 4b29c02bbab8
Revises: f875ddb7f441
Create Date: 2025-11-20 15:34:10.692821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b29c02bbab8'
down_revision: Union[str, None] = 'f875ddb7f441'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 2: AWS Cognito Integration + Enterprise Security

    Adds:
    - cognito_user_id to users table
    - last_login_at for security monitoring
    - login_attempts table for brute force detection
    - auth_audit_log table for compliance
    """
    from sqlalchemy import text

    print("📦 Phase 2: AWS Cognito Integration")
    print("=" * 70)

    # Step 1: Add Cognito user ID to users table
    print("🔐 Step 1: Adding cognito_user_id to users table...")
    op.add_column('users', sa.Column('cognito_user_id', sa.String(255), nullable=True))
    op.create_index('idx_users_cognito_id', 'users', ['cognito_user_id'], unique=True)
    print("✅ cognito_user_id column added")

    # Step 2: Add last_login_at for security monitoring
    print("⏱️  Step 2: Adding last_login_at for security monitoring...")
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('login_count', sa.Integer(), server_default='0'))
    print("✅ Login tracking columns added")

    # Step 3: Create login_attempts table (brute force detection)
    print("🚨 Step 3: Creating login_attempts table for brute force detection...")
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
        sa.Column('attempted_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.Index('idx_login_attempts_email', 'email'),
        sa.Index('idx_login_attempts_ip', 'ip_address'),
        sa.Index('idx_login_attempts_timestamp', 'attempted_at'),
    )
    print("✅ login_attempts table created")

    # Step 4: Create auth_audit_log table (comprehensive compliance logging)
    print("📝 Step 4: Creating auth_audit_log for compliance...")
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
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id']),
        sa.Index('idx_auth_audit_event_type', 'event_type'),
        sa.Index('idx_auth_audit_user_id', 'user_id'),
        sa.Index('idx_auth_audit_org_id', 'organization_id'),
        sa.Index('idx_auth_audit_timestamp', 'timestamp'),
    )
    print("✅ auth_audit_log table created")

    # Step 5: Create cognito_tokens table (token tracking for revocation)
    print("🎫 Step 5: Creating cognito_tokens table for token management...")
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

    # Step 6: Enable RLS on new tables
    print("🔒 Step 6: Enabling Row-Level Security on new tables...")

    op.execute(text("ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY"))
    op.execute(text("ALTER TABLE auth_audit_log ENABLE ROW LEVEL SECURITY"))
    op.execute(text("ALTER TABLE cognito_tokens ENABLE ROW LEVEL SECURITY"))

    # Tenant isolation policies
    op.execute(text("""
        CREATE POLICY tenant_isolation_login_attempts ON login_attempts
        USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
    """))

    op.execute(text("""
        CREATE POLICY tenant_isolation_auth_audit_log ON auth_audit_log
        USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
    """))

    op.execute(text("""
        CREATE POLICY tenant_isolation_cognito_tokens ON cognito_tokens
        USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER)
    """))

    # Platform owner metadata access
    op.execute(text("""
        CREATE POLICY platform_owner_metadata_login_attempts ON login_attempts
        FOR SELECT
        USING (current_setting('app.current_organization_id', TRUE) = '1')
    """))

    op.execute(text("""
        CREATE POLICY platform_owner_metadata_auth_audit_log ON auth_audit_log
        FOR SELECT
        USING (current_setting('app.current_organization_id', TRUE) = '1')
    """))

    op.execute(text("""
        CREATE POLICY platform_owner_metadata_cognito_tokens ON cognito_tokens
        FOR SELECT
        USING (current_setting('app.current_organization_id', TRUE) = '1')
    """))

    print("✅ Row-Level Security enabled on 3 new tables")

    print("")
    print("=" * 70)
    print("✅ PHASE 2 MIGRATION COMPLETE: AWS Cognito Integration")
    print("=" * 70)
    print("")
    print("🎯 ACCOMPLISHMENTS:")
    print("  ✅ cognito_user_id added to users table")
    print("  ✅ Login tracking columns added (last_login_at, login_count)")
    print("  ✅ login_attempts table created (brute force detection)")
    print("  ✅ auth_audit_log table created (compliance logging)")
    print("  ✅ cognito_tokens table created (token management)")
    print("  ✅ Row-Level Security enabled on 3 new tables")
    print("  ✅ 6 RLS policies created (tenant isolation + platform owner)")
    print("")
    print("🔐 SECURITY FEATURES:")
    print("  ✅ Brute force detection via login_attempts")
    print("  ✅ Complete auth audit trail for compliance")
    print("  ✅ Token revocation support via cognito_tokens")
    print("  ✅ PostgreSQL RLS enforces multi-tenancy")
    print("")
    print("🚀 NEXT STEPS:")
    print("  - Implement Cognito authentication middleware")
    print("  - Create organization admin routes")
    print("  - Create platform admin routes")
    print("")
    print("=" * 70)


def downgrade() -> None:
    """
    Rollback Phase 2: Remove Cognito integration
    """
    from sqlalchemy import text

    print("⚠️  Rolling back Phase 2: AWS Cognito Integration")

    # Drop RLS policies
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

    # Drop columns from users table
    op.drop_index('idx_users_cognito_id', table_name='users')
    op.drop_column('users', 'cognito_user_id')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'login_count')

    print("✅ Phase 2 rollback complete")
