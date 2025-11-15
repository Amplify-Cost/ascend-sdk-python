"""add_risk_scoring_configs_table

Revision ID: 91e6b34f6aea
Revises: 046903af7235
Create Date: 2025-11-14 18:30:44.001687

"""
from typing import Sequence, Union
from datetime import datetime, UTC

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '91e6b34f6aea'
down_revision: Union[str, None] = '046903af7235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create risk_scoring_configs table."""

    # Create risk_scoring_configs table
    op.create_table(
        'risk_scoring_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_version', sa.String(length=20), nullable=False),
        sa.Column('algorithm_version', sa.String(length=20), nullable=False),
        sa.Column('environment_weights', JSONB, nullable=False),
        sa.Column('action_weights', JSONB, nullable=False),
        sa.Column('resource_multipliers', JSONB, nullable=False),
        sa.Column('pii_weights', JSONB, nullable=False),
        sa.Column('component_percentages', JSONB, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('activated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(
        'ix_risk_scoring_configs_id',
        'risk_scoring_configs',
        ['id'],
        unique=False
    )
    op.create_index(
        'ix_risk_scoring_configs_is_active',
        'risk_scoring_configs',
        ['is_active'],
        unique=False
    )
    op.create_index(
        'ix_risk_scoring_configs_config_version',
        'risk_scoring_configs',
        ['config_version'],
        unique=False
    )

    # Insert factory default configuration
    # These are the validated weights from Enterprise Hybrid Risk Scoring v2.0.0
    op.execute(
        """
        INSERT INTO risk_scoring_configs (
            config_version,
            algorithm_version,
            environment_weights,
            action_weights,
            resource_multipliers,
            pii_weights,
            component_percentages,
            description,
            is_active,
            is_default,
            created_at,
            created_by
        ) VALUES (
            '2.0.0',
            '2.0.0',
            '{"production": 35, "staging": 20, "development": 5}'::jsonb,
            '{"delete": 25, "write": 20, "read": 10, "list": 8, "describe": 5}'::jsonb,
            '{
                "rds": 1.2, "dynamodb": 1.2, "s3": 1.1, "secretsmanager": 1.2,
                "iam": 1.2, "kms": 1.2, "ec2": 1.0, "lambda": 0.9,
                "cloudwatch": 0.8, "sns": 0.9, "sqs": 0.9, "api_gateway": 1.0,
                "cloudformation": 1.1, "ecs": 1.0, "eks": 1.1, "elasticache": 1.1,
                "route53": 0.9, "cloudfront": 1.0, "elb": 1.0, "vpc": 1.0
            }'::jsonb,
            '{"high_sensitivity": 30, "medium_sensitivity": 20, "low_sensitivity": 10, "none": 0}'::jsonb,
            '{"environment": 35, "data_sensitivity": 30, "action_type": 25, "operational_context": 10}'::jsonb,
            'Factory default configuration - Enterprise Hybrid Risk Scoring v2.0.0',
            true,
            true,
            CURRENT_TIMESTAMP,
            'system'
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema: Drop risk_scoring_configs table."""

    # Drop indexes
    op.drop_index('ix_risk_scoring_configs_config_version', table_name='risk_scoring_configs')
    op.drop_index('ix_risk_scoring_configs_is_active', table_name='risk_scoring_configs')
    op.drop_index('ix_risk_scoring_configs_id', table_name='risk_scoring_configs')

    # Drop table
    op.drop_table('risk_scoring_configs')
