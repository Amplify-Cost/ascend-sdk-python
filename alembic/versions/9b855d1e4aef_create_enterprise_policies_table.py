"""create enterprise policies table

Revision ID: 9b855d1e4aef
Revises: 57bbe98d1d09
Create Date: 2025-10-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '9b855d1e4aef'
down_revision = '57bbe98d1d09'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'enterprise_policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('policy_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('effect', sa.String(), nullable=False),
        sa.Column('actions', postgresql.JSONB(), nullable=True),
        sa.Column('resources', postgresql.JSONB(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('priority', sa.Integer(), default=100),
        sa.Column('status', sa.String(), default='active'),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_index('idx_enterprise_policies_status', 'enterprise_policies', ['status'])
    op.create_index('idx_enterprise_policies_effect', 'enterprise_policies', ['effect'])
    
    # Insert the test policy into the table
    op.execute("""
        INSERT INTO enterprise_policies (policy_name, description, effect, actions, resources, conditions, priority, status, created_by)
        VALUES (
            'Production DB Modification Approval',
            'Require approval for all production database modifications',
            'require_approval',
            '["database_modification"]'::jsonb,
            '["*"]'::jsonb,
            '{"environment": "production"}'::jsonb,
            100,
            'active',
            'system'
        );
    """)

def downgrade():
    op.drop_index('idx_enterprise_policies_effect', 'enterprise_policies')
    op.drop_index('idx_enterprise_policies_status', 'enterprise_policies')
    op.drop_table('enterprise_policies')
