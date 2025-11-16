"""Add trigger for automatic risk_level synchronization

Revision ID: 20251116_trigger
Revises: 20251116_backfill
Create Date: 2025-11-16 20:15:00

🏢 ENTERPRISE PHASE 3: Database-Level Data Consistency
Prevents future NULL risk_level values by automatically calculating from risk_score
Uses PostgreSQL trigger for real-time synchronization
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251116_trigger'
down_revision: Union[str, None] = '20251116_backfill'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    🏢 ENTERPRISE PHASE 3: Add PostgreSQL trigger for automatic risk_level sync

    Benefits:
    - Prevents future NULL values (database-level enforcement)
    - Zero application code changes required
    - Automatic calculation on INSERT/UPDATE
    - Consistent with Phase 2 mapping logic
    - Performance: Executes in microseconds
    """

    # Step 1: Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_risk_level()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only sync if risk_score is present
            IF NEW.risk_score IS NOT NULL THEN
                NEW.risk_level := CASE
                    WHEN NEW.risk_score >= 90 THEN 'critical'
                    WHEN NEW.risk_score >= 70 THEN 'high'
                    WHEN NEW.risk_score >= 40 THEN 'medium'
                    ELSE 'low'
                END;
            -- If risk_score is NULL, use action_type defaults
            ELSIF NEW.risk_level IS NULL AND NEW.action_type IS NOT NULL THEN
                NEW.risk_level := CASE
                    WHEN NEW.action_type IN ('database_delete', 'system_command', 'file_write') THEN 'high'
                    WHEN NEW.action_type IN ('database_execute', 'api_call', 'external_api') THEN 'medium'
                    ELSE 'low'
                END;
                -- Also set default risk_score to match
                NEW.risk_score := CASE
                    WHEN NEW.action_type IN ('database_delete', 'system_command', 'file_write') THEN 75.0
                    WHEN NEW.action_type IN ('database_execute', 'api_call', 'external_api') THEN 50.0
                    ELSE 25.0
                END;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Step 2: Create trigger on agent_actions table
    op.execute("""
        CREATE TRIGGER agent_actions_sync_risk_level
        BEFORE INSERT OR UPDATE ON agent_actions
        FOR EACH ROW
        EXECUTE FUNCTION sync_risk_level();
    """)

    print("✅ ENTERPRISE PHASE 3: Database trigger created")
    print("   - Function: sync_risk_level()")
    print("   - Trigger: agent_actions_sync_risk_level")
    print("   - Scope: BEFORE INSERT OR UPDATE")
    print("   - Effect: Automatic risk_level calculation")


def downgrade() -> None:
    """
    Rollback: Remove trigger and function
    """
    # Drop trigger first (depends on function)
    op.execute("""
        DROP TRIGGER IF EXISTS agent_actions_sync_risk_level ON agent_actions;
    """)

    # Then drop function
    op.execute("""
        DROP FUNCTION IF EXISTS sync_risk_level();
    """)

    print("⚠️ Rolled back database trigger and function")
