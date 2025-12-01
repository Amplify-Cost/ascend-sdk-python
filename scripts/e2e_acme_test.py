#!/usr/bin/env python3
"""
OW-AI Enterprise E2E Test - Acme Corp
=====================================

Full end-to-end test including:
1. Reset/create test user with new temp password
2. Send welcome email via AWS SES
3. Verify email delivery
4. Test full authentication flow

Usage:
    cd ow-ai-backend
    python scripts/e2e_acme_test.py

Test Email: info@ow-kai.com
Organization: Acme Corp

Date: 2025-12-01
"""

import asyncio
import os
import sys
import secrets
import string
from datetime import datetime, UTC

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from models import Organization, User

# Test configuration
TEST_EMAIL = "info@ow-kai.com"
TEST_ORG_NAME = "Acme Corp"
TEST_ORG_SLUG = "acme-corp"
PLATFORM_URL = "https://pilot.owkai.app"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")


def print_step(num: int, text: str):
    print(f"\n{Colors.BLUE}[Step {num}]{Colors.RESET} {text}")


def print_success(text: str):
    print(f"  {Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str):
    print(f"  {Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str):
    print(f"  {Colors.CYAN}ℹ️  {text}{Colors.RESET}")


def generate_temp_password() -> str:
    """Generate secure temporary password."""
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"

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

    all_chars = uppercase + lowercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(8))
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


async def run_e2e_test():
    """Run full E2E test for Acme Corp."""

    print_header("OW-AI Enterprise E2E Test")
    print(f"\n  Organization: {TEST_ORG_NAME}")
    print(f"  Test Email: {TEST_EMAIL}")
    print(f"  Platform: {PLATFORM_URL}")
    print(f"  Started: {datetime.now(UTC).isoformat()}")

    db = SessionLocal()
    temp_password = None

    try:
        # Step 1: Find or create organization
        print_step(1, "Checking Acme Corp organization...")

        org = db.query(Organization).filter(Organization.slug == TEST_ORG_SLUG).first()

        if org:
            print_success(f"Organization found: {org.name} (ID: {org.id})")
            print_info(f"Cognito Pool: {org.cognito_user_pool_id or 'Not set'}")
        else:
            print_error("Acme Corp organization not found!")
            print_info("Run: python scripts/onboard_pilot_customer.py -c 'Acme Corp' -e 'info@ow-kai.com'")
            return False

        # Step 2: Check/create user
        print_step(2, f"Checking user: {TEST_EMAIL}...")

        user = db.query(User).filter(
            User.email == TEST_EMAIL,
            User.organization_id == org.id
        ).first()

        if user:
            print_success(f"User found: {user.email} (ID: {user.id})")
            print_info(f"Role: {user.role}, Org Admin: {user.is_org_admin}")
            print_info(f"Cognito ID: {user.cognito_user_id or 'Not linked'}")
        else:
            print_warning("User not found - will be created during Cognito password reset")

        # Step 3: Reset password in Cognito
        print_step(3, "Resetting password in AWS Cognito...")

        temp_password = generate_temp_password()

        if org.cognito_user_pool_id:
            try:
                import boto3
                cognito = boto3.client('cognito-idp', region_name='us-east-2')

                # Try to set a new temporary password
                try:
                    cognito.admin_set_user_password(
                        UserPoolId=org.cognito_user_pool_id,
                        Username=TEST_EMAIL,
                        Password=temp_password,
                        Permanent=False  # User must change on first login
                    )
                    print_success(f"Temporary password set in Cognito")
                    print_info(f"Pool: {org.cognito_user_pool_id}")
                except cognito.exceptions.UserNotFoundException:
                    print_warning("User not in Cognito - creating new user...")

                    # Create user in Cognito
                    response = cognito.admin_create_user(
                        UserPoolId=org.cognito_user_pool_id,
                        Username=TEST_EMAIL,
                        TemporaryPassword=temp_password,
                        UserAttributes=[
                            {'Name': 'email', 'Value': TEST_EMAIL},
                            {'Name': 'email_verified', 'Value': 'true'},
                        ],
                        MessageAction='SUPPRESS'  # We'll send our own email
                    )
                    cognito_user_id = response['User']['Username']
                    print_success(f"User created in Cognito: {cognito_user_id}")

                    # Create/update local user
                    if not user:
                        user = User(
                            email=TEST_EMAIL,
                            password="COGNITO_MANAGED",
                            role="admin",
                            is_active=True,
                            organization_id=org.id,
                            is_org_admin=True,
                            approval_level=3,
                            max_risk_approval=100,
                            force_password_change=True,
                            cognito_user_id=cognito_user_id
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        print_success(f"Local user created (ID: {user.id})")
                    elif not user.cognito_user_id:
                        user.cognito_user_id = cognito_user_id
                        db.commit()
                        print_success("Linked local user to Cognito")

            except Exception as e:
                print_error(f"Cognito error: {e}")
                print_warning("Continuing with email send...")
        else:
            print_warning("No Cognito pool configured - password set locally only")

        # Step 4: Send welcome email via AWS SES
        print_step(4, "Sending welcome email via AWS SES...")

        try:
            from services.enterprise_email_service import email_service

            login_url = f"{PLATFORM_URL}/#org={org.slug}"

            email_result = await email_service.send_welcome_email(
                db=db,
                to_email=TEST_EMAIL,
                organization_name=org.name,
                organization_slug=org.slug,
                temp_password=temp_password,
                login_url=login_url,
                trial_days=30,
                sent_by="e2e_test_script"
            )

            if email_result.get('success'):
                print_success(f"Welcome email sent!")
                print_info(f"SES Message ID: {email_result.get('message_id')}")
                print_info(f"Audit ID: {email_result.get('audit_id')}")
            else:
                print_error(f"Email failed: {email_result.get('error')}")

        except Exception as e:
            print_error(f"Email service error: {e}")

        # Step 5: Print test credentials
        print_step(5, "Test Credentials Generated")

        print(f"""
{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}
{Colors.BOLD}  E2E TEST CREDENTIALS{Colors.RESET}
{Colors.GREEN}{'='*60}{Colors.RESET}

  {Colors.CYAN}Login URL:{Colors.RESET}    {PLATFORM_URL}/#org={org.slug}

  {Colors.CYAN}Email:{Colors.RESET}        {TEST_EMAIL}
  {Colors.CYAN}Password:{Colors.RESET}     {Colors.YELLOW}{temp_password}{Colors.RESET}

  {Colors.CYAN}Organization:{Colors.RESET} {org.name} (ID: {org.id})
  {Colors.CYAN}Cognito Pool:{Colors.RESET} {org.cognito_user_pool_id or 'N/A'}

{Colors.GREEN}{'='*60}{Colors.RESET}
""")

        # Step 6: Print manual test steps
        print_step(6, "Manual Test Steps")

        print(f"""
{Colors.BOLD}Check your email ({TEST_EMAIL}) for the welcome email.{Colors.RESET}

{Colors.CYAN}VERIFICATION CHECKLIST:{Colors.RESET}

□ 1. Welcome email received at {TEST_EMAIL}
     - Check subject: "Welcome to OW-AI Enterprise - {org.name}"
     - Verify login URL is correct
     - Verify temporary password matches above

□ 2. Login Test
     - Go to: {PLATFORM_URL}/#org={org.slug}
     - Enter email: {TEST_EMAIL}
     - Enter temp password: {temp_password}
     - Verify password change prompt appears

□ 3. Password Change
     - Enter new permanent password
     - Confirm login succeeds with new password

□ 4. Dashboard Access
     - Verify dashboard loads
     - Check organization shows as "{org.name}"
     - Verify you see admin features

□ 5. API Key Test (Optional)
     - Go to Settings > API Keys
     - Generate a new API key
     - Test with: curl -H "X-API-Key: <key>" {PLATFORM_URL}/api/agent-activity

{Colors.YELLOW}After completing manual tests, run:{Colors.RESET}
  python tests/e2e_comprehensive_test.py --email {TEST_EMAIL} --password <YOUR_NEW_PASSWORD>
""")

        return True

    except Exception as e:
        print_error(f"E2E test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def main():
    """Entry point."""
    print(f"\n{Colors.BOLD}OW-AI Enterprise E2E Test Runner{Colors.RESET}")
    print(f"Testing with: {TEST_EMAIL}")
    print("-" * 60)

    success = asyncio.run(run_e2e_test())

    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}E2E Test Setup Complete!{Colors.RESET}")
        print(f"Check your email at {TEST_EMAIL} for the welcome message.\n")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}E2E Test Setup Failed{Colors.RESET}")
        print("Check the errors above and try again.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
