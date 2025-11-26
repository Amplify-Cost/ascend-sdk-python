#!/usr/bin/env python3
"""
OW-AI Enterprise Pilot Customer Onboarding Script

CONCIERGE MVP ONBOARDING
========================
This script automates the technical steps for onboarding a new pilot customer.
Designed for startup phase where manual review and personal touch is preferred.

Usage:
    python scripts/onboard_pilot_customer.py --company "Acme Corp" --email "admin@acme.com"

What this script does:
1. Creates organization record in database
2. Provisions dedicated AWS Cognito user pool
3. Creates admin user account
4. Generates welcome email content

After running:
- Call the customer to walk them through first login
- Schedule 30-minute setup call
- Monitor their first week of usage

Engineer: Donald King (OW-AI Enterprise)
Date: 2025-11-25
"""

import argparse
import asyncio
import os
import sys
import re
import secrets
import string
from datetime import datetime, timedelta, UTC
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Organization, User
from services.cognito_pool_provisioner import CognitoPoolProvisioner, get_provisioner


# ============================================
# CONFIGURATION
# ============================================

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

# Platform info for emails
PLATFORM_CONFIG = {
    "platform_url": "https://pilot.owkai.app",
    "support_email": "support@owkai.com",
    "founder_name": "Donald",
    "founder_title": "Founder"
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
    # Convert to lowercase
    slug = company_name.lower()

    # Remove special characters except spaces and hyphens
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)

    # Replace spaces with hyphens
    slug = re.sub(r"\s+", "-", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def generate_temp_password() -> str:
    """
    Generate temporary password for initial login.

    Requirements:
    - 16 characters minimum
    - Uppercase, lowercase, numbers, symbols
    - Enterprise-grade entropy
    """
    # Character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"

    # Ensure at least 2 of each
    password = [
        secrets.choice(uppercase),
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(digits),
        secrets.choice(symbols),
        secrets.choice(symbols),
    ]

    # Fill remaining 8 characters
    all_chars = uppercase + lowercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(8))

    # Shuffle for randomness
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


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
# ONBOARDING STEPS
# ============================================

def create_organization(db: Session, company_name: str, admin_email: str) -> Organization:
    """
    Step 1: Create organization record in database.

    Args:
        db: Database session
        company_name: Customer's company name
        admin_email: Admin user's email

    Returns:
        Organization: Created organization object
    """
    print_step(1, "Creating organization record...")

    slug = generate_slug(company_name)

    # Extract email domain for multi-tenant routing
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

    # Create organization with email domain for multi-tenant routing
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
        email_domains=[email_domain] if email_domain else None  # Multi-tenant email routing
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    print_success(f"Organization created: {org.name} (ID: {org.id})")
    print_success(f"Slug: {org.slug}")
    print_success(f"Email domain: {email_domain}")
    print_success(f"Trial ends: {trial_ends_at.strftime('%Y-%m-%d')}")

    return org


async def provision_cognito_pool(db: Session, org: Organization, admin_email: str) -> dict:
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


def create_admin_user(db: Session, org: Organization, admin_email: str) -> tuple[User, str]:
    """
    Step 3: Create admin user in database.

    Note: Cognito user is created by the pool provisioner.
    This creates the local database record.

    Args:
        db: Database session
        org: Organization object
        admin_email: Admin user's email

    Returns:
        tuple: (User object, temporary password)
    """
    print_step(3, "Creating admin user record...")

    # Check if user already exists
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print_warning(f"User already exists: {admin_email} (ID: {existing.id})")
        return existing, "[Use existing password or reset via Cognito]"

    # Generate temporary password
    temp_password = generate_temp_password()

    # Create user (password not stored locally - Cognito handles auth)
    user = User(
        email=admin_email,
        password="COGNITO_MANAGED",  # Placeholder - actual auth via Cognito
        role="admin",
        is_active=True,
        organization_id=org.id,
        is_org_admin=True,
        approval_level=3,  # Admin gets high approval level
        max_risk_approval=100,  # Can approve any risk level
        force_password_change=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print_success(f"Admin user created: {admin_email} (ID: {user.id})")
    print_success(f"Role: admin, Org Admin: Yes")

    return user, temp_password


def generate_welcome_email(
    company_name: str,
    admin_email: str,
    temp_password: str,
    org_slug: str,
    pool_id: str
) -> str:
    """
    Step 4: Generate welcome email content.

    Args:
        company_name: Customer's company name
        admin_email: Admin user's email
        temp_password: Temporary password for first login
        org_slug: Organization slug
        pool_id: Cognito pool ID

    Returns:
        str: Email content (copy/paste into email client)
    """
    print_step(4, "Generating welcome email...")

    email_content = f"""
================================================================================
                    WELCOME EMAIL - COPY AND SEND
================================================================================

TO: {admin_email}
SUBJECT: Welcome to OW-AI Enterprise - Your Pilot Access is Ready!

--------------------------------------------------------------------------------

Hi there,

Welcome to the OW-AI Enterprise pilot program! I'm {PLATFORM_CONFIG['founder_name']},
{PLATFORM_CONFIG['founder_title']} at OW-AI, and I'm excited to have {company_name}
on board.

Your account is now ready. Here's how to get started:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔐 YOUR LOGIN CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your Organization Login URL: {PLATFORM_CONFIG['platform_url']}/#org={org_slug}

Email: {admin_email}
Temporary Password: {temp_password}

⚠️ You'll be prompted to change your password on first login.
⚠️ We recommend enabling MFA (optional but highly recommended).

💡 TIP: Bookmark your organization URL - it automatically connects
   you to your dedicated authentication system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Log in and change your password
2. I'll call you within 24 hours for a quick setup call
3. We'll configure your first AI agent together
4. You'll have direct Slack/email access to me during the pilot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 YOUR PILOT INCLUDES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 30-day full access to OW-AI Enterprise
✅ 100,000 API calls included
✅ Up to 10 team members
✅ Up to 5 MCP server connections
✅ Personal onboarding support from {PLATFORM_CONFIG['founder_name']}
✅ Enterprise security features (MFA, audit logs, compliance)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions? Reply to this email or reach me at {PLATFORM_CONFIG['support_email']}.

Looking forward to working with you!

{PLATFORM_CONFIG['founder_name']}
{PLATFORM_CONFIG['founder_title']}, OW-AI

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

================================================================================
                    INTERNAL NOTES (DO NOT SEND)
================================================================================

Organization ID: Check database
Organization Slug: {org_slug}
Cognito Pool ID: {pool_id}
Onboarded at: {datetime.now(UTC).isoformat()}

NEXT STEPS FOR YOU:
□ Send this email to {admin_email}
□ Add to CRM/tracking spreadsheet
□ Schedule 30-min setup call within 24 hours
□ Set reminder to check their usage after 1 week
□ Plan for conversion discussion at day 21

================================================================================
"""

    print_success("Welcome email generated!")
    print_success("Copy the content above and send via your email client")

    return email_content


# ============================================
# MAIN ONBOARDING FLOW
# ============================================

async def onboard_customer(company_name: str, admin_email: str, dry_run: bool = False):
    """
    Complete onboarding flow for a new pilot customer.

    Args:
        company_name: Customer's company name
        admin_email: Admin user's email
        dry_run: If True, don't make actual changes
    """
    print_header(f"OW-AI Enterprise Pilot Onboarding")
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
            print(f"  2. Provision Cognito pool for: {generate_slug(company_name)}")
            print(f"  3. Create admin user: {admin_email}")
            print(f"  4. Generate welcome email")
            print("\n  Run without --dry-run to execute.")
            return

        # Step 1: Create organization
        org = create_organization(db, company_name, admin_email)

        # Step 2: Provision Cognito pool
        pool_result = await provision_cognito_pool(db, org, admin_email)

        # Step 3: Create admin user
        user, temp_password = create_admin_user(db, org, admin_email)

        # Step 4: Generate welcome email
        email_content = generate_welcome_email(
            company_name=company_name,
            admin_email=admin_email,
            temp_password=temp_password,
            org_slug=org.slug,
            pool_id=pool_result.get("user_pool_id", "N/A")
        )

        # Print summary
        print_header("ONBOARDING COMPLETE")
        print(f"""
  Organization: {org.name} (ID: {org.id})
  Slug: {org.slug}
  Admin: {admin_email} (ID: {user.id})
  Cognito Pool: {pool_result.get('user_pool_id', 'N/A')}
  Trial Ends: {org.trial_ends_at.strftime('%Y-%m-%d') if org.trial_ends_at else 'N/A'}

  NEXT STEPS:
  1. Copy and send the welcome email above
  2. Call {admin_email.split('@')[0]} within 24 hours
  3. Schedule 30-minute setup call
  4. Add to tracking spreadsheet/CRM
""")

        # Print the email content for easy copy/paste
        print(email_content)

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
        description="Onboard a new pilot customer to OW-AI Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/onboard_pilot_customer.py --company "Acme Corp" --email "admin@acme.com"
  python scripts/onboard_pilot_customer.py -c "Big Bank" -e "ciso@bigbank.com" --dry-run

After running:
  1. Send the generated welcome email
  2. Call the customer for setup assistance
  3. Add to your tracking spreadsheet
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
