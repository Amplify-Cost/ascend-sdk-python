#!/usr/bin/env python3
"""
OW-AI Enterprise Quick Customer Onboarding Script
==================================================

This script automates the complete onboarding flow for a new enterprise customer:
1. Creates organization
2. Provisions Cognito user pool
3. Creates org admin user
4. Generates API key for SDK integration
5. Sends welcome email with credentials

Usage:
    python quick_onboard_customer.py \
        --name "Acme Financial Corp" \
        --slug "acme-financial" \
        --email-domain "acme-financial.com" \
        --admin-email "admin@acme-financial.com" \
        --admin-name "John Smith" \
        --mfa-required

Environment Variables:
    OWKAI_ADMIN_EMAIL: Platform admin email
    OWKAI_ADMIN_PASSWORD: Platform admin password
    OWKAI_API_URL: API endpoint (default: https://pilot.owkai.app)

Security: SOC 2, PCI-DSS, HIPAA Compliant
Author: OW-AI Enterprise
Date: 2025-11-30
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any


class CustomerOnboarder:
    """Handles complete customer onboarding workflow"""

    def __init__(self, api_url: str, admin_email: str, admin_password: str):
        self.api_url = api_url
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.session = requests.Session()
        self.auth_cookies = None

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{level}] {timestamp} - {message}")

    def login_as_admin(self) -> bool:
        """Authenticate as platform admin"""
        self.log("Authenticating as platform admin...")

        try:
            response = self.session.post(
                f"{self.api_url}/api/auth/login",
                json={
                    "email": self.admin_email,
                    "password": self.admin_password
                }
            )

            if response.status_code == 200:
                self.log("Platform admin authenticated successfully")
                return True
            else:
                self.log(f"Authentication failed: {response.text}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Authentication error: {e}", "ERROR")
            return False

    def create_organization(
        self,
        name: str,
        slug: str,
        email_domains: list,
        plan: str = "enterprise",
        settings: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create new organization"""
        self.log(f"Creating organization: {name} ({slug})")

        default_settings = {
            "mfa_required": False,
            "session_timeout_minutes": 30,
            "max_users": 100
        }

        if settings:
            default_settings.update(settings)

        try:
            response = self.session.post(
                f"{self.api_url}/api/platform-admin/organizations",
                json={
                    "name": name,
                    "slug": slug,
                    "email_domains": email_domains,
                    "plan": plan,
                    "settings": default_settings
                }
            )

            if response.status_code in [200, 201]:
                org = response.json()
                self.log(f"Organization created with ID: {org.get('id')}")
                return org
            else:
                self.log(f"Failed to create organization: {response.text}", "ERROR")
                return None

        except Exception as e:
            self.log(f"Error creating organization: {e}", "ERROR")
            return None

    def provision_cognito(
        self,
        organization_id: int,
        mfa_configuration: str = "OPTIONAL"
    ) -> Optional[Dict]:
        """Provision Cognito user pool for organization"""
        self.log(f"Provisioning Cognito pool for org {organization_id}...")

        try:
            response = self.session.post(
                f"{self.api_url}/api/cognito-pools/provision",
                json={
                    "organization_id": organization_id,
                    "mfa_configuration": mfa_configuration,
                    "password_policy": {
                        "minimum_length": 12,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_numbers": True,
                        "require_symbols": True
                    }
                }
            )

            if response.status_code in [200, 201]:
                result = response.json()
                self.log(f"Cognito pool provisioned: {result.get('cognito_user_pool_id')}")
                return result
            else:
                self.log(f"Failed to provision Cognito: {response.text}", "ERROR")
                return None

        except Exception as e:
            self.log(f"Error provisioning Cognito: {e}", "ERROR")
            return None

    def create_org_admin(
        self,
        organization_id: int,
        email: str,
        name: str
    ) -> Optional[Dict]:
        """Create organization admin user"""
        self.log(f"Creating org admin: {email}")

        try:
            response = self.session.post(
                f"{self.api_url}/api/platform-admin/organizations/{organization_id}/users",
                json={
                    "email": email,
                    "name": name,
                    "role": "org_admin",
                    "send_invite": True
                }
            )

            if response.status_code in [200, 201]:
                user = response.json()
                self.log(f"Org admin created with ID: {user.get('user_id')}")
                return user
            else:
                self.log(f"Failed to create org admin: {response.text}", "ERROR")
                return None

        except Exception as e:
            self.log(f"Error creating org admin: {e}", "ERROR")
            return None

    def generate_api_key(
        self,
        organization_id: int,
        name: str = "Production AI Agent"
    ) -> Optional[Dict]:
        """Generate API key for SDK integration"""
        self.log(f"Generating API key for org {organization_id}...")

        try:
            # First, we need to switch context to the org admin
            # For simplicity, using platform admin endpoint
            response = self.session.post(
                f"{self.api_url}/api/platform-admin/organizations/{organization_id}/api-keys",
                json={
                    "name": name,
                    "description": "API key for AI agent SDK integration",
                    "permissions": ["agent_actions", "read_policies", "read_alerts"]
                }
            )

            if response.status_code in [200, 201]:
                key = response.json()
                self.log(f"API key generated: {key.get('key_id')}")
                return key
            else:
                self.log(f"Failed to generate API key: {response.text}", "WARN")
                return None

        except Exception as e:
            self.log(f"Error generating API key: {e}", "WARN")
            return None

    def onboard_customer(
        self,
        org_name: str,
        org_slug: str,
        email_domains: list,
        admin_email: str,
        admin_name: str,
        mfa_required: bool = False,
        plan: str = "enterprise"
    ) -> Dict[str, Any]:
        """Complete customer onboarding workflow"""

        result = {
            "success": False,
            "organization": None,
            "cognito": None,
            "admin_user": None,
            "api_key": None,
            "login_url": None,
            "errors": []
        }

        self.log("="*60)
        self.log("Starting Customer Onboarding")
        self.log("="*60)

        # Step 1: Authenticate
        if not self.login_as_admin():
            result["errors"].append("Failed to authenticate as platform admin")
            return result

        # Step 2: Create Organization
        org = self.create_organization(
            name=org_name,
            slug=org_slug,
            email_domains=email_domains,
            plan=plan,
            settings={"mfa_required": mfa_required}
        )

        if not org:
            result["errors"].append("Failed to create organization")
            return result

        result["organization"] = org
        org_id = org.get("id")

        # Step 3: Provision Cognito
        mfa_config = "ON" if mfa_required else "OPTIONAL"
        cognito = self.provision_cognito(org_id, mfa_config)

        if cognito:
            result["cognito"] = cognito
        else:
            result["errors"].append("Failed to provision Cognito (non-critical)")

        # Step 4: Create Org Admin
        admin = self.create_org_admin(org_id, admin_email, admin_name)

        if admin:
            result["admin_user"] = admin
        else:
            result["errors"].append("Failed to create org admin")
            return result

        # Step 5: Generate API Key
        api_key = self.generate_api_key(org_id)

        if api_key:
            result["api_key"] = api_key
        else:
            result["errors"].append("Failed to generate API key (can be done later)")

        # Set login URL
        result["login_url"] = f"{self.api_url}/#org={org_slug}"
        result["success"] = True

        self.log("="*60)
        self.log("Customer Onboarding Complete!")
        self.log("="*60)

        return result


def print_onboarding_summary(result: Dict):
    """Print formatted onboarding summary"""

    print("\n" + "="*70)
    print("                    CUSTOMER ONBOARDING SUMMARY")
    print("="*70)

    if not result["success"]:
        print("\n[FAILED] Onboarding did not complete successfully")
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")
        return

    print("\n[SUCCESS] Customer onboarded successfully!\n")

    # Organization Details
    org = result.get("organization", {})
    print("ORGANIZATION")
    print("-" * 40)
    print(f"  Name:     {org.get('name', 'N/A')}")
    print(f"  Slug:     {org.get('slug', 'N/A')}")
    print(f"  ID:       {org.get('id', 'N/A')}")

    # Cognito Details
    cognito = result.get("cognito", {})
    if cognito:
        print("\nCOGNITO USER POOL")
        print("-" * 40)
        print(f"  Pool ID:  {cognito.get('cognito_user_pool_id', 'N/A')}")
        print(f"  Client:   {cognito.get('cognito_app_client_id', 'N/A')}")

    # Admin User
    admin = result.get("admin_user", {})
    print("\nORGANIZATION ADMIN")
    print("-" * 40)
    print(f"  Email:    {admin.get('email', 'N/A')}")
    print(f"  Temp Pass: {admin.get('temporary_password', 'N/A')}")
    print(f"  Status:   {admin.get('status', 'N/A')}")

    # API Key
    api_key = result.get("api_key", {})
    if api_key:
        print("\nAPI KEY (SDK Integration)")
        print("-" * 40)
        print(f"  Key ID:   {api_key.get('key_id', 'N/A')}")
        print(f"  API Key:  {api_key.get('api_key', 'N/A')}")
        print("\n  [!] SAVE THIS API KEY - It will not be shown again!")

    # Login URL
    print("\nLOGIN URL")
    print("-" * 40)
    print(f"  {result.get('login_url', 'N/A')}")

    # Next Steps
    print("\n" + "="*70)
    print("                         NEXT STEPS")
    print("="*70)
    print("""
    1. Share the temporary password with the org admin securely

    2. Org admin should login at the URL above and:
       - Set new password (12+ chars, uppercase, lowercase, number, symbol)
       - Set up MFA if required

    3. For SDK integration, customer should:
       - Set environment variables:
         export OWKAI_API_URL=https://pilot.owkai.app
         export OWKAI_API_KEY=<api-key-above>

       - Install SDK:
         pip install owkai-sdk   # Python
         npm install @owkai/sdk  # Node.js

       - See integration examples in /integration-examples/

    4. Documentation:
       - E2E Testing Guide: /E2E_ENTERPRISE_INTEGRATION_TESTING_GUIDE.md
       - SDK Examples: /integration-examples/
    """)
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="OW-AI Enterprise Quick Customer Onboarding"
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Organization name (e.g., 'Acme Financial Corp')"
    )

    parser.add_argument(
        "--slug",
        required=True,
        help="Organization slug (e.g., 'acme-financial')"
    )

    parser.add_argument(
        "--email-domain",
        required=True,
        action="append",
        dest="email_domains",
        help="Email domain(s) for the organization (can specify multiple)"
    )

    parser.add_argument(
        "--admin-email",
        required=True,
        help="Org admin email address"
    )

    parser.add_argument(
        "--admin-name",
        required=True,
        help="Org admin full name"
    )

    parser.add_argument(
        "--mfa-required",
        action="store_true",
        help="Require MFA for all users"
    )

    parser.add_argument(
        "--plan",
        default="enterprise",
        choices=["starter", "professional", "enterprise"],
        help="Subscription plan (default: enterprise)"
    )

    parser.add_argument(
        "--api-url",
        default=os.getenv("OWKAI_API_URL", "https://pilot.owkai.app"),
        help="API endpoint URL"
    )

    args = parser.parse_args()

    # Get admin credentials
    admin_email = os.getenv("OWKAI_ADMIN_EMAIL")
    admin_password = os.getenv("OWKAI_ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        print("\n[ERROR] Platform admin credentials required.")
        print("Set environment variables:")
        print("  export OWKAI_ADMIN_EMAIL=admin@owkai.app")
        print("  export OWKAI_ADMIN_PASSWORD=<password>")
        sys.exit(1)

    # Initialize onboarder
    onboarder = CustomerOnboarder(
        api_url=args.api_url,
        admin_email=admin_email,
        admin_password=admin_password
    )

    # Run onboarding
    result = onboarder.onboard_customer(
        org_name=args.name,
        org_slug=args.slug,
        email_domains=args.email_domains,
        admin_email=args.admin_email,
        admin_name=args.admin_name,
        mfa_required=args.mfa_required,
        plan=args.plan
    )

    # Print summary
    print_onboarding_summary(result)

    # Exit code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
