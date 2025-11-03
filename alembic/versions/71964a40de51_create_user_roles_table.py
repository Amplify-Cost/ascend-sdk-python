"""create_user_roles_table

Revision ID: 71964a40de51
Revises: 4eb7744831d8
Create Date: 2025-11-03 14:56:18.786445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71964a40de51'
down_revision: Union[str, None] = '4eb7744831d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_roles table for enterprise role management
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            permissions JSONB NOT NULL DEFAULT '{}',
            level INTEGER NOT NULL DEFAULT 1,
            risk_level VARCHAR(20) DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER REFERENCES users(id),
            is_active BOOLEAN DEFAULT true
        );
    """)

    # Create indexes for performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_level ON user_roles(level);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_name ON user_roles(name);")

    # Insert default enterprise roles
    op.execute("""
        INSERT INTO user_roles (name, description, permissions, level, risk_level, is_active)
        VALUES
            ('Admin', 'Full system access and control',
             '{"dashboard": true, "users": true, "alerts": true, "rules": true, "governance": true, "analytics": true, "settings": true}'::jsonb,
             5, 'Critical', true),
            ('Security Analyst', 'Review and manage security alerts',
             '{"dashboard": true, "alerts": true, "rules": true, "analytics": true}'::jsonb,
             4, 'High', true),
            ('Compliance Officer', 'Monitor compliance and governance',
             '{"dashboard": true, "governance": true, "analytics": true}'::jsonb,
             3, 'Medium', true),
            ('Operator', 'Basic monitoring and reporting',
             '{"dashboard": true, "alerts": true}'::jsonb,
             2, 'Low', true),
            ('Viewer', 'Read-only access to dashboards',
             '{"dashboard": true}'::jsonb,
             1, 'Low', true)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_user_roles_name;")
    op.execute("DROP INDEX IF EXISTS idx_user_roles_level;")

    # Drop the table
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE;")
