"""SEC-076: Add organization_id to WorkflowExecution, WorkflowStep, PolicyEvaluation

Multi-tenant isolation for enterprise workflow and policy analytics.

Revision ID: sec076_multi_tenant
Revises: 
Create Date: 2025-12-04

Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312
Author: Ascend Platform Engineering
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sec076_multi_tenant'
down_revision = None
branch_labels = ('sec076',)
depends_on = None


def upgrade() -> None:
    """
    SEC-076: Add organization_id columns for multi-tenant isolation.
    
    Tables affected:
    - workflow_executions
    - workflow_steps
    - policy_evaluations
    """
    # WorkflowExecution - Add organization_id
    op.add_column(
        'workflow_executions',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        'ix_workflow_executions_organization_id',
        'workflow_executions',
        ['organization_id']
    )
    op.create_foreign_key(
        'fk_workflow_executions_organization_id',
        'workflow_executions',
        'organizations',
        ['organization_id'],
        ['id']
    )
    
    # WorkflowStep - Add organization_id
    op.add_column(
        'workflow_steps',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        'ix_workflow_steps_organization_id',
        'workflow_steps',
        ['organization_id']
    )
    op.create_foreign_key(
        'fk_workflow_steps_organization_id',
        'workflow_steps',
        'organizations',
        ['organization_id'],
        ['id']
    )
    
    # PolicyEvaluation - Add organization_id
    op.add_column(
        'policy_evaluations',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        'ix_policy_evaluations_organization_id',
        'policy_evaluations',
        ['organization_id']
    )
    op.create_foreign_key(
        'fk_policy_evaluations_organization_id',
        'policy_evaluations',
        'organizations',
        ['organization_id'],
        ['id']
    )
    
    print("✅ SEC-076: Multi-tenant isolation columns added successfully")


def downgrade() -> None:
    """Remove organization_id columns (rollback)."""
    # PolicyEvaluation
    op.drop_constraint('fk_policy_evaluations_organization_id', 'policy_evaluations', type_='foreignkey')
    op.drop_index('ix_policy_evaluations_organization_id', 'policy_evaluations')
    op.drop_column('policy_evaluations', 'organization_id')
    
    # WorkflowStep
    op.drop_constraint('fk_workflow_steps_organization_id', 'workflow_steps', type_='foreignkey')
    op.drop_index('ix_workflow_steps_organization_id', 'workflow_steps')
    op.drop_column('workflow_steps', 'organization_id')
    
    # WorkflowExecution
    op.drop_constraint('fk_workflow_executions_organization_id', 'workflow_executions', type_='foreignkey')
    op.drop_index('ix_workflow_executions_organization_id', 'workflow_executions')
    op.drop_column('workflow_executions', 'organization_id')
    
    print("⚠️ SEC-076: Multi-tenant isolation columns removed")
