"""SEC-046: Add processing_time_ms to agent_actions for performance analytics

Revision ID: 20251202_sec046_pt
Revises: 20251202_sec046_p2
Create Date: 2025-12-02

Enterprise Feature: Response time tracking for API analytics dashboard
Compliance: SOC 2 CC7.1 (Performance Monitoring), HIPAA 164.312(b)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from typing import Sequence, Union

# revision identifiers
revision: str = '20251202_sec046_pt'
down_revision: Union[str, None] = '20251202_sec046_p2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """
    Check if column exists (idempotent pattern)

    Banking-Level Security: Uses SQLAlchemy Inspector for injection-safe introspection.
    PCI-DSS 6.5.1 Compliant: No string interpolation in SQL queries.
    """
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def index_exists(index_name: str) -> bool:
    """
    Check if index exists

    Banking-Level Security: Uses SQLAlchemy Inspector for injection-safe introspection.
    PCI-DSS 6.5.1 Compliant: No string interpolation in SQL queries.
    """
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    # Get all indexes across all tables
    for table_name in inspector.get_table_names():
        indexes = inspector.get_indexes(table_name)
        if any(idx['name'] == index_name for idx in indexes):
            return True
    return False


def upgrade() -> None:
    """
    SEC-046: Add processing_time_ms column for API response time tracking.

    Enterprise Pattern: Idempotent, logged, indexed for analytics
    """
    print("=" * 70)
    print("SEC-046: Adding processing_time_ms for performance analytics")
    print("=" * 70)

    if not column_exists('agent_actions', 'processing_time_ms'):
        op.add_column('agent_actions',
            sa.Column('processing_time_ms', sa.Integer(), nullable=True))
        print("  Added: processing_time_ms")
    else:
        print("  Exists: processing_time_ms")

    # Index for analytics queries
    if not index_exists('ix_agent_actions_processing_time_ms'):
        op.create_index('ix_agent_actions_processing_time_ms', 'agent_actions', ['processing_time_ms'])
        print("  Index: ix_agent_actions_processing_time_ms created")

    print("")
    print("=" * 70)
    print("SEC-046 MIGRATION COMPLETE: processing_time_ms added")
    print("=" * 70)
    print("")
    print("FEATURE ENABLED:")
    print("  - API response time tracking in analytics dashboard")
    print("  - Endpoint performance metrics by action_type")
    print("")
    print("COMPLIANCE:")
    print("  SOC 2 CC7.1  - Performance monitoring")
    print("  HIPAA 164.312(b) - Audit controls")
    print("=" * 70)


def downgrade() -> None:
    """SEC-046: Remove processing_time_ms column (reversible)"""
    print("=" * 70)
    print("SEC-046: Rolling back processing_time_ms")
    print("=" * 70)

    if index_exists('ix_agent_actions_processing_time_ms'):
        op.drop_index('ix_agent_actions_processing_time_ms', 'agent_actions')
        print("  Dropped: ix_agent_actions_processing_time_ms")

    if column_exists('agent_actions', 'processing_time_ms'):
        op.drop_column('agent_actions', 'processing_time_ms')
        print("  Dropped: processing_time_ms")

    print("")
    print("=" * 70)
    print("SEC-046 ROLLBACK COMPLETE")
    print("=" * 70)
