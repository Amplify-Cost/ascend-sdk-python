"""SEC-RLS-003: Fix auth_lookup_api_key to return ALL matching keys

CRITICAL FIX: The original SEC-RLS-002 migration used LIMIT 1, which breaks
authentication when multiple API keys share the same 16-character prefix.

Problem:
- Multiple keys can share prefix "owkai_super_admi" (first 16 chars)
- LIMIT 1 returns only the first row (often wrong organization)
- Hash verification fails for keys that are not first in result set

Solution:
- Remove LIMIT 1 from auth_lookup_api_key function
- Application iterates through ALL matching keys
- Hash verified against each candidate until match found

Revision ID: sec_rls_003_multi_key
Revises: sec_rls_002_auth_func
Create Date: 2024-12-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sec_rls_003_multi_key'
down_revision = 'sec_rls_002_auth_func'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # SEC-RLS-003: Fix auth_lookup_api_key to return ALL matching keys
    # ═══════════════════════════════════════════════════════════════════════════

    # Update function to return ALL matching keys (remove LIMIT 1)
    op.execute("""
        CREATE OR REPLACE FUNCTION auth_lookup_api_key(p_prefix VARCHAR(20))
        RETURNS TABLE (
            id INTEGER,
            key_hash VARCHAR(100),
            salt VARCHAR(32),
            user_id INTEGER,
            organization_id INTEGER,
            expires_at TIMESTAMPTZ,
            is_active BOOLEAN
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $func$
        BEGIN
            -- SEC-RLS-003: Returns ALL matching keys (no LIMIT 1)
            -- Multiple keys may share the same 16-char prefix
            -- Application code iterates through candidates and verifies hash against each
            --
            -- Security controls:
            -- 1. SECURITY DEFINER - runs with function owner privileges
            -- 2. SET search_path - prevents search_path injection attacks
            -- 3. Minimal columns - only auth-required fields returned
            -- 4. Hash verification done in application layer (constant-time comparison)

            RETURN QUERY
            SELECT
                ak.id,
                ak.key_hash,
                ak.salt,
                ak.user_id,
                ak.organization_id,
                ak.expires_at,
                ak.is_active
            FROM api_keys ak
            WHERE ak.key_prefix = p_prefix
              AND ak.is_active = true;
        END;
        $func$;
    """)

    # Update function owner back to auth_service
    op.execute("""
        ALTER FUNCTION auth_lookup_api_key(VARCHAR(20)) OWNER TO auth_service;
    """)

    # Add updated comment
    op.execute("""
        COMMENT ON FUNCTION auth_lookup_api_key(VARCHAR(20)) IS
        'SEC-RLS-003: Zero Trust authentication bootstrap function. '
        'Returns ALL matching API keys by prefix (no LIMIT 1). '
        'Supports multiple keys with same prefix - hash verified in application. '
        'Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)(1), NIST 800-53 AC-3';
    """)


def downgrade():
    # Revert to LIMIT 1 version (not recommended)
    op.execute("""
        CREATE OR REPLACE FUNCTION auth_lookup_api_key(p_prefix VARCHAR(20))
        RETURNS TABLE (
            id INTEGER,
            key_hash VARCHAR(100),
            salt VARCHAR(32),
            user_id INTEGER,
            organization_id INTEGER,
            expires_at TIMESTAMPTZ,
            is_active BOOLEAN
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $func$
        BEGIN
            RETURN QUERY
            SELECT
                ak.id,
                ak.key_hash,
                ak.salt,
                ak.user_id,
                ak.organization_id,
                ak.expires_at,
                ak.is_active
            FROM api_keys ak
            WHERE ak.key_prefix = p_prefix
              AND ak.is_active = true
            LIMIT 1;
        END;
        $func$;
    """)

    op.execute("""
        ALTER FUNCTION auth_lookup_api_key(VARCHAR(20)) OWNER TO auth_service;
    """)
