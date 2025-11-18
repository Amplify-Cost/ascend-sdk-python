"""add playbook versioning phase3

Revision ID: 20251118_164732
Revises: 79d6be706f83
Create Date: 2025-11-18 16:47:32

🏢 ENTERPRISE PLAYBOOK VERSIONING SYSTEM

Phase 3 Database Migration: Add version control, analytics, scheduling

Tables Added:
1. playbook_versions - Version history with full audit trail
2. playbook_execution_logs - Enhanced execution analytics
3. playbook_schedules - Time-based automation scheduling
4. playbook_templates - Shareable template library

Business Value:
- Compliance audit trails (SOX, PCI-DSS)
- Rollback capability for failed updates
- Performance analytics and optimization
- Automated scheduling for off-hours processing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251118_164732'
down_revision = '79d6be706f83'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # PLAYBOOK VERSIONS TABLE
    # ========================================================================
    op.create_table(
        'playbook_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('playbook_id', sa.String(255), nullable=False, index=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_tag', sa.String(100), nullable=True),
        sa.Column('is_current', sa.Boolean(), default=False, index=True),

        # Snapshot of playbook configuration
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('approval_required', sa.Boolean(), nullable=False),
        sa.Column('trigger_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('actions', postgresql.JSON(astext_type=sa.Text()), nullable=False),

        # Change tracking
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(50), default='UPDATE'),
        sa.Column('changed_fields', postgresql.JSON(astext_type=sa.Text()), default=list),
        sa.Column('diff_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Audit metadata
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Performance tracking
        sa.Column('execution_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('failure_count', sa.Integer(), default=0),
        sa.Column('avg_execution_time', sa.Float(), nullable=True),

        # Rollback tracking
        sa.Column('rolled_back_at', sa.DateTime(), nullable=True),
        sa.Column('rolled_back_by', sa.Integer(), nullable=True),
        sa.Column('rollback_reason', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['playbook_id'], ['automation_playbooks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['rolled_back_by'], ['users.id'])
    )

    # Composite indexes for fast lookups
    op.create_index('ix_playbook_version_lookup', 'playbook_versions', ['playbook_id', 'version_number'])
    op.create_index('ix_playbook_current_version', 'playbook_versions', ['playbook_id', 'is_current'])

    # ========================================================================
    # PLAYBOOK EXECUTION LOGS TABLE
    # ========================================================================
    op.create_table(
        'playbook_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('playbook_id', sa.String(255), nullable=False, index=True),
        sa.Column('playbook_version_id', sa.Integer(), nullable=True, index=True),
        sa.Column('execution_id', sa.Integer(), nullable=True, index=True),

        # Execution context
        sa.Column('triggered_by_action_id', sa.Integer(), nullable=True, index=True),
        sa.Column('execution_mode', sa.String(50), default='automatic'),

        # Timing metrics
        sa.Column('started_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Step execution tracking
        sa.Column('steps_executed', postgresql.JSON(astext_type=sa.Text()), default=list),
        sa.Column('steps_total', sa.Integer(), default=0),
        sa.Column('steps_successful', sa.Integer(), default=0),
        sa.Column('steps_failed', sa.Integer(), default=0),

        # Result tracking
        sa.Column('execution_status', sa.String(50), index=True),
        sa.Column('final_action', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_stack', sa.Text(), nullable=True),

        # Performance metrics
        sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
        sa.Column('memory_usage_mb', sa.Float(), nullable=True),
        sa.Column('api_calls_made', sa.Integer(), default=0),

        # Input/Output data
        sa.Column('input_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # User context
        sa.Column('executed_by_user_id', sa.Integer(), nullable=True),

        # Analytics flags
        sa.Column('was_successful', sa.Boolean(), index=True),
        sa.Column('cost_impact', sa.Float(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['playbook_id'], ['automation_playbooks.id']),
        sa.ForeignKeyConstraint(['playbook_version_id'], ['playbook_versions.id']),
        sa.ForeignKeyConstraint(['execution_id'], ['playbook_executions.id']),
        sa.ForeignKeyConstraint(['triggered_by_action_id'], ['agent_actions.id']),
        sa.ForeignKeyConstraint(['executed_by_user_id'], ['users.id'])
    )

    # Analytics indexes
    op.create_index('ix_execution_analytics', 'playbook_execution_logs',
                    ['playbook_id', 'started_at', 'execution_status'])
    op.create_index('ix_execution_performance', 'playbook_execution_logs',
                    ['playbook_id', 'was_successful', 'duration_ms'])

    # ========================================================================
    # PLAYBOOK SCHEDULES TABLE
    # ========================================================================
    op.create_table(
        'playbook_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('playbook_id', sa.String(255), nullable=False, index=True),

        # Schedule configuration
        sa.Column('schedule_name', sa.String(255), nullable=False),
        sa.Column('schedule_type', sa.String(50), nullable=False, index=True),

        # Schedule parameters
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=True),
        sa.Column('event_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Status and control
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('is_paused', sa.Boolean(), default=False),

        # Execution window
        sa.Column('start_time', sa.String(10), nullable=True),
        sa.Column('end_time', sa.String(10), nullable=True),
        sa.Column('timezone', sa.String(50), default='UTC'),

        # Execution limits
        sa.Column('max_executions', sa.Integer(), nullable=True),
        sa.Column('executions_remaining', sa.Integer(), nullable=True),

        # Last execution tracking
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('last_execution_status', sa.String(50), nullable=True),
        sa.Column('next_execution_at', sa.DateTime(), nullable=True, index=True),

        # Audit fields
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['playbook_id'], ['automation_playbooks.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )

    # ========================================================================
    # PLAYBOOK TEMPLATES TABLE
    # ========================================================================
    op.create_table(
        'playbook_templates',
        sa.Column('id', sa.String(255), nullable=False),

        # Template metadata
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, index=True),

        # Template configuration
        sa.Column('trigger_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('actions', postgresql.JSON(astext_type=sa.Text()), nullable=False),

        # Template properties
        sa.Column('complexity', sa.String(50), default='medium'),
        sa.Column('estimated_savings_per_month', sa.Float(), nullable=True),
        sa.Column('use_case', sa.Text(), nullable=True),

        # Usage tracking
        sa.Column('times_used', sa.Integer(), default=0),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),

        # Visibility and access
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('industry_tags', postgresql.JSON(astext_type=sa.Text()), default=list),

        # Version and maintenance
        sa.Column('template_version', sa.String(50), default='1.0'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now()),

        # Audit
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )

    # Template indexes
    op.create_index('ix_template_category', 'playbook_templates', ['category', 'is_public'])
    op.create_index('ix_template_usage', 'playbook_templates', ['times_used', 'average_rating'])


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('playbook_templates')
    op.drop_table('playbook_schedules')
    op.drop_table('playbook_execution_logs')
    op.drop_table('playbook_versions')
