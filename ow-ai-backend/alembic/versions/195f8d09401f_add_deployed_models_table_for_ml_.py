"""add_deployed_models_table_for_ml_registry

Enterprise ML Model Registry Schema

Purpose: Track deployed AI/ML models for governance, compliance scanning, and agent workflows
Compliance: SOX, GDPR, HIPAA, PCI-DSS audit requirements
Architecture: PostgreSQL with JSONB for flexible metadata storage

Revision ID: 195f8d09401f
Revises: 20251119_enterprise_wf
Create Date: 2025-11-19 20:56:27.191954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '195f8d09401f'
down_revision: Union[str, None] = '20251119_enterprise_wf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create deployed_models table for enterprise ML model registry.

    This table enables:
    - Agent compliance scanning (agents can query what models exist)
    - Governance enforcement (GDPR, SOX, HIPAA approvals)
    - Risk assessment and audit trails
    - Integration with external registries (MLflow, SageMaker, Azure ML)
    """
    op.create_table('deployed_models',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('model_name', sa.String(length=500), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),

        # Deployment tracking
        sa.Column('environment', sa.String(length=50), nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deployed_by', sa.String(length=255), nullable=False),

        # Ownership
        sa.Column('model_owner', sa.String(length=255), nullable=False),
        sa.Column('business_unit', sa.String(length=255), nullable=True),

        # Compliance and governance
        sa.Column('compliance_status', sa.Enum('COMPLIANT', 'PENDING_REVIEW', 'NON_COMPLIANT', 'AUDIT_REQUIRED', 'DEPRECATED', name='compliancestatus'), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('last_audit', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_audit_due', sa.DateTime(timezone=True), nullable=True),

        # Regulatory approvals - GDPR
        sa.Column('gdpr_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gdpr_approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gdpr_approved_by', sa.String(length=255), nullable=True),

        # Regulatory approvals - SOX
        sa.Column('sox_compliant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sox_approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sox_approved_by', sa.String(length=255), nullable=True),

        # Regulatory approvals - PCI-DSS
        sa.Column('pci_dss_compliant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pci_approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pci_approved_by', sa.String(length=255), nullable=True),

        # Regulatory approvals - HIPAA
        sa.Column('hipaa_compliant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hipaa_approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hipaa_approved_by', sa.String(length=255), nullable=True),

        # Technical metadata
        sa.Column('model_type', sa.String(length=100), nullable=True),
        sa.Column('framework', sa.String(length=100), nullable=True),
        sa.Column('framework_version', sa.String(length=50), nullable=True),

        # Risk assessment
        sa.Column('risk_level', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='modelrisklevel'), nullable=False, server_default='MEDIUM'),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_justification', sa.Text(), nullable=True),

        # Model performance
        sa.Column('accuracy_score', sa.Integer(), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Data governance
        sa.Column('data_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_classification', sa.String(length=50), nullable=True),
        sa.Column('contains_pii', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('contains_phi', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('contains_pci', sa.Boolean(), nullable=False, server_default='false'),

        # Model lifecycle
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('decommission_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decommission_reason', sa.Text(), nullable=True),

        # External registry integration
        sa.Column('external_registry_type', sa.String(length=100), nullable=True),
        sa.Column('external_registry_id', sa.String(length=500), nullable=True),
        sa.Column('external_registry_url', sa.String(length=1000), nullable=True),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_by', sa.String(length=255), nullable=True),

        # Flexible metadata
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Documentation
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('use_cases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('bias_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Approval workflow integration
        sa.Column('requires_approval_for_changes', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approval_workflow_id', sa.String(length=100), nullable=True),

        # Primary key and constraints
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index(op.f('ix_deployed_models_model_id'), 'deployed_models', ['model_id'], unique=True)
    op.create_index(op.f('ix_deployed_models_environment'), 'deployed_models', ['environment'], unique=False)
    op.create_index(op.f('ix_deployed_models_compliance_status'), 'deployed_models', ['compliance_status'], unique=False)
    op.create_index(op.f('ix_deployed_models_risk_level'), 'deployed_models', ['risk_level'], unique=False)
    op.create_index(op.f('ix_deployed_models_status'), 'deployed_models', ['status'], unique=False)

def downgrade() -> None:
    """Drop deployed_models table and indexes."""
    op.drop_index(op.f('ix_deployed_models_status'), table_name='deployed_models')
    op.drop_index(op.f('ix_deployed_models_risk_level'), table_name='deployed_models')
    op.drop_index(op.f('ix_deployed_models_compliance_status'), table_name='deployed_models')
    op.drop_index(op.f('ix_deployed_models_environment'), table_name='deployed_models')
    op.drop_index(op.f('ix_deployed_models_model_id'), table_name='deployed_models')
    op.drop_table('deployed_models')
