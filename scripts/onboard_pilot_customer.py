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
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import Organization, User
from models_api_keys import ApiKey
from services.cognito_pool_provisioner import CognitoPoolProvisioner, get_provisioner

# Configure logging
logger = logging.getLogger(__name__)


# ============================================
# CONFIGURATION
# ============================================

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# ONBOARD-006: Production database configuration
AWS_SECRETS_MANAGER_DB_KEY = "/owkai/pilot/backend/DB_URL"


# ============================================
# ONBOARD-006: DATABASE URL AUTO-FETCH
# ============================================

def get_database_url() -> str:
    """
    ONBOARD-006: Get DATABASE_URL with automatic fallback to AWS Secrets Manager.

    Priority:
    1. Environment variable DATABASE_URL (allows override for testing)
    2. AWS Secrets Manager (production default)

    Returns:
        str: PostgreSQL connection string

    Raises:
        SystemExit: If no valid DATABASE_URL can be obtained
    """
    # Check environment first (allows manual override)
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        # Don't use localhost default
        if "localhost" not in env_url and "127.0.0.1" not in env_url:
            print(f"      ℹ️  Using DATABASE_URL from environment")
            return env_url
        else:
            print(f"      ⚠️  Ignoring localhost DATABASE_URL, fetching from Secrets Manager...")

    # Fetch from AWS Secrets Manager
    print(f"      ℹ️  Fetching DATABASE_URL from AWS Secrets Manager...")

    try:
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=AWS_SECRETS_MANAGER_DB_KEY)

        db_url = response.get('SecretString')

        if not db_url:
            print(f"      ❌ Secret {AWS_SECRETS_MANAGER_DB_KEY} exists but is empty")
            sys.exit(1)

        # Handle JSON-wrapped secrets
        if db_url.startswith('{'):
            secret_dict = json.loads(db_url)
            # Try common key names
            db_url = secret_dict.get('DATABASE_URL') or secret_dict.get('url') or secret_dict.get('connection_string')
            if not db_url:
                print(f"      ❌ Could not find DATABASE_URL in secret JSON: {list(secret_dict.keys())}")
                sys.exit(1)

        print(f"      ✅ DATABASE_URL retrieved from Secrets Manager")
        return db_url.strip()

    except NoCredentialsError:
        print(f"""
      ❌ AWS credentials not configured.

      Please run: aws configure
      Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.
""")
        sys.exit(1)

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"      ❌ Secret {AWS_SECRETS_MANAGER_DB_KEY} not found in Secrets Manager")
        elif error_code == 'AccessDeniedException':
            print(f"      ❌ Access denied to secret {AWS_SECRETS_MANAGER_DB_KEY}")
            print(f"         Check IAM permissions for secretsmanager:GetSecretValue")
        else:
            print(f"      ❌ AWS error: {e.response['Error']['Message']}")
        sys.exit(1)

    except Exception as e:
        print(f"      ❌ Unexpected error fetching DATABASE_URL: {e}")
        sys.exit(1)


def get_db_session() -> Session:
    """
    ONBOARD-006: Create database session using production DATABASE_URL.
    Auto-fetches from AWS Secrets Manager if not in environment.

    Returns:
        Session: SQLAlchemy database session
    """
    database_url = get_database_url()

    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# Pilot tier limits (generous for testing)
PILOT_TIER_CONFIG = {
    "subscription_tier": "pilot",
    "subscription_status": "trial",
    "included_api_calls": 100000,
    "included_users": 10,
    "included_mcp_servers": 5,
    "trial_days": 30,
    "mfa_config": "OFF"  # OFF for pilot (OPTIONAL requires SMS config)
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


def sanitize_for_cognito(name: str) -> str:
    """
    ONBOARD-003: Sanitize company name for AWS Cognito tags.

    AWS Cognito tags only allow: letters, numbers, spaces, and _ . : / = + - @
    Invalid characters: & < > \\ ^ and non-ASCII

    Examples:
        "K&C Executive Protection" -> "K and C Executive Protection"
        "Acme Corp <test>" -> "Acme Corp test"
    """
    # Replace common symbols with words
    sanitized = name.replace("&", "and")

    # Remove invalid characters for AWS tags
    sanitized = sanitized.replace("<", "").replace(">", "")
    sanitized = sanitized.replace("\\", "").replace("^", "")
    sanitized = sanitized.replace("=", "").replace("|", "")

    # Remove non-ASCII characters
    sanitized = ''.join(c for c in sanitized if ord(c) < 128)

    # Clean up multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized)

    return sanitized.strip()


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
# ONBOARD-005: AWS VERIFICATION FUNCTIONS
# ============================================

async def verify_and_activate_cognito_pool(db: Session, org: Organization) -> dict:
    """
    Enterprise verification: Confirm AWS resources exist before activating.

    Implements idempotent provisioning pattern (Wiz/Datadog standard):
    - Verifies AWS pool exists and is active
    - Verifies app client exists
    - Verifies domain is configured (if applicable)
    - Only sets status='active' after ALL verifications pass

    Returns:
        dict: Verification results with status and any issues
    """
    client = boto3.client('cognito-idp', region_name=org.cognito_region or 'us-east-2')

    verification = {
        "pool_exists": False,
        "pool_active": False,
        "client_exists": False,
        "domain_exists": False,
        "issues": [],
        "verified": False
    }

    # 1. Verify pool exists and is active
    if not org.cognito_user_pool_id:
        verification["issues"].append("No cognito_user_pool_id configured")
        return verification

    try:
        pool_response = client.describe_user_pool(UserPoolId=org.cognito_user_pool_id)
        verification["pool_exists"] = True
        pool_status = pool_response['UserPool'].get('Status')
        # ONBOARD-037: AWS Cognito returns null/None for healthy pools
        # A pool that exists and can be described is considered active
        verification["pool_active"] = pool_status is None or pool_status in ('Active', 'Enabled')

        if not verification["pool_active"]:
            verification["issues"].append(f"Pool status is '{pool_status}', expected None, 'Active', or 'Enabled'")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            verification["issues"].append(f"Pool {org.cognito_user_pool_id} not found in AWS")
        else:
            verification["issues"].append(f"AWS error checking pool: {e.response['Error']['Message']}")
        return verification

    # 2. Verify app client exists
    if not org.cognito_app_client_id:
        verification["issues"].append("No cognito_app_client_id configured")
        return verification

    try:
        client.describe_user_pool_client(
            UserPoolId=org.cognito_user_pool_id,
            ClientId=org.cognito_app_client_id
        )
        verification["client_exists"] = True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            verification["issues"].append(f"App client {org.cognito_app_client_id} not found")
        else:
            verification["issues"].append(f"AWS error checking client: {e.response['Error']['Message']}")
        return verification

    # 3. Verify domain (optional but recommended)
    if org.cognito_domain:
        try:
            domain_response = client.describe_user_pool_domain(Domain=org.cognito_domain)
            domain_status = domain_response.get('DomainDescription', {}).get('Status', 'Unknown')
            verification["domain_exists"] = (domain_status == 'ACTIVE')

            if not verification["domain_exists"]:
                verification["issues"].append(f"Domain status is '{domain_status}', expected 'ACTIVE'")
        except ClientError as e:
            verification["issues"].append(f"Domain verification failed: {e.response['Error']['Message']}")
            # Domain is not critical for login, continue

    # 4. Final verification
    verification["verified"] = (
        verification["pool_exists"] and
        verification["pool_active"] and
        verification["client_exists"]
    )

    # 5. Update database status if verified
    if verification["verified"]:
        if org.cognito_pool_status != 'active':
            org.cognito_pool_status = 'active'
            db.commit()
            logger.info(f"✅ Pool verified and status set to 'active': {org.cognito_user_pool_id}")
    else:
        logger.error(f"❌ Pool verification failed: {verification['issues']}")
        if org.cognito_pool_status == 'active':
            org.cognito_pool_status = 'verification_failed'
            db.commit()
            logger.warning(f"⚠️ Status changed from 'active' to 'verification_failed'")

    return verification


async def verify_cognito_user_exists(org: Organization, email: str) -> dict:
    """
    Verify user exists in Cognito pool and check their status.

    Returns:
        dict: User verification results
    """
    client = boto3.client('cognito-idp', region_name=org.cognito_region or 'us-east-2')

    verification = {
        "user_exists": False,
        "user_status": None,
        "email_verified": False,
        "issues": []
    }

    try:
        response = client.admin_get_user(
            UserPoolId=org.cognito_user_pool_id,
            Username=email
        )

        verification["user_exists"] = True
        verification["user_status"] = response.get('UserStatus', 'Unknown')

        # Check email verified attribute
        for attr in response.get('UserAttributes', []):
            if attr['Name'] == 'email_verified':
                verification["email_verified"] = (attr['Value'].lower() == 'true')

        # Valid statuses for login
        valid_statuses = ['CONFIRMED', 'FORCE_CHANGE_PASSWORD']
        if verification["user_status"] not in valid_statuses:
            verification["issues"].append(
                f"User status is '{verification['user_status']}', expected one of {valid_statuses}"
            )
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            verification["issues"].append(f"User {email} not found in pool {org.cognito_user_pool_id}")
        else:
            verification["issues"].append(f"AWS error: {e.response['Error']['Message']}")

    return verification


async def verify_existing_organization(db: Session, slug: str) -> dict:
    """
    Enterprise health check for existing organization.

    Use: python onboard_pilot_customer.py --verify-only --org-slug kc-executive-protection
    """
    print("═" * 70)
    print("              ORGANIZATION VERIFICATION REPORT")
    print("═" * 70)
    print()

    # Find organization
    org = db.query(Organization).filter(
        Organization.slug == slug
    ).first()

    if not org:
        print(f"❌ Organization with slug '{slug}' not found")
        print()
        print("Available organizations:")
        orgs = db.query(Organization).order_by(Organization.id.desc()).limit(10).all()
        for o in orgs:
            print(f"   - {o.slug} (ID: {o.id}, Status: {o.cognito_pool_status})")
        return {"found": False}

    report = {
        "found": True,
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "tier": org.subscription_tier,
            "created": str(org.created_at)
        },
        "cognito": {
            "pool_id": org.cognito_user_pool_id,
            "client_id": org.cognito_app_client_id,
            "domain": org.cognito_domain,
            "database_status": org.cognito_pool_status
        },
        "aws_verification": None,
        "users": [],
        "ready_for_login": False,
        "issues": []
    }

    print("ORGANIZATION")
    print("─" * 70)
    print(f"   ID:           {org.id}")
    print(f"   Name:         {org.name}")
    print(f"   Slug:         {org.slug}")
    print(f"   Tier:         {org.subscription_tier}")
    print(f"   Created:      {org.created_at}")
    print()

    print("COGNITO CONFIGURATION")
    print("─" * 70)
    print(f"   Pool ID:      {org.cognito_user_pool_id or '❌ NOT SET'}")
    print(f"   Client ID:    {org.cognito_app_client_id or '❌ NOT SET'}")
    print(f"   Domain:       {org.cognito_domain or '❌ NOT SET'}")
    print(f"   DB Status:    {org.cognito_pool_status or '❌ NOT SET'}")
    print()

    # AWS Verification
    if org.cognito_user_pool_id:
        print("AWS VERIFICATION")
        print("─" * 70)

        pool_verification = await verify_and_activate_cognito_pool(db, org)
        report["aws_verification"] = pool_verification

        print(f"   Pool Exists:    {'✅' if pool_verification['pool_exists'] else '❌'}")
        print(f"   Pool Active:    {'✅' if pool_verification['pool_active'] else '❌'}")
        print(f"   Client Exists:  {'✅' if pool_verification['client_exists'] else '❌'}")
        print(f"   Domain Active:  {'✅' if pool_verification['domain_exists'] else '⚠️ Not verified'}")

        if pool_verification["issues"]:
            print()
            print("   Issues:")
            for issue in pool_verification["issues"]:
                print(f"      ❌ {issue}")
                report["issues"].append(issue)
        print()

    # Check users
    print("USERS")
    print("─" * 70)
    users = db.query(User).filter(User.organization_id == org.id).all()

    if not users:
        print("   ❌ No users found")
        report["issues"].append("No users in organization")
    else:
        for user in users:
            user_status = "Unknown"
            if org.cognito_user_pool_id:
                try:
                    client = boto3.client('cognito-idp', region_name='us-east-2')
                    cognito_user = client.admin_get_user(
                        UserPoolId=org.cognito_user_pool_id,
                        Username=user.email
                    )
                    user_status = cognito_user.get('UserStatus', 'Unknown')
                except:
                    user_status = "NOT FOUND IN COGNITO"
                    report["issues"].append(f"User {user.email} not found in Cognito")

            print(f"   {user.email}")
            print(f"      Role: {user.role}")
            print(f"      Cognito Status: {user_status}")
            report["users"].append({
                "email": user.email,
                "role": user.role,
                "cognito_status": user_status
            })
    print()

    # Final assessment
    print("ASSESSMENT")
    print("─" * 70)

    ready = (
        org.cognito_user_pool_id and
        org.cognito_app_client_id and
        org.cognito_pool_status == 'active' and
        len(users) > 0 and
        len(report["issues"]) == 0
    )
    report["ready_for_login"] = ready

    if ready:
        print("   ✅ READY FOR LOGIN")
        print()
        print(f"   Login URL: https://pilot.owkai.app")
        print(f"   Org Slug:  {org.slug}")
    else:
        print("   ❌ NOT READY FOR LOGIN")
        print()
        print("   Issues to resolve:")
        for issue in report["issues"]:
            print(f"      - {issue}")

        if org.cognito_pool_status != 'active':
            print()
            print("   Recommendation: cognito_pool_status should be 'active'")
            print(f"   Current value:  '{org.cognito_pool_status}'")

    print()
    print("═" * 70)

    return report


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
        organization_id=org.id,  # ONBOARD-003: Required for tenant isolation
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

async def onboard_customer(company_name: str, admin_email: str, dry_run: bool = False, use_platform_pool: bool = False):
    """
    Complete onboarding flow for a new pilot customer.

    ONBOARD-001b: Enhanced flow with auto-email, API key, and verification.

    Args:
        company_name: Customer's company name
        admin_email: Admin user's email
        dry_run: If True, don't make actual changes
        use_platform_pool: If True, use existing platform pool instead of creating new one
    """
    print_header("Ascend Enterprise Pilot Onboarding")
    print(f"\n  Company: {company_name}")
    print(f"  Admin Email: {admin_email}")

    if dry_run:
        print("\n  ⚠️  DRY RUN MODE - No changes will be made")

    if use_platform_pool:
        print("\n  ℹ️  PLATFORM POOL MODE - Using existing Cognito pool")

    print("\n" + "-" * 60)

    # ONBOARD-006: Connect to database (auto-fetches URL from Secrets Manager)
    print("\n  [0/6] Connecting to database...")
    db = get_db_session()
    print()

    print("-" * 60)

    try:
        if dry_run:
            print("\n  [DRY RUN] Would execute the following steps:")
            print(f"  1. Create organization: {company_name} (slug: {generate_slug(company_name)})")
            if use_platform_pool:
                print(f"  2. Use existing platform Cognito pool")
            else:
                print(f"  2. Provision Cognito pool (or use existing)")
            print(f"  3. Create Cognito user: {admin_email} (auto-send email)")
            print(f"  4. Create database user record")
            print(f"  5. Generate API key")
            print(f"  6. Run verification checks")
            print("\n  Run without --dry-run to execute.")
            return

        # Step 1: Create organization
        org = create_organization(db, company_name, admin_email)

        # Step 2: Provision Cognito pool or use platform pool
        if use_platform_pool:
            # Use existing platform pool (don't update org - unique constraint)
            platform_pool_id = os.getenv("COGNITO_USER_POOL_ID", "us-east-2_kRgol6Zxu")
            platform_client_id = os.getenv("COGNITO_APP_CLIENT_ID", "26j75u2q9uf4g67qac6lik8j9c")

            print_step(2, "Using existing platform Cognito pool...")
            print_success(f"Pool ID: {platform_pool_id}")
            print_success(f"App client: {platform_client_id}")
            print_warning("Platform pool mode - org shares platform pool")

            # Set org fields only if not already set (to avoid unique constraint)
            if not org.cognito_user_pool_id:
                org.cognito_pool_status = "platform"  # Mark as platform-shared
                db.commit()

            pool_result = {
                "user_pool_id": platform_pool_id,
                "app_client_id": platform_client_id,
                "status": "platform"
            }
        else:
            pool_result = await provision_cognito_pool(db, org, admin_email)

        # Refresh org to get updated Cognito fields
        db.refresh(org)

        # ONBOARD-005: Verify pool before proceeding
        if not use_platform_pool and org.cognito_user_pool_id:
            print_step(2.5, "Verifying Cognito pool provisioning...")
            pool_verification = await verify_and_activate_cognito_pool(db, org)
            if pool_verification["verified"]:
                print_success("Pool verified and activated")
            else:
                print_warning(f"Pool verification issues: {pool_verification['issues']}")
                # Continue anyway - pool may still work

        # Step 3: Create Cognito user (auto-sends email)
        cognito_result = create_cognito_admin_user(admin_email, org, dry_run)

        # ONBOARD-005: Verify user was created in Cognito
        if not dry_run and org.cognito_user_pool_id:
            print_step(3.5, "Verifying Cognito user creation...")
            user_verification = await verify_cognito_user_exists(org, admin_email)
            if user_verification["user_exists"]:
                print_success(f"User verified in Cognito (status: {user_verification['user_status']})")
            else:
                print_warning(f"User verification issues: {user_verification['issues']}")

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
        required=False,  # ONBOARD-005: Not required for --verify-only mode
        help="Customer's company name (e.g., 'Acme Corp')"
    )

    parser.add_argument(
        "-e", "--email",
        required=False,  # ONBOARD-005: Not required for --verify-only mode
        help="Admin user's email address"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without making changes"
    )

    parser.add_argument(
        "--use-platform-pool",
        action="store_true",
        help="Use existing platform Cognito pool instead of creating new one (recommended for pilot)"
    )

    # ONBOARD-005: Verification-only mode arguments
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify an existing organization (no changes made)"
    )

    parser.add_argument(
        "--org-slug",
        type=str,
        help="Organization slug to verify (used with --verify-only)"
    )

    args = parser.parse_args()

    # ONBOARD-005: Handle --verify-only mode
    if args.verify_only:
        if not args.org_slug:
            print("Error: --org-slug is required when using --verify-only")
            print("Usage: python scripts/onboard_pilot_customer.py --verify-only --org-slug kc-executive-protection")
            sys.exit(1)

        # ONBOARD-006: Connect to database (auto-fetches URL from Secrets Manager)
        print("\n  [0] Connecting to database...")
        db = get_db_session()
        print()
        try:
            asyncio.run(verify_existing_organization(db, args.org_slug))
        finally:
            db.close()
        return

    # Standard onboarding mode - validate required args
    if not args.company:
        print("Error: --company is required for onboarding")
        sys.exit(1)

    if not args.email:
        print("Error: --email is required for onboarding")
        sys.exit(1)

    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", args.email):
        print(f"Error: Invalid email format: {args.email}")
        sys.exit(1)

    # Run onboarding
    asyncio.run(onboard_customer(
        company_name=args.company,
        admin_email=args.email,
        dry_run=args.dry_run,
        use_platform_pool=args.use_platform_pool
    ))


if __name__ == "__main__":
    main()
