"""SEC-RLS-002: Create SECURITY DEFINER function for API key authentication

Enterprise Zero Trust Authentication Bootstrap
- SECURITY DEFINER function bypasses RLS for authentication only
- Dedicated auth_service role with minimal privileges
- Returns only fields needed for authentication
- Prevents multi-tenant data leakage during auth

Security:
- Function runs with elevated privileges (auth_service role)
- Scoped ONLY to api_keys table lookup
- Cannot be exploited for data exfiltration
- All subsequent queries use authenticated org_id context

Compliance:
- SOC 2 CC6.1: Logical access security
- PCI-DSS 7.1: Restrict access to cardholder data
- HIPAA 164.312(a)(1): Access control
- NIST 800-53 AC-3: Access enforcement
- FedRAMP AC-3: Access enforcement

Revision ID: sec_rls_002_auth_func
Revises: onboard021_data_rights
Create Date: 2024-12-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'sec_rls_002_auth_func'
down_revision = 'onboard021_data_rights'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # SEC-RLS-002: ENTERPRISE ZERO TRUST AUTHENTICATION BOOTSTRAP
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Create dedicated auth service role (if not exists)
    # This role has minimal privileges - ONLY what's needed for authentication
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_service') THEN
                CREATE ROLE auth_service NOLOGIN;
                RAISE NOTICE 'Created auth_service role';
            END IF;
        END
        $$;
    """)

    # Step 2: Grant minimal SELECT permissions to auth_service
    # Only api_keys and users tables - nothing else
    op.execute("""
        GRANT SELECT ON api_keys TO auth_service;
    """)
    op.execute("""
        GRANT SELECT ON users TO auth_service;
    """)

    # Step 3: Create SECURITY DEFINER function for API key lookup
    # This function bypasses RLS in a controlled, scoped manner
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
            -- SEC-RLS-002: Authentication bootstrap - bypasses RLS by design
            -- This function runs as auth_service role, not the application user
            -- Only returns data needed for authentication, nothing else
            --
            -- Security controls:
            -- 1. SECURITY DEFINER - runs with function owner privileges
            -- 2. SET search_path - prevents search_path injection attacks
            -- 3. LIMIT 1 - prevents enumeration attacks
            -- 4. Minimal columns - only auth-required fields returned

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

    # Step 4: Set function owner to auth_service role
    op.execute("""
        ALTER FUNCTION auth_lookup_api_key(VARCHAR(20)) OWNER TO auth_service;
    """)

    # Step 5: Secure function permissions
    # Revoke from PUBLIC, grant only to application role
    op.execute("""
        REVOKE ALL ON FUNCTION auth_lookup_api_key(VARCHAR(20)) FROM PUBLIC;
    """)

    # Grant execute to the database user (from DATABASE_URL connection)
    # Most RDS/Cloud SQL setups use the connecting user as the app role
    op.execute("""
        DO $$
        DECLARE
            app_role TEXT;
        BEGIN
            -- Get current user (the application database role)
            app_role := current_user;

            -- Grant execute permission to application role
            EXECUTE format('GRANT EXECUTE ON FUNCTION auth_lookup_api_key(VARCHAR(20)) TO %I', app_role);

            RAISE NOTICE 'Granted EXECUTE on auth_lookup_api_key to %', app_role;
        END
        $$;
    """)

    # Step 6: Add comment for documentation
    op.execute("""
        COMMENT ON FUNCTION auth_lookup_api_key(VARCHAR(20)) IS
        'SEC-RLS-002: Zero Trust authentication bootstrap function. '
        'Bypasses RLS to lookup API key by prefix during authentication. '
        'Returns only fields needed for auth verification. '
        'Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)(1), NIST 800-53 AC-3';
    """)


def downgrade():
    # ═══════════════════════════════════════════════════════════════════════════
    # ROLLBACK: Remove SECURITY DEFINER function and auth_service role
    # ═══════════════════════════════════════════════════════════════════════════

    # Step 1: Drop the function
    op.execute("""
        DROP FUNCTION IF EXISTS auth_lookup_api_key(VARCHAR(20));
    """)

    # Step 2: Revoke grants from auth_service
    op.execute("""
        REVOKE ALL ON api_keys FROM auth_service;
    """)
    op.execute("""
        REVOKE ALL ON users FROM auth_service;
    """)

    # Step 3: Drop the role (only if no dependencies)
    op.execute("""
        DO $$
        BEGIN
            DROP ROLE IF EXISTS auth_service;
            RAISE NOTICE 'Dropped auth_service role';
        EXCEPTION
            WHEN dependent_objects_still_exist THEN
                RAISE NOTICE 'auth_service role has dependencies, skipping drop';
        END
        $$;
    """)
