"""Add immutable audit trail tables

Revision ID: immutable_audit_v1
Revises: be858bdecce8
Create Date: 2025-08-14 22:44:26.845705

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'immutable_audit_v1'
down_revision: Union[str, None] = 'be858bdecce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create immutable_audit_logs table
    op.create_table(
        'immutable_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('compliance_tags', sa.JSON(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('chain_hash', sa.String(length=64), nullable=False),
        sa.Column('evidence_pack_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sequence_number')
    )
    
    # Create indexes
    op.create_index('idx_audit_timestamp', 'immutable_audit_logs', ['timestamp'])
    op.create_index('idx_audit_actor', 'immutable_audit_logs', ['actor_id'])
    op.create_index('idx_audit_sequence', 'immutable_audit_logs', ['sequence_number'])
    
    # Create evidence_packs table
    op.create_table(
        'evidence_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('manifest_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_integrity_checks table
    op.create_table(
        'audit_integrity_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('check_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('start_sequence', sa.Integer(), nullable=False),
        sa.Column('end_sequence', sa.Integer(), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('check_duration_ms', sa.Integer(), nullable=False),
        sa.Column('records_per_second', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('audit_integrity_checks')
    op.drop_table('evidence_packs')
    op.drop_index('idx_audit_sequence', table_name='immutable_audit_logs')
    op.drop_index('idx_audit_actor', table_name='immutable_audit_logs')
    op.drop_index('idx_audit_timestamp', table_name='immutable_audit_logs')
    op.drop_table('immutable_audit_logs')
