"""
Phase 10C: Spend Control API Routes

Admin endpoints for managing spend limits and kill-switch.

Endpoints:
- GET /api/billing/spend-limits - Get org spend limit
- POST /api/billing/spend-limits - Set/update spend limit
- POST /api/billing/kill-switch/{org_id}/trigger - Trigger kill switch
- POST /api/billing/kill-switch/{org_id}/release - Release kill switch
- GET /api/billing/spend-limits/status - Get current status

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10C
Date: 2025-12-21
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from dependencies import get_current_user, get_organization_filter
from services.spend_control_service import (
    get_spend_control_service,
    SpendCheckResult,
    SpendLimitConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/billing",
    tags=["Billing - Spend Control"]
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SpendLimitRequest(BaseModel):
    """Request to set spend limit"""
    monthly_limit: float = Field(..., gt=0, description="Monthly limit in USD")
    warning_threshold_percent: float = Field(
        default=80.0,
        ge=0,
        le=100,
        description="Warning threshold percentage"
    )
    hard_limit_action: str = Field(
        default="block",
        description="Action at limit: block, notify, none"
    )


class SpendLimitResponse(BaseModel):
    """Spend limit configuration response"""
    organization_id: int
    monthly_limit: float
    warning_threshold_percent: float
    hard_limit_action: str
    current_spend: float
    utilization_percent: float
    status: str
    limit_enforced: bool
    kill_switch_triggered: bool

    class Config:
        from_attributes = True


class KillSwitchRequest(BaseModel):
    """Request to trigger/release kill switch"""
    reason: str = Field(..., min_length=10, description="Reason (min 10 chars)")


class SpendStatusResponse(BaseModel):
    """Current spend status"""
    allowed: bool
    blocked: bool
    current_spend: float
    monthly_limit: float
    utilization_percent: float
    status: str
    warning_triggered: bool
    kill_switch_active: bool
    message: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/spend-limits", response_model=SpendLimitResponse)
async def get_spend_limit(
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get spend limit configuration for current organization.

    Returns current spend limit settings and status.
    """
    service = get_spend_control_service()
    config = await service.get_spend_limit(db, org_id)

    if not config:
        # Return default response if no limit configured
        return SpendLimitResponse(
            organization_id=org_id,
            monthly_limit=0,
            warning_threshold_percent=80.0,
            hard_limit_action="none",
            current_spend=0,
            utilization_percent=0,
            status="no_limit",
            limit_enforced=False,
            kill_switch_triggered=False
        )

    utilization = (config.current_spend / config.monthly_limit * 100) if config.monthly_limit > 0 else 0

    return SpendLimitResponse(
        organization_id=org_id,
        monthly_limit=config.monthly_limit,
        warning_threshold_percent=config.warning_threshold_percent,
        hard_limit_action=config.hard_limit_action,
        current_spend=config.current_spend,
        utilization_percent=utilization,
        status="active" if not config.kill_switch_triggered else "killed",
        limit_enforced=config.limit_enforced,
        kill_switch_triggered=config.kill_switch_triggered
    )


@router.post("/spend-limits", response_model=SpendLimitResponse)
async def set_spend_limit(
    request: SpendLimitRequest,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set or update spend limit for current organization.

    Requires admin role.
    """
    # Check admin permission
    user_role = current_user.get("role", "")
    if user_role not in ["admin", "owner", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to manage spend limits"
        )

    service = get_spend_control_service()
    success = await service.set_spend_limit(
        db=db,
        organization_id=org_id,
        monthly_limit=request.monthly_limit,
        warning_threshold_percent=request.warning_threshold_percent,
        hard_limit_action=request.hard_limit_action,
        user_id=current_user.get("user_id")
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set spend limit"
        )

    # Return updated configuration
    config = await service.get_spend_limit(db, org_id)
    utilization = (config.current_spend / config.monthly_limit * 100) if config.monthly_limit > 0 else 0

    return SpendLimitResponse(
        organization_id=org_id,
        monthly_limit=config.monthly_limit,
        warning_threshold_percent=config.warning_threshold_percent,
        hard_limit_action=config.hard_limit_action,
        current_spend=config.current_spend,
        utilization_percent=utilization,
        status="active",
        limit_enforced=config.limit_enforced,
        kill_switch_triggered=config.kill_switch_triggered
    )


@router.get("/spend-limits/status", response_model=SpendStatusResponse)
async def get_spend_status(
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current spend status for organization.

    Fast endpoint using Redis cache.
    """
    service = get_spend_control_service()
    result = await service.check_spend_limit(org_id)

    return SpendStatusResponse(
        allowed=result.allowed,
        blocked=result.blocked,
        current_spend=result.current_spend,
        monthly_limit=result.monthly_limit,
        utilization_percent=result.utilization_percent,
        status=result.status,
        warning_triggered=result.warning_triggered,
        kill_switch_active=result.kill_switch_active,
        message=result.message
    )


@router.post("/kill-switch/{target_org_id}/trigger")
async def trigger_kill_switch(
    target_org_id: int,
    request: KillSwitchRequest,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger kill switch for an organization.

    Immediately blocks all API access.
    Requires admin role on target org or super_admin.
    """
    # Check permission
    user_role = current_user.get("role", "")
    if user_role == "super_admin":
        pass  # Super admin can trigger on any org
    elif user_role in ["admin", "owner"] and target_org_id == org_id:
        pass  # Admin can trigger on own org
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to trigger kill switch"
        )

    service = get_spend_control_service()
    success = await service.trigger_kill_switch(
        db=db,
        organization_id=target_org_id,
        reason=request.reason,
        user_id=current_user.get("user_id")
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger kill switch"
        )

    logger.warning(
        f"Kill switch triggered for org {target_org_id} by user {current_user.get('user_id')}: "
        f"{request.reason}"
    )

    return {
        "success": True,
        "message": f"Kill switch triggered for organization {target_org_id}",
        "organization_id": target_org_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "triggered_by": current_user.get("user_id")
    }


@router.post("/kill-switch/{target_org_id}/release")
async def release_kill_switch(
    target_org_id: int,
    request: KillSwitchRequest,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Release kill switch for an organization.

    Restores API access.
    Requires admin role on target org or super_admin.
    """
    # Check permission
    user_role = current_user.get("role", "")
    if user_role == "super_admin":
        pass
    elif user_role in ["admin", "owner"] and target_org_id == org_id:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to release kill switch"
        )

    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID required to release kill switch"
        )

    service = get_spend_control_service()
    success = await service.release_kill_switch(
        db=db,
        organization_id=target_org_id,
        reason=request.reason,
        user_id=user_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release kill switch"
        )

    logger.info(
        f"Kill switch released for org {target_org_id} by user {user_id}: "
        f"{request.reason}"
    )

    return {
        "success": True,
        "message": f"Kill switch released for organization {target_org_id}",
        "organization_id": target_org_id,
        "released_at": datetime.now(timezone.utc).isoformat(),
        "released_by": user_id
    }
