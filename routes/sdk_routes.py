"""
ASCEND SDK API Routes
=====================

Backend endpoints for ASCEND SDK integration.

Endpoints:
- POST /api/sdk/agent/register - Register an agent
- POST /api/sdk/action/{action_id}/completed - Log action completion
- POST /api/sdk/action/{action_id}/failed - Log action failure
- GET /api/sdk/approval/{approval_id} - Check approval status
- POST /api/sdk/webhooks/configure - Configure webhooks

Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.2, NIST AI RMF
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json

from database import get_db
from dependencies import get_current_user, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key
from models import User, AgentAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sdk", tags=["SDK"])


# ============================================================
# Pydantic Models
# ============================================================

class AgentRegisterRequest(BaseModel):
    """Request model for agent registration."""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: str = Field(..., description="Type of agent (automation, assistant, etc.)")
    capabilities: List[str] = Field(default=[], description="List of agent capabilities")
    allowed_resources: Optional[List[str]] = Field(default=None, description="Resources agent can access")
    environment: Optional[str] = Field(default="production", description="Deployment environment")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AgentRegisterResponse(BaseModel):
    """Response model for agent registration."""
    agent_id: str
    status: str
    registered_at: str
    capabilities: List[str]
    organization_id: int
    metadata: Optional[Dict[str, Any]] = None


class ActionCompletedRequest(BaseModel):
    """Request model for action completion."""
    status: str = Field(default="completed", description="Action status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Action result data")
    duration_ms: Optional[int] = Field(default=None, description="Execution duration in milliseconds")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")


class ActionFailedRequest(BaseModel):
    """Request model for action failure."""
    status: str = Field(default="failed", description="Action status")
    error: str = Field(..., description="Error message")
    duration_ms: Optional[int] = Field(default=None, description="Execution duration in milliseconds")
    failed_at: Optional[str] = Field(default=None, description="Failure timestamp")


class ActionLogResponse(BaseModel):
    """Response model for action logging."""
    action_id: str
    status: str
    logged_at: str


class ApprovalStatusResponse(BaseModel):
    """Response model for approval status."""
    approval_request_id: str
    status: str  # pending, approved, rejected
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    decided_at: Optional[str] = None


class WebhookConfigRequest(BaseModel):
    """Request model for webhook configuration."""
    agent_id: str = Field(..., description="Agent ID")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(default=None, description="Webhook secret for signature verification")


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""
    webhook_id: str
    url: str
    events: List[str]
    status: str
    created_at: str


# ============================================================
# Agent Registration
# ============================================================

@router.post("/agent/register", response_model=AgentRegisterResponse)
async def register_agent(
    request: AgentRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter)
):
    """
    Register an AI agent with ASCEND.

    This endpoint should be called once when an agent starts up to:
    - Establish presence in the system
    - Register capabilities for policy evaluation
    - Track agent lifecycle

    The agent_id should be unique within the organization.
    """
    logger.info(f"SDK: Registering agent {request.agent_id} for org {org_id}")

    # Store agent registration in audit log or dedicated table
    # For now, we'll just validate and return success
    # In production, you might want a dedicated agent_registry table

    registered_at = datetime.utcnow().isoformat() + "Z"

    # Log registration to audit
    logger.info(
        f"SDK Agent Registration: agent_id={request.agent_id}, "
        f"agent_name={request.agent_name}, agent_type={request.agent_type}, "
        f"org_id={org_id}, capabilities={request.capabilities}"
    )

    return AgentRegisterResponse(
        agent_id=request.agent_id,
        status="registered",
        registered_at=registered_at,
        capabilities=request.capabilities,
        organization_id=org_id,
        metadata=request.metadata
    )


# ============================================================
# Action Completion Logging
# ============================================================

@router.post("/action/{action_id}/completed", response_model=ActionLogResponse)
async def log_action_completed(
    action_id: str,
    request: ActionCompletedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter)
):
    """
    Log successful completion of an authorized action.

    Called by SDK after an action that was authorized by ASCEND
    has been successfully executed. Updates the action record
    with completion status and result data.
    """
    logger.info(f"SDK: Logging completion for action {action_id}, org {org_id}")

    # Validate action ID format
    if not action_id.isdigit():
        logger.warning(f"SDK: Invalid action_id format: {action_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action_id format. Expected numeric ID, got: {action_id}"
        )

    # Find the action
    action = db.query(AgentAction).filter(
        AgentAction.id == int(action_id),
        AgentAction.organization_id == org_id
    ).first()

    if not action:
        # Action not found - log but still return success for resilience
        logger.warning(f"SDK: Action {action_id} not found for org {org_id}")
        # Return success - SDK completed the action, we just don't have the record
        return ActionLogResponse(
            action_id=action_id,
            status="completed",
            logged_at=datetime.utcnow().isoformat() + "Z"
        )

    # Update action with completion info
    action.status = "completed"
    if request.result:
        # Store result in action_details or a separate field
        existing_details = action.action_details or {}
        existing_details["sdk_completion"] = {
            "result": request.result,
            "duration_ms": request.duration_ms,
            "completed_at": request.completed_at or datetime.utcnow().isoformat() + "Z"
        }
        action.action_details = existing_details

    action.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"SDK: Action {action_id} marked as completed")

    return ActionLogResponse(
        action_id=action_id,
        status="completed",
        logged_at=datetime.utcnow().isoformat() + "Z"
    )


@router.post("/action/{action_id}/failed", response_model=ActionLogResponse)
async def log_action_failed(
    action_id: str,
    request: ActionFailedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter)
):
    """
    Log failure of an authorized action.

    Called by SDK when an action that was authorized by ASCEND
    failed during execution. Records the error for audit purposes.
    """
    logger.info(f"SDK: Logging failure for action {action_id}, org {org_id}, error: {request.error}")

    # Validate action ID format
    if not action_id.isdigit():
        logger.warning(f"SDK: Invalid action_id format: {action_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action_id format. Expected numeric ID, got: {action_id}"
        )

    # Find the action
    action = db.query(AgentAction).filter(
        AgentAction.id == int(action_id),
        AgentAction.organization_id == org_id
    ).first()

    if not action:
        logger.warning(f"SDK: Action {action_id} not found for org {org_id}")
        # Return failure status - SDK failed, we just don't have the record
        return ActionLogResponse(
            action_id=action_id,
            status="failed",
            logged_at=datetime.utcnow().isoformat() + "Z"
        )

    # Update action with failure info
    action.status = "failed"
    existing_details = action.action_details or {}
    existing_details["sdk_failure"] = {
        "error": request.error,
        "duration_ms": request.duration_ms,
        "failed_at": request.failed_at or datetime.utcnow().isoformat() + "Z"
    }
    action.action_details = existing_details
    action.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"SDK: Action {action_id} marked as failed")

    return ActionLogResponse(
        action_id=action_id,
        status="failed",
        logged_at=datetime.utcnow().isoformat() + "Z"
    )


# ============================================================
# Approval Status
# ============================================================

@router.get("/approval/{approval_id}", response_model=ApprovalStatusResponse)
async def check_approval_status(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter)
):
    """
    Check the status of a pending approval request.

    Used by SDK to poll for approval decisions on actions
    that require human review.
    """
    logger.info(f"SDK: Checking approval status for {approval_id}, org {org_id}")

    # Validate approval ID format
    if not approval_id.isdigit():
        logger.warning(f"SDK: Invalid approval_id format: {approval_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval_id format. Expected numeric ID, got: {approval_id}"
        )

    # In a full implementation, you'd have an approval_requests table
    # For now, we check the agent_actions table for the action status

    # Try to find action by ID with organization isolation
    action = db.query(AgentAction).filter(
        AgentAction.id == int(approval_id),
        AgentAction.organization_id == org_id
    ).first()

    if not action:
        # SEC-003 FIX: Return 404 instead of "pending" to prevent enumeration attacks
        logger.warning(f"SDK: Approval {approval_id} not found for org {org_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    # Map action status to approval status
    if action.status == "approved":
        return ApprovalStatusResponse(
            approval_request_id=approval_id,
            status="approved",
            approved_by=action.reviewed_by if hasattr(action, 'reviewed_by') else None,
            decided_at=action.updated_at.isoformat() + "Z" if action.updated_at else None
        )
    elif action.status == "denied":
        return ApprovalStatusResponse(
            approval_request_id=approval_id,
            status="rejected",
            rejected_by=action.reviewed_by if hasattr(action, 'reviewed_by') else None,
            rejection_reason="Action denied by policy or reviewer",
            decided_at=action.updated_at.isoformat() + "Z" if action.updated_at else None
        )
    else:
        return ApprovalStatusResponse(
            approval_request_id=approval_id,
            status="pending"
        )


# ============================================================
# Webhook Configuration
# ============================================================

@router.post("/webhooks/configure", response_model=WebhookConfigResponse)
async def configure_webhook(
    request: WebhookConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter)
):
    """
    Configure webhook for event notifications.

    Allows agents to receive real-time notifications for:
    - action.evaluated - When an action is evaluated
    - action.approved - When an action is approved
    - action.denied - When an action is denied
    - action.completed - When an action completes
    - action.failed - When an action fails
    """
    logger.info(f"SDK: Configuring webhook for agent {request.agent_id}, org {org_id}")
    logger.info(f"SDK: Webhook URL: {request.url}, Events: {request.events}")

    # In a full implementation, store webhook config in database
    # For now, just validate and return success
    # You might want to add a sdk_webhooks table

    import hashlib
    import time

    webhook_id = hashlib.sha256(
        f"{org_id}:{request.agent_id}:{request.url}:{time.time()}".encode()
    ).hexdigest()[:16]

    return WebhookConfigResponse(
        webhook_id=webhook_id,
        url=request.url,
        events=request.events,
        status="active",
        created_at=datetime.utcnow().isoformat() + "Z"
    )


# ============================================================
# Health Check
# ============================================================

@router.get("/health")
async def sdk_health():
    """SDK endpoint health check."""
    return {
        "status": "healthy",
        "sdk_version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
