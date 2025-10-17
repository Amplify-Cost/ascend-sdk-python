"""create_smart_rules_table

Revision ID: 7a3cfedc32f0
Revises: 
Create Date: 2025-09-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '7a3cfedc32f0'
down_revision = None  # Update this if there's a previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create smart_rules table
    op.execute("""
        CREATE TABLE IF NOT EXISTS smart_rules (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255),
            action_type VARCHAR(255),
            description TEXT,
            condition TEXT,
            action VARCHAR(100),
            risk_level VARCHAR(50),
            recommendation TEXT,
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample data
    op.execute("""
        INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification)
        VALUES 
        ('security-scanner-01', 'vulnerability_scan', 'High-risk scan approval', 'risk_level = high', 'require_approval', 'high', 'Manual approval', 'Security'),
"""create_smart_rules_table

Revision ID: 7a3cfedc32f0
Revises: 
Create Date: 2025-09-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '7a3cfedc32f0'
down_revision = None  # Update this if there's a previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Create smart_rules table
    op.execute("""
        CREATE TABLE IF NOT EXISTS smart_rules (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255),
            action_type VARCHAR(255),
            description TEXT,
            condition TEXT,
            action VARCHAR(100),
            risk_level VARCHAR(50),
            recommendation TEXT,
            justification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample data
    op.execute("""
        INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification)
        VALUES 
        ('security-scanner-01', 'vulnerability_scan', 'High-risk scan approval', 'risk_level = high', 'require_approval', 'high', 'Manual approval', 'Security'),
        ('compliance-agent', 'compliance_check', 'Auto-approve compliance', 'risk_level = low', 'auto_approve', 'low', 'Automated', 'Routine'),
        ('threat-detector', 'anomaly_detection', 'Alert anomalies', 'action_type = anomaly', 'alert', 'medium', 'Monitor', 'Detection')
        ON CONFLICT DO NOTHING
    """)


def downgrade():
    op.drop_table('smart_rules')        ('compliance-agent', 'compliance_check', 'Auto-approve compliance', 'risk_level = low', 'auto_approve', 'low', 'Automated', 'Routine'),
        ('threat-detector', 'anomaly_detection', 'Alert anomalies', 'action_type = anomaly', 'alert', 'medium', 'Monitor', 'Detection')
        ON CONFLICT DO NOTHING
    """)


def downgrade():
    op.drop_table('smart_rules')"""create_smart_rules_table

Revision ID: 7a3cfedc32f0
Revises: bed60fa85b1b
Create Date: 2025-09-25 14:39:52.566211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3cfedc32f0'
down_revision: Union[str, None] = 'bed60fa85b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
