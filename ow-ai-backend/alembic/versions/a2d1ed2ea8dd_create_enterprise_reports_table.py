"""create_enterprise_reports_table

Revision ID: a2d1ed2ea8dd
Revises: 07d1a4d8402b
Create Date: 2025-10-31 21:38:22.470545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2d1ed2ea8dd'
down_revision: Union[str, None] = '07d1a4d8402b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create enterprise_reports table for storing generated compliance reports."""
    op.create_table(
        'enterprise_reports',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('classification', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), server_default='completed', nullable=False),
        sa.Column('format', sa.String(20), server_default='PDF', nullable=False),
        sa.Column('file_size', sa.String(50), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=True),  # Path to actual PDF file
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('department', sa.String(255), server_default='Information Security', nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('content', sa.JSON, nullable=True),  # Store report data as JSON
        sa.Column('download_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=True),
        # Add indexes for common queries
        sa.Index('idx_enterprise_reports_type', 'type'),
        sa.Index('idx_enterprise_reports_classification', 'classification'),
        sa.Index('idx_enterprise_reports_created_at', 'created_at'),
        sa.Index('idx_enterprise_reports_author', 'author')
    )


def downgrade() -> None:
    """Drop enterprise_reports table."""
    op.drop_index('idx_enterprise_reports_author')
    op.drop_index('idx_enterprise_reports_created_at')
    op.drop_index('idx_enterprise_reports_classification')
    op.drop_index('idx_enterprise_reports_type')
    op.drop_table('enterprise_reports')
