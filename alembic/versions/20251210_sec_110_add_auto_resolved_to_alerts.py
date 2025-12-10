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

Revision ID: sec_110_auto_resolved
Revises: sec_096_prefix_len
Create Date: 2025-12-10
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sec_110_auto_resolved'
down_revision = 'sec_096_prefix_len'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # SEC-110: Add auto_resolved columns to alerts table
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Add auto_resolved boolean column (default FALSE)
    op.add_column('alerts', sa.Column(
        'auto_resolved',
        sa.Boolean(),
        nullable=False,
        server_default='false'
    ))

    # Step 2: Add auto_resolved_at timestamp column
    op.add_column('alerts', sa.Column(
        'auto_resolved_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))

    # Step 3: Add auto_resolved_reason text column for audit trail
    op.add_column('alerts', sa.Column(
        'auto_resolved_reason',
        sa.String(255),
        nullable=True
    ))

    # Step 4: Add index for auto_resolved queries (analytics performance)
    op.create_index(
        'idx_alerts_auto_resolved',
        'alerts',
        ['auto_resolved'],
        postgresql_where=sa.text('auto_resolved = true')
    )


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
