"""add soft delete to playbooks

Revision ID: 20251118_185410
Revises: 56cafdd6712b
Create Date: 2025-11-18 18:54:10

🏢 ENTERPRISE PLAYBOOK SOFT DELETE

Phase 4: Soft Delete Implementation

Changes:
1. Add soft delete columns to automation_playbooks table
2. Fix cascade delete rules for playbook_execution_logs
3. Fix cascade delete rules for playbook_schedules
4. Add indexes for performance

Business Value:
- 30-day recovery window (prevent accidental deletion)
- Complete audit trail (SOX, PCI-DSS compliance)
- Forensic investigation capability
- Self-service recovery (reduce admin burden)

Pattern: Splunk SOAR + Palo Alto Cortex XSOAR
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251118_185410'
down_revision = '56cafdd6712b'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # ADD SOFT DELETE COLUMNS TO automation_playbooks
    # ========================================================================

    # Add is_deleted flag (indexed for fast filtering)
    op.add_column('automation_playbooks',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_automation_playbooks_is_deleted', 'automation_playbooks', ['is_deleted'])

    # Add deleted_at timestamp
    op.add_column('automation_playbooks',
        sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Add deleted_by user reference
    op.add_column('automation_playbooks',
        sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_automation_playbooks_deleted_by',
        'automation_playbooks', 'users',
        ['deleted_by'], ['id']
    )

    # Add deletion_reason for audit trail
    op.add_column('automation_playbooks',
        sa.Column('deletion_reason', sa.Text(), nullable=True))

    # ========================================================================
    # FIX CASCADE DELETE RULES
    # ========================================================================

    # Fix playbook_execution_logs foreign key to cascade delete
    # This prevents orphaned records when playbook is hard deleted
    op.drop_constraint('playbook_execution_logs_playbook_id_fkey',
                      'playbook_execution_logs', type_='foreignkey')
    op.create_foreign_key(
        'playbook_execution_logs_playbook_id_fkey',
        'playbook_execution_logs', 'automation_playbooks',
        ['playbook_id'], ['id'],
        ondelete='CASCADE'
    )

    # Fix playbook_schedules foreign key to cascade delete
    op.drop_constraint('playbook_schedules_playbook_id_fkey',
                      'playbook_schedules', type_='foreignkey')
    op.create_foreign_key(
        'playbook_schedules_playbook_id_fkey',
        'playbook_schedules', 'automation_playbooks',
        ['playbook_id'], ['id'],
        ondelete='CASCADE'
    )

    # ========================================================================
    # ADD COMPOSITE INDEX FOR DELETED PLAYBOOK QUERIES
    # ========================================================================

    # Index for finding deleted playbooks eligible for recovery
    # (deleted = true, deleted_at > 30 days ago)
    op.create_index(
        'ix_automation_playbooks_deleted_recovery',
        'automation_playbooks',
        ['is_deleted', 'deleted_at']
    )


def downgrade():
    # Drop indexes
    op.drop_index('ix_automation_playbooks_deleted_recovery', 'automation_playbooks')
    op.drop_index('ix_automation_playbooks_is_deleted', 'automation_playbooks')

    # Revert foreign key cascade rules
    op.drop_constraint('playbook_schedules_playbook_id_fkey',
                      'playbook_schedules', type_='foreignkey')
    op.create_foreign_key(
        'playbook_schedules_playbook_id_fkey',
        'playbook_schedules', 'automation_playbooks',
        ['playbook_id'], ['id']
    )

    op.drop_constraint('playbook_execution_logs_playbook_id_fkey',
                      'playbook_execution_logs', type_='foreignkey')
    op.create_foreign_key(
        'playbook_execution_logs_playbook_id_fkey',
        'playbook_execution_logs', 'automation_playbooks',
        ['playbook_id'], ['id']
    )

    # Drop soft delete columns
    op.drop_constraint('fk_automation_playbooks_deleted_by',
                      'automation_playbooks', type_='foreignkey')
    op.drop_column('automation_playbooks', 'deletion_reason')
    op.drop_column('automation_playbooks', 'deleted_by')
    op.drop_column('automation_playbooks', 'deleted_at')
    op.drop_column('automation_playbooks', 'is_deleted')
