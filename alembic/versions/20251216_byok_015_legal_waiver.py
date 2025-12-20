"""BYOK-015: Add legal acknowledgment column to tenant_encryption_keys

This migration adds the legal_acknowledgment_at column to track when
customers accepted the BYOK risk acknowledgment.

Requirement: Defense in Depth - Customer must acknowledge risks before BYOK activation

Revision ID: byok_015_legal_waiver
Revises: 20251211_byok_001_tenant_encryption_schema
Create Date: 2025-12-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'byok_015_legal_waiver'
down_revision = 'byok_001_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add legal_acknowledgment_at column to tenant_encryption_keys.

    This column stores when the customer acknowledged the BYOK risks:
    - Permanent data loss if CMK is deleted
    - Key management responsibility
    - No liability for key mismanagement
    """
    # Add legal_acknowledgment_at column
    op.add_column(
        'tenant_encryption_keys',
        sa.Column(
            'legal_acknowledgment_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when customer acknowledged BYOK risks'
        )
    )

    # Add acknowledged_by column to track who accepted
    op.add_column(
        'tenant_encryption_keys',
        sa.Column(
            'acknowledged_by_user_id',
            sa.Integer,
            nullable=True,
            comment='User ID who acknowledged BYOK terms'
        )
    )

    # Add index for queries on acknowledgment status
    op.create_index(
        'idx_tenant_encryption_keys_acknowledged',
        'tenant_encryption_keys',
        ['organization_id', 'legal_acknowledgment_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove legal acknowledgment columns."""
    op.drop_index('idx_tenant_encryption_keys_acknowledged', table_name='tenant_encryption_keys')
    op.drop_column('tenant_encryption_keys', 'acknowledged_by_user_id')
    op.drop_column('tenant_encryption_keys', 'legal_acknowledgment_at')
