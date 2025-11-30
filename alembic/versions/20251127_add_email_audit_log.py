"""Add email audit log table for enterprise email tracking

Revision ID: 20251127_email_audit
Revises: 20251126_tenant_isolation
Create Date: 2025-11-27

Banking-Level Security: Complete audit trail for all email communications
Compliance: SOC 2, HIPAA, PCI-DSS, GDPR

SEC-022: Connected orphan migration to main chain by setting
down_revision to '20251126_tenant_isolation'. This ensures the
migration runs in proper sequence after tenant isolation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Sequence, Union

# revision identifiers
revision: str = '20251127_email_audit'
# SEC-022: Connected to main migration chain
down_revision: Union[str, None] = '20251126_tenant_isolation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email audit log table
    op.create_table(
        'email_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('to_email', sa.String(255), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False),  # welcome, invitation, password_reset, etc.
        sa.Column('organization_slug', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # sent, failed, bounced
        sa.Column('message_id', sa.String(255), nullable=True),  # SES message ID
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_by', sa.String(255), nullable=False, server_default='system'),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('ix_email_audit_to_email', 'email_audit_log', ['to_email'])
    op.create_index('ix_email_audit_email_type', 'email_audit_log', ['email_type'])
    op.create_index('ix_email_audit_org_slug', 'email_audit_log', ['organization_slug'])
    op.create_index('ix_email_audit_sent_at', 'email_audit_log', ['sent_at'])
    op.create_index('ix_email_audit_status', 'email_audit_log', ['status'])


def downgrade() -> None:
    op.drop_index('ix_email_audit_status', 'email_audit_log')
    op.drop_index('ix_email_audit_sent_at', 'email_audit_log')
    op.drop_index('ix_email_audit_org_slug', 'email_audit_log')
    op.drop_index('ix_email_audit_email_type', 'email_audit_log')
    op.drop_index('ix_email_audit_to_email', 'email_audit_log')
    op.drop_table('email_audit_log')
