"""
SEC-065: Enterprise Executive Brief API Routes

Enterprise-grade REST API for executive briefing system with:
- Cached brief retrieval (<100ms)
- On-demand regeneration with rate limiting
- Historical brief access for audit
- Multi-tenant isolation (banking-level security)

Compliance:
- SOC 2 AU-6: Audit record review
- SOC 2 AU-7: Audit reduction and report generation
- NIST 800-53 AU-6: Audit Review, Analysis, Reporting
- PCI-DSS 10.6: Review logs daily

Document ID: SEC-065
Publisher: Ascend (OW-kai Corporation)
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, get_organization_filter
from services.executive_brief_service import (
    ExecutiveBriefService,
    get_executive_brief_service
)

logger = logging.getLogger(__name__)

# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(
    prefix="/api/executive-briefs",
    tags=["Executive Briefs"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RegenerateBriefRequest(BaseModel):
    """Request model for brief regeneration"""
    time_period: str = Field(
        default="24h",
        description="Analysis period: 24h, 7d, 30d, 90d"
    )
    force: bool = Field(
        default=False,
        description="Force regeneration (admin only, bypasses cooldown)"
    )


class BriefMetrics(BaseModel):
    """Key metrics in executive brief"""
    threats_detected: int
    threats_prevented: int
    cost_savings: str
    system_accuracy: str


class BriefRecommendation(BaseModel):
    """Recommendation item"""
    priority: str
    action: str
    timeframe: str
    owner: str


class BriefMeta(BaseModel):
    """Brief metadata"""
    organization_id: int
    has_activity: bool
    llm_model: Optional[str] = None
    generation_time_ms: Optional[int] = None


class ExecutiveBriefResponse(BaseModel):
    """Full executive brief response"""
    brief_id: str
    generated_at: str
    generated_by: str
    expires_at: str
    time_period: str
    alert_count: int
    high_priority_count: int
    critical_count: int
    summary: str
    key_metrics: dict
    recommendations: list
    risk_assessment: str
    distribution_list: list
    generation_method: str
    is_expired: bool
    is_current: bool
    version: int
    meta: dict


class CooldownResponse(BaseModel):
    """Cooldown status response"""
    can_regenerate: bool
    seconds_remaining: int
    message: str


class BriefHistoryResponse(BaseModel):
    """Brief history list response"""
    briefs: list
    total: int
    limit: int
    offset: int


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get(
    "/latest",
    response_model=ExecutiveBriefResponse,
    summary="Get Latest Executive Brief",
    description="""
    Retrieve the current cached executive brief for the organization.

    Performance: <100ms (indexed query)

    Returns cached brief if valid, or triggers generation if none exists.

    Compliance: SOC 2 AU-7, NIST AU-6
    """
)
async def get_latest_brief(
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get the latest valid executive brief"""
    logger.info(f"SEC-065: GET /latest called by user={current_user.get('email')} org={org_id}")

    try:
        service = get_executive_brief_service(db, org_id)

        # Try to get cached brief
        brief = service.get_cached_brief()

        if brief:
            # Record view for audit
            service.record_view(brief.brief_id, current_user.get('email', 'unknown'))
            return brief.to_api_response()

        # No cached brief - generate one
        logger.info(f"SEC-065: No cached brief found for org={org_id}, generating...")
        brief = service.generate_brief(
            time_period="24h",
            user_email=current_user.get('email', 'system')
        )

        return brief.to_api_response()

    except Exception as e:
        logger.error(f"SEC-065: Failed to get latest brief: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve executive brief: {str(e)}"
        )


@router.post(
    "/regenerate",
    response_model=ExecutiveBriefResponse,
    summary="Regenerate Executive Brief",
    description="""
    Force regeneration of the executive brief.

    Rate Limited: 5-minute cooldown between regenerations.

    This endpoint:
    1. Checks cooldown period
    2. Fetches latest alerts from database
    3. Generates new AI summary
    4. Stores brief with audit trail
    5. Marks previous brief as superseded

    Performance: 2-5 seconds (includes LLM call)

    Compliance: SOC 2 AU-6, PCI-DSS 10.6
    """
)
async def regenerate_brief(
    request: RegenerateBriefRequest,
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Regenerate executive brief with rate limiting"""
    user_email = current_user.get('email', 'unknown')
    user_role = current_user.get('role', 'user')

    logger.info(
        f"SEC-065: POST /regenerate called by user={user_email} "
        f"org={org_id} period={request.time_period}"
    )

    try:
        service = get_executive_brief_service(db, org_id)

        # Check if force is allowed (admin only)
        force = request.force and user_role in ('admin', 'platform_admin', 'org_admin')

        if request.force and not force:
            logger.warning(
                f"SEC-065: Non-admin user {user_email} attempted force regeneration"
            )

        # Attempt generation
        brief = service.generate_brief(
            time_period=request.time_period,
            user_email=user_email,
            force=force
        )

        return brief.to_api_response()

    except ValueError as e:
        # Rate limit error
        logger.warning(f"SEC-065: Rate limit hit for org={org_id}: {e}")
        raise HTTPException(status_code=429, detail=str(e))

    except Exception as e:
        logger.error(f"SEC-065: Failed to regenerate brief: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate executive brief: {str(e)}"
        )


@router.get(
    "/cooldown",
    response_model=CooldownResponse,
    summary="Check Regeneration Cooldown",
    description="""
    Check if brief regeneration is currently allowed.

    Returns cooldown status and remaining seconds if rate limited.
    """
)
async def check_cooldown(
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Check regeneration cooldown status"""
    try:
        service = get_executive_brief_service(db, org_id)
        can_regen, remaining = service.can_regenerate()

        if can_regen:
            message = "Regeneration available"
        else:
            message = f"Please wait {remaining} seconds before regenerating"

        return CooldownResponse(
            can_regenerate=can_regen,
            seconds_remaining=remaining,
            message=message
        )

    except Exception as e:
        logger.error(f"SEC-065: Cooldown check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    response_model=BriefHistoryResponse,
    summary="Get Brief History",
    description="""
    Retrieve historical executive briefs for audit purposes.

    Compliance: SOC 2 AU-6 - Audit record review

    Supports pagination via limit/offset parameters.
    """
)
async def get_brief_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get historical executive briefs"""
    logger.info(
        f"SEC-065: GET /history called by user={current_user.get('email')} "
        f"org={org_id} limit={limit} offset={offset}"
    )

    try:
        service = get_executive_brief_service(db, org_id)
        briefs = service.get_brief_history(limit=limit, offset=offset)

        return BriefHistoryResponse(
            briefs=[b.to_api_response() for b in briefs],
            total=len(briefs),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"SEC-065: Failed to get brief history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{brief_id}",
    response_model=ExecutiveBriefResponse,
    summary="Get Specific Brief",
    description="""
    Retrieve a specific executive brief by ID.

    Used for viewing historical briefs or sharing specific briefings.

    Compliance: SOC 2 AU-6 - Individual record access
    """
)
async def get_brief_by_id(
    brief_id: str,
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get a specific executive brief by ID"""
    logger.info(
        f"SEC-065: GET /{brief_id} called by user={current_user.get('email')} org={org_id}"
    )

    try:
        service = get_executive_brief_service(db, org_id)
        brief = service.get_brief_by_id(brief_id)

        if not brief:
            raise HTTPException(
                status_code=404,
                detail=f"Brief not found: {brief_id}"
            )

        # Record view for audit
        service.record_view(brief_id, current_user.get('email', 'unknown'))

        return brief.to_api_response()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-065: Failed to get brief {brief_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEGACY ENDPOINT COMPATIBILITY
# Maintains backward compatibility with existing frontend
# =============================================================================

@router.post(
    "/generate",
    response_model=ExecutiveBriefResponse,
    summary="Generate Brief (Legacy)",
    description="""
    Legacy endpoint for backward compatibility.

    Redirects to /regenerate with proper rate limiting.

    DEPRECATED: Use /regenerate instead.
    """
)
async def generate_brief_legacy(
    request: RegenerateBriefRequest,
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Legacy endpoint - redirects to regenerate"""
    logger.info(
        f"SEC-065: Legacy /generate called, redirecting to /regenerate "
        f"user={current_user.get('email')} org={org_id}"
    )

    return await regenerate_brief(request, current_user, org_id, db)
