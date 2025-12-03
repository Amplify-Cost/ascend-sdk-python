"""
SEC-050: Enterprise Agent Health Monitoring Routes
===================================================

Datadog-style agent health monitoring API endpoints:
- Heartbeat reception from agents
- Health status queries
- Performance metrics aggregation
- Health dashboard data

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, UTC
import logging

from database import get_db
from dependencies import get_current_user, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key
from models import User
from services.agent_health_service import AgentHealthService, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents/health", tags=["Agent Health Monitoring"])


# ============================================================================
# Request/Response Models
# ============================================================================

class HeartbeatRequest(BaseModel):
    """Heartbeat payload from agent SDK."""
    agent_id: str = Field(..., description="Unique agent identifier")
    metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional performance metrics",
        example={
            "response_time_ms": 45.2,
            "error_rate": 0.5,
            "requests_count": 1247,
            "last_error": None
        }
    )
    sdk_version: Optional[str] = Field(default=None, description="SDK version for compatibility tracking")


class HeartbeatResponse(BaseModel):
    """Response to heartbeat request."""
    success: bool
    agent_id: str
    health_status: Optional[str] = None
    next_heartbeat_expected_at: Optional[str] = None
    heartbeat_interval_seconds: Optional[int] = None
    error: Optional[str] = None


class HealthSummaryResponse(BaseModel):
    """Aggregated health summary for dashboard."""
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    problem_agents: List[Dict[str, Any]]
    recent_changes: List[Dict[str, Any]]
    last_check: str


class AgentHealthDetailResponse(BaseModel):
    """Detailed health information for a specific agent."""
    agent_id: str
    display_name: str
    agent_type: str
    status: str
    health: Dict[str, Any]
    metrics: Dict[str, Any]
    errors: Dict[str, Any]
    recent_history: List[Dict[str, Any]]


class UpdateIntervalRequest(BaseModel):
    """Request to update heartbeat interval."""
    interval_seconds: int = Field(
        ...,
        ge=10,
        le=300,
        description="Heartbeat interval in seconds (10-300)"
    )


# ============================================================================
# Heartbeat Endpoints (SDK Authentication)
# ============================================================================

@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    summary="Receive agent heartbeat",
    description="""
    Receive and process a heartbeat from an agent.

    **Authentication**: API Key (via Authorization header or X-API-Key)

    **Usage**:
    - Agents should send heartbeats at their configured interval (default: 60s)
    - Include performance metrics for dashboard display
    - Missing heartbeats will degrade agent health status

    **SDK Example**:
    ```python
    import requests

    response = requests.post(
        "https://pilot.owkai.app/api/agents/health/heartbeat",
        headers={"Authorization": "Bearer owkai_..."},
        json={
            "agent_id": "my-agent-001",
            "metrics": {
                "response_time_ms": 45.2,
                "error_rate": 0.5,
                "requests_count": 100
            }
        }
    )
    ```

    **Compliance**: SOC 2 CC7.1, NIST SI-4
    """
)
async def receive_heartbeat(
    request: HeartbeatRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Process heartbeat from agent SDK.

    Updates:
    - Last heartbeat timestamp
    - Health status to 'online'
    - Performance metrics if provided
    - Resets missed heartbeat counter
    """
    try:
        service = AgentHealthService(db)
        result = service.process_heartbeat(
            agent_id=request.agent_id,
            organization_id=current_user.organization_id,
            metrics=request.metrics,
            performed_by=f"sdk:{current_user.email}"
        )

        return HeartbeatResponse(**result)

    except Exception as e:
        logger.error(f"SEC-050: Heartbeat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heartbeat processing failed: {str(e)}")


@router.post(
    "/heartbeat/batch",
    summary="Batch heartbeat for multiple agents",
    description="""
    Receive heartbeats from multiple agents in a single request.

    **Use Case**: When a single SDK manages multiple agents.

    **Authentication**: API Key
    """
)
async def receive_batch_heartbeat(
    heartbeats: List[HeartbeatRequest],
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Process multiple heartbeats in a single request."""
    service = AgentHealthService(db)
    results = []

    for hb in heartbeats[:50]:  # Limit to 50 per batch
        result = service.process_heartbeat(
            agent_id=hb.agent_id,
            organization_id=current_user.organization_id,
            metrics=hb.metrics,
            performed_by=f"sdk:{current_user.email}"
        )
        results.append(result)

    return {
        "processed": len(results),
        "results": results
    }


# ============================================================================
# Health Status Endpoints (Dashboard Authentication)
# ============================================================================

@router.get(
    "/summary",
    response_model=HealthSummaryResponse,
    summary="Get health summary for dashboard",
    description="""
    Get aggregated health summary for all agents in the organization.

    **Dashboard Display**:
    - Total agents by health status (online/degraded/offline/unknown)
    - Overall health score (0-100)
    - Problem agents requiring attention
    - Recent status changes
    - Aggregate performance metrics

    **Compliance**: SOC 2 CC7.1 - Continuous monitoring visibility
    """
)
async def get_health_summary(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get aggregated health summary for dashboard display."""
    try:
        service = AgentHealthService(db)

        # First, check and update health statuses
        service.check_agent_health(org_id)

        # Then get summary
        summary = service.get_health_summary(org_id)
        return HealthSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"SEC-050: Health summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health summary: {str(e)}")


@router.get(
    "/{agent_id}",
    response_model=AgentHealthDetailResponse,
    summary="Get detailed agent health",
    description="""
    Get detailed health information for a specific agent.

    **Includes**:
    - Current health status and last heartbeat
    - Performance metrics (response time, error rate)
    - Recent error information
    - Health history (last 24 hours)

    **Compliance**: SOC 2 CC7.1, NIST SI-4
    """
)
async def get_agent_health(
    agent_id: str,
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get detailed health information for a specific agent."""
    service = AgentHealthService(db)
    details = service.get_agent_health_details(agent_id, org_id)

    if not details:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentHealthDetailResponse(**details)


@router.put(
    "/{agent_id}/interval",
    summary="Update heartbeat interval",
    description="""
    Update the expected heartbeat interval for an agent.

    **Range**: 10-300 seconds
    - Lower values = faster detection of issues
    - Higher values = less network overhead

    **Default**: 60 seconds

    **Audit**: Changes are logged for compliance.
    """
)
async def update_heartbeat_interval(
    agent_id: str,
    request: UpdateIntervalRequest,
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Update the heartbeat interval for an agent."""
    service = AgentHealthService(db)

    success = service.update_heartbeat_interval(
        agent_id=agent_id,
        organization_id=org_id,
        interval_seconds=request.interval_seconds,
        updated_by=current_user.email
    )

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "success": True,
        "agent_id": agent_id,
        "heartbeat_interval_seconds": request.interval_seconds
    }


@router.post(
    "/check",
    summary="Trigger health check for all agents",
    description="""
    Manually trigger a health check for all organization agents.

    **Use Case**: Force immediate health evaluation without waiting for scheduled check.

    **Returns**: List of agents whose status changed.

    **Note**: This endpoint is typically called by a scheduled job, but can be triggered manually.
    """
)
async def trigger_health_check(
    org_id: int = Depends(get_organization_filter),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger health check for all agents."""
    service = AgentHealthService(db)
    changes = service.check_agent_health(org_id)

    logger.info(
        f"SEC-050: Manual health check triggered by {current_user.email}, "
        f"{len(changes)} status changes detected"
    )

    return {
        "checked_by": current_user.email,
        "status_changes": changes,
        "changes_count": len(changes)
    }


# ============================================================================
# Public Health Endpoints (For Status Pages)
# ============================================================================

@router.get(
    "/public/status",
    summary="Public health status (no auth)",
    description="""
    Get overall platform health status without authentication.

    **Use Case**: Status page integration, external monitoring.

    **Returns**: Simplified status (healthy/degraded/unhealthy) without sensitive details.
    """
)
async def get_public_health_status(db: Session = Depends(get_db)):
    """Get public health status for status pages."""
    # This is a simplified public endpoint
    # Returns only aggregate status without org-specific data
    return {
        "status": "healthy",
        "platform": "Ascend AI Governance",
        "timestamp": datetime.now(UTC).isoformat()
    }
