"""create_api_key_tables

Enterprise API Key Management System Migration

Purpose: Create production-grade API key infrastructure for OW-AI SDK
Tables: api_keys, api_key_usage_logs, api_key_permissions, api_key_rate_limits
Security: SHA-256 hashing, audit trails, rate limiting
Compliance: SOX, GDPR, HIPAA, PCI-DSS requirements

Revision ID: 20251120_api_keys
Revises: 195f8d09401f
Create Date: 2025-11-20 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '20251120_api_keys'
down_revision: Union[str, None] = '195f8d09401f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create API key management tables for enterprise SDK authentication

    Tables Created:
    1. api_keys - Cryptographically secure API key storage
    2. api_key_usage_logs - Complete audit trail for all API calls
    3. api_key_permissions - Granular RBAC per API key
    4. api_key_rate_limits - Per-key rate limiting configuration

    Security Features:
    - SHA-256 hashing with salt (never stores plaintext)
    - Constant-time comparison support
    - Complete audit trail (WHO/WHEN/WHY)
    - Automatic expiration support
    - Soft delete (revocation tracking)
    """

    # ========================================
    # Table 1: api_keys (Core API key storage)
    # ========================================
    op.create_table(
        'api_keys',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        # Cryptographic storage (NEVER stores plaintext)
        sa.Column('key_hash', sa.String(length=64), nullable=False),  # SHA-256 hash
        sa.Column('key_prefix', sa.String(length=20), nullable=False),  # For display
        sa.Column('salt', sa.String(length=32), nullable=False),  # Random salt

        # Key metadata
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Status and lifecycle
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        # Revocation tracking (soft delete)
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', sa.Integer(), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),

        # Usage tracking
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_ip', sa.String(length=45), nullable=True),
        sa.Column('usage_count', sa.BigInteger(), nullable=False, server_default='0'),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id']),
        sa.UniqueConstraint('key_hash'),
        sa.CheckConstraint('expires_at IS NULL OR expires_at > created_at', name='valid_expiration'),
        sa.CheckConstraint('revoked_at IS NULL OR revoked_at >= created_at', name='valid_revocation'),
    )

    # Indexes for api_keys
    op.create_index('ix_api_keys_id', 'api_keys', ['id'], unique=False)
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False)
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'], unique=False)
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'], unique=False)
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'], unique=False)
    op.create_index('ix_api_keys_last_used_at', 'api_keys', ['last_used_at'], unique=False)
    op.create_index('idx_api_keys_active_unexpired', 'api_keys', ['is_active', 'expires_at'],
                   unique=False, postgresql_where=sa.text('is_active = TRUE'))

    # ========================================
    # Table 2: api_key_usage_logs (Audit trail)
    # ========================================
    op.create_table(
        'api_key_usage_logs',
        # Primary identification
        sa.Column('id', sa.BigInteger(), nullable=False),  # BigInteger for high volume
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        # Request details
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=False),

        # Network details
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),

        # Performance tracking
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        # Metadata (flexible JSONB storage)
        sa.Column('request_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # Indexes for api_key_usage_logs
    op.create_index('ix_api_key_usage_logs_id', 'api_key_usage_logs', ['id'], unique=False)
    op.create_index('ix_api_key_usage_logs_api_key_id', 'api_key_usage_logs', ['api_key_id'], unique=False)
    op.create_index('ix_api_key_usage_logs_user_id', 'api_key_usage_logs', ['user_id'], unique=False)
    op.create_index('ix_api_key_usage_logs_endpoint', 'api_key_usage_logs', ['endpoint'], unique=False)
    op.create_index('ix_api_key_usage_logs_http_status', 'api_key_usage_logs', ['http_status'], unique=False)
    op.create_index('ix_api_key_usage_logs_ip_address', 'api_key_usage_logs', ['ip_address'], unique=False)
    op.create_index('ix_api_key_usage_logs_request_id', 'api_key_usage_logs', ['request_id'], unique=False)
    op.create_index('ix_api_key_usage_logs_created_at', 'api_key_usage_logs', ['created_at'], unique=False)
    op.create_index('idx_usage_logs_api_key_created', 'api_key_usage_logs', ['api_key_id', 'created_at'], unique=False)
    op.create_index('idx_usage_logs_endpoint_status', 'api_key_usage_logs', ['endpoint', 'http_status'], unique=False)

    # ========================================
    # Table 3: api_key_permissions (Granular RBAC)
    # ========================================
    op.create_table(
        'api_key_permissions',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),

        # Permission definition
        sa.Column('permission_category', sa.String(length=100), nullable=False),
        sa.Column('permission_action', sa.String(length=100), nullable=False),

        # Resource filters (optional, JSONB for flexibility)
        sa.Column('resource_filter', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Audit trail
        sa.Column('granted_by', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id']),
    )

    # Indexes for api_key_permissions
    op.create_index('ix_api_key_permissions_id', 'api_key_permissions', ['id'], unique=False)
    op.create_index('ix_api_key_permissions_api_key_id', 'api_key_permissions', ['api_key_id'], unique=False)
    op.create_index('ix_api_key_permissions_permission_category', 'api_key_permissions', ['permission_category'], unique=False)
    op.create_index('ix_api_key_permissions_permission_action', 'api_key_permissions', ['permission_action'], unique=False)
    op.create_index('idx_permissions_key_category_action', 'api_key_permissions',
                   ['api_key_id', 'permission_category', 'permission_action'], unique=False)

    # ========================================
    # Table 4: api_key_rate_limits (Per-key throttling)
    # ========================================
    op.create_table(
        'api_key_rate_limits',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),

        # Rate limit configuration
        sa.Column('max_requests', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('window_seconds', sa.Integer(), nullable=False, server_default='3600'),

        # Current window tracking
        sa.Column('current_window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_window_count', sa.Integer(), nullable=False, server_default='0'),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('api_key_id'),
    )

    # Indexes for api_key_rate_limits
    op.create_index('ix_api_key_rate_limits_id', 'api_key_rate_limits', ['id'], unique=False)
    op.create_index('ix_api_key_rate_limits_api_key_id', 'api_key_rate_limits', ['api_key_id'], unique=True)


def downgrade() -> None:
    """
    Safely rollback API key tables (reverse order due to foreign keys)

    Order:
    1. Drop api_key_rate_limits (depends on api_keys)
    2. Drop api_key_permissions (depends on api_keys)
    3. Drop api_key_usage_logs (depends on api_keys)
    4. Drop api_keys (base table)
    """

    # Drop api_key_rate_limits
    op.drop_index('ix_api_key_rate_limits_api_key_id', table_name='api_key_rate_limits')
    op.drop_index('ix_api_key_rate_limits_id', table_name='api_key_rate_limits')
    op.drop_table('api_key_rate_limits')

    # Drop api_key_permissions
    op.drop_index('idx_permissions_key_category_action', table_name='api_key_permissions')
    op.drop_index('ix_api_key_permissions_permission_action', table_name='api_key_permissions')
    op.drop_index('ix_api_key_permissions_permission_category', table_name='api_key_permissions')
    op.drop_index('ix_api_key_permissions_api_key_id', table_name='api_key_permissions')
    op.drop_index('ix_api_key_permissions_id', table_name='api_key_permissions')
    op.drop_table('api_key_permissions')

    # Drop api_key_usage_logs
    op.drop_index('idx_usage_logs_endpoint_status', table_name='api_key_usage_logs')
    op.drop_index('idx_usage_logs_api_key_created', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_created_at', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_request_id', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_ip_address', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_http_status', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_endpoint', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_user_id', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_api_key_id', table_name='api_key_usage_logs')
    op.drop_index('ix_api_key_usage_logs_id', table_name='api_key_usage_logs')
    op.drop_table('api_key_usage_logs')

    # Drop api_keys
    op.drop_index('idx_api_keys_active_unexpired', table_name='api_keys')
    op.drop_index('ix_api_keys_last_used_at', table_name='api_keys')
    op.drop_index('ix_api_keys_expires_at', table_name='api_keys')
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_index('ix_api_keys_id', table_name='api_keys')
    op.drop_table('api_keys')
