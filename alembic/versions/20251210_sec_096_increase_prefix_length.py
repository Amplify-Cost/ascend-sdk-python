"""SEC-096: Increase API key prefix length to prevent collisions

Problem:
- Current prefix length is 16 characters
- Role prefix "owkai_super_admin_" is 18 characters
- ALL super_admin keys share the same 16-char prefix "owkai_super_admi"
- This causes 5 keys to collide, requiring iteration through all candidates

Solution:
- Increase prefix from 16 to 32 characters
- 32 chars = 18 (role prefix) + 14 (random chars)
- 14 random chars = ~84 bits of entropy
- Collision probability: 1 in 2^84

Changes:
1. Increase key_prefix column from VARCHAR(20) to VARCHAR(40)
2. Update auth_lookup_api_key function parameter to VARCHAR(40)

Backward Compatibility:
- Existing keys with 16-char prefixes continue to work
- SEC-RLS-003 iterates all matching candidates
- New keys get 32-char prefixes, eliminating future collisions

Revision ID: sec_096_prefix_len
Revises: sec_rls_003_multi_key
Create Date: 2024-12-10
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sec_096_prefix_len'
down_revision = 'sec_rls_003_multi_key'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # SEC-096: Increase API key prefix length to prevent collisions
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Increase key_prefix column size from VARCHAR(20) to VARCHAR(40)
    op.alter_column('api_keys', 'key_prefix',
        existing_type=sa.VARCHAR(20),
        type_=sa.VARCHAR(40),
        existing_nullable=False)

    # Step 2: Update auth_lookup_api_key function to accept VARCHAR(40)
    op.execute("""
        CREATE OR REPLACE FUNCTION auth_lookup_api_key(p_prefix VARCHAR(40))
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
            -- SEC-096: Updated to accept 32-char prefix (VARCHAR(40) for headroom)
            -- SEC-RLS-003: Returns ALL matching keys (no LIMIT 1)
            -- Multiple keys may share the same prefix
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

    # Step 3: Update function owner to auth_service
    op.execute("""
        ALTER FUNCTION auth_lookup_api_key(VARCHAR(40)) OWNER TO auth_service;
    """)

    # Step 4: Add updated comment
    op.execute("""
        COMMENT ON FUNCTION auth_lookup_api_key(VARCHAR(40)) IS
        'SEC-096: Zero Trust authentication bootstrap function. '
        'Accepts 32-char prefix (VARCHAR(40)) to prevent collisions. '
        'Returns ALL matching API keys by prefix. '
        'Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)(1), NIST 800-53 AC-3';
    """)


def downgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # ROLLBACK: Revert to VARCHAR(20) prefix
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Revert function to VARCHAR(20)
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
              AND ak.is_active = true;
        END;
        $func$;
    """)

    op.execute("""
        ALTER FUNCTION auth_lookup_api_key(VARCHAR(20)) OWNER TO auth_service;
    """)

    # Step 2: Revert column size (WARNING: may truncate data if > 20 chars exist)
    op.alter_column('api_keys', 'key_prefix',
        existing_type=sa.VARCHAR(40),
        type_=sa.VARCHAR(20),
        existing_nullable=False)
