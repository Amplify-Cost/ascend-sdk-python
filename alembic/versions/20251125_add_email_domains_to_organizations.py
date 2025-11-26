"""add email_domains to organizations

Enterprise Multi-Tenant Email Domain Mapping
============================================

Adds email_domains array column to organizations table for
automatic organization detection from user email addresses.

Use Case:
- User enters email: john@acme.com
- Backend looks up organization with email_domains containing 'acme.com'
- Returns organization's Cognito pool configuration
- User authenticates against their organization's dedicated Cognito pool

Security:
- Enables zero-trust authentication routing
- Prevents cross-tenant authentication attempts
- Banking-level tenant isolation

Revision ID: 20251125_email_domains
Revises: dc7bcb592c17
Create Date: 2025-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20251125_email_domains'
down_revision: Union[str, None] = 'dc7bcb592c17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_domains array column to organizations table."""

    # Add email_domains column as TEXT array
    op.add_column(
        'organizations',
        sa.Column(
            'email_domains',
            postgresql.ARRAY(sa.String(255)),
            nullable=True,
            comment='List of email domains belonging to this organization (e.g., ["acme.com", "acme.net"])'
        )
    )

    # Create index for faster domain lookups
    op.create_index(
        'ix_organizations_email_domains',
        'organizations',
        ['email_domains'],
        postgresql_using='gin'  # GIN index is optimal for array contains queries
    )

    # Seed initial email domains for existing organizations
    # Using raw SQL for array operations
    from sqlalchemy import text

    connection = op.get_bind()

    # OW-AI Internal (org 1)
    connection.execute(text("""
        UPDATE organizations
        SET email_domains = ARRAY['owkai.com', 'owkai.app', 'owai.com']
        WHERE slug = 'owai-internal' OR slug = 'owkai-internal'
    """))

    # Acme Corp (org 4) - test organization
    connection.execute(text("""
        UPDATE organizations
        SET email_domains = ARRAY['acmecorp.test', 'acme.com']
        WHERE slug = 'acme-corp'
    """))

    print("  Added email_domains column to organizations")
    print("  Created GIN index for array lookups")
    print("  Seeded email domains for existing organizations")


def downgrade() -> None:
    """Remove email_domains column from organizations table."""

    op.drop_index('ix_organizations_email_domains', table_name='organizations')
    op.drop_column('organizations', 'email_domains')
