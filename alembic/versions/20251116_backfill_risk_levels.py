"""Backfill risk_level from risk_score

Revision ID: 20251116_backfill
Revises: 20251115_185707
Create Date: 2025-11-16 19:39:03

🏢 ENTERPRISE PHASE 2: Data Quality Fix
Backfill risk_level field from risk_score values
Resolves UI displaying "null" for risk levels
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251116_backfill'
down_revision: Union[str, None] = '20251115_185707'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    🏢 ENTERPRISE: Backfill risk_level from risk_score

    Mapping:
    - risk_score >= 90: 'critical'
    - risk_score >= 70: 'high'
    - risk_score >= 40: 'medium'
    - risk_score < 40: 'low'
    """

    # Step 1: Backfill risk_level based on risk_score (for NULL risk_level)
    op.execute("""
        UPDATE agent_actions
        SET risk_level = CASE
            WHEN risk_score >= 90 THEN 'critical'
            WHEN risk_score >= 70 THEN 'high'
            WHEN risk_score >= 40 THEN 'medium'
            ELSE 'low'
        END
        WHERE risk_level IS NULL AND risk_score IS NOT NULL;
    """)

    # Step 2: For actions with NULL risk_score, set default based on action_type
    op.execute("""
        UPDATE agent_actions
        SET
            risk_level = CASE
                WHEN action_type IN ('database_delete', 'system_command', 'file_write') THEN 'high'
                WHEN action_type IN ('database_execute', 'api_call', 'external_api') THEN 'medium'
                ELSE 'low'
            END,
            risk_score = CASE
                WHEN action_type IN ('database_delete', 'system_command', 'file_write') THEN 75.0
                WHEN action_type IN ('database_execute', 'api_call', 'external_api') THEN 50.0
                ELSE 25.0
            END
        WHERE risk_level IS NULL AND risk_score IS NULL;
    """)

    print("✅ ENTERPRISE PHASE 2: Backfilled risk_level values")
    print("   - Updated risk_level from risk_score")
    print("   - Set defaults for NULL values based on action_type")


def downgrade() -> None:
    """
    Rollback: Set risk_level back to NULL
    (Does not restore original data, sets to NULL for safety)
    """
    op.execute("""
        UPDATE agent_actions
        SET risk_level = NULL
        WHERE risk_level IN ('low', 'medium', 'high', 'critical');
    """)

    print("⚠️ Rolled back risk_level backfill (set to NULL)")
