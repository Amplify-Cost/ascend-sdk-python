"""OW-kai Enterprise Phase 4: Compliance Export Tables

Revision ID: 20251128_compliance_export
Revises: 20251128_servicenow
Create Date: 2025-11-28 20:00:00.000000

Creates tables for enterprise compliance export system:
- compliance_export_jobs: Tracks export requests and status
- compliance_export_downloads: Audit trail for downloads
- compliance_schedules: Scheduled compliance reports

SEC-022: Fixed migration chain - down_revision corrected from
'20251128_servicenow_integration' to '20251128_servicenow' to match
the actual revision ID declared in 20251128_servicenow_integration.py
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251128_compliance_export'
# SEC-022: Corrected down_revision to match actual ServiceNow revision ID
down_revision: Union[str, None] = '20251128_servicenow'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================
    # Compliance Export Jobs Table
    # ============================================
    op.create_table(
        'compliance_export_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Export Configuration
        sa.Column('framework', sa.String(50), nullable=False),  # sox, pci_dss, hipaa, gdpr, soc2, nist_csf, iso_27001
        sa.Column('report_type', sa.String(50), nullable=False),  # audit_trail, access_log, etc.
        sa.Column('export_format', sa.String(20), default='json'),  # json, csv, pdf, xml, xlsx

        # Date Range
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),

        # Status
        sa.Column('status', sa.String(20), default='pending'),  # pending, processing, completed, failed, expired
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Output
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),

        # Security
        sa.Column('file_hash', sa.String(64), nullable=True),  # SHA-256 hash
        sa.Column('data_classification', sa.String(20), default='confidential'),
        sa.Column('include_pii', sa.Boolean(), default=False),

        # Metadata
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('requested_by', sa.Integer(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for compliance_export_jobs
    op.create_index(
        'ix_compliance_export_jobs_org_id',
        'compliance_export_jobs',
        ['organization_id']
    )
    op.create_index(
        'ix_compliance_export_jobs_framework',
        'compliance_export_jobs',
        ['framework']
    )
    op.create_index(
        'ix_compliance_export_jobs_status',
        'compliance_export_jobs',
        ['status']
    )
    op.create_index(
        'ix_compliance_export_jobs_created_at',
        'compliance_export_jobs',
        ['created_at']
    )

    # ============================================
    # Compliance Export Downloads Table
    # ============================================
    op.create_table(
        'compliance_export_downloads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('export_job_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Download Info
        sa.Column('downloaded_by', sa.Integer(), nullable=False),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('user_agent', sa.String(500), nullable=True),

        # Verification
        sa.Column('verified_hash', sa.Boolean(), default=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['export_job_id'], ['compliance_export_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['downloaded_by'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for compliance_export_downloads
    op.create_index(
        'ix_compliance_export_downloads_job_id',
        'compliance_export_downloads',
        ['export_job_id']
    )
    op.create_index(
        'ix_compliance_export_downloads_org_id',
        'compliance_export_downloads',
        ['organization_id']
    )
    op.create_index(
        'ix_compliance_export_downloads_downloaded_at',
        'compliance_export_downloads',
        ['downloaded_at']
    )

    # ============================================
    # Compliance Schedules Table
    # ============================================
    op.create_table(
        'compliance_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Schedule Config
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('export_format', sa.String(20), default='pdf'),

        # Schedule
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('is_active', sa.Boolean(), default=True),

        # Recipients
        sa.Column('email_recipients', sa.JSON(), nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),

        # Retention
        sa.Column('retention_days', sa.Integer(), default=90),

        # Metadata
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )

    # Indexes for compliance_schedules
    op.create_index(
        'ix_compliance_schedules_org_id',
        'compliance_schedules',
        ['organization_id']
    )
    op.create_index(
        'ix_compliance_schedules_framework',
        'compliance_schedules',
        ['framework']
    )
    op.create_index(
        'ix_compliance_schedules_is_active',
        'compliance_schedules',
        ['is_active']
    )
    op.create_index(
        'ix_compliance_schedules_next_run_at',
        'compliance_schedules',
        ['next_run_at']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_compliance_schedules_next_run_at', table_name='compliance_schedules')
    op.drop_index('ix_compliance_schedules_is_active', table_name='compliance_schedules')
    op.drop_index('ix_compliance_schedules_framework', table_name='compliance_schedules')
    op.drop_index('ix_compliance_schedules_org_id', table_name='compliance_schedules')

    op.drop_index('ix_compliance_export_downloads_downloaded_at', table_name='compliance_export_downloads')
    op.drop_index('ix_compliance_export_downloads_org_id', table_name='compliance_export_downloads')
    op.drop_index('ix_compliance_export_downloads_job_id', table_name='compliance_export_downloads')

    op.drop_index('ix_compliance_export_jobs_created_at', table_name='compliance_export_jobs')
    op.drop_index('ix_compliance_export_jobs_status', table_name='compliance_export_jobs')
    op.drop_index('ix_compliance_export_jobs_framework', table_name='compliance_export_jobs')
    op.drop_index('ix_compliance_export_jobs_org_id', table_name='compliance_export_jobs')

    # Drop tables
    op.drop_table('compliance_schedules')
    op.drop_table('compliance_export_downloads')
    op.drop_table('compliance_export_jobs')
