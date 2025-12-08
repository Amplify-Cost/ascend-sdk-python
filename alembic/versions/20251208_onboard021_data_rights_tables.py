"""ONBOARD-021: Create data rights tables with tenant isolation

Enterprise GDPR/CCPA Data Subject Rights Tables
- DataSubjectRequest: GDPR Art. 15, 17, 20 / CCPA 1798.100
- ConsentRecord: GDPR Art. 6-7
- DataLineage: GDPR Art. 30 Records of Processing
- DataErasureLog: GDPR Art. 17 Proof of Deletion

Security:
- organization_id on all tables (NOT NULL, indexed)
- RLS enabled with tenant isolation policies
- Foreign keys to organizations and users tables

Compliance: GDPR, CCPA, SOC 2 CC6.1, HIPAA 164.312(a)(1), PCI-DSS 7.1

Revision ID: onboard021_data_rights
Revises: rbac002_user_platform
Create Date: 2024-12-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'onboard021_data_rights'
down_revision = 'rbac002_user_platform'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # DATA SUBJECT REQUESTS (GDPR Art. 15, 17, 20 / CCPA 1798.100)
    # ═══════════════════════════════════════════════════════════════════════════
    op.create_table(
        'data_subject_requests',
        # Primary identifiers
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', sa.String(50), unique=True, nullable=False),

        # ONBOARD-019: Enterprise tenant isolation
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Request details
        sa.Column('subject_email', sa.String(255), nullable=False),
        sa.Column('subject_id', sa.String(100), nullable=True),
        sa.Column('subject_name', sa.String(255), nullable=True),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('legal_basis', sa.String(50), nullable=False),

        # Status tracking
        sa.Column('status', sa.String(50), nullable=False, server_default='RECEIVED'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='NORMAL'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Request content
        sa.Column('request_details', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('identity_verification', postgresql.JSON(), nullable=True),
        sa.Column('verification_status', sa.String(50), nullable=True),

        # Processing details
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('processing_notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),

        # Results and delivery
        sa.Column('result_data', postgresql.JSON(), nullable=True),
        sa.Column('delivery_method', sa.String(50), nullable=True),
        sa.Column('delivery_status', sa.String(50), nullable=True),
        sa.Column('export_format', sa.String(50), nullable=True),

        # Compliance tracking
        sa.Column('compliance_framework', sa.String(20), nullable=False, server_default='GDPR'),
        sa.Column('retention_period', sa.Integer(), nullable=False, server_default='2555'),
        sa.Column('reason', sa.Text(), nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes for data_subject_requests
    op.create_index('ix_data_subject_requests_organization_id', 'data_subject_requests', ['organization_id'])
    op.create_index('ix_data_subject_requests_subject_email', 'data_subject_requests', ['subject_email'])
    op.create_index('ix_data_subject_requests_status', 'data_subject_requests', ['status'])
    op.create_index('ix_data_subject_requests_request_type', 'data_subject_requests', ['request_type'])
    op.create_index('ix_data_subject_requests_created_at', 'data_subject_requests', ['created_at'])

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA LINEAGE (GDPR Art. 30 - Records of Processing)
    # ═══════════════════════════════════════════════════════════════════════════
    op.create_table(
        'data_lineage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # ONBOARD-019: Enterprise tenant isolation
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Data subject identification
        sa.Column('subject_email', sa.String(255), nullable=False),
        sa.Column('subject_id', sa.String(100), nullable=True),

        # Data location and type
        sa.Column('data_category', sa.String(100), nullable=False),
        sa.Column('data_source', sa.String(100), nullable=False),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('table_name', sa.String(100), nullable=True),
        sa.Column('column_name', sa.String(100), nullable=True),
        sa.Column('record_id', sa.String(100), nullable=True),

        # Data classification
        sa.Column('sensitivity_level', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('legal_basis_processing', sa.String(100), nullable=True),
        sa.Column('processing_purpose', sa.Text(), nullable=True),
        sa.Column('retention_period', sa.String(100), nullable=True),

        # Tracking metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorded_by', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_deletion', sa.DateTime(timezone=True), nullable=True),

        # Cross-references
        sa.Column('related_requests', postgresql.JSON(), nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes for data_lineage
    op.create_index('ix_data_lineage_organization_id', 'data_lineage', ['organization_id'])
    op.create_index('ix_data_lineage_subject_email', 'data_lineage', ['subject_email'])
    op.create_index('ix_data_lineage_subject_id', 'data_lineage', ['subject_id'])
    op.create_index('ix_data_lineage_data_category', 'data_lineage', ['data_category'])

    # ═══════════════════════════════════════════════════════════════════════════
    # CONSENT RECORDS (GDPR Art. 6-7)
    # ═══════════════════════════════════════════════════════════════════════════
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # ONBOARD-019: Enterprise tenant isolation
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Subject identification
        sa.Column('subject_email', sa.String(255), nullable=False),
        sa.Column('subject_id', sa.String(100), nullable=True),

        # Consent details
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.String(50), nullable=False),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='false'),

        # Consent status
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),

        # Metadata
        sa.Column('consent_method', sa.String(50), nullable=False, server_default='API'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),

        # Tracking
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorded_by', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes for consent_records
    op.create_index('ix_consent_records_organization_id', 'consent_records', ['organization_id'])
    op.create_index('ix_consent_records_subject_email', 'consent_records', ['subject_email'])
    op.create_index('ix_consent_records_subject_id', 'consent_records', ['subject_id'])
    op.create_index('ix_consent_records_consent_type', 'consent_records', ['consent_type'])

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA ERASURE LOGS (GDPR Art. 17 - Proof of Deletion)
    # ═══════════════════════════════════════════════════════════════════════════
    op.create_table(
        'data_erasure_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # ONBOARD-019: Enterprise tenant isolation
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Erasure request reference
        sa.Column('request_id', sa.String(50), nullable=False),
        sa.Column('subject_email', sa.String(255), nullable=False),

        # Erasure details
        sa.Column('erasure_type', sa.String(50), nullable=False, server_default='FULL_ERASURE'),
        sa.Column('data_category', sa.String(100), nullable=True),
        sa.Column('source_table', sa.String(100), nullable=True),
        sa.Column('tables_affected', postgresql.JSON(), nullable=True),
        sa.Column('records_affected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_deleted', sa.Integer(), nullable=False, server_default='0'),

        # Execution details
        sa.Column('executed_by', sa.Integer(), nullable=True),
        sa.Column('executed_by_email', sa.String(255), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('execution_method', sa.String(50), nullable=False, server_default='AUTOMATED'),

        # Compliance
        sa.Column('legal_basis', sa.String(100), nullable=True),
        sa.Column('retention_exception', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('exception_reason', sa.Text(), nullable=True),

        # Verification
        sa.Column('verification_hash', sa.String(64), nullable=True),
        sa.Column('backup_status', sa.String(50), nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id'], ondelete='SET NULL'),
    )

    # Indexes for data_erasure_logs
    op.create_index('ix_data_erasure_logs_organization_id', 'data_erasure_logs', ['organization_id'])
    op.create_index('ix_data_erasure_logs_request_id', 'data_erasure_logs', ['request_id'])
    op.create_index('ix_data_erasure_logs_subject_email', 'data_erasure_logs', ['subject_email'])
    op.create_index('ix_data_erasure_logs_executed_at', 'data_erasure_logs', ['executed_at'])

    # ═══════════════════════════════════════════════════════════════════════════
    # ROW LEVEL SECURITY (Defense-in-Depth)
    # ═══════════════════════════════════════════════════════════════════════════

    # Enable RLS on all data rights tables
    op.execute("ALTER TABLE data_subject_requests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE data_lineage ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE data_erasure_logs ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for tenant isolation
    # These policies use the app.current_organization_id session variable
    op.execute("""
        CREATE POLICY tenant_isolation_data_subject_requests ON data_subject_requests
        FOR ALL USING (
            organization_id = COALESCE(
                current_setting('app.current_organization_id', true)::integer,
                organization_id
            )
        )
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_data_lineage ON data_lineage
        FOR ALL USING (
            organization_id = COALESCE(
                current_setting('app.current_organization_id', true)::integer,
                organization_id
            )
        )
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_consent_records ON consent_records
        FOR ALL USING (
            organization_id = COALESCE(
                current_setting('app.current_organization_id', true)::integer,
                organization_id
            )
        )
    """)

    op.execute("""
        CREATE POLICY tenant_isolation_data_erasure_logs ON data_erasure_logs
        FOR ALL USING (
            organization_id = COALESCE(
                current_setting('app.current_organization_id', true)::integer,
                organization_id
            )
        )
    """)


def downgrade():
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS tenant_isolation_data_erasure_logs ON data_erasure_logs")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_consent_records ON consent_records")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_data_lineage ON data_lineage")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_data_subject_requests ON data_subject_requests")

    # Drop indexes
    op.drop_index('ix_data_erasure_logs_executed_at', table_name='data_erasure_logs')
    op.drop_index('ix_data_erasure_logs_subject_email', table_name='data_erasure_logs')
    op.drop_index('ix_data_erasure_logs_request_id', table_name='data_erasure_logs')
    op.drop_index('ix_data_erasure_logs_organization_id', table_name='data_erasure_logs')

    op.drop_index('ix_consent_records_consent_type', table_name='consent_records')
    op.drop_index('ix_consent_records_subject_id', table_name='consent_records')
    op.drop_index('ix_consent_records_subject_email', table_name='consent_records')
    op.drop_index('ix_consent_records_organization_id', table_name='consent_records')

    op.drop_index('ix_data_lineage_data_category', table_name='data_lineage')
    op.drop_index('ix_data_lineage_subject_id', table_name='data_lineage')
    op.drop_index('ix_data_lineage_subject_email', table_name='data_lineage')
    op.drop_index('ix_data_lineage_organization_id', table_name='data_lineage')

    op.drop_index('ix_data_subject_requests_created_at', table_name='data_subject_requests')
    op.drop_index('ix_data_subject_requests_request_type', table_name='data_subject_requests')
    op.drop_index('ix_data_subject_requests_status', table_name='data_subject_requests')
    op.drop_index('ix_data_subject_requests_subject_email', table_name='data_subject_requests')
    op.drop_index('ix_data_subject_requests_organization_id', table_name='data_subject_requests')

    # Drop tables
    op.drop_table('data_erasure_logs')
    op.drop_table('consent_records')
    op.drop_table('data_lineage')
    op.drop_table('data_subject_requests')
