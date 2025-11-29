"""Enterprise ServiceNow Integration Migration

OW-kai Enterprise Integration Phase 3: ServiceNow Connector
Banking-Level ITSM Integration: OAuth2 auth, encrypted credentials, audit trails

Purpose: Create ServiceNow integration infrastructure
Tables: servicenow_connections, servicenow_tickets, servicenow_sync_logs
Security: AES-256 encrypted credentials, tenant isolation
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, ITIL v4

Revision ID: 20251128_servicenow
Revises: 20251128_notifications
Create Date: 2025-11-28 18:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '20251128_servicenow'
down_revision: Union[str, Sequence[str], None] = '20251128_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create ServiceNow integration tables.

    Tables Created:
    1. servicenow_connections - Instance connection configurations
    2. servicenow_tickets - Tickets created from OW-kai
    3. servicenow_sync_logs - Audit trail for sync operations

    Security Features:
    - AES-256 encrypted credentials
    - Multi-tenant isolation via organization_id
    - Complete audit trail for compliance
    - OAuth2 token management
    """

    # ========================================
    # Table 1: servicenow_connections
    # ========================================
    op.create_table(
        'servicenow_connections',
        # Primary identification
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Instance configuration
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instance_url', sa.String(length=512), nullable=False),

        # Authentication (encrypted)
        sa.Column('auth_type', sa.String(length=20), nullable=False, server_default='oauth2'),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('encryption_salt', sa.String(length=32), nullable=False),

        # OAuth2 specific (encrypted)
        sa.Column('encrypted_client_id', sa.Text(), nullable=True),
        sa.Column('encrypted_client_secret', sa.Text(), nullable=True),
        sa.Column('token_endpoint', sa.String(length=512), nullable=True),

        # Connection settings
        sa.Column('api_version', sa.String(length=20), nullable=False, server_default='v2'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),

        # Default ticket configuration
        sa.Column('default_assignment_group', sa.String(length=255), nullable=True),
        sa.Column('default_caller_id', sa.String(length=255), nullable=True),
        sa.Column('default_category', sa.String(length=255), nullable=True),
        sa.Column('default_subcategory', sa.String(length=255), nullable=True),

        # CMDB integration
        sa.Column('cmdb_class', sa.String(length=255), nullable=True),
        sa.Column('cmdb_lookup_field', sa.String(length=255), nullable=True),

        # Field mappings (JSONB)
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_error', sa.Text(), nullable=True),

        # Metrics
        sa.Column('total_tickets_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_sync_errors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),

        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.UniqueConstraint('connection_id'),
    )

    # Indexes for servicenow_connections
    op.create_index('ix_servicenow_connections_id', 'servicenow_connections', ['id'], unique=False)
    op.create_index('ix_servicenow_connections_organization_id', 'servicenow_connections', ['organization_id'], unique=False)
    op.create_index('ix_servicenow_connections_connection_id', 'servicenow_connections', ['connection_id'], unique=True)
    op.create_index('ix_servicenow_connections_is_active', 'servicenow_connections', ['is_active'], unique=False)
    op.create_index('ix_servicenow_connections_created_at', 'servicenow_connections', ['created_at'], unique=False)
    op.create_index('idx_snow_conn_org_active', 'servicenow_connections', ['organization_id', 'is_active'],
                   unique=False, postgresql_where=sa.text('is_active = TRUE'))

    # ========================================
    # Table 2: servicenow_tickets
    # ========================================
    op.create_table(
        'servicenow_tickets',
        # Primary identification
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),

        # Ticket identification
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('servicenow_sys_id', sa.String(length=64), nullable=True),
        sa.Column('servicenow_number', sa.String(length=64), nullable=True),

        # Ticket type and content
        sa.Column('ticket_type', sa.String(length=50), nullable=False),
        sa.Column('short_description', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('work_notes', sa.Text(), nullable=True),

        # Classification
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='3'),
        sa.Column('impact', sa.String(length=10), nullable=False, server_default='2'),
        sa.Column('urgency', sa.String(length=10), nullable=False, server_default='2'),
        sa.Column('state', sa.String(length=10), nullable=False, server_default='1'),

        # Assignment
        sa.Column('assignment_group', sa.String(length=255), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('caller_id', sa.String(length=255), nullable=True),

        # Categorization
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('subcategory', sa.String(length=255), nullable=True),

        # CMDB reference
        sa.Column('cmdb_ci', sa.String(length=255), nullable=True),
        sa.Column('cmdb_ci_sys_id', sa.String(length=64), nullable=True),

        # OW-kai source reference
        sa.Column('source_type', sa.String(length=100), nullable=True),
        sa.Column('source_id', sa.String(length=64), nullable=True),
        sa.Column('source_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # ServiceNow response data
        sa.Column('servicenow_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('servicenow_link', sa.String(length=1024), nullable=True),

        # Sync status
        sa.Column('sync_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('sync_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),

        # Bidirectional sync
        sa.Column('servicenow_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('local_updated_at', sa.DateTime(timezone=True), nullable=True),

        # Custom fields
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['connection_id'], ['servicenow_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('ticket_id'),
    )

    # Indexes for servicenow_tickets
    op.create_index('ix_servicenow_tickets_id', 'servicenow_tickets', ['id'], unique=False)
    op.create_index('ix_servicenow_tickets_organization_id', 'servicenow_tickets', ['organization_id'], unique=False)
    op.create_index('ix_servicenow_tickets_connection_id', 'servicenow_tickets', ['connection_id'], unique=False)
    op.create_index('ix_servicenow_tickets_ticket_id', 'servicenow_tickets', ['ticket_id'], unique=True)
    op.create_index('ix_servicenow_tickets_servicenow_sys_id', 'servicenow_tickets', ['servicenow_sys_id'], unique=False)
    op.create_index('ix_servicenow_tickets_servicenow_number', 'servicenow_tickets', ['servicenow_number'], unique=False)
    op.create_index('ix_servicenow_tickets_ticket_type', 'servicenow_tickets', ['ticket_type'], unique=False)
    op.create_index('ix_servicenow_tickets_state', 'servicenow_tickets', ['state'], unique=False)
    op.create_index('ix_servicenow_tickets_sync_status', 'servicenow_tickets', ['sync_status'], unique=False)
    op.create_index('ix_servicenow_tickets_source_type', 'servicenow_tickets', ['source_type'], unique=False)
    op.create_index('ix_servicenow_tickets_source_id', 'servicenow_tickets', ['source_id'], unique=False)
    op.create_index('ix_servicenow_tickets_created_at', 'servicenow_tickets', ['created_at'], unique=False)
    op.create_index('idx_snow_tickets_org_status', 'servicenow_tickets', ['organization_id', 'sync_status'], unique=False)
    op.create_index('idx_snow_tickets_conn_type', 'servicenow_tickets', ['connection_id', 'ticket_type'], unique=False)
    op.create_index('idx_snow_tickets_pending', 'servicenow_tickets', ['sync_status'],
                   unique=False, postgresql_where=sa.text("sync_status = 'pending'"))

    # ========================================
    # Table 3: servicenow_sync_logs
    # ========================================
    op.create_table(
        'servicenow_sync_logs',
        # Primary identification
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('ticket_id', sa.BigInteger(), nullable=True),

        # Operation details
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),

        # Request/Response
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        # Status
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['connection_id'], ['servicenow_connections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ticket_id'], ['servicenow_tickets.id'], ondelete='SET NULL'),
    )

    # Indexes for servicenow_sync_logs
    op.create_index('ix_servicenow_sync_logs_id', 'servicenow_sync_logs', ['id'], unique=False)
    op.create_index('ix_servicenow_sync_logs_organization_id', 'servicenow_sync_logs', ['organization_id'], unique=False)
    op.create_index('ix_servicenow_sync_logs_operation', 'servicenow_sync_logs', ['operation'], unique=False)
    op.create_index('ix_servicenow_sync_logs_success', 'servicenow_sync_logs', ['success'], unique=False)
    op.create_index('ix_servicenow_sync_logs_created_at', 'servicenow_sync_logs', ['created_at'], unique=False)
    op.create_index('idx_snow_logs_org_created', 'servicenow_sync_logs', ['organization_id', 'created_at'], unique=False)
    op.create_index('idx_snow_logs_conn_success', 'servicenow_sync_logs', ['connection_id', 'success'], unique=False)


def downgrade() -> None:
    """
    Safely rollback ServiceNow tables (reverse order due to foreign keys)
    """

    # Drop servicenow_sync_logs
    op.drop_index('idx_snow_logs_conn_success', table_name='servicenow_sync_logs')
    op.drop_index('idx_snow_logs_org_created', table_name='servicenow_sync_logs')
    op.drop_index('ix_servicenow_sync_logs_created_at', table_name='servicenow_sync_logs')
    op.drop_index('ix_servicenow_sync_logs_success', table_name='servicenow_sync_logs')
    op.drop_index('ix_servicenow_sync_logs_operation', table_name='servicenow_sync_logs')
    op.drop_index('ix_servicenow_sync_logs_organization_id', table_name='servicenow_sync_logs')
    op.drop_index('ix_servicenow_sync_logs_id', table_name='servicenow_sync_logs')
    op.drop_table('servicenow_sync_logs')

    # Drop servicenow_tickets
    op.drop_index('idx_snow_tickets_pending', table_name='servicenow_tickets')
    op.drop_index('idx_snow_tickets_conn_type', table_name='servicenow_tickets')
    op.drop_index('idx_snow_tickets_org_status', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_created_at', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_source_id', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_source_type', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_sync_status', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_state', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_ticket_type', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_servicenow_number', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_servicenow_sys_id', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_ticket_id', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_connection_id', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_organization_id', table_name='servicenow_tickets')
    op.drop_index('ix_servicenow_tickets_id', table_name='servicenow_tickets')
    op.drop_table('servicenow_tickets')

    # Drop servicenow_connections
    op.drop_index('idx_snow_conn_org_active', table_name='servicenow_connections')
    op.drop_index('ix_servicenow_connections_created_at', table_name='servicenow_connections')
    op.drop_index('ix_servicenow_connections_is_active', table_name='servicenow_connections')
    op.drop_index('ix_servicenow_connections_connection_id', table_name='servicenow_connections')
    op.drop_index('ix_servicenow_connections_organization_id', table_name='servicenow_connections')
    op.drop_index('ix_servicenow_connections_id', table_name='servicenow_connections')
    op.drop_table('servicenow_connections')
