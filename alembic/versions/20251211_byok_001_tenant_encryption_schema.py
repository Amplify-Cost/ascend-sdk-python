"""BYOK-001: Tenant encryption keys schema for BYOK/CMK support

Revision ID: byok_001_schema
Revises: c10d8fe3d900
Create Date: 2025-12-11

SEC Ticket: BYOK-001
Requirement: Zero Breaking Changes - additive only, no modifications to existing tables
Compliance: SOC 2 Type II, PCI-DSS 3.5, HIPAA 164.312, FedRAMP SC-12, NIST 800-53 SC-12/SC-13

This migration creates the schema for Bring Your Own Key (BYOK) / Customer Managed Key (CMK)
support. It is ADDITIVE ONLY and does not modify any existing tables.

Tables created:
- tenant_encryption_keys: Stores customer CMK ARN and status
- encrypted_data_keys: Stores DEKs encrypted by customer CMK (envelope encryption)
- byok_audit_log: Audit trail for all BYOK operations

All tables have RLS policies for multi-tenant isolation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'byok_001_schema'
down_revision = 'c10d8fe3d900'
branch_labels = ('byok',)
depends_on = None


def upgrade() -> None:
    # === BYOK-001: tenant_encryption_keys table ===
    # Stores customer's CMK ARN and configuration
    op.create_table(
        'tenant_encryption_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Customer's KMS key ARN (cross-account)
        sa.Column('cmk_arn', sa.String(512), nullable=False),
        sa.Column('cmk_alias', sa.String(255), nullable=True),

        # Key metadata
        sa.Column('key_provider', sa.String(50), server_default='aws_kms', nullable=False),
        sa.Column('key_spec', sa.String(50), server_default='SYMMETRIC_DEFAULT', nullable=False),

        # Key version tracking for rotation detection (BYOK-011)
        sa.Column('cmk_key_id', sa.String(128), nullable=True),  # AWS KMS Key ID (changes on rotation)
        sa.Column('last_key_version', sa.String(128), nullable=True),  # For detecting rotation

        # Status tracking
        sa.Column('status', sa.String(50), server_default='pending_validation', nullable=False),
        sa.Column('status_reason', sa.Text(), nullable=True),
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_rotation_at', sa.DateTime(timezone=True), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', name='uq_tenant_encryption_keys_org'),
        sa.CheckConstraint(
            "status IN ('pending_validation', 'active', 'revoked', 'rotation_pending', 'error')",
            name='ck_tenant_encryption_keys_status'
        ),
        sa.CheckConstraint(
            "key_provider IN ('aws_kms')",  # Future: 'azure_keyvault', 'gcp_kms'
            name='ck_tenant_encryption_keys_provider'
        )
    )

    # Index for fast lookup by organization
    op.create_index(
        'idx_tenant_encryption_keys_org',
        'tenant_encryption_keys',
        ['organization_id']
    )

    # Index for status queries (health check)
    op.create_index(
        'idx_tenant_encryption_keys_status',
        'tenant_encryption_keys',
        ['status']
    )

    # === BYOK-001: encrypted_data_keys table ===
    # Stores DEKs encrypted by customer CMK (envelope encryption pattern)
    op.create_table(
        'encrypted_data_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Encrypted DEK (Data Encryption Key)
        sa.Column('encrypted_dek', sa.LargeBinary(), nullable=False),
        sa.Column('dek_algorithm', sa.String(50), server_default='AES-256-GCM', nullable=False),

        # Key context for additional authenticated data (AAD)
        sa.Column('encryption_context', postgresql.JSONB(), server_default='{}', nullable=False),

        # Versioning for rotation (BYOK-007, BYOK-011)
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_current', sa.Boolean(), server_default='true', nullable=False),

        # CMK version that encrypted this DEK (for rotation tracking)
        sa.Column('cmk_key_version', sa.String(128), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'version', name='uq_encrypted_data_keys_org_version')
    )

    # Index for current DEK lookup (most common query)
    op.create_index(
        'idx_encrypted_data_keys_current',
        'encrypted_data_keys',
        ['organization_id'],
        postgresql_where=sa.text('is_current = TRUE')
    )

    # Index for version queries
    op.create_index(
        'idx_encrypted_data_keys_org_version',
        'encrypted_data_keys',
        ['organization_id', 'version']
    )

    # === BYOK-001: byok_audit_log table ===
    # Audit trail for all BYOK operations (compliance requirement)
    op.create_table(
        'byok_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Operation details
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('cmk_arn', sa.String(512), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Additional metadata
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "operation IN ('key_registered', 'key_validated', 'key_revoked', 'key_rotated', "
            "'dek_generated', 'encrypt', 'decrypt', 'access_denied', 'auto_rotation_detected', "
            "'validation_failed', 'health_check')",
            name='ck_byok_audit_log_operation'
        )
    )

    # Index for audit queries (most recent first)
    op.create_index(
        'idx_byok_audit_log_org_time',
        'byok_audit_log',
        ['organization_id', sa.text('created_at DESC')]
    )

    # Index for operation type queries
    op.create_index(
        'idx_byok_audit_log_operation',
        'byok_audit_log',
        ['operation', 'created_at']
    )

    # === RLS POLICIES ===
    # CRITICAL: Maintain multi-tenant isolation

    # Enable RLS on all BYOK tables
    op.execute("ALTER TABLE tenant_encryption_keys ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE encrypted_data_keys ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE byok_audit_log ENABLE ROW LEVEL SECURITY")

    # RLS policy: users can only see their organization's encryption keys
    op.execute("""
        CREATE POLICY tenant_encryption_keys_isolation ON tenant_encryption_keys
        FOR ALL
        USING (organization_id = COALESCE(
            NULLIF(current_setting('app.current_organization_id', true), '')::INTEGER,
            0
        ))
    """)

    # RLS policy: users can only see their organization's DEKs
    op.execute("""
        CREATE POLICY encrypted_data_keys_isolation ON encrypted_data_keys
        FOR ALL
        USING (organization_id = COALESCE(
            NULLIF(current_setting('app.current_organization_id', true), '')::INTEGER,
            0
        ))
    """)

    # RLS policy: users can only see their organization's audit logs
    op.execute("""
        CREATE POLICY byok_audit_log_isolation ON byok_audit_log
        FOR ALL
        USING (organization_id = COALESCE(
            NULLIF(current_setting('app.current_organization_id', true), '')::INTEGER,
            0
        ))
    """)

    # === BYOK Service Role ===
    # Create a role for the encryption service that can bypass RLS for health checks
    # This is similar to auth_service role pattern from SEC-RLS-002
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'byok_service') THEN
                CREATE ROLE byok_service NOLOGIN;
            END IF;
        END
        $$;
    """)

    # Grant byok_service SELECT on tenant_encryption_keys for health checks
    op.execute("GRANT SELECT ON tenant_encryption_keys TO byok_service")
    op.execute("GRANT SELECT, INSERT ON encrypted_data_keys TO byok_service")
    op.execute("GRANT SELECT, INSERT ON byok_audit_log TO byok_service")

    # Bypass RLS for byok_service (needed for cross-tenant health checks)
    op.execute("""
        CREATE POLICY byok_service_all_keys ON tenant_encryption_keys
        FOR SELECT
        TO byok_service
        USING (true)
    """)

    op.execute("""
        CREATE POLICY byok_service_all_deks ON encrypted_data_keys
        FOR ALL
        TO byok_service
        USING (true)
    """)

    op.execute("""
        CREATE POLICY byok_service_all_audit ON byok_audit_log
        FOR ALL
        TO byok_service
        USING (true)
    """)

    # === Updated timestamp trigger ===
    op.execute("""
        CREATE OR REPLACE FUNCTION update_tenant_encryption_keys_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_tenant_encryption_keys_updated_at
        BEFORE UPDATE ON tenant_encryption_keys
        FOR EACH ROW
        EXECUTE FUNCTION update_tenant_encryption_keys_updated_at();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_tenant_encryption_keys_updated_at ON tenant_encryption_keys")
    op.execute("DROP FUNCTION IF EXISTS update_tenant_encryption_keys_updated_at()")

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS byok_service_all_audit ON byok_audit_log")
    op.execute("DROP POLICY IF EXISTS byok_service_all_deks ON encrypted_data_keys")
    op.execute("DROP POLICY IF EXISTS byok_service_all_keys ON tenant_encryption_keys")
    op.execute("DROP POLICY IF EXISTS byok_audit_log_isolation ON byok_audit_log")
    op.execute("DROP POLICY IF EXISTS encrypted_data_keys_isolation ON encrypted_data_keys")
    op.execute("DROP POLICY IF EXISTS tenant_encryption_keys_isolation ON tenant_encryption_keys")

    # Revoke grants
    op.execute("REVOKE ALL ON byok_audit_log FROM byok_service")
    op.execute("REVOKE ALL ON encrypted_data_keys FROM byok_service")
    op.execute("REVOKE ALL ON tenant_encryption_keys FROM byok_service")

    # Drop role (if no other dependencies)
    op.execute("""
        DO $$
        BEGIN
            DROP ROLE IF EXISTS byok_service;
        EXCEPTION
            WHEN dependent_objects_still_exist THEN
                NULL;
        END
        $$;
    """)

    # Drop indexes
    op.drop_index('idx_byok_audit_log_operation', table_name='byok_audit_log')
    op.drop_index('idx_byok_audit_log_org_time', table_name='byok_audit_log')
    op.drop_index('idx_encrypted_data_keys_org_version', table_name='encrypted_data_keys')
    op.drop_index('idx_encrypted_data_keys_current', table_name='encrypted_data_keys')
    op.drop_index('idx_tenant_encryption_keys_status', table_name='tenant_encryption_keys')
    op.drop_index('idx_tenant_encryption_keys_org', table_name='tenant_encryption_keys')

    # Drop tables
    op.drop_table('byok_audit_log')
    op.drop_table('encrypted_data_keys')
    op.drop_table('tenant_encryption_keys')
