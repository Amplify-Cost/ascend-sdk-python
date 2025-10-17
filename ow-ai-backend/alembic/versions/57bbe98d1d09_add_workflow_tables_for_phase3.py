"""Add workflow tables for Phase 3

Revision ID: 57bbe98d1d09
Revises: bed60fa85b1b
Create Date: 2025-09-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '57bbe98d1d09'
down_revision = 'bed60fa85b1b'
branch_labels = None
depends_on = None

def upgrade():
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('steps', postgresql.JSONB(), nullable=True),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('workflow_metadata', postgresql.JSONB(), nullable=True)
    )
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('workflow_id', sa.String(), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('action_id', sa.Integer(), sa.ForeignKey('agent_actions.id'), nullable=True),
        sa.Column('executed_by', sa.String(), nullable=True),
        sa.Column('execution_status', sa.String(), nullable=False),
        sa.Column('execution_details', postgresql.JSONB(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('approval_chain', postgresql.JSONB(), nullable=True)
    )
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('workflow_id', sa.String(), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(), nullable=False),
        sa.Column('step_type', sa.String(), nullable=False),
        sa.Column('timeout_hours', sa.Integer(), server_default='24'),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Add workflow columns to agent_actions
    op.add_column('agent_actions', sa.Column('workflow_id', sa.String(), nullable=True))
    op.add_column('agent_actions', sa.Column('workflow_execution_id', sa.Integer(), nullable=True))
    op.add_column('agent_actions', sa.Column('workflow_stage', sa.String(), nullable=True))
    op.add_column('agent_actions', sa.Column('current_approval_level', sa.Integer(), server_default='0'))
    op.add_column('agent_actions', sa.Column('required_approval_level', sa.Integer(), server_default='1'))
    op.add_column('agent_actions', sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agent_actions', sa.Column('pending_approvers', sa.Text(), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_agent_actions_workflow',
        'agent_actions', 'workflows',
        ['workflow_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_agent_actions_workflow_execution',
        'agent_actions', 'workflow_executions',
        ['workflow_execution_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create indexes
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['execution_status'])
    op.create_index('idx_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('idx_agent_actions_workflow_id', 'agent_actions', ['workflow_id'])
    op.create_index('idx_agent_actions_sla_deadline', 'agent_actions', ['sla_deadline'])
    
    # Insert workflow templates
    op.execute("""
        INSERT INTO workflows (id, name, description, created_by, status, steps, trigger_conditions, workflow_metadata) VALUES
        ('risk_90_100', 'Critical Risk - 3-Level Approval', 
         'Three-stage approval for extremely high-risk actions',
         'system', 'active',
         '[{"stage": 1, "name": "Security Review", "timeout_hours": 2},
           {"stage": 2, "name": "Senior Management", "timeout_hours": 4},
           {"stage": 3, "name": "Executive Authorization", "timeout_hours": 8}]'::jsonb,
         '{"min_risk": 90, "max_risk": 100}'::jsonb,
         '{"sla_hours": 4}'::jsonb),
         
        ('risk_70_89', 'High Risk - 2-Level Approval',
         'Two-stage approval for high-risk actions',
         'system', 'active',
         '[{"stage": 1, "name": "Security Review", "timeout_hours": 4},
           {"stage": 2, "name": "Management Approval", "timeout_hours": 12}]'::jsonb,
         '{"min_risk": 70, "max_risk": 89}'::jsonb,
         '{"sla_hours": 8}'::jsonb),
         
        ('risk_50_69', 'Medium Risk - 2-Level Approval',
         'Two-stage approval for medium-risk actions',
         'system', 'active',
         '[{"stage": 1, "name": "Team Lead Review", "timeout_hours": 8},
           {"stage": 2, "name": "Manager Approval", "timeout_hours": 16}]'::jsonb,
         '{"min_risk": 50, "max_risk": 69}'::jsonb,
         '{"sla_hours": 16}'::jsonb),
         
        ('risk_0_49', 'Low Risk - Single Approval',
         'Single approval for low-risk actions',
         'system', 'active',
         '[{"stage": 1, "name": "Supervisor Approval", "timeout_hours": 24}]'::jsonb,
         '{"min_risk": 0, "max_risk": 49}'::jsonb,
         '{"sla_hours": 24}'::jsonb);
    """)

def downgrade():
    op.drop_constraint('fk_agent_actions_workflow_execution', 'agent_actions', type_='foreignkey')
    op.drop_constraint('fk_agent_actions_workflow', 'agent_actions', type_='foreignkey')
    op.drop_index('idx_agent_actions_sla_deadline', 'agent_actions')
    op.drop_index('idx_agent_actions_workflow_id', 'agent_actions')
    op.drop_index('idx_workflow_executions_workflow_id', 'workflow_executions')
    op.drop_index('idx_workflow_executions_status', 'workflow_executions')
    op.drop_index('idx_workflows_status', 'workflows')
    op.drop_column('agent_actions', 'pending_approvers')
    op.drop_column('agent_actions', 'sla_deadline')
    op.drop_column('agent_actions', 'required_approval_level')
    op.drop_column('agent_actions', 'current_approval_level')
    op.drop_column('agent_actions', 'workflow_stage')
    op.drop_column('agent_actions', 'workflow_execution_id')
    op.drop_column('agent_actions', 'workflow_id')
    op.drop_table('workflow_steps')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
