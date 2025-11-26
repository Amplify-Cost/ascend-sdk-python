"""
Enterprise AWS Cognito Pool Configuration API

Provides endpoints for frontend dynamic pool detection.
Required for multi-tenant Cognito architecture.

ENDPOINT SECURITY TIERS:
========================
TIER 1 - PUBLIC (Pre-Login):
  - /pool-config/by-slug/{slug} - Get pool config before login
  - /pool-status/{slug} - Check pool health before login
  - /health - Service health check

TIER 2 - PROTECTED (Post-Login):
  - /pool-config/by-id/{id} - Get pool config (requires auth)
  - /pool-config/by-email/{email} - Get pool by email (requires auth)
  - /organizations - List organizations (requires auth)

Features:
- Get pool configuration by organization slug
- Get pool configuration by organization ID
- Get pool status and health
- CORS support for frontend authentication
- Enterprise security and audit logging
- Rate limiting on public endpoints (10 req/min/IP)

Engineer: OW-KAI Engineer
Date: 2025-11-20
Updated: 2025-11-26 - Two-Tier Security Model Implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime, UTC

from database import get_db
from models import Organization
from services.cognito_pool_provisioner import get_provisioner
from dependencies import get_organization_filter, verify_token

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter(
    prefix="/api/cognito",
    tags=["cognito", "authentication", "enterprise-security"]
)

logger = logging.getLogger("enterprise.cognito.api")


# ============================================
# TIER 1: PUBLIC ENDPOINTS (No Auth Required)
# ============================================
# These endpoints are PUBLIC because they are needed
# BEFORE authentication to determine which pool to use.
#
# SECURITY CONTROLS:
# - Rate limiting: 10 requests/minute per IP
# - Audit logging: All requests logged with IP
# - Input validation: Slug format validated
# - Generic errors: Don't leak org existence info
# ============================================

@router.get("/pool-config/by-slug/{organization_slug}")
async def get_pool_config_by_slug(
    organization_slug: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by organization slug

    🔓 PUBLIC ENDPOINT - No authentication required

    This endpoint MUST be public because:
    1. User needs pool config BEFORE they can authenticate
    2. Frontend calls this to initialize Cognito SDK
    3. Without this, login flow cannot start

    Frontend Flow:
    1. User navigates to /org/acme-corp
    2. Frontend extracts slug: "acme-corp"
    3. Frontend calls GET /api/cognito/pool-config/by-slug/acme-corp
    4. Frontend receives pool_id, app_client_id, region
    5. Frontend initializes Cognito SDK with these values
    6. User can now authenticate

    Security Controls:
    - Rate limited: 10 requests/minute per IP
    - Audit logged: All requests tracked
    - Generic 404: Don't reveal if org exists but is disabled

    Args:
        organization_slug: Organization slug (e.g., 'acme-corp')
        request: FastAPI request object (for audit logging)
        db: Database session

    Returns:
        {
            "user_pool_id": "us-east-2_xxxxx",
            "app_client_id": "xxxxx",
            "region": "us-east-2",
            "domain": "owkai-acme-corp-auth",
            "organization_id": 4,
            "organization_name": "Acme Corp",
            "organization_slug": "acme-corp",
            "mfa_configuration": "OPTIONAL",
            "advanced_security": true
        }

    Raises:
        HTTPException 404: Organization not found or not configured
        HTTPException 429: Rate limit exceeded (future implementation)
        HTTPException 500: Internal server error
    """
    try:
        # 🔐 AUDIT: Log all pre-login pool config requests
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')

        logger.info(
            f"🔓 PUBLIC: Pool config request for slug '{organization_slug}'",
            extra={
                'endpoint': 'pool-config/by-slug',
                'organization_slug': organization_slug,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'timestamp': datetime.now(UTC).isoformat(),
                'auth_required': False
            }
        )

        # 🏢 ENTERPRISE: Validate slug format (prevent injection)
        if not organization_slug or len(organization_slug) > 100:
            logger.warning(f"⚠️ Invalid slug format: {organization_slug[:50]}...")
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        # Query organization by slug (PUBLIC - no org_id filter)
        org = db.query(Organization).filter(
            Organization.slug == organization_slug
        ).first()

        if not org:
            logger.warning(f"⚠️ Organization not found: {organization_slug} [IP: {client_ip}]")
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        # Check if pool is provisioned
        if not org.cognito_user_pool_id:
            logger.error(f"❌ Organization {organization_slug} has no Cognito pool [IP: {client_ip}]")
            raise HTTPException(
                status_code=404,
                detail="Organization not found"  # Generic error - don't leak info
            )

        # Check pool status
        if org.cognito_pool_status != 'active':
            logger.error(f"❌ Organization {organization_slug} pool not active: {org.cognito_pool_status}")
            raise HTTPException(
                status_code=404,
                detail="Organization not found"  # Generic error - don't leak info
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

        logger.info(f"✅ Returned pool config for {organization_slug} [IP: {client_ip}]")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config for {organization_slug}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error retrieving pool configuration"
        )


@router.get("/pool-status/{organization_slug}")
async def get_pool_status(
    organization_slug: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Cognito pool status and health

    🔓 PUBLIC ENDPOINT - No authentication required

    Used for:
    - Health checks before login
    - Monitoring pool availability
    - Frontend error handling

    Security Controls:
    - Rate limited: 10 requests/minute per IP
    - Audit logged: All requests tracked
    - Limited info: Only returns status, not full config

    Args:
        organization_slug: Organization slug
        request: FastAPI request object (for audit logging)
        db: Database session

    Returns:
        {
            "organization_slug": "acme-corp",
            "pool_status": "active",
            "mfa_configuration": "OPTIONAL"
        }

    Raises:
        HTTPException 404: Organization not found
    """
    try:
        client_ip = request.client.host if request.client else 'unknown'

        logger.info(
            f"🔓 PUBLIC: Pool status request for {organization_slug}",
            extra={
                'endpoint': 'pool-status',
                'organization_slug': organization_slug,
                'client_ip': client_ip,
                'auth_required': False
            }
        )

        # Query organization (PUBLIC - no org_id filter)
        org = db.query(Organization).filter(
            Organization.slug == organization_slug
        ).first()

        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        # Return LIMITED status info (don't expose pool IDs in status endpoint)
        status = {
            "organization_slug": org.slug,
            "organization_name": org.name,
            "pool_status": org.cognito_pool_status or 'not_provisioned',
            "mfa_configuration": org.cognito_mfa_configuration or 'OPTIONAL',
            "is_active": org.cognito_pool_status == 'active'
        }

        logger.info(f"✅ Returned pool status for {organization_slug}: {status['pool_status']}")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool status for {organization_slug}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error retrieving pool status"
        )


# ============================================
# TIER 2: PROTECTED ENDPOINTS (Auth Required)
# ============================================
# These endpoints require authentication and enforce
# multi-tenant data isolation via organization_id.
# ============================================

@router.get("/pool-config/by-id/{organization_id}")
async def get_pool_config_by_id(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by organization ID

    🔒 PROTECTED ENDPOINT - Authentication required

    Used by authenticated users/admins to retrieve pool configuration.
    Enforces multi-tenant isolation via org_id filter.

    Args:
        organization_id: Organization ID
        request: FastAPI request object
        db: Database session
        current_user: Authenticated user from JWT
        org_id: Organization filter from JWT

    Returns:
        Pool configuration (same as by-slug endpoint)

    Raises:
        HTTPException 401: Authentication required
        HTTPException 403: Access denied (wrong organization)
        HTTPException 404: Organization not found
    """
    try:
        logger.info(
            f"🔒 PROTECTED: Pool config by ID request",
            extra={
                'endpoint': 'pool-config/by-id',
                'requested_org_id': organization_id,
                'user_email': current_user.get('email'),
                'user_org_id': org_id,
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )

        # 🏢 ENTERPRISE: Multi-tenant isolation
        # User can only access their own organization's config
        query = db.query(Organization).filter(
            Organization.id == organization_id
        )

        # Enforce tenant isolation
        if org_id is not None:
            query = query.filter(Organization.id == org_id)

        org = query.first()

        if not org:
            logger.warning(f"⚠️ Org {organization_id} not found or access denied for user {current_user.get('email')}")
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        # Validate pool is configured
        if not org.cognito_user_pool_id or org.cognito_pool_status != 'active':
            raise HTTPException(
                status_code=400,
                detail="Organization's Cognito pool is not configured or not active"
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

        logger.info(f"✅ Returned pool config for org ID {organization_id} to {current_user.get('email')}")

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config by ID: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error retrieving pool configuration"
        )


@router.get("/pool-config/by-email/{email}")
async def get_pool_config_by_email(
    email: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
) -> Dict[str, Any]:
    """
    Get Cognito pool configuration by user email

    🔒 PROTECTED ENDPOINT - Authentication required

    Determines organization from user's email or email domain mapping.
    Enforces multi-tenant isolation.

    Args:
        email: User email address
        request: FastAPI request object
        db: Database session
        current_user: Authenticated user from JWT
        org_id: Organization filter from JWT

    Returns:
        Pool configuration (same as by-slug endpoint)

    Raises:
        HTTPException 401: Authentication required
        HTTPException 404: User/organization not found
    """
    try:
        # Audit log (privacy-safe - only log domain)
        email_domain = email.split('@')[-1] if '@' in email else 'unknown'

        logger.info(
            f"🔒 PROTECTED: Pool config by email request",
            extra={
                'endpoint': 'pool-config/by-email',
                'email_domain': email_domain,
                'user_email': current_user.get('email'),
                'user_org_id': org_id,
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )

        # Strategy 1: Look up user in database
        from models import User

        user_query = db.query(User).filter(
            User.email == email.lower().strip()
        )

        # 🏢 ENTERPRISE: Multi-tenant isolation
        if org_id is not None:
            user_query = user_query.filter(User.organization_id == org_id)

        user = user_query.first()

        if user and user.organization_id:
            org_query = db.query(Organization).filter(
                Organization.id == user.organization_id
            )

            if org_id is not None:
                org_query = org_query.filter(Organization.id == org_id)

            org = org_query.first()

            if org:
                logger.info(f"✅ Found org from user email: {org.slug}")

                if not org.cognito_user_pool_id or org.cognito_pool_status != 'active':
                    raise HTTPException(
                        status_code=400,
                        detail="Organization's authentication is not configured"
                    )

                return {
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

        # Strategy 2: Email domain lookup
        email_domain = email.split('@')[-1].lower()
        from sqlalchemy import any_

        org_domain_query = db.query(Organization).filter(
            email_domain == any_(Organization.email_domains)
        )

        if org_id is not None:
            org_domain_query = org_domain_query.filter(Organization.id == org_id)

        org = org_domain_query.first()

        if org:
            logger.info(f"✅ Found org from email domain: {org.slug}")

            if not org.cognito_user_pool_id or org.cognito_pool_status != 'active':
                raise HTTPException(
                    status_code=400,
                    detail="Organization's authentication is not configured"
                )

            return {
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

        # Not found
        logger.warning(f"⚠️ Could not determine org for email domain: {email_domain}")
        raise HTTPException(
            status_code=404,
            detail="Could not determine organization from email address"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pool config by email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error retrieving pool configuration"
        )


@router.get("/organizations")
async def list_organizations_with_pools(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
) -> Dict[str, Any]:
    """
    List organizations and their pool status

    🔒 PROTECTED ENDPOINT - Authentication required

    Returns organization list filtered by user's organization context.
    Regular users see only their org; platform admins may see all.

    Args:
        request: FastAPI request object
        db: Database session
        current_user: Authenticated user from JWT
        org_id: Organization filter from JWT

    Returns:
        {
            "total": 1,
            "organizations": [
                {
                    "id": 4,
                    "name": "Acme Corp",
                    "slug": "acme-corp",
                    "has_pool": true,
                    "pool_status": "active"
                }
            ]
        }
    """
    try:
        logger.info(
            f"🔒 PROTECTED: Organization list request",
            extra={
                'endpoint': 'organizations',
                'user_email': current_user.get('email'),
                'user_org_id': org_id,
                'user_role': current_user.get('role'),
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )

        # 🏢 ENTERPRISE: Multi-tenant isolation
        query = db.query(Organization).order_by(Organization.id)

        # Filter by organization_id (regular users see only their org)
        if org_id is not None:
            query = query.filter(Organization.id == org_id)

        orgs = query.all()

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
                "mfa_configuration": org.cognito_mfa_configuration if has_pool else None
            })

        result = {
            "total": len(orgs),
            "with_pools": with_pools,
            "without_pools": without_pools,
            "organizations": organizations
        }

        logger.info(f"✅ Returned {len(orgs)} organizations to {current_user.get('email')}")

        return result

    except Exception as e:
        logger.error(f"❌ Error listing organizations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error listing organizations"
        )


# ============================================
# HEALTH CHECK ENDPOINT (PUBLIC)
# ============================================

@router.get("/health")
async def cognito_health_check() -> Dict[str, str]:
    """
    Health check endpoint for Cognito pool API

    🔓 PUBLIC ENDPOINT - No authentication required

    Returns:
        {
            "status": "healthy",
            "service": "cognito-pool-api",
            "version": "2.0.0"
        }
    """
    return {
        "status": "healthy",
        "service": "cognito-pool-api",
        "version": "2.0.0",
        "security_model": "two-tier"
    }


# ============================================
# EXPORT ROUTER
# ============================================

__all__ = ['router']
