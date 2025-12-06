"""
Enterprise AWS Cognito Pool Configuration API

Provides endpoints for frontend dynamic pool detection.
Required for multi-tenant Cognito architecture.

Features:
- Get pool configuration by organization slug
- Get pool configuration by organization ID
- Get pool status and health
- CORS support for frontend authentication
- Enterprise security and audit logging

Engineer: OW-KAI Engineer
Date: 2025-11-20
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from database import get_db
from models import Organization
from services.cognito_pool_provisioner import get_provisioner

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter(
    prefix="/api/cognito",
    tags=["cognito", "authentication", "enterprise-security"]
)

logger = logging.getLogger("enterprise.cognito.api")


# ============================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================
# These endpoints are PUBLIC because they are needed
# BEFORE authentication to determine which pool to use

@router.get("/pool-config/by-slug/{organization_slug}")
async def get_pool_config_by_slug(
    organization_slug: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by organization slug

    PUBLIC ENDPOINT - Required for frontend dynamic pool detection

    Frontend Flow:
    1. User enters email on login page
    2. Frontend extracts organization slug from subdomain or path
    3. Frontend calls this endpoint to get pool configuration
    4. Frontend uses pool config to authenticate user

    Args:
        organization_slug: Organization slug (e.g., 'owai-internal')
        request: FastAPI request object (for logging)
        db: Database session

    Returns:
        {
            "user_pool_id": "us-east-2_xxxxx",
            "app_client_id": "xxxxx",
            "region": "us-east-2",
            "domain": "owkai-org-slug-auth",
            "organization_id": 1,
            "organization_name": "OW-AI Internal",
            "organization_slug": "owai-internal",
            "mfa_configuration": "OPTIONAL",
            "advanced_security": true
        }

    Raises:
        HTTPException 404: Organization not found
        HTTPException 400: Pool not provisioned or not active
    """

    try:
        # Audit log the request
        logger.info(f"🔐 AUDIT: Pool config request by slug", extra={
            'organization_slug': organization_slug,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        })

        # Find organization
        org = db.query(Organization).filter(
            Organization.slug == organization_slug
        ).first()

        if not org:
            logger.warning(f"⚠️  Organization not found: {organization_slug}")
            raise HTTPException(
                status_code=404,
                detail=f"Organization '{organization_slug}' not found"
            )

        # Check if pool is provisioned
        if not org.cognito_user_pool_id:
            logger.error(f"❌ Organization {organization_slug} has no Cognito pool")
            raise HTTPException(
                status_code=400,
                detail=f"Organization '{organization_slug}' has no Cognito pool configured. "
                       f"Please contact your administrator."
            )

        # Check pool status
        if org.cognito_pool_status != 'active':
            logger.error(f"❌ Organization {organization_slug} pool status: {org.cognito_pool_status}")
            raise HTTPException(
                status_code=400,
                detail=f"Organization '{organization_slug}' Cognito pool is not active. "
                       f"Status: {org.cognito_pool_status}. Please contact your administrator."
            )

        # Return pool configuration
        config = {
            "user_pool_id": org.cognito_user_pool_id,
            "app_client_id": org.cognito_app_client_id,
            "region": org.cognito_region or 'us-east-2',
            "domain": org.cognito_domain,
            "organization_id": org.id,
            "organization_name": org.name,
            "organization_slug": org.slug,
            "mfa_configuration": org.cognito_mfa_configuration or 'OPTIONAL',
            "advanced_security": org.cognito_advanced_security or False
        }

        logger.info(f"✅ Returned pool config for {organization_slug}")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config for {organization_slug}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving pool configuration: {str(e)}"
        )


@router.get("/pool-config/by-id/{organization_id}")
async def get_pool_config_by_id(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by organization ID

    PUBLIC ENDPOINT - Required for frontend dynamic pool detection

    Alternative to slug-based lookup when organization ID is known.

    Args:
        organization_id: Organization ID
        request: FastAPI request object (for logging)
        db: Database session

    Returns:
        Same as get_pool_config_by_slug

    Raises:
        HTTPException 404: Organization not found
        HTTPException 400: Pool not provisioned or not active
    """

    try:
        # Audit log the request
        logger.info(f"🔐 AUDIT: Pool config request by ID", extra={
            'organization_id': organization_id,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        })

        # Find organization
        org = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        if not org:
            logger.warning(f"⚠️  Organization not found: ID {organization_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Organization ID {organization_id} not found"
            )

        # Check if pool is provisioned
        if not org.cognito_user_pool_id:
            logger.error(f"❌ Organization ID {organization_id} has no Cognito pool")
            raise HTTPException(
                status_code=400,
                detail=f"Organization ID {organization_id} has no Cognito pool configured. "
                       f"Please contact your administrator."
            )

        # Check pool status
        if org.cognito_pool_status != 'active':
            logger.error(f"❌ Organization ID {organization_id} pool status: {org.cognito_pool_status}")
            raise HTTPException(
                status_code=400,
                detail=f"Organization ID {organization_id} Cognito pool is not active. "
                       f"Status: {org.cognito_pool_status}. Please contact your administrator."
            )

        # Return pool configuration
        config = {
            "user_pool_id": org.cognito_user_pool_id,
            "app_client_id": org.cognito_app_client_id,
            "region": org.cognito_region or 'us-east-2',
            "domain": org.cognito_domain,
            "organization_id": org.id,
            "organization_name": org.name,
            "organization_slug": org.slug,
            "mfa_configuration": org.cognito_mfa_configuration or 'OPTIONAL',
            "advanced_security": org.cognito_advanced_security or False
        }

        logger.info(f"✅ Returned pool config for organization ID {organization_id}")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config for organization ID {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving pool configuration: {str(e)}"
        )


@router.get("/pool-config/by-email/{email}")
async def get_pool_config_by_email(
    email: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by user email

    PUBLIC ENDPOINT - Required for frontend dynamic pool detection

    Determines organization from user's email domain or database lookup.

    Frontend Flow:
    1. User enters email on login page
    2. Frontend calls this endpoint with email
    3. Backend determines organization from email
    4. Backend returns pool configuration
    5. Frontend uses pool config to authenticate user

    Args:
        email: User email address
        request: FastAPI request object (for logging)
        db: Database session

    Returns:
        Same as get_pool_config_by_slug

    Raises:
        HTTPException 404: User/organization not found
        HTTPException 400: Pool not provisioned or not active
    """

    try:
        # Audit log the request (don't log full email for privacy)
        email_domain = email.split('@')[-1] if '@' in email else 'unknown'
        logger.info(f"🔐 AUDIT: Pool config request by email domain", extra={
            'email_domain': email_domain,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        })

        # Strategy 1: Look up user in database
        # This requires users table to have organization_id
        from models import User

        user = db.query(User).filter(
            User.email == email.lower().strip()
        ).first()

        if user and user.organization_id:
            org = db.query(Organization).filter(
                Organization.id == user.organization_id
            ).first()

            if org:
                logger.info(f"✅ Found organization from user email: {org.slug}")

                # Check if pool is provisioned
                if not org.cognito_user_pool_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Your organization has no Cognito pool configured. "
                               f"Please contact your administrator."
                    )

                # Check pool status
                if org.cognito_pool_status != 'active':
                    raise HTTPException(
                        status_code=400,
                        detail=f"Your organization's Cognito pool is not active. "
                               f"Please contact your administrator."
                    )

                # Return pool configuration
                config = {
                    "user_pool_id": org.cognito_user_pool_id,
                    "app_client_id": org.cognito_app_client_id,
                    "region": org.cognito_region or 'us-east-2',
                    "domain": org.cognito_domain,
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "organization_slug": org.slug,
                    "mfa_configuration": org.cognito_mfa_configuration or 'OPTIONAL',
                    "advanced_security": org.cognito_advanced_security or False
                }

                return config

        # Strategy 2: Check if email domain matches organization
        # This is a fallback for new users not yet in database
        email_domain = email.split('@')[-1].lower()

        # Check for common organization email patterns
        # Example: admin@owkai.com -> owai-internal
        # This mapping should be configured per deployment
        domain_to_slug_mapping = {
            'owkai.com': 'owai-internal',
            'owkai.app': 'owai-internal',
            # Add more mappings as needed
        }

        if email_domain in domain_to_slug_mapping:
            org_slug = domain_to_slug_mapping[email_domain]
            org = db.query(Organization).filter(
                Organization.slug == org_slug
            ).first()

            if org:
                logger.info(f"✅ Found organization from email domain mapping: {org.slug}")

                if not org.cognito_user_pool_id or org.cognito_pool_status != 'active':
                    raise HTTPException(
                        status_code=400,
                        detail="Your organization's authentication is not configured. "
                               "Please contact your administrator."
                    )

                config = {
                    "user_pool_id": org.cognito_user_pool_id,
                    "app_client_id": org.cognito_app_client_id,
                    "region": org.cognito_region or 'us-east-2',
                    "domain": org.cognito_domain,
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "organization_slug": org.slug,
                    "mfa_configuration": org.cognito_mfa_configuration or 'OPTIONAL',
                    "advanced_security": org.cognito_advanced_security or False
                }

                return config

        # Not found
        logger.warning(f"⚠️  Could not determine organization for email domain: {email_domain}")
        raise HTTPException(
            status_code=404,
            detail="Could not determine your organization from email address. "
                   "Please contact your administrator or use organization-specific login URL."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config by email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving pool configuration: {str(e)}"
        )


@router.get("/pool-config/by-email-domain/{email}")
async def get_pool_config_by_email_domain(
    email: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    SEC-101: Alias for by-email route to match frontend expectation.
    PUBLIC ENDPOINT - Required for frontend dynamic pool detection.
    """
    return await get_pool_config_by_email(email, request, db)


@router.get("/pool-status/{organization_slug}")
async def get_pool_status(
    organization_slug: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool status and health

    PUBLIC ENDPOINT - Used for health checks and monitoring

    Args:
        organization_slug: Organization slug
        request: FastAPI request object (for logging)
        db: Database session

    Returns:
        {
            "organization_slug": "owai-internal",
            "pool_status": "active",
            "pool_id": "us-east-2_xxxxx",
            "created_at": "2025-11-20T10:00:00",
            "mfa_enabled": true,
            "advanced_security_enabled": true
        }

    Raises:
        HTTPException 404: Organization not found
    """

    try:
        logger.info(f"🔐 AUDIT: Pool status request for {organization_slug}")

        # Find organization
        org = db.query(Organization).filter(
            Organization.slug == organization_slug
        ).first()

        if not org:
            raise HTTPException(
                status_code=404,
                detail=f"Organization '{organization_slug}' not found"
            )

        # Return status
        status = {
            "organization_slug": org.slug,
            "organization_id": org.id,
            "organization_name": org.name,
            "pool_status": org.cognito_pool_status or 'not_provisioned',
            "pool_id": org.cognito_user_pool_id,
            "app_client_id": org.cognito_app_client_id,
            "domain": org.cognito_domain,
            "region": org.cognito_region,
            "created_at": org.cognito_pool_created_at.isoformat() if org.cognito_pool_created_at else None,
            "mfa_configuration": org.cognito_mfa_configuration,
            "advanced_security_enabled": org.cognito_advanced_security or False
        }

        logger.info(f"✅ Returned pool status for {organization_slug}: {status['pool_status']}")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool status for {organization_slug}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error retrieving pool status: {str(e)}"
        )


@router.get("/organizations")
async def list_organizations_with_pools(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all organizations and their pool status

    PUBLIC ENDPOINT - Used for admin/monitoring dashboards

    Returns:
        {
            "total": 3,
            "with_pools": 2,
            "without_pools": 1,
            "organizations": [
                {
                    "id": 1,
                    "name": "OW-AI Internal",
                    "slug": "owai-internal",
                    "has_pool": true,
                    "pool_status": "active"
                },
                ...
            ]
        }
    """

    try:
        logger.info(f"🔐 AUDIT: Organization list request")

        # Get all organizations
        orgs = db.query(Organization).order_by(Organization.id).all()

        organizations = []
        with_pools = 0
        without_pools = 0

        for org in orgs:
            has_pool = bool(org.cognito_user_pool_id)

            if has_pool:
                with_pools += 1
            else:
                without_pools += 1

            organizations.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "has_pool": has_pool,
                "pool_status": org.cognito_pool_status if has_pool else None,
                "pool_id": org.cognito_user_pool_id if has_pool else None,
                "mfa_configuration": org.cognito_mfa_configuration if has_pool else None,
                "created_at": org.cognito_pool_created_at.isoformat() if org.cognito_pool_created_at else None
            })

        result = {
            "total": len(orgs),
            "with_pools": with_pools,
            "without_pools": without_pools,
            "organizations": organizations
        }

        logger.info(f"✅ Returned organization list: {len(orgs)} total")

        return result

    except Exception as e:
        logger.error(f"❌ Error listing organizations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error listing organizations: {str(e)}"
        )


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@router.get("/health")
async def cognito_health_check() -> Dict[str, str]:
    """
    Health check endpoint for Cognito pool API

    PUBLIC ENDPOINT

    Returns:
        {
            "status": "healthy",
            "service": "cognito-pool-api",
            "version": "1.0.0"
        }
    """

    return {
        "status": "healthy",
        "service": "cognito-pool-api",
        "version": "1.0.0"
    }


# ============================================
# EXPORT ROUTER
# ============================================

__all__ = ['router']
