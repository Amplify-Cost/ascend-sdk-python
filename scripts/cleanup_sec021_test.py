#!/usr/bin/env python3
"""
SEC-021 Test Data Cleanup Script
================================
Removes test data for donald.king@amplifycoast.com to allow re-testing.

Usage:
    python scripts/cleanup_sec021_test.py

This script handles foreign key constraints by deleting in correct order:
1. email_verification_audits (depends on signup_requests)
2. signup_requests (depends on users)
3. users
4. organizations

SAFE: Only removes specific test data, not production data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text

TEST_EMAIL = "donald.king@amplifycoast.com"
TEST_ORG_SLUG = "amplifycoast"

def cleanup_test_data():
    """Remove all test data for SEC-021 re-testing."""
    db = SessionLocal()

    try:
        print(f"🧹 SEC-021 Test Data Cleanup")
        print(f"=" * 50)
        print(f"Email: {TEST_EMAIL}")
        print(f"Org Slug: {TEST_ORG_SLUG}")
        print()

        # ===================================================
        # Step 1: Find signup_request IDs first
        # ===================================================
        signup_ids = db.execute(
            text("""
                SELECT id FROM signup_requests
                WHERE email = :email OR organization_slug = :slug
            """),
            {"email": TEST_EMAIL, "slug": TEST_ORG_SLUG}
        ).fetchall()

        signup_id_list = [row[0] for row in signup_ids]
        print(f"📍 Found signup_request IDs: {signup_id_list}")

        # ===================================================
        # Step 2: Delete email_verification_audits FIRST
        # (FK constraint: references signup_requests)
        # ===================================================
        if signup_id_list:
            for sid in signup_id_list:
                audit_deleted = db.execute(
                    text("DELETE FROM email_verification_audits WHERE signup_request_id = :sid"),
                    {"sid": sid}
                ).rowcount
                if audit_deleted:
                    print(f"✅ Deleted {audit_deleted} email_verification_audits for signup {sid}")

        # ===================================================
        # Step 3: Delete signup_requests SECOND
        # (FK constraint: references users)
        # ===================================================
        signup_result = db.execute(
            text("""
                DELETE FROM signup_requests
                WHERE email = :email OR organization_slug = :slug
                RETURNING id, email, status, organization_slug
            """),
            {"email": TEST_EMAIL, "slug": TEST_ORG_SLUG}
        ).fetchall()

        if signup_result:
            for row in signup_result:
                print(f"✅ Deleted signup_request: ID={row[0]}, Email={row[1]}, Status={row[2]}, Slug={row[3]}")
        else:
            print(f"📍 No signup_requests found")

        # ===================================================
        # Step 4: Delete signup_attempts (rate limiting)
        # ===================================================
        attempts_deleted = db.execute(
            text("DELETE FROM signup_attempts WHERE email LIKE :email_pattern"),
            {"email_pattern": f"%amplifycoast%"}
        ).rowcount

        if attempts_deleted:
            print(f"✅ Deleted {attempts_deleted} signup_attempts (rate limit cleared)")

        # Also clear rate limits for the exact email
        attempts_deleted2 = db.execute(
            text("DELETE FROM signup_attempts WHERE email = :email"),
            {"email": TEST_EMAIL}
        ).rowcount

        if attempts_deleted2:
            print(f"✅ Deleted {attempts_deleted2} signup_attempts for {TEST_EMAIL}")

        # ===================================================
        # Step 5: Delete users THIRD
        # (Now safe - no more FK references)
        # ===================================================
        user_result = db.execute(
            text("DELETE FROM users WHERE email = :email RETURNING id, email, organization_id"),
            {"email": TEST_EMAIL}
        ).fetchone()

        if user_result:
            print(f"✅ Deleted user: {user_result[1]} (ID: {user_result[0]}, Org: {user_result[2]})")
        else:
            print(f"📍 No user found with email '{TEST_EMAIL}'")

        # ===================================================
        # Step 6: Find and delete organization
        # ===================================================
        org_result = db.execute(
            text("SELECT id, name, slug, cognito_pool_status FROM organizations WHERE slug = :slug"),
            {"slug": TEST_ORG_SLUG}
        ).fetchone()

        if org_result:
            org_id = org_result[0]
            print(f"📍 Found organization: {org_result[1]} (ID: {org_id}, Status: {org_result[3]})")

            # Check for remaining users in this org
            remaining_users = db.execute(
                text("SELECT COUNT(*) FROM users WHERE organization_id = :org_id"),
                {"org_id": org_id}
            ).scalar()

            if remaining_users == 0:
                # Safe to delete org
                db.execute(
                    text("DELETE FROM organizations WHERE id = :org_id"),
                    {"org_id": org_id}
                )
                print(f"✅ Deleted organization: {TEST_ORG_SLUG} (ID: {org_id})")
            else:
                print(f"⚠️  Organization has {remaining_users} other users, not deleting")
        else:
            print(f"📍 No organization found with slug '{TEST_ORG_SLUG}'")

        # ===================================================
        # Step 7: Delete from email_audit_log
        # ===================================================
        email_audit_deleted = db.execute(
            text("DELETE FROM email_audit_log WHERE to_email = :email OR organization_slug = :slug"),
            {"email": TEST_EMAIL, "slug": TEST_ORG_SLUG}
        ).rowcount

        if email_audit_deleted:
            print(f"✅ Deleted {email_audit_deleted} email_audit_log entries")

        db.commit()

        print()
        print(f"=" * 50)
        print(f"✅ SEC-021 cleanup complete!")
        print(f"")
        print(f"You can now re-test the signup flow:")
        print(f"1. Go to https://pilot.owkai.app/signup")
        print(f"2. Sign up with {TEST_EMAIL}")
        print(f"3. Verify email")
        print(f"4. Check for welcome email with login URL")
        print(f"5. Login at the org-specific URL")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_test_data()
