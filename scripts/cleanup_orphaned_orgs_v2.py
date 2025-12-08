#!/usr/bin/env python3
"""
SEC-021 Comprehensive Cleanup Script v5
=======================================
Removes ALL orphaned organizations except owkai-internal (ID 1).
Uses completely isolated database connections per operation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import DATABASE_URL

# ONLY keep owkai-internal
KEEP_ORG_IDS = [1]

def get_fresh_connection():
    """Create a fresh database connection."""
    engine = create_engine(DATABASE_URL)
    return engine.connect()

def delete_org_data(org_id: int) -> bool:
    """Delete all data for a single organization using isolated connection."""
    conn = get_fresh_connection()
    trans = conn.begin()

    try:
        # Tables that may reference organization_id
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

        deleted = []
        for table in tables:
            try:
                result = conn.execute(
                    text(f"DELETE FROM {table} WHERE organization_id = :oid"),
                    {"oid": org_id}
                )
                if result.rowcount > 0:
                    deleted.append(f"{table}:{result.rowcount}")
            except Exception:
                pass  # Table might not exist or not have org_id column

        if deleted:
            print(f"   - Deleted: {', '.join(deleted)}")

        # Get users in this org
        users = conn.execute(
            text("SELECT id, email FROM users WHERE organization_id = :oid"),
            {"oid": org_id}
        ).fetchall()

        if users:
            for uid, email in users:
                # Delete email_verification_audits via signup_requests
                sids = conn.execute(
                    text("SELECT id FROM signup_requests WHERE user_id = :uid"),
                    {"uid": uid}
                ).fetchall()
                for (sid,) in sids:
                    conn.execute(
                        text("DELETE FROM email_verification_audits WHERE signup_request_id = :sid"),
                        {"sid": sid}
                    )
                conn.execute(
                    text("DELETE FROM signup_requests WHERE user_id = :uid"),
                    {"uid": uid}
                )

            conn.execute(
                text("DELETE FROM users WHERE organization_id = :oid"),
                {"oid": org_id}
            )
            print(f"   - Deleted {len(users)} users")

        # Delete signup_requests with this org_id
        result = conn.execute(
            text("DELETE FROM signup_requests WHERE organization_id = :oid"),
            {"oid": org_id}
        )
        if result.rowcount > 0:
            print(f"   - Deleted {result.rowcount} signup_requests")

        # Finally delete organization
        conn.execute(
            text("DELETE FROM organizations WHERE id = :oid"),
            {"oid": org_id}
        )
        print(f"   ✅ Organization {org_id} deleted")

        trans.commit()
        return True

    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:100]}")
        trans.rollback()
        return False
    finally:
        conn.close()

def cleanup():
    """Main cleanup function."""
    print("🧹 SEC-021 Cleanup v5 - Keeping only owkai-internal (ID 1)")
    print("=" * 60)

    # Get org list with fresh connection
    conn = get_fresh_connection()
    orgs = conn.execute(text(
        "SELECT id, name, slug FROM organizations ORDER BY id"
    )).fetchall()
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
        if delete_org_data(org_id):
            success += 1

    # Clean orphaned signups with fresh connection
    print("\n🧹 Cleaning orphaned data...")
    conn = get_fresh_connection()
    trans = conn.begin()
    try:
        orphans = conn.execute(text(
            "SELECT id, email FROM signup_requests WHERE organization_id IS NULL"
        )).fetchall()

        for sid, email in orphans:
            conn.execute(
                text("DELETE FROM email_verification_audits WHERE signup_request_id = :sid"),
                {"sid": sid}
            )
            conn.execute(
                text("DELETE FROM signup_requests WHERE id = :sid"),
                {"sid": sid}
            )
            print(f"   - Deleted orphan signup: {email}")

        conn.execute(text("DELETE FROM signup_attempts"))
        print("   - Cleared rate limits")
        trans.commit()
    except Exception as e:
        print(f"   ⚠️ Orphan cleanup error: {e}")
        trans.rollback()
    finally:
        conn.close()

    # Final report
    print("\n" + "=" * 60)
    print(f"✅ Deleted {success}/{len(to_delete)} organizations")

    conn = get_fresh_connection()
    remaining = conn.execute(
        text("SELECT id, name, slug FROM organizations ORDER BY id")
    ).fetchall()
    conn.close()

    print("\n📋 Remaining:")
    for org in remaining:
        print(f"   [{org[0]}] {org[1]} ({org[2]})")

if __name__ == "__main__":
    cleanup()
