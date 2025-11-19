"""Enterprise workflow configuration schema with real data persistence

Revision ID: 20251119_enterprise_wf
Revises:
Create Date: 2025-11-19

🏢 ENTERPRISE SOLUTION:
- Adds workflow configuration columns for real-time editing
- Supports approval levels, timeouts, escalation, emergency overrides
- Full audit trail with user tracking
- Eliminates hardcoded config_workflows.py dependency
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, UTC
import json


# revision identifiers, used by Alembic.
revision = '20251119_enterprise_wf'
down_revision = '20251118_185410'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for workflow configuration management
    op.add_column('workflows', sa.Column('risk_threshold_min', sa.Integer(), nullable=True))
    op.add_column('workflows', sa.Column('risk_threshold_max', sa.Integer(), nullable=True))
    op.add_column('workflows', sa.Column('approval_levels', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('workflows', sa.Column('approvers', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('workflows', sa.Column('timeout_hours', sa.Integer(), nullable=True, server_default='24'))
    op.add_column('workflows', sa.Column('emergency_override', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('workflows', sa.Column('escalation_minutes', sa.Integer(), nullable=True, server_default='480'))
    op.add_column('workflows', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('workflows', sa.Column('modified_by', sa.String(255), nullable=True))
    op.add_column('workflows', sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True))

    # Add indexes for performance
    op.create_index('ix_workflows_risk_threshold', 'workflows', ['risk_threshold_min', 'risk_threshold_max'])
    op.create_index('ix_workflows_is_active', 'workflows', ['is_active'])

    # Populate existing workflows with enterprise data based on config_workflows.py structure
    conn = op.get_bind()

    # Define enterprise workflow configurations
    workflow_configs = {
        'risk_90_100': {
            'risk_min': 90,
            'risk_max': 100,
            'approval_levels': 3,
            'approvers': ['security@company.com', 'senior@company.com', 'executive@company.com'],
            'timeout_hours': 2,
            'emergency_override': True,
            'escalation_minutes': 30
        },
        'risk_70_89': {
            'risk_min': 70,
            'risk_max': 89,
            'approval_levels': 2,
            'approvers': ['security@company.com', 'senior@company.com'],
            'timeout_hours': 4,
            'emergency_override': False,
            'escalation_minutes': 60
        },
        'risk_50_69': {
            'risk_min': 50,
            'risk_max': 69,
            'approval_levels': 2,
            'approvers': ['security@company.com', 'security2@company.com'],
            'timeout_hours': 8,
            'emergency_override': False,
            'escalation_minutes': 120
        },
        'risk_0_49': {
            'risk_min': 0,
            'risk_max': 49,
            'approval_levels': 1,
            'approvers': ['security@company.com'],
            'timeout_hours': 24,
            'emergency_override': False,
            'escalation_minutes': 480
        }
    }

    # Update each workflow with enterprise configuration
    for workflow_id, config in workflow_configs.items():
        # Use CAST for JSONB type
        approvers_json = json.dumps(config['approvers'])
        conn.execute(
            sa.text("""
                UPDATE workflows
                SET risk_threshold_min = :risk_min,
                    risk_threshold_max = :risk_max,
                    approval_levels = :approval_levels,
                    approvers = CAST(:approvers AS jsonb),
                    timeout_hours = :timeout_hours,
                    emergency_override = :emergency_override,
                    escalation_minutes = :escalation_minutes,
                    is_active = true,
                    modified_by = 'system_migration',
                    last_modified = :last_modified
                WHERE id = :workflow_id
            """),
            {
                'workflow_id': workflow_id,
                'risk_min': config['risk_min'],
                'risk_max': config['risk_max'],
                'approval_levels': config['approval_levels'],
                'approvers': approvers_json,
                'timeout_hours': config['timeout_hours'],
                'emergency_override': config['emergency_override'],
                'escalation_minutes': config['escalation_minutes'],
                'last_modified': datetime.now(UTC)
            }
        )

    print("✅ Enterprise workflow configurations migrated to database")


def downgrade():
    # Remove indexes
    op.drop_index('ix_workflows_is_active', table_name='workflows')
    op.drop_index('ix_workflows_risk_threshold', table_name='workflows')

    # Remove columns
    op.drop_column('workflows', 'last_modified')
    op.drop_column('workflows', 'modified_by')
    op.drop_column('workflows', 'is_active')
    op.drop_column('workflows', 'escalation_minutes')
    op.drop_column('workflows', 'emergency_override')
    op.drop_column('workflows', 'timeout_hours')
    op.drop_column('workflows', 'approvers')
    op.drop_column('workflows', 'approval_levels')
    op.drop_column('workflows', 'risk_threshold_max')
    op.drop_column('workflows', 'risk_threshold_min')
