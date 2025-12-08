#!/usr/bin/env python3
"""
SEC-021 Direct Cleanup Script
==============================
Uses psycopg2 directly with autocommit to avoid SQLAlchemy transaction issues.
"""

import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from environment or AWS Secrets Manager
def get_db_url():
    # Try environment first
    url = os.environ.get('DATABASE_URL')
    if url:
        return url

    # Load from config module
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import DATABASE_URL
    return DATABASE_URL

def parse_db_url(url):
    """Parse database URL into connection params."""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password,
    }

# Only keep owkai-internal
KEEP_ORG_IDS = [1]

def get_connection():
    """Get a fresh connection with autocommit."""
    db_url = get_db_url()
    params = parse_db_url(db_url)
    conn = psycopg2.connect(**params)
    conn.autocommit = True  # Critical: avoids transaction state issues
    return conn

def delete_organization(org_id: int) -> bool:
    """Delete a single organization and all its data."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Tables that reference organization_id
        tables = [
            'pending_actions',
            'agent_actions',
            'alerts',
            'smart_rules',
            'rule_feedback',
            'automation_playbooks',
            'playbook_versions',
            'playbook_execution_logs',
            'workflows',
            'workflow_steps',
            'enterprise_policies',
            'policy_templates',
            'api_keys',
            'audit_logs',
            'risk_scoring_configs',
            'notification_channels',
            'webhook_endpoints',
            'servicenow_configs',
            'integration_configs',
            'compliance_export_jobs',
            'cognito_pool_audit',
            'email_audit_log',
            'mcp_governance_decisions',
            'agent_registry',
        ]

        deleted_info = []
        for table in tables:
            try:
                cur.execute(f"DELETE FROM {table} WHERE organization_id = %s", (org_id,))
                if cur.rowcount > 0:
                    deleted_info.append(f"{table}:{cur.rowcount}")
            except psycopg2.Error:
                pass  # Table might not exist

        if deleted_info:
            print(f"   - Deleted: {', '.join(deleted_info)}")

        # Handle users and their signup data
        cur.execute("SELECT id, email FROM users WHERE organization_id = %s", (org_id,))
        users = cur.fetchall()

        if users:
            for uid, email in users:
                # Delete email_verification_audits via signup_requests
                cur.execute("SELECT id FROM signup_requests WHERE user_id = %s", (uid,))
                for (sid,) in cur.fetchall():
                    cur.execute("DELETE FROM email_verification_audits WHERE signup_request_id = %s", (sid,))
                cur.execute("DELETE FROM signup_requests WHERE user_id = %s", (uid,))

            cur.execute("DELETE FROM users WHERE organization_id = %s", (org_id,))
            print(f"   - Deleted {len(users)} users")

        # Delete signup_requests with this org
        cur.execute("DELETE FROM signup_requests WHERE organization_id = %s", (org_id,))
        if cur.rowcount > 0:
            print(f"   - Deleted {cur.rowcount} signup_requests")

        # Finally delete the organization
        cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
        print(f"   ✅ Organization {org_id} deleted")

        return True

    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:100]}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    """Main cleanup function."""
    print("🧹 SEC-021 Direct Cleanup - Keeping only owkai-internal (ID 1)")
    print("=" * 60)

    # Get list of organizations
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, slug FROM organizations ORDER BY id")
    orgs = cur.fetchall()
    cur.close()
    conn.close()

    print("\n📋 Organizations:")
    to_delete = []
    for org in orgs:
        if org[0] in KEEP_ORG_IDS:
            print(f"  [{org[0]}] {org[1]} ({org[2]}) - ✅ KEEP")
        else:
            print(f"  [{org[0]}] {org[1]} ({org[2]}) - ❌ DELETE")
            to_delete.append(org[0])

    if not to_delete:
        print("\n✅ Nothing to delete!")
        return

    print(f"\n🗑️  Deleting {len(to_delete)} organizations...\n")

    success = 0
    for org_id in to_delete:
        print(f"🧹 Org {org_id}:")
        if delete_organization(org_id):
            success += 1

    # Clean orphaned signup data
    print("\n🧹 Cleaning orphaned signup data...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, email FROM signup_requests WHERE organization_id IS NULL")
        orphans = cur.fetchall()

        for sid, email in orphans:
            cur.execute("DELETE FROM email_verification_audits WHERE signup_request_id = %s", (sid,))
            cur.execute("DELETE FROM signup_requests WHERE id = %s", (sid,))
            print(f"   - Deleted orphan signup: {email}")

        cur.execute("DELETE FROM signup_attempts")
        print("   - Cleared rate limits")

    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    finally:
        cur.close()
        conn.close()

    # Final report
    print("\n" + "=" * 60)
    print(f"✅ Deleted {success}/{len(to_delete)} organizations")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, slug FROM organizations ORDER BY id")
    remaining = cur.fetchall()
    cur.close()
    conn.close()

    print("\n📋 Remaining:")
    for org in remaining:
        print(f"   [{org[0]}] {org[1]} ({org[2]})")

if __name__ == "__main__":
    main()
