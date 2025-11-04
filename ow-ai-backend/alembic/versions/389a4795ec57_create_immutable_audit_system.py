"""create_immutable_audit_system

Revision ID: 389a4795ec57
Revises: 71964a40de51
Create Date: 2025-11-03 16:29:02.283336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '389a4795ec57'
down_revision: Union[str, None] = '71964a40de51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create enterprise immutable audit system."""
    # Enable UUID extension for PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create immutable_audit_logs table (WORM design)
    op.execute("""
        CREATE TABLE IF NOT EXISTS immutable_audit_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sequence_number SERIAL UNIQUE NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source_system VARCHAR(100) NOT NULL DEFAULT 'ow-ai',

            -- Event data
            event_type VARCHAR(50) NOT NULL,
            actor_id VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100) NOT NULL,
            action VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            compliance_tags JSONB DEFAULT '[]'::jsonb,

            -- Immutability (hash-chaining for tamper detection)
            content_hash VARCHAR(64) NOT NULL,
            previous_hash VARCHAR(64),
            chain_hash VARCHAR(64) NOT NULL,

            -- Evidence and retention
            evidence_pack_id UUID,
            retention_until TIMESTAMP WITH TIME ZONE,
            legal_hold BOOLEAN DEFAULT FALSE,

            -- Metadata
            ip_address VARCHAR(45),
            user_agent TEXT,
            session_id VARCHAR(100)
        );
    """)

    # Create indexes for performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON immutable_audit_logs(timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor ON immutable_audit_logs(actor_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_resource ON immutable_audit_logs(resource_type, resource_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_compliance ON immutable_audit_logs USING GIN(compliance_tags);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_retention ON immutable_audit_logs(retention_until);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_sequence ON immutable_audit_logs(sequence_number);")

    # Create evidence_packs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS evidence_packs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            case_number VARCHAR(100),
            investigation_id VARCHAR(100),
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE NOT NULL,
            actor_ids JSONB,
            resource_types JSONB,
            manifest_hash VARCHAR(64) NOT NULL,
            signature BYTEA,
            certificate_info JSONB,
            status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP WITH TIME ZONE,
            legal_hold BOOLEAN DEFAULT FALSE,
            retention_policy VARCHAR(50),
            compliance_frameworks JSONB
        );
    """)

    # Create audit_integrity_checks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_integrity_checks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            check_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            start_sequence INTEGER NOT NULL,
            end_sequence INTEGER NOT NULL,
            total_records INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL,
            broken_chains JSONB,
            invalid_hashes JSONB,
            check_duration_ms INTEGER NOT NULL,
            records_per_second INTEGER NOT NULL,
            details JSONB,
            remediation_actions JSONB
        );
    """)

    print("✅ Enterprise immutable audit system tables created successfully")


def downgrade() -> None:
    """Downgrade schema - Remove immutable audit system."""
    # Drop tables in reverse order (respects foreign keys)
    op.execute("DROP TABLE IF EXISTS audit_integrity_checks CASCADE;")
    op.execute("DROP TABLE IF EXISTS evidence_packs CASCADE;")
    op.execute("DROP TABLE IF EXISTS immutable_audit_logs CASCADE;")

    print("✅ Enterprise immutable audit system tables dropped")
