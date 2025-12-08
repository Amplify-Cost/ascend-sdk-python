#!/usr/bin/env python3
"""
SEC-021 Comprehensive Cleanup Script v4
=======================================
Removes ALL orphaned organizations except owkai-internal (ID 1).
Uses fresh sessions to avoid transaction issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text

# ONLY keep owkai-internal
KEEP_ORG_IDS = [1]

def delete_org_data(org_id: int):
    """Delete all data for a single organization using fresh session."""
    db = SessionLocal()
    try:
        # Delete from all tables that reference organization_id
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
                r = db.execute(text(f"DELETE FROM {table} WHERE organization_id = :oid"), {"oid": org_id})
                if r.rowcount > 0:
                    deleted.append(f"{table}:{r.rowcount}")
            except:
                pass  # Table might not exist or not have org_id

        if deleted:
            print(f"   - Deleted: {', '.join(deleted)}")

        # Get and delete users
        users = db.execute(
            text("SELECT id, email FROM users WHERE organization_id = :oid"), {"oid": org_id}
        ).fetchall()

        if users:
            for uid, email in users:
                # Delete email_verification_audits via signup_requests
                sids = db.execute(
                    text("SELECT id FROM signup_requests WHERE user_id = :uid"), {"uid": uid}
                ).fetchall()
                for (sid,) in sids:
                    db.execute(text("DELETE FROM email_verification_audits WHERE signup_request_id = :sid"), {"sid": sid})
                db.execute(text("DELETE FROM signup_requests WHERE user_id = :uid"), {"uid": uid})

            db.execute(text("DELETE FROM users WHERE organization_id = :oid"), {"oid": org_id})
            print(f"   - Deleted {len(users)} users")

        # Delete signup_requests with org_id
        r = db.execute(text("DELETE FROM signup_requests WHERE organization_id = :oid"), {"oid": org_id})
        if r.rowcount > 0:
            print(f"   - Deleted {r.rowcount} signup_requests")

        # Finally delete organization
        db.execute(text("DELETE FROM organizations WHERE id = :oid"), {"oid": org_id})
        print(f"   ✅ Organization {org_id} deleted")

        db.commit()
        return True

    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:80]}")
        db.rollback()
        return False
    finally:
        db.close()

def cleanup():
    """Main cleanup function."""
    print("🧹 SEC-021 Cleanup - Keeping only owkai-internal (ID 1)")
    print("=" * 60)

    # Get org list
    db = SessionLocal()
    orgs = db.execute(text(
        "SELECT id, name, slug FROM organizations ORDER BY id"
    )).fetchall()
    db.close()

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

    # Clean orphaned signups
    print("\n🧹 Cleaning orphaned data...")
    db = SessionLocal()
    try:
        orphans = db.execute(text(
            "SELECT id, email FROM signup_requests WHERE organization_id IS NULL"
        )).fetchall()

        for sid, email in orphans:
            db.execute(text("DELETE FROM email_verification_audits WHERE signup_request_id = :sid"), {"sid": sid})
            db.execute(text("DELETE FROM signup_requests WHERE id = :sid"), {"sid": sid})
            print(f"   - Deleted signup: {email}")

        db.execute(text("DELETE FROM signup_attempts"))
        print("   - Cleared rate limits")
        db.commit()
    finally:
        db.close()

    # Report
    print("\n" + "=" * 60)
    print(f"✅ Deleted {success}/{len(to_delete)} organizations")

    db = SessionLocal()
    remaining = db.execute(text("SELECT id, name, slug FROM organizations ORDER BY id")).fetchall()
    db.close()

    print("\n📋 Remaining:")
    for org in remaining:
        print(f"   [{org[0]}] {org[1]} ({org[2]})")

if __name__ == "__main__":
    cleanup()
