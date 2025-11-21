#!/usr/bin/env python3
"""
Enterprise Cognito Pool Provisioning CLI Script

Provisions dedicated AWS Cognito user pools for organizations.
Required for HIPAA, PCI-DSS, SOC 2, GDPR compliance.

Usage:
    python scripts/provision_cognito_pool.py --org-id 1 --admin-email admin@owkai.com
    python scripts/provision_cognito_pool.py --org-slug owai-internal --admin-email admin@owkai.com
    python scripts/provision_cognito_pool.py --provision-all

Features:
- Provision single organization by ID or slug
- Provision all organizations missing pools
- Idempotent (safe to re-run)
- Complete audit trail
- Progress reporting
- Error recovery

Engineer: OW-KAI Engineer
Date: 2025-11-20
"""

import sys
import os
import argparse
import asyncio
import logging
from typing import Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db
from models import Organization
from services.cognito_pool_provisioner import get_provisioner

# ============================================
# LOGGING CONFIGURATION
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cognito_pool_provisioning.log')
    ]
)

logger = logging.getLogger('enterprise.cognito.provisioning.cli')


# ============================================
# CLI FUNCTIONS
# ============================================

async def provision_single_organization(
    org_id: Optional[int] = None,
    org_slug: Optional[str] = None,
    admin_email: Optional[str] = None,
    password_policy: Optional[dict] = None,
    mfa_config: str = 'OPTIONAL'
) -> bool:
    """
    Provision Cognito pool for a single organization

    Args:
        org_id: Organization ID (optional if org_slug provided)
        org_slug: Organization slug (optional if org_id provided)
        admin_email: Initial admin user email (required)
        password_policy: Custom password policy (optional)
        mfa_config: MFA configuration (OFF, OPTIONAL, REQUIRED)

    Returns:
        True if successful, False otherwise
    """

    if not org_id and not org_slug:
        logger.error("❌ Either org_id or org_slug must be provided")
        return False

    if not admin_email:
        logger.error("❌ Admin email is required")
        return False

    db = next(get_db())
    provisioner = get_provisioner()

    try:
        # ============================================
        # STEP 1: Find Organization
        # ============================================

        logger.info("🔍 Finding organization...")

        if org_id:
            org = db.query(Organization).filter(
                Organization.id == org_id
            ).first()
        else:
            org = db.query(Organization).filter(
                Organization.slug == org_slug
            ).first()

        if not org:
            identifier = f"ID {org_id}" if org_id else f"slug '{org_slug}'"
            logger.error(f"❌ Organization not found: {identifier}")
            return False

        logger.info(f"✅ Found organization: {org.name} (ID: {org.id}, Slug: {org.slug})")

        # ============================================
        # STEP 2: Check Current Pool Status
        # ============================================

        if org.cognito_user_pool_id and org.cognito_pool_status == 'active':
            logger.info(f"ℹ️  Pool already exists: {org.cognito_user_pool_id}")
            logger.info(f"   Status: {org.cognito_pool_status}")
            logger.info(f"   Domain: {org.cognito_domain}")
            logger.info(f"   Region: {org.cognito_region}")
            logger.info("✅ Nothing to do - pool already active")
            return True

        # ============================================
        # STEP 3: Provision Pool
        # ============================================

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"🚀 Starting Cognito Pool Provisioning")
        logger.info("=" * 60)
        logger.info(f"   Organization: {org.name}")
        logger.info(f"   Organization ID: {org.id}")
        logger.info(f"   Organization Slug: {org.slug}")
        logger.info(f"   Admin Email: {admin_email}")
        logger.info(f"   MFA Configuration: {mfa_config}")
        logger.info("=" * 60)
        logger.info("")

        start_time = datetime.now()

        result = await provisioner.create_organization_pool(
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            admin_email=admin_email,
            db=db,
            password_policy=password_policy,
            mfa_config=mfa_config
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # ============================================
        # STEP 4: Report Success
        # ============================================

        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 POOL PROVISIONING SUCCESSFUL")
        logger.info("=" * 60)
        logger.info(f"   User Pool ID: {result['user_pool_id']}")
        logger.info(f"   App Client ID: {result['app_client_id']}")
        logger.info(f"   Domain: {result['domain']}")
        logger.info(f"   Region: {result['region']}")
        logger.info(f"   Pool ARN: {result.get('pool_arn', 'N/A')}")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info("=" * 60)
        logger.info("")

        logger.info("📋 Next Steps:")
        logger.info("   1. Test login with admin credentials")
        logger.info("   2. Configure frontend for this organization")
        logger.info("   3. Migrate existing users (if any)")
        logger.info("")

        return True

    except Exception as e:
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ POOL PROVISIONING FAILED")
        logger.error("=" * 60)
        logger.error(f"   Error: {str(e)}")
        logger.error("=" * 60)
        logger.error("")
        return False

    finally:
        db.close()


async def provision_all_organizations(
    default_admin_email: str,
    password_policy: Optional[dict] = None,
    mfa_config: str = 'OPTIONAL',
    skip_existing: bool = True
) -> dict:
    """
    Provision Cognito pools for all organizations

    Args:
        default_admin_email: Default admin email (can be overridden per org)
        password_policy: Default password policy for all orgs
        mfa_config: Default MFA configuration
        skip_existing: Skip organizations with existing pools

    Returns:
        {
            'total': 10,
            'provisioned': 8,
            'skipped': 2,
            'failed': 0,
            'results': [...]
        }
    """

    db = next(get_db())
    provisioner = get_provisioner()

    try:
        # ============================================
        # STEP 1: Find All Organizations
        # ============================================

        logger.info("🔍 Finding all organizations...")

        orgs = db.query(Organization).order_by(Organization.id).all()

        if not orgs:
            logger.warning("⚠️  No organizations found in database")
            return {
                'total': 0,
                'provisioned': 0,
                'skipped': 0,
                'failed': 0,
                'results': []
            }

        logger.info(f"✅ Found {len(orgs)} organizations")
        logger.info("")

        # ============================================
        # STEP 2: Filter Organizations
        # ============================================

        orgs_to_provision = []

        for org in orgs:
            if skip_existing and org.cognito_user_pool_id and org.cognito_pool_status == 'active':
                logger.info(f"⏭️  Skipping {org.name} (pool already exists)")
                continue

            orgs_to_provision.append(org)

        if not orgs_to_provision:
            logger.info("✅ All organizations already have active pools")
            return {
                'total': len(orgs),
                'provisioned': 0,
                'skipped': len(orgs),
                'failed': 0,
                'results': []
            }

        logger.info(f"📊 Organizations to provision: {len(orgs_to_provision)}")
        logger.info("")

        # ============================================
        # STEP 3: Provision Each Organization
        # ============================================

        results = []
        provisioned_count = 0
        failed_count = 0

        for i, org in enumerate(orgs_to_provision, 1):
            logger.info(f"{'=' * 60}")
            logger.info(f"Processing {i}/{len(orgs_to_provision)}: {org.name}")
            logger.info(f"{'=' * 60}")

            try:
                # Use organization-specific admin email if available
                admin_email = getattr(org, 'admin_email', None) or default_admin_email

                result = await provisioner.create_organization_pool(
                    organization_id=org.id,
                    organization_name=org.name,
                    organization_slug=org.slug,
                    admin_email=admin_email,
                    db=db,
                    password_policy=password_policy,
                    mfa_config=mfa_config
                )

                results.append({
                    'organization_id': org.id,
                    'organization_name': org.name,
                    'organization_slug': org.slug,
                    'status': 'success',
                    'user_pool_id': result['user_pool_id'],
                    'app_client_id': result['app_client_id'],
                    'domain': result['domain'],
                    'duration_ms': result.get('duration_ms')
                })

                provisioned_count += 1
                logger.info(f"✅ Success: {org.name}")

            except Exception as e:
                results.append({
                    'organization_id': org.id,
                    'organization_name': org.name,
                    'organization_slug': org.slug,
                    'status': 'failed',
                    'error': str(e)
                })

                failed_count += 1
                logger.error(f"❌ Failed: {org.name} - {str(e)}")

            logger.info("")

        # ============================================
        # STEP 4: Report Summary
        # ============================================

        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 BATCH PROVISIONING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"   Total Organizations: {len(orgs)}")
        logger.info(f"   Provisioned: {provisioned_count}")
        logger.info(f"   Skipped: {len(orgs) - len(orgs_to_provision)}")
        logger.info(f"   Failed: {failed_count}")
        logger.info("=" * 60)
        logger.info("")

        return {
            'total': len(orgs),
            'provisioned': provisioned_count,
            'skipped': len(orgs) - len(orgs_to_provision),
            'failed': failed_count,
            'results': results
        }

    finally:
        db.close()


async def get_pool_status(org_id: Optional[int] = None, org_slug: Optional[str] = None):
    """
    Get current pool status for an organization

    Args:
        org_id: Organization ID (optional if org_slug provided)
        org_slug: Organization slug (optional if org_id provided)
    """

    if not org_id and not org_slug:
        logger.error("❌ Either org_id or org_slug must be provided")
        return

    db = next(get_db())

    try:
        # Find organization
        if org_id:
            org = db.query(Organization).filter(Organization.id == org_id).first()
        else:
            org = db.query(Organization).filter(Organization.slug == org_slug).first()

        if not org:
            identifier = f"ID {org_id}" if org_id else f"slug '{org_slug}'"
            logger.error(f"❌ Organization not found: {identifier}")
            return

        # Display status
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 COGNITO POOL STATUS")
        logger.info("=" * 60)
        logger.info(f"   Organization: {org.name}")
        logger.info(f"   Organization ID: {org.id}")
        logger.info(f"   Organization Slug: {org.slug}")
        logger.info("")
        logger.info(f"   Pool Status: {org.cognito_pool_status or 'NOT PROVISIONED'}")
        logger.info(f"   User Pool ID: {org.cognito_user_pool_id or 'N/A'}")
        logger.info(f"   App Client ID: {org.cognito_app_client_id or 'N/A'}")
        logger.info(f"   Domain: {org.cognito_domain or 'N/A'}")
        logger.info(f"   Region: {org.cognito_region or 'N/A'}")
        logger.info(f"   Pool ARN: {org.cognito_pool_arn or 'N/A'}")
        logger.info(f"   MFA Config: {org.cognito_mfa_configuration or 'N/A'}")
        logger.info(f"   Advanced Security: {org.cognito_advanced_security or False}")
        logger.info(f"   Created At: {org.cognito_pool_created_at or 'N/A'}")
        logger.info("=" * 60)
        logger.info("")

    finally:
        db.close()


# ============================================
# MAIN CLI ENTRY POINT
# ============================================

def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description='Enterprise Cognito Pool Provisioning CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Provision pool for organization ID 1
  python scripts/provision_cognito_pool.py --org-id 1 --admin-email admin@owkai.com

  # Provision pool for organization by slug
  python scripts/provision_cognito_pool.py --org-slug owai-internal --admin-email admin@owkai.com

  # Provision pools for all organizations
  python scripts/provision_cognito_pool.py --provision-all --admin-email admin@owkai.com

  # Check pool status
  python scripts/provision_cognito_pool.py --status --org-id 1

  # Provision with MFA required
  python scripts/provision_cognito_pool.py --org-id 2 --admin-email admin@org2.com --mfa REQUIRED
        """
    )

    # Mutually exclusive actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--provision-all', action='store_true',
                              help='Provision pools for all organizations')
    action_group.add_argument('--status', action='store_true',
                              help='Check pool status for an organization')

    # Organization identifiers (for single org operations)
    org_group = parser.add_mutually_exclusive_group()
    org_group.add_argument('--org-id', type=int,
                           help='Organization ID')
    org_group.add_argument('--org-slug', type=str,
                           help='Organization slug')

    # Configuration options
    parser.add_argument('--admin-email', type=str,
                        help='Admin user email address')
    parser.add_argument('--mfa', type=str, choices=['OFF', 'OPTIONAL', 'REQUIRED'],
                        default='OPTIONAL',
                        help='MFA configuration (default: OPTIONAL)')
    parser.add_argument('--min-password-length', type=int, default=12,
                        help='Minimum password length (default: 12)')
    parser.add_argument('--include-existing', action='store_true',
                        help='Include organizations with existing pools (re-provision)')

    args = parser.parse_args()

    # ============================================
    # VALIDATE ARGUMENTS
    # ============================================

    if args.status:
        # Status check
        if not args.org_id and not args.org_slug:
            parser.error("--status requires either --org-id or --org-slug")

        asyncio.run(get_pool_status(
            org_id=args.org_id,
            org_slug=args.org_slug
        ))

    elif args.provision_all:
        # Batch provisioning
        if not args.admin_email:
            parser.error("--provision-all requires --admin-email")

        password_policy = {
            'MinimumLength': args.min_password_length,
            'RequireUppercase': True,
            'RequireLowercase': True,
            'RequireNumbers': True,
            'RequireSymbols': True,
            'TemporaryPasswordValidityDays': 7
        }

        result = asyncio.run(provision_all_organizations(
            default_admin_email=args.admin_email,
            password_policy=password_policy,
            mfa_config=args.mfa,
            skip_existing=not args.include_existing
        ))

        # Exit with error code if any failed
        sys.exit(0 if result['failed'] == 0 else 1)

    else:
        # Single organization provisioning
        if not args.org_id and not args.org_slug:
            parser.error("Either --org-id or --org-slug is required")

        if not args.admin_email:
            parser.error("--admin-email is required")

        password_policy = {
            'MinimumLength': args.min_password_length,
            'RequireUppercase': True,
            'RequireLowercase': True,
            'RequireNumbers': True,
            'RequireSymbols': True,
            'TemporaryPasswordValidityDays': 7
        }

        success = asyncio.run(provision_single_organization(
            org_id=args.org_id,
            org_slug=args.org_slug,
            admin_email=args.admin_email,
            password_policy=password_policy,
            mfa_config=args.mfa
        ))

        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
