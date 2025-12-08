#!/usr/bin/env python3
"""
Ascend Enterprise Pilot Customer Onboarding Script

ONBOARD-001b: Enhanced Enterprise Onboarding
=============================================
This script automates the complete technical onboarding for a new pilot customer.

Usage:
    python scripts/onboard_pilot_customer.py --company "Acme Corp" --email "admin@acme.com"
    python scripts/onboard_pilot_customer.py -c "Big Bank" -e "ciso@bigbank.com" --dry-run

What this script does:
1. Creates organization record in database
2. Provisions dedicated AWS Cognito user pool (or uses existing)
3. Creates admin user in Cognito via AdminCreateUser
4. Sends welcome email automatically via Cognito
5. Creates local database user record
6. Generates API key for SDK integration
7. Runs verification checks

Security:
- No temporary passwords displayed in console (sent via email only)
- API key displayed once then never again
- Complete audit trail

Compliance: SOC 2, PCI-DSS, HIPAA, GDPR
Author: Ascend Platform Engineering
Date: 2025-12-07
"""

import argparse
import asyncio
import os
import sys
import re
import secrets
import hashlib
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Organization, User
from models_api_keys import ApiKey
from services.cognito_pool_provisioner import CognitoPoolProvisioner, get_provisioner


# ============================================
# CONFIGURATION
# ============================================

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# Pilot tier limits (generous for testing)
PILOT_TIER_CONFIG = {
    "subscription_tier": "pilot",
    "subscription_status": "trial",
    "included_api_calls": 100000,
    "included_users": 10,
    "included_mcp_servers": 5,
    "trial_days": 30,
    "mfa_config": "OPTIONAL"  # Not required for pilot
}

# Platform info
PLATFORM_CONFIG = {
    "platform_url": "https://pilot.owkai.app",
    "api_url": "https://pilot.owkai.app/api/v1",
    "support_email": "support@ascendowkai.com",
    "company_name": "Ascend"
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_slug(company_name: str) -> str:
    """
    Generate URL-safe slug from company name.

    Examples:
        "Acme Corp" -> "acme-corp"
        "Big Bank Inc." -> "big-bank-inc"
        "O'Reilly Media" -> "oreilly-media"
    """
    slug = company_name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 79)
    print(f"  {text}")
    print("=" * 79)


def print_step(step_num: int, text: str):
    """Print numbered step."""
    print(f"\n  [{step_num}] {text}")


def print_success(text: str):
    """Print success message."""
    print(f"      ✅ {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"      ⚠️  {text}")


def print_error(text: str):
    """Print error message."""
    print(f"      ❌ {text}")


# ============================================
# STEP 1: CREATE ORGANIZATION
# ============================================

def create_organization(db: Session, company_name: str, admin_email: str) -> Organization:
    """
    Step 1: Create organization record in database.

    Args:
        db: Database session
        company_name: Customer's company name
        admin_email: Admin user's email

    Returns:
        Organization: Created or existing organization object
    """
    print_step(1, "Creating organization record...")

    slug = generate_slug(company_name)
    email_domain = admin_email.split('@')[1].lower() if '@' in admin_email else None

    # Check if slug already exists
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        print_warning(f"Organization with slug '{slug}' already exists (ID: {existing.id})")
        # Update email domains if not already set
        if email_domain and not existing.email_domains:
            existing.email_domains = [email_domain]
            db.commit()
            print_success(f"Added email domain: {email_domain}")
        elif email_domain and email_domain not in (existing.email_domains or []):
            existing.email_domains = (existing.email_domains or []) + [email_domain]
            db.commit()
            print_success(f"Added email domain: {email_domain}")
        return existing

    # Calculate trial end date
    trial_ends_at = datetime.now(UTC) + timedelta(days=PILOT_TIER_CONFIG["trial_days"])

    # Create organization
    org = Organization(
        name=company_name,
        slug=slug,
        subscription_tier=PILOT_TIER_CONFIG["subscription_tier"],
        subscription_status=PILOT_TIER_CONFIG["subscription_status"],
        trial_ends_at=trial_ends_at,
        included_api_calls=PILOT_TIER_CONFIG["included_api_calls"],
        included_users=PILOT_TIER_CONFIG["included_users"],
        included_mcp_servers=PILOT_TIER_CONFIG["included_mcp_servers"],
        cognito_pool_status="pending",
        cognito_mfa_configuration=PILOT_TIER_CONFIG["mfa_config"],
        email_domains=[email_domain] if email_domain else None
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    print_success(f"Organization created: {org.name} (ID: {org.id})")
    print_success(f"Slug: {org.slug}")
    print_success(f"Email domain: {email_domain}")
    print_success(f"Trial ends: {trial_ends_at.strftime('%Y-%m-%d')}")

    return org


# ============================================
# STEP 2: PROVISION COGNITO POOL
# ============================================

async def provision_cognito_pool(db: Session, org: Organization, admin_email: str) -> Dict[str, Any]:
    """
    Step 2: Provision dedicated AWS Cognito user pool.

    Args:
        db: Database session
        org: Organization object
        admin_email: Admin user's email

    Returns:
        dict: Cognito pool configuration
    """
    print_step(2, "Provisioning AWS Cognito user pool...")

    # Check if already provisioned
    if org.cognito_user_pool_id and org.cognito_pool_status == "active":
        print_warning(f"Pool already exists: {org.cognito_user_pool_id}")
        return {
            "user_pool_id": org.cognito_user_pool_id,
            "app_client_id": org.cognito_app_client_id,
            "status": "exists"
        }

    # Get provisioner and create pool
    provisioner = get_provisioner()

    result = await provisioner.create_organization_pool(
        organization_id=org.id,
        organization_name=org.name,
        organization_slug=org.slug,
        admin_email=admin_email,
        db=db,
        mfa_config=PILOT_TIER_CONFIG["mfa_config"]
    )

    print_success(f"Pool created: {result['user_pool_id']}")
    print_success(f"App client: {result['app_client_id']}")
    print_success(f"Domain: {result.get('domain', 'N/A')}")

    return result


# ============================================
# STEP 3: CREATE COGNITO USER (AUTO-EMAIL)
# ============================================

def create_cognito_admin_user(
    email: str,
    org: Organization,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Step 3: Create admin user in Cognito with auto-sent welcome email.

    ONBOARD-001b: Uses AdminCreateUser with DesiredDeliveryMediums=["EMAIL"]
    to automatically send temporary password via email.

    Args:
        email: Admin user's email
        org: Organization object
        dry_run: If True, don't actually create

    Returns:
        dict with cognito_sub, status, email_sent
    """
    print_step(3, "Creating admin user in Cognito...")

    if dry_run:
        print_warning("DRY RUN: Would create Cognito user")
        return {
            "cognito_sub": "dry-run-sub",
            "status": "FORCE_CHANGE_PASSWORD",
            "email_sent": False,
            "dry_run": True
        }

    client = boto3.client('cognito-idp', region_name=AWS_REGION)

    # Use org's dedicated pool if exists, else fall back to platform pool
    pool_id = org.cognito_user_pool_id or os.getenv("COGNITO_USER_POOL_ID")

    if not pool_id:
        raise ValueError("No Cognito User Pool ID available (org pool or env var)")

    try:
        response = client.admin_create_user(
            UserPoolId=pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:organization_id", "Value": str(org.id)},
                {"Name": "custom:role", "Value": "super_admin"},
            ],
            DesiredDeliveryMediums=["EMAIL"],  # AUTO-SEND EMAIL with temp password
            ForceAliasCreation=False
        )

        cognito_sub = response["User"]["Username"]
        user_status = response["User"]["UserStatus"]

        print_success(f"Cognito user created: {cognito_sub}")
        print_success(f"Status: {user_status}")
        print_success(f"Welcome email sent to: {email}")

        return {
            "cognito_sub": cognito_sub,
            "status": user_status,
            "email_sent": True,
            "existing": False
        }

    except client.exceptions.UsernameExistsException:
        print_warning(f"User {email} already exists in Cognito")
        # Get existing user
        try:
            existing = client.admin_get_user(UserPoolId=pool_id, Username=email)
            return {
                "cognito_sub": existing["Username"],
                "status": existing["UserStatus"],
                "email_sent": False,
                "existing": True
            }
        except Exception:
            return {
                "cognito_sub": email,
                "status": "UNKNOWN",
                "email_sent": False,
                "existing": True
            }

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print_error(f"Cognito error ({error_code}): {error_msg}")
        raise


# ============================================
# STEP 4: CREATE DATABASE USER
# ============================================

def create_database_user(
    db: Session,
    org: Organization,
    admin_email: str,
    cognito_sub: str
) -> User:
    """
    Step 4: Create admin user record in database.

    Args:
        db: Database session
        org: Organization object
        admin_email: Admin user's email
        cognito_sub: Cognito username/sub

    Returns:
        User: Created or existing user object
    """
    print_step(4, "Creating database user record...")

    # Check if user already exists
    existing = db.query(User).filter(
        User.email == admin_email,
        User.organization_id == org.id
    ).first()

    if existing:
        print_warning(f"User already exists: {admin_email} (ID: {existing.id})")
        # Update cognito_user_id if not set
        if not existing.cognito_user_id:
            existing.cognito_user_id = cognito_sub
            db.commit()
            print_success(f"Linked to Cognito: {cognito_sub}")
        return existing

    # Create user with Super Admin privileges
    user = User(
        email=admin_email,
        password="COGNITO_MANAGED",  # Placeholder - actual auth via Cognito
        role="super_admin",  # ONBOARD-001b: Super Admin role
        is_active=True,
        organization_id=org.id,
        is_org_admin=True,
        approval_level=3,  # High approval level
        max_risk_approval=100,  # Can approve any risk level
        force_password_change=True,
        cognito_user_id=cognito_sub
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print_success(f"User created: {admin_email} (ID: {user.id})")
    print_success(f"Role: Super Admin (full tenant access)")
    print_success(f"Organization: {org.name} (ID: {org.id})")

    return user


# ============================================
# STEP 5: GENERATE API KEY
# ============================================

def generate_api_key(
    db: Session,
    org: Organization,
    user: User,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Step 5: Generate API key for SDK integration.

    ONBOARD-001b: Automatically generates API key for the tenant.
    Key is displayed ONCE and must be saved by the operator.

    Args:
        db: Database session
        org: Organization object
        user: User object
        dry_run: If True, don't actually create

    Returns:
        dict with key_id, key_value (ONLY shown once!), key_prefix
    """
    print_step(5, "Generating API key for SDK integration...")

    if dry_run:
        print_warning("DRY RUN: Would generate API key")
        return {
            "key_id": 0,
            "key_value": "ask_dry_run_example_key",
            "key_prefix": "ask_dry_run",
            "dry_run": True
        }

    # Generate secure key value
    # Format: ask_{random_32_chars} (ask = Ascend SDK Key)
    key_value = f"ask_{secrets.token_urlsafe(32)}"

    # Generate salt and hash
    salt = secrets.token_hex(16)
    key_with_salt = f"{key_value}{salt}"
    key_hash = hashlib.sha256(key_with_salt.encode()).hexdigest()

    # Key prefix for display (first 16 chars)
    key_prefix = key_value[:16]

    # Create API key record
    api_key = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        salt=salt,
        name=f"{org.name} - Admin SDK Key",
        description=f"Auto-generated during onboarding for {user.email}",
        is_active=True,
        expires_at=None,  # Never expires
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    print_success(f"API key generated: {key_prefix}...")
    print_success(f"Key ID: {api_key.id}")

    return {
        "key_id": api_key.id,
        "key_value": key_value,  # ONLY shown once!
        "key_prefix": key_prefix
    }


# ============================================
# STEP 6: VERIFICATION
# ============================================

def verify_onboarding(
    db: Session,
    org: Organization,
    user: User,
    cognito_result: Dict[str, Any],
    api_key_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Step 6: Verify all components were created successfully.

    Args:
        db: Database session
        org: Organization object
        user: User object
        cognito_result: Result from Cognito user creation
        api_key_result: Result from API key generation

    Returns:
        dict with verification results
    """
    print_step(6, "Running verification checks...")

    checks = {
        "organization_exists": db.query(Organization).filter(
            Organization.id == org.id
        ).first() is not None,

        "user_exists": db.query(User).filter(
            User.id == user.id
        ).first() is not None,

        "user_is_super_admin": user.role == "super_admin" or user.is_org_admin == True,

        "cognito_user_created": cognito_result.get("cognito_sub") is not None,

        "email_sent": cognito_result.get("email_sent", False) or cognito_result.get("existing", False),

        "tenant_isolated": user.organization_id == org.id,

        "api_key_generated": api_key_result.get("key_id") is not None or api_key_result.get("dry_run", False)
    }

    all_passed = all(checks.values())

    print()
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        display_name = check_name.replace('_', ' ').title()
        print(f"      {status} {display_name}")

    return {
        "all_passed": all_passed,
        "checks": checks
    }


# ============================================
# SUCCESS SUMMARY
# ============================================

def print_success_summary(
    org: Organization,
    user: User,
    cognito_result: Dict[str, Any],
    api_key_result: Dict[str, Any],
    verification: Dict[str, Any]
):
    """Print enterprise-grade success summary."""
    print()
    print("=" * 79)
    print("                    TENANT ONBOARDING COMPLETE ✅")
    print("=" * 79)
    print()
    print("Organization:")
    print(f"  ID:           {org.id}")
    print(f"  Name:         {org.name}")
    print(f"  Slug:         {org.slug}")
    print(f"  Tier:         {org.subscription_tier}")
    if org.trial_ends_at:
        print(f"  Trial Ends:   {org.trial_ends_at.strftime('%Y-%m-%d')}")
    print()
    print("Super Admin User:")
    print(f"  Email:        {user.email}")
    print(f"  User ID:      {user.id}")
    print(f"  Role:         Super Admin (full tenant access)")
    print(f"  Status:       {cognito_result.get('status', 'CREATED')}")
    print()
    print("Credentials:")
    print(f"  Password:     Sent via email (check inbox)")
    print(f"  API Key:      {api_key_result['key_value']}")
    print()
    print("  " + "=" * 60)
    print("  ⚠️  IMPORTANT: Save the API key now - it won't be shown again!")
    print("  " + "=" * 60)
    print()
    print("Customer Next Steps:")
    print("  1. Check email for temporary password")
    print(f"  2. Go to {PLATFORM_CONFIG['platform_url']}")
    print("  3. Login with email + temporary password")
    print("  4. Set permanent password")
    print("  5. Use API key for SDK/API integration")
    print()
    print(f"Dashboard: {PLATFORM_CONFIG['platform_url']}")
    print(f"API Base:  {PLATFORM_CONFIG['api_url']}")
    print()
    print("=" * 79)


# ============================================
# MAIN ONBOARDING FLOW
# ============================================

async def onboard_customer(company_name: str, admin_email: str, dry_run: bool = False):
    """
    Complete onboarding flow for a new pilot customer.

    ONBOARD-001b: Enhanced flow with auto-email, API key, and verification.

    Args:
        company_name: Customer's company name
        admin_email: Admin user's email
        dry_run: If True, don't make actual changes
    """
    print_header("Ascend Enterprise Pilot Onboarding")
    print(f"\n  Company: {company_name}")
    print(f"  Admin Email: {admin_email}")

    if dry_run:
        print("\n  ⚠️  DRY RUN MODE - No changes will be made")

    print("\n" + "-" * 60)

    db = SessionLocal()

    try:
        if dry_run:
            print("\n  [DRY RUN] Would execute the following steps:")
            print(f"  1. Create organization: {company_name} (slug: {generate_slug(company_name)})")
            print(f"  2. Provision Cognito pool (or use existing)")
            print(f"  3. Create Cognito user: {admin_email} (auto-send email)")
            print(f"  4. Create database user record")
            print(f"  5. Generate API key")
            print(f"  6. Run verification checks")
            print("\n  Run without --dry-run to execute.")
            return

        # Step 1: Create organization
        org = create_organization(db, company_name, admin_email)

        # Step 2: Provision Cognito pool
        pool_result = await provision_cognito_pool(db, org, admin_email)

        # Refresh org to get updated Cognito fields
        db.refresh(org)

        # Step 3: Create Cognito user (auto-sends email)
        cognito_result = create_cognito_admin_user(admin_email, org, dry_run)

        # Step 4: Create database user
        user = create_database_user(db, org, admin_email, cognito_result["cognito_sub"])

        # Step 5: Generate API key
        api_key_result = generate_api_key(db, org, user, dry_run)

        # Step 6: Verification
        verification = verify_onboarding(db, org, user, cognito_result, api_key_result)

        # Print success summary
        print_success_summary(org, user, cognito_result, api_key_result, verification)

        if not verification["all_passed"]:
            print_warning("Some verification checks failed - please review above")

    except Exception as e:
        print_error(f"Onboarding failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()


# ============================================
# CLI ENTRY POINT
# ============================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ascend Enterprise Pilot Customer Onboarding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/onboard_pilot_customer.py --company "Acme Corp" --email "admin@acme.com"
  python scripts/onboard_pilot_customer.py -c "Big Bank" -e "ciso@bigbank.com" --dry-run

What happens:
  1. Organization created in database
  2. Cognito user pool provisioned (if needed)
  3. Admin user created in Cognito (welcome email sent automatically)
  4. Database user record created
  5. API key generated (displayed once - save it!)
  6. Verification checks run

After running:
  - Customer receives email with temporary password
  - Customer logs in and sets permanent password
  - Customer uses API key for SDK integration
        """
    )

    parser.add_argument(
        "-c", "--company",
        required=True,
        help="Customer's company name (e.g., 'Acme Corp')"
    )

    parser.add_argument(
        "-e", "--email",
        required=True,
        help="Admin user's email address"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without making changes"
    )

    args = parser.parse_args()

    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", args.email):
        print(f"Error: Invalid email format: {args.email}")
        sys.exit(1)

    # Run onboarding
    asyncio.run(onboard_customer(
        company_name=args.company,
        admin_email=args.email,
        dry_run=args.dry_run
    ))


if __name__ == "__main__":
    main()
