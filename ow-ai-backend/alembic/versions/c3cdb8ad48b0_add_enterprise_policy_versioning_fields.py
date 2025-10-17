"""add_enterprise_policy_versioning_fields

Revision ID: c3cdb8ad48b0
Revises: 5476f60dc90c
Create Date: $(date '+%Y-%m-%d %H:%M:%S.%f')

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3cdb8ad48b0'
down_revision = '5476f60dc90c'
branch_labels = None
depends_on = None

def upgrade():
    # Add enterprise policy versioning fields to mcp_policies table
    op.add_column('mcp_policies', sa.Column('policy_status', sa.String(50), nullable=False, server_default='draft'))
    op.add_column('mcp_policies', sa.Column('major_version', sa.Integer, nullable=False, server_default='1'))
    op.add_column('mcp_policies', sa.Column('minor_version', sa.Integer, nullable=False, server_default='0'))
    op.add_column('mcp_policies', sa.Column('patch_version', sa.Integer, nullable=False, server_default='0'))
    op.add_column('mcp_policies', sa.Column('version_hash', sa.String(64), nullable=True))
    op.add_column('mcp_policies', sa.Column('parent_policy_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mcp_policies', sa.Column('deployment_timestamp', sa.DateTime(timezone=True), nullable=True))
    op.add_column('mcp_policies', sa.Column('rollback_target_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mcp_policies', sa.Column('natural_language_description', sa.Text, nullable=True))
    op.add_column('mcp_policies', sa.Column('test_results', sa.JSON, nullable=True))
    op.add_column('mcp_policies', sa.Column('approval_required', sa.Boolean, nullable=False, server_default='true'))
    op.add_column('mcp_policies', sa.Column('approved_by', sa.String(200), nullable=True))
    op.add_column('mcp_policies', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add indexes for enterprise queries
    op.create_index('idx_mcp_policies_status', 'mcp_policies', ['policy_status'])
    op.create_index('idx_mcp_policies_version', 'mcp_policies', ['major_version', 'minor_version', 'patch_version'])
    op.create_index('idx_mcp_policies_deployment', 'mcp_policies', ['deployment_timestamp'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_mcp_policies_parent', 'mcp_policies', 'mcp_policies', ['parent_policy_id'], ['id'])
    op.create_foreign_key('fk_mcp_policies_rollback', 'mcp_policies', 'mcp_policies', ['rollback_target_id'], ['id'])

def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_mcp_policies_rollback', 'mcp_policies', type_='foreignkey')
    op.drop_constraint('fk_mcp_policies_parent', 'mcp_policies', type_='foreignkey')
    
    # Remove indexes
    op.drop_index('idx_mcp_policies_deployment', 'mcp_policies')
    op.drop_index('idx_mcp_policies_version', 'mcp_policies')
    op.drop_index('idx_mcp_policies_status', 'mcp_policies')
    
    # Remove columns
    op.drop_column('mcp_policies', 'approved_at')
    op.drop_column('mcp_policies', 'approved_by')
    op.drop_column('mcp_policies', 'approval_required')
    op.drop_column('mcp_policies', 'test_results')
    op.drop_column('mcp_policies', 'natural_language_description')
    op.drop_column('mcp_policies', 'rollback_target_id')
    op.drop_column('mcp_policies', 'deployment_timestamp')
    op.drop_column('mcp_policies', 'parent_policy_id')
    op.drop_column('mcp_policies', 'version_hash')
    op.drop_column('mcp_policies', 'patch_version')
    op.drop_column('mcp_policies', 'minor_version')
    op.drop_column('mcp_policies', 'major_version')
    op.drop_column('mcp_policies', 'policy_status')
