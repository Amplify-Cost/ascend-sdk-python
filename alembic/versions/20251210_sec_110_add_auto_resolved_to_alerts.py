"""SEC-110: Add auto_resolved columns to alerts table

Problem:
- unified_metrics_engine.py queries: COUNT(CASE WHEN auto_resolved = true THEN 1 END)
- Column doesn't exist in alerts table
- Causes: psycopg2.errors.UndefinedColumn: column "auto_resolved" does not exist
- Analytics dashboard broken

Solution:
- Add auto_resolved BOOLEAN DEFAULT FALSE
- Add auto_resolved_at TIMESTAMP for tracking
- Add auto_resolved_reason VARCHAR(255) for audit trail

Compliance:
- Enables automation tracking metrics
- Supports SOC 2 PI-1 performance monitoring
- NIST 800-53 AU-6 audit review

Note: This migration is idempotent - it checks if columns exist before adding them.
This allows it to run safely even if the migration chain is incomplete.

Revision ID: sec_110_auto_resolved
Revises: None
Create Date: 2025-12-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = 'sec_110_auto_resolved'
down_revision = None  # Standalone migration - no dependencies
branch_labels = ('sec_110',)  # Create separate branch
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name):
    """Check if an index exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes('alerts')
    return any(idx['name'] == index_name for idx in indexes)


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # SEC-110: Add auto_resolved columns to alerts table (IDEMPOTENT)
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Add auto_resolved boolean column (default FALSE)
    if not column_exists('alerts', 'auto_resolved'):
        op.add_column('alerts', sa.Column(
            'auto_resolved',
            sa.Boolean(),
            nullable=False,
            server_default='false'
        ))
        print("✅ SEC-110: Added auto_resolved column")
    else:
        print("ℹ️ SEC-110: auto_resolved column already exists")

    # Step 2: Add auto_resolved_at timestamp column
    if not column_exists('alerts', 'auto_resolved_at'):
        op.add_column('alerts', sa.Column(
            'auto_resolved_at',
            sa.DateTime(timezone=True),
            nullable=True
        ))
        print("✅ SEC-110: Added auto_resolved_at column")
    else:
        print("ℹ️ SEC-110: auto_resolved_at column already exists")

    # Step 3: Add auto_resolved_reason text column for audit trail
    if not column_exists('alerts', 'auto_resolved_reason'):
        op.add_column('alerts', sa.Column(
            'auto_resolved_reason',
            sa.String(255),
            nullable=True
        ))
        print("✅ SEC-110: Added auto_resolved_reason column")
    else:
        print("ℹ️ SEC-110: auto_resolved_reason column already exists")

    # Step 4: Add index for auto_resolved queries (analytics performance)
    if not index_exists('idx_alerts_auto_resolved'):
        op.create_index(
            'idx_alerts_auto_resolved',
            'alerts',
            ['auto_resolved'],
            postgresql_where=sa.text('auto_resolved = true')
        )
        print("✅ SEC-110: Added idx_alerts_auto_resolved index")
    else:
        print("ℹ️ SEC-110: idx_alerts_auto_resolved index already exists")


def downgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # ROLLBACK: Remove auto_resolved columns
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Drop index
    op.drop_index('idx_alerts_auto_resolved', table_name='alerts')

    # Step 2: Drop columns in reverse order
    op.drop_column('alerts', 'auto_resolved_reason')
    op.drop_column('alerts', 'auto_resolved_at')
    op.drop_column('alerts', 'auto_resolved')
