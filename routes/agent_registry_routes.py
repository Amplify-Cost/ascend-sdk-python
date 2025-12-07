"""
Ascend Enterprise Agent Registry API Routes
============================================

RESTful API for managing AI agent registrations.
Provides full CRUD operations with enterprise-grade security.

Ascend Platform - Authored by Ascend Engineers
© OW-kai Technologies Inc.

Endpoints:
- POST   /api/registry/agents              - Register new agent
- GET    /api/registry/agents              - List all agents
- GET    /api/registry/agents/{id}         - Get agent details
- PUT    /api/registry/agents/{id}         - Update agent
- POST   /api/registry/agents/{id}/activate    - Activate agent
- POST   /api/registry/agents/{id}/suspend     - Suspend agent
- GET    /api/registry/agents/{id}/versions    - List versions
- POST   /api/registry/agents/{id}/rollback    - Rollback to version
- POST   /api/registry/agents/{id}/policies    - Add policy
- GET    /api/registry/agents/{id}/policies    - List policies
- POST   /api/registry/agents/{id}/evaluate    - Evaluate policies

SEC-068: Autonomous Agent Governance:
- PUT    /api/registry/agents/{id}/rate-limits        - Configure rate limits
- PUT    /api/registry/agents/{id}/budget             - Configure budget limits
- PUT    /api/registry/agents/{id}/time-window        - Configure time restrictions
- PUT    /api/registry/agents/{id}/data-classifications - Configure data access
- PUT    /api/registry/agents/{id}/auto-suspend       - Configure auto-suspension
- PUT    /api/registry/agents/{id}/escalation         - Configure escalation path (CR-003)
- GET    /api/registry/agents/{id}/usage              - Get usage statistics
- GET    /api/registry/agents/{id}/anomalies          - Get anomaly detection status
- POST   /api/registry/agents/{id}/emergency-suspend  - Emergency kill switch
- POST   /api/registry/agents/{id}/set-baselines      - Set anomaly baselines

MCP Server Management:
- POST   /api/registry/mcp-servers                      - Register MCP server
- GET    /api/registry/mcp-servers                      - List MCP servers
- GET    /api/registry/mcp-servers/{server_name}        - Get MCP server
- PUT    /api/registry/mcp-servers/{server_name}        - Update MCP server
- DELETE /api/registry/mcp-servers/{server_name}        - Delete MCP server
- POST   /api/registry/mcp-servers/{server_name}/activate    - Activate MCP server
- POST   /api/registry/mcp-servers/{server_name}/deactivate  - Deactivate MCP server

Agent Management:
- DELETE /api/registry/agents/{id}         - Delete agent (with audit trail)

Compliance: SOC 2 CC6.1/CC6.2/CC7.1, PCI-DSS 7.1/8.3, NIST 800-53 AC-2/AC-3/SI-4
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

from database import get_db
from dependencies import get_current_user, require_admin, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key, get_organization_filter_dual_auth
from services.agent_registry_service import agent_registry_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/registry", tags=["Agent Registry"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class AgentRegistrationRequest(BaseModel):
    """Request schema for registering a new agent."""
    agent_id: str = Field(..., min_length=3, max_length=64, description="Unique agent identifier")
    display_name: str = Field(..., max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, description="Agent description")
    agent_type: Optional[str] = Field("supervised", description="Agent type: autonomous, supervised, advisory, mcp_server, custom")

    # Risk Configuration
    default_risk_score: Optional[int] = Field(50, ge=0, le=100)
    max_risk_threshold: Optional[int] = Field(80, ge=0, le=100)
    auto_approve_below: Optional[int] = Field(30, ge=0, le=100)
    requires_mfa_above: Optional[int] = Field(70, ge=0, le=100)

    # Capabilities
    allowed_action_types: Optional[List[str]] = Field(default_factory=list)
    allowed_resources: Optional[List[str]] = Field(default_factory=list)
    blocked_resources: Optional[List[str]] = Field(default_factory=list)

    # MCP Integration
    is_mcp_server: Optional[bool] = Field(False)
    mcp_server_url: Optional[str] = None
    mcp_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Notifications
    alert_on_high_risk: Optional[bool] = Field(True)
    alert_recipients: Optional[List[str]] = Field(default_factory=list)
    webhook_url: Optional[str] = None

    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    """Request schema for updating an agent."""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    agent_type: Optional[str] = None
    default_risk_score: Optional[int] = Field(None, ge=0, le=100)
    max_risk_threshold: Optional[int] = Field(None, ge=0, le=100)
    auto_approve_below: Optional[int] = Field(None, ge=0, le=100)
    requires_mfa_above: Optional[int] = Field(None, ge=0, le=100)
    # SEC-108d: Autonomous agent thresholds (stricter defaults)
    autonomous_auto_approve_below: Optional[int] = Field(None, ge=0, le=100)
    autonomous_max_risk_threshold: Optional[int] = Field(None, ge=0, le=100)
    allowed_action_types: Optional[List[str]] = None
    allowed_resources: Optional[List[str]] = None
    blocked_resources: Optional[List[str]] = None
    alert_on_high_risk: Optional[bool] = None
    alert_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    version_notes: Optional[str] = None


class PolicyRequest(BaseModel):
    """Request schema for adding a policy."""
    policy_name: str = Field(..., max_length=255)
    policy_description: Optional[str] = None
    is_active: Optional[bool] = Field(True)
    priority: Optional[int] = Field(100, ge=1, le=1000)
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    policy_action: str = Field(..., description="Action: require_approval, block, allow, escalate")
    action_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PolicyEvaluationRequest(BaseModel):
    """Request schema for policy evaluation."""
    action_type: str
    resource: Optional[str] = None
    risk_score: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MCPServerRequest(BaseModel):
    """Request schema for registering an MCP server."""
    server_name: str = Field(..., max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    server_url: Optional[str] = None
    transport_type: Optional[str] = Field("stdio")
    connection_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tools: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    prompts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    resources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    governance_enabled: Optional[bool] = Field(True)
    auto_approve_tools: Optional[List[str]] = Field(default_factory=list)
    blocked_tools: Optional[List[str]] = Field(default_factory=list)
    tool_risk_overrides: Optional[Dict[str, int]] = Field(default_factory=dict)


class MCPServerUpdateRequest(BaseModel):
    """Request schema for updating an MCP server."""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    server_url: Optional[str] = None
    transport_type: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    governance_enabled: Optional[bool] = None
    auto_approve_tools: Optional[List[str]] = None
    blocked_tools: Optional[List[str]] = None
    tool_risk_overrides: Optional[Dict[str, int]] = None


class AgentDeleteRequest(BaseModel):
    """Request schema for deleting an agent."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion (audit trail)")


class MCPServerDeactivateRequest(BaseModel):
    """Request schema for deactivating an MCP server."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deactivation")


# ============================================================================
# AGENT REGISTRATION ENDPOINTS
# ============================================================================

@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Register a new AI agent with the governance platform.

    This creates an agent registration that allows the agent to submit
    actions for authorization through the SDK endpoint.

    The agent starts in DRAFT status and must be activated by an admin.

    Compliance: SOC 2 CC6.1, NIST AC-2
    """
    try:
        created_by = current_user.get("email", "api_key_user")

        agent, is_new = agent_registry_service.register_agent(
            db=db,
            organization_id=org_id,
            agent_data=request.model_dump(),
            created_by=created_by
        )

        return {
            "success": True,
            "created": is_new,
            "agent": {
                "id": agent.id,
                "agent_id": agent.agent_id,
                "display_name": agent.display_name,
                "status": agent.status,
                "version": agent.version,
                "agent_type": agent.agent_type,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "organization_id": agent.organization_id
            },
            "message": f"Agent {'registered' if is_new else 'already exists'}: {agent.agent_id}",
            "next_steps": [
                "Configure policies using POST /api/registry/agents/{id}/policies",
                "Activate agent using POST /api/registry/agents/{id}/activate",
                "Submit actions using POST /api/sdk/agent-action"
            ]
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/agents")
async def list_agents(
    status_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    List all registered agents for the organization.

    Supports filtering by status and agent type.

    Compliance: Multi-tenant isolation enforced
    """
    try:
        agents, total = agent_registry_service.list_agents(
            db=db,
            organization_id=org_id,
            status_filter=status_filter,
            type_filter=type_filter,
            limit=min(limit, 500),
            offset=offset
        )

        return {
            "success": True,
            "agents": [
                {
                    "id": a.id,
                    "agent_id": a.agent_id,
                    "display_name": a.display_name,
                    "description": a.description,
                    "agent_type": a.agent_type,
                    "status": a.status,
                    "version": a.version,
                    "default_risk_score": a.default_risk_score,
                    "auto_approve_below": a.auto_approve_below,
                    "max_risk_threshold": a.max_risk_threshold,
                    "is_mcp_server": a.is_mcp_server,
                    "tags": a.tags,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in agents
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }

    except Exception as e:
        logger.error(f"List agents failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Get detailed information about a registered agent.

    Compliance: Multi-tenant isolation enforced
    """
    agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)

    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

    return {
        "success": True,
        "agent": {
            "id": agent.id,
            "agent_id": agent.agent_id,
            "display_name": agent.display_name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "version": agent.version,
            "version_notes": agent.version_notes,

            "risk_config": {
                "default_risk_score": agent.default_risk_score,
                "max_risk_threshold": agent.max_risk_threshold,
                "auto_approve_below": agent.auto_approve_below,
                "requires_mfa_above": agent.requires_mfa_above,
                # SEC-108d: Include autonomous thresholds
                "autonomous_auto_approve_below": agent.autonomous_auto_approve_below,
                "autonomous_max_risk_threshold": agent.autonomous_max_risk_threshold
            },

            "capabilities": {
                "allowed_action_types": agent.allowed_action_types,
                "allowed_resources": agent.allowed_resources,
                "blocked_resources": agent.blocked_resources
            },

            "mcp_integration": {
                "is_mcp_server": agent.is_mcp_server,
                "mcp_server_url": agent.mcp_server_url,
                "mcp_capabilities": agent.mcp_capabilities
            },

            "notifications": {
                "alert_on_high_risk": agent.alert_on_high_risk,
                "alert_recipients": agent.alert_recipients,
                "webhook_url": agent.webhook_url
            },

            "tags": agent.tags,
            "metadata": agent.agent_metadata,

            "audit": {
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "created_by": agent.created_by,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "updated_by": agent.updated_by,
                "approved_at": agent.approved_at.isoformat() if agent.approved_at else None,
                "approved_by": agent.approved_by
            }
        }
    }


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    Update an agent's configuration.

    Significant changes will create a new version.

    Compliance: SOC 2 CC8.1 (change management)
    """
    try:
        updated_by = current_user.get("email", "unknown")

        # Filter out None values
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No updates provided")

        agent = agent_registry_service.update_agent(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            updates=updates,
            updated_by=updated_by
        )

        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

        return {
            "success": True,
            "message": f"Agent updated: {agent_id}",
            "agent": {
                "id": agent.id,
                "agent_id": agent.agent_id,
                "version": agent.version,
                "status": agent.status,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent update failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/agents/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Activate an agent for production use.

    Requires admin privileges.

    Compliance: SOC 2 CC6.2 (access authorization)
    """
    try:
        approved_by = current_user.get("email", "admin")

        agent = agent_registry_service.activate_agent(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            approved_by=approved_by
        )

        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

        return {
            "success": True,
            "message": f"Agent activated: {agent_id}",
            "agent": {
                "id": agent.id,
                "agent_id": agent.agent_id,
                "status": agent.status,
                "approved_at": agent.approved_at.isoformat() if agent.approved_at else None,
                "approved_by": agent.approved_by
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent activation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/agents/{agent_id}/suspend")
async def suspend_agent(
    agent_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Suspend an agent (emergency disable).

    Use for security incidents or policy violations.

    Compliance: SOC 2 CC6.2, NIST AC-2(3)
    """
    try:
        suspended_by = current_user.get("email", "admin")

        agent = agent_registry_service.suspend_agent(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            suspended_by=suspended_by,
            reason=reason
        )

        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

        return {
            "success": True,
            "message": f"Agent suspended: {agent_id}",
            "agent": {
                "id": agent.id,
                "agent_id": agent.agent_id,
                "status": agent.status
            },
            "reason": reason
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent suspension failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# VERSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/agents/{agent_id}/versions")
async def list_versions(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    List all versions of an agent.

    Compliance: SOC 2 CC8.1 (version history)
    """
    versions = agent_registry_service.list_versions(db, org_id, agent_id)

    return {
        "success": True,
        "agent_id": agent_id,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "version_notes": v.version_notes,
                "is_active": v.is_active,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": v.created_by
            }
            for v in versions
        ]
    }


@router.post("/agents/{agent_id}/rollback")
async def rollback_version(
    agent_id: str,
    target_version: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Rollback an agent to a previous version.

    Requires admin privileges.

    Compliance: SOC 2 CC8.1 (rollback capability)
    """
    try:
        performed_by = current_user.get("email", "admin")

        agent = agent_registry_service.rollback_to_version(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            target_version=target_version,
            performed_by=performed_by
        )

        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

        return {
            "success": True,
            "message": f"Agent rolled back to version {target_version}",
            "agent": {
                "id": agent.id,
                "agent_id": agent.agent_id,
                "version": agent.version,
                "version_notes": agent.version_notes
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent rollback failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# POLICY MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/agents/{agent_id}/policies", status_code=status.HTTP_201_CREATED)
async def add_policy(
    agent_id: str,
    request: PolicyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    Add a policy to an agent.

    Policies define conditions and actions for agent authorization.

    Compliance: NIST AC-3 (access enforcement)
    """
    try:
        created_by = current_user.get("email", "unknown")

        policy = agent_registry_service.add_policy(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            policy_data=request.model_dump(),
            created_by=created_by
        )

        return {
            "success": True,
            "message": f"Policy added to agent {agent_id}",
            "policy": {
                "id": policy.id,
                "policy_name": policy.policy_name,
                "policy_action": policy.policy_action,
                "priority": policy.priority,
                "is_active": policy.is_active
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Add policy failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/agents/{agent_id}/policies")
async def list_policies(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    List all policies for an agent.
    """
    from models_agent_registry import AgentPolicy, RegisteredAgent
    from sqlalchemy import and_

    agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent not found: {agent_id}")

    policies = db.query(AgentPolicy).filter(
        AgentPolicy.agent_id == agent.id
    ).order_by(AgentPolicy.priority).all()

    return {
        "success": True,
        "agent_id": agent_id,
        "policies": [
            {
                "id": p.id,
                "policy_name": p.policy_name,
                "policy_description": p.policy_description,
                "policy_action": p.policy_action,
                "priority": p.priority,
                "is_active": p.is_active,
                "conditions": p.conditions,
                "action_params": p.action_params,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in policies
        ]
    }


@router.post("/agents/{agent_id}/evaluate")
async def evaluate_policies(
    agent_id: str,
    request: PolicyEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Evaluate policies for a proposed action.

    Use this to test policy configuration before submitting real actions.

    Compliance: NIST AC-3 (access enforcement)
    """
    try:
        context = {
            "action_type": request.action_type,
            "resource": request.resource,
            "risk_score": request.risk_score,
            **request.metadata
        }

        result = agent_registry_service.evaluate_policies(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            action_context=context
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "evaluation": result
        }

    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# MCP SERVER ENDPOINTS
# ============================================================================

@router.post("/mcp-servers", status_code=status.HTTP_201_CREATED)
async def register_mcp_server(
    request: MCPServerRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    Register an MCP server for governance.

    MCP servers can then have their tools governed through OW-AI.

    Compliance: SOC 2 CC6.1
    """
    try:
        created_by = current_user.get("email", "unknown")

        server = agent_registry_service.register_mcp_server(
            db=db,
            organization_id=org_id,
            server_data=request.model_dump(),
            created_by=created_by
        )

        return {
            "success": True,
            "message": f"MCP server registered: {server.server_name}",
            "server": {
                "id": server.id,
                "server_name": server.server_name,
                "display_name": server.display_name,
                "transport_type": server.transport_type,
                "governance_enabled": server.governance_enabled,
                "is_active": server.is_active
            }
        }

    except Exception as e:
        logger.error(f"MCP server registration failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/mcp-servers")
async def list_mcp_servers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    List all MCP servers for the organization.
    """
    servers = agent_registry_service.list_mcp_servers(db, org_id)

    return {
        "success": True,
        "servers": [
            {
                "id": s.id,
                "server_name": s.server_name,
                "display_name": s.display_name,
                "description": s.description,
                "transport_type": s.transport_type,
                "governance_enabled": s.governance_enabled,
                "is_active": s.is_active,
                "health_status": s.health_status,
                "discovered_tools": s.discovered_tools,
                "auto_approve_tools": s.auto_approve_tools,
                "blocked_tools": s.blocked_tools
            }
            for s in servers
        ]
    }


@router.get("/mcp-servers/{server_name}")
async def get_mcp_server(
    server_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Get detailed information about an MCP server.

    Compliance: Multi-tenant isolation enforced
    """
    server = agent_registry_service.get_mcp_server(db, org_id, server_name)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server not found: {server_name}"
        )

    return {
        "success": True,
        "server": {
            "id": server.id,
            "server_name": server.server_name,
            "display_name": server.display_name,
            "description": server.description,
            "server_url": server.server_url,
            "transport_type": server.transport_type,
            "connection_config": server.connection_config,
            "governance_enabled": server.governance_enabled,
            "is_active": server.is_active,
            "health_status": server.health_status,
            "discovered_tools": server.discovered_tools,
            "discovered_prompts": server.discovered_prompts,
            "discovered_resources": server.discovered_resources,
            "auto_approve_tools": server.auto_approve_tools,
            "blocked_tools": server.blocked_tools,
            "tool_risk_overrides": server.tool_risk_overrides,
            "created_at": server.created_at.isoformat() if server.created_at else None,
            "created_by": server.created_by,
            "updated_at": server.updated_at.isoformat() if server.updated_at else None
        }
    }


@router.put("/mcp-servers/{server_name}")
async def update_mcp_server(
    server_name: str,
    request: MCPServerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    Update an MCP server configuration.

    Compliance: SOC 2 CC8.1 (change management)
    """
    try:
        updated_by = current_user.get("email", "unknown")

        # Filter out None values
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )

        server = agent_registry_service.update_mcp_server(
            db=db,
            organization_id=org_id,
            server_name=server_name,
            updates=updates,
            updated_by=updated_by
        )

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server not found: {server_name}"
            )

        return {
            "success": True,
            "message": f"MCP server updated: {server_name}",
            "server": {
                "id": server.id,
                "server_name": server.server_name,
                "display_name": server.display_name,
                "is_active": server.is_active,
                "governance_enabled": server.governance_enabled,
                "updated_at": server.updated_at.isoformat() if server.updated_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP server update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/mcp-servers/{server_name}")
async def delete_mcp_server(
    server_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Delete an MCP server registration.

    Requires admin privileges.

    Compliance: SOC 2 CC6.2, NIST AC-2
    """
    try:
        deleted_by = current_user.get("email", "admin")

        deleted = agent_registry_service.delete_mcp_server(
            db=db,
            organization_id=org_id,
            server_name=server_name,
            deleted_by=deleted_by
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server not found: {server_name}"
            )

        return {
            "success": True,
            "message": f"MCP server deleted: {server_name}",
            "deleted_by": deleted_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP server deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/mcp-servers/{server_name}/activate")
async def activate_mcp_server(
    server_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Activate an MCP server.

    Requires admin privileges.

    Compliance: SOC 2 CC6.2
    """
    try:
        activated_by = current_user.get("email", "admin")

        server = agent_registry_service.activate_mcp_server(
            db=db,
            organization_id=org_id,
            server_name=server_name,
            activated_by=activated_by
        )

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server not found: {server_name}"
            )

        return {
            "success": True,
            "message": f"MCP server activated: {server_name}",
            "server": {
                "id": server.id,
                "server_name": server.server_name,
                "is_active": server.is_active
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP server activation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/mcp-servers/{server_name}/deactivate")
async def deactivate_mcp_server(
    server_name: str,
    request: MCPServerDeactivateRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Deactivate an MCP server.

    Use for maintenance or security incidents.
    Requires admin privileges.

    Compliance: SOC 2 CC6.2, NIST AC-2(3)
    """
    try:
        deactivated_by = current_user.get("email", "admin")
        reason = request.reason if request else None

        server = agent_registry_service.deactivate_mcp_server(
            db=db,
            organization_id=org_id,
            server_name=server_name,
            deactivated_by=deactivated_by,
            reason=reason
        )

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server not found: {server_name}"
            )

        return {
            "success": True,
            "message": f"MCP server deactivated: {server_name}",
            "server": {
                "id": server.id,
                "server_name": server.server_name,
                "is_active": server.is_active
            },
            "reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP server deactivation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# AGENT DELETE ENDPOINT
# ============================================================================

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    request: AgentDeleteRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Delete an agent registration.

    This permanently removes the agent and all associated policies.
    An audit trail entry is created for compliance.

    Requires admin privileges.

    Compliance: SOC 2 CC6.2, NIST AC-2
    """
    try:
        deleted_by = current_user.get("email", "admin")
        reason = request.reason if request else None

        deleted = agent_registry_service.delete_agent(
            db=db,
            organization_id=org_id,
            agent_id=agent_id,
            deleted_by=deleted_by,
            reason=reason
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )

        return {
            "success": True,
            "message": f"Agent deleted: {agent_id}",
            "deleted_by": deleted_by,
            "reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# SEC-068: AUTONOMOUS AGENT GOVERNANCE
# Enterprise-grade controls for autonomous AI agents
# Ascend Platform - Authored by Ascend Engineers
# © OW-kai Technologies Inc.
# Compliance: SOC 2 CC6.1/CC6.2/CC7.1, NIST AC-3/SI-4, PCI-DSS 7.1
# ============================================================================

class RateLimitConfigRequest(BaseModel):
    """SEC-068: Rate limit configuration for agents."""
    max_actions_per_minute: Optional[int] = Field(None, ge=1, le=10000, description="Max actions per minute (None = unlimited)")
    max_actions_per_hour: Optional[int] = Field(None, ge=1, le=100000, description="Max actions per hour")
    max_actions_per_day: Optional[int] = Field(None, ge=1, le=1000000, description="Max actions per day")


class BudgetConfigRequest(BaseModel):
    """SEC-068: Budget configuration for agents."""
    max_daily_budget_usd: Optional[float] = Field(None, ge=0, le=1000000, description="Max daily budget in USD")
    budget_alert_threshold_percent: int = Field(80, ge=1, le=100, description="Alert when this % of budget is used")
    auto_suspend_on_exceeded: bool = Field(True, description="Auto-suspend when budget exceeded")


class TimeWindowConfigRequest(BaseModel):
    """SEC-068: Time window restrictions for agents."""
    enabled: bool = Field(True, description="Enable time window restrictions")
    start_time: str = Field("09:00", description="Start time (HH:MM)")
    end_time: str = Field("17:00", description="End time (HH:MM)")
    timezone: str = Field("UTC", description="Timezone (e.g., 'America/New_York')")
    allowed_days: List[int] = Field([1, 2, 3, 4, 5], description="Allowed days (1=Mon, 7=Sun)")

    # CR-008: Validate time format (HH:MM) with proper hour/minute ranges
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """CR-008: Validate time is in HH:MM format with valid hour (00-23) and minute (00-59)."""
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(
                f"Invalid time format '{v}'. Must be HH:MM with hours 00-23 and minutes 00-59"
            )
        return v

    @field_validator('allowed_days')
    @classmethod
    def validate_days(cls, v: List[int]) -> List[int]:
        """Validate days are 1-7 (Monday=1 to Sunday=7)."""
        for day in v:
            if day < 1 or day > 7:
                raise ValueError(f"Invalid day {day}. Days must be 1-7 (Monday=1, Sunday=7)")
        return v


class DataClassificationConfigRequest(BaseModel):
    """SEC-068: Data classification restrictions for agents."""
    allowed_classifications: List[str] = Field([], description="Allowed data classifications")
    blocked_classifications: List[str] = Field([], description="Blocked data classifications")


class AutoSuspendConfigRequest(BaseModel):
    """SEC-068: Auto-suspension trigger configuration."""
    enabled: bool = Field(True, description="Enable auto-suspension")
    on_error_rate: Optional[float] = Field(None, ge=0, le=1, description="Suspend if error rate exceeds (0-1)")
    on_offline_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Suspend if offline > N minutes")
    on_budget_exceeded: bool = Field(True, description="Suspend when budget exceeded")
    on_rate_exceeded: bool = Field(False, description="Suspend when rate limit exceeded")


class EmergencySuspendRequest(BaseModel):
    """SEC-068: Emergency suspension request."""
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for emergency suspension")


@router.put("/agents/{agent_id}/rate-limits")
async def configure_rate_limits(
    agent_id: str,
    config: RateLimitConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Configure rate limits for an agent.

    Rate limits control how many actions an agent can perform per time period.
    Exceeding rate limits blocks further actions until the window resets.

    Compliance: NIST SI-4, Datadog rate limiting patterns
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update rate limit configuration
        agent.max_actions_per_minute = config.max_actions_per_minute
        agent.max_actions_per_hour = config.max_actions_per_hour
        agent.max_actions_per_day = config.max_actions_per_day

        db.commit()

        logger.info(f"SEC-068: Rate limits configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "rate_limits": {
                "per_minute": config.max_actions_per_minute,
                "per_hour": config.max_actions_per_hour,
                "per_day": config.max_actions_per_day
            },
            "configured_by": current_user.get("email"),
            "compliance": "SEC-068 / NIST SI-4"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Rate limit configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}/budget")
async def configure_budget(
    agent_id: str,
    config: BudgetConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Configure budget limits for an agent.

    Budget limits control daily spending. When exceeded, the agent
    can be automatically suspended if configured.

    Compliance: PCI-DSS 7.1, SOC 2 A1.1
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update budget configuration
        agent.max_daily_budget_usd = config.max_daily_budget_usd
        agent.budget_alert_threshold_percent = config.budget_alert_threshold_percent
        agent.auto_suspend_on_budget_exceeded = config.auto_suspend_on_exceeded

        db.commit()

        logger.info(f"SEC-068: Budget configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "budget": {
                "max_daily_usd": config.max_daily_budget_usd,
                "alert_threshold_percent": config.budget_alert_threshold_percent,
                "auto_suspend_on_exceeded": config.auto_suspend_on_exceeded
            },
            "current_spend_usd": agent.current_daily_spend_usd,
            "configured_by": current_user.get("email"),
            "compliance": "SEC-068 / PCI-DSS 7.1"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Budget configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}/time-window")
async def configure_time_window(
    agent_id: str,
    config: TimeWindowConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Configure time window restrictions for an agent.

    Time windows restrict when an agent can operate.
    Useful for business hours enforcement.

    Compliance: SOC 2 A1.1
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update time window configuration
        agent.time_window_enabled = config.enabled
        agent.time_window_start = config.start_time
        agent.time_window_end = config.end_time
        agent.time_window_timezone = config.timezone
        agent.time_window_days = config.allowed_days

        db.commit()

        logger.info(f"SEC-068: Time window configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "time_window": {
                "enabled": config.enabled,
                "start": config.start_time,
                "end": config.end_time,
                "timezone": config.timezone,
                "allowed_days": config.allowed_days
            },
            "configured_by": current_user.get("email"),
            "compliance": "SEC-068 / SOC 2 A1.1"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Time window configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}/data-classifications")
async def configure_data_classifications(
    agent_id: str,
    config: DataClassificationConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Configure data classification restrictions for an agent.

    Controls what types of data an agent can access.
    Blocked classifications take precedence over allowed.

    Compliance: HIPAA 164.312, PCI-DSS 3.4, GDPR
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update data classification configuration
        agent.allowed_data_classifications = config.allowed_classifications
        agent.blocked_data_classifications = config.blocked_classifications

        db.commit()

        logger.info(f"SEC-068: Data classifications configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "data_classifications": {
                "allowed": config.allowed_classifications,
                "blocked": config.blocked_classifications
            },
            "configured_by": current_user.get("email"),
            "compliance": "SEC-068 / HIPAA / PCI-DSS / GDPR"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Data classification configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}/auto-suspend")
async def configure_auto_suspend(
    agent_id: str,
    config: AutoSuspendConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Configure auto-suspension triggers for an agent.

    Auto-suspension automatically disables agents when thresholds are exceeded.
    Critical for autonomous agent safety.

    Compliance: SOC 2 CC6.2, NIST AC-2(3)
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update auto-suspend configuration
        agent.auto_suspend_enabled = config.enabled
        agent.auto_suspend_on_error_rate = config.on_error_rate
        agent.auto_suspend_on_offline_minutes = config.on_offline_minutes
        agent.auto_suspend_on_budget_exceeded = config.on_budget_exceeded
        agent.auto_suspend_on_rate_exceeded = config.on_rate_exceeded

        db.commit()

        logger.info(f"SEC-068: Auto-suspend configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "auto_suspend": {
                "enabled": config.enabled,
                "on_error_rate": config.on_error_rate,
                "on_offline_minutes": config.on_offline_minutes,
                "on_budget_exceeded": config.on_budget_exceeded,
                "on_rate_exceeded": config.on_rate_exceeded
            },
            "configured_by": current_user.get("email"),
            "compliance": "SEC-068 / SOC 2 CC6.2"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Auto-suspend configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/usage")
async def get_agent_usage(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Get usage statistics for an agent.

    Returns rate limit usage, budget usage, and anomaly detection status.

    Compliance: SOC 2 AU-6, NIST AU-6
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "rate_limits": {
                "per_minute": {
                    "limit": agent.max_actions_per_minute,
                    "current": agent.current_minute_count,
                    "remaining": (agent.max_actions_per_minute - agent.current_minute_count) if agent.max_actions_per_minute else None
                },
                "per_hour": {
                    "limit": agent.max_actions_per_hour,
                    "current": agent.current_hour_count,
                    "remaining": (agent.max_actions_per_hour - agent.current_hour_count) if agent.max_actions_per_hour else None
                },
                "per_day": {
                    "limit": agent.max_actions_per_day,
                    "current": agent.current_day_count,
                    "remaining": (agent.max_actions_per_day - agent.current_day_count) if agent.max_actions_per_day else None
                }
            },
            "budget": {
                "max_daily_usd": agent.max_daily_budget_usd,
                "current_spend_usd": agent.current_daily_spend_usd,
                "remaining_usd": (agent.max_daily_budget_usd - agent.current_daily_spend_usd) if agent.max_daily_budget_usd else None,
                "alert_sent": agent.budget_alert_sent
            },
            "anomaly_detection": {
                "enabled": agent.anomaly_detection_enabled,
                "last_check": agent.last_anomaly_check.isoformat() if agent.last_anomaly_check else None,
                "last_detected": agent.last_anomaly_detected.isoformat() if agent.last_anomaly_detected else None,
                "count_24h": agent.anomaly_count_24h,
                "threshold_percent": agent.anomaly_threshold_percent
            },
            "auto_suspend": {
                "enabled": agent.auto_suspend_enabled,
                "suspended_at": agent.auto_suspended_at.isoformat() if agent.auto_suspended_at else None,
                "reason": agent.auto_suspend_reason
            },
            "health": {
                "status": agent.health_status,
                "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
                "error_rate_percent": agent.error_rate_percent
            },
            "compliance": "SEC-068 / SOC 2 AU-6"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Usage retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/anomalies")
async def get_agent_anomalies(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Get anomaly detection status for an agent.

    Compares current behavior against established baselines.

    Compliance: SOC 2 CC7.1, NIST SI-4
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Run anomaly detection
        anomaly_result = agent_registry_service.detect_anomalies(
            db, agent,
            current_action_rate=agent.current_hour_count,
            current_error_rate=agent.error_rate_percent,
            current_risk_score=agent.default_risk_score
        )

        return {
            "agent_id": agent_id,
            "anomaly_detection": {
                "enabled": agent.anomaly_detection_enabled,
                "has_anomaly": anomaly_result.get("has_anomaly", False),
                "severity": anomaly_result.get("severity"),
                "anomalies": anomaly_result.get("anomalies", []),
                "count_24h": agent.anomaly_count_24h
            },
            "baselines": {
                "actions_per_hour": agent.baseline_actions_per_hour,
                "error_rate": agent.baseline_error_rate,
                "avg_risk_score": agent.baseline_avg_risk_score,
                "threshold_percent": agent.anomaly_threshold_percent
            },
            "current_values": {
                "actions_this_hour": agent.current_hour_count,
                "error_rate": agent.error_rate_percent,
                "default_risk_score": agent.default_risk_score
            },
            "last_check": agent.last_anomaly_check.isoformat() if agent.last_anomaly_check else None,
            "last_detected": agent.last_anomaly_detected.isoformat() if agent.last_anomaly_detected else None,
            "compliance": "SEC-068 / SOC 2 CC7.1"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/emergency-suspend")
async def emergency_suspend_agent(
    agent_id: str,
    request: EmergencySuspendRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Emergency suspension of an agent.

    Immediately suspends the agent, bypassing normal workflows.
    Use for security incidents or policy violations.

    Compliance: SOC 2 CC6.2, NIST IR-4
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        if agent.status == "suspended":
            raise HTTPException(status_code=400, detail="Agent is already suspended")

        # Perform emergency suspension
        agent_registry_service.auto_suspend_agent(
            db, agent,
            reason=f"EMERGENCY: {request.reason}",
            trigger="emergency_manual"
        )

        logger.warning(f"SEC-068 EMERGENCY: Agent {agent_id} suspended by {current_user.get('email')}: {request.reason}")

        return {
            "success": True,
            "agent_id": agent_id,
            "status": "suspended",
            "reason": request.reason,
            "suspended_by": current_user.get("email"),
            "suspended_at": datetime.utcnow().isoformat(),
            "alert": "EMERGENCY SUSPENSION - All stakeholders notified",
            "compliance": "SEC-068 / SOC 2 CC6.2 / NIST IR-4"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Emergency suspension failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/set-baselines")
async def set_agent_baselines(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    SEC-068: Set baseline metrics for anomaly detection.

    Captures current metrics as the baseline for future anomaly detection.
    Should be called after agent behavior stabilizes.

    Compliance: SOC 2 CC7.1, NIST SI-4
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Set current values as baselines
        agent.baseline_actions_per_hour = float(agent.current_hour_count) if agent.current_hour_count else 10.0
        agent.baseline_error_rate = agent.error_rate_percent if agent.error_rate_percent else 0.0
        agent.baseline_avg_risk_score = float(agent.default_risk_score)

        # Reset anomaly counters
        agent.anomaly_count_24h = 0
        agent.last_anomaly_detected = None

        db.commit()

        logger.info(f"SEC-068: Baselines set for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "baselines": {
                "actions_per_hour": agent.baseline_actions_per_hour,
                "error_rate": agent.baseline_error_rate,
                "avg_risk_score": agent.baseline_avg_risk_score,
                "threshold_percent": agent.anomaly_threshold_percent
            },
            "set_by": current_user.get("email"),
            "set_at": datetime.utcnow().isoformat(),
            "compliance": "SEC-068 / SOC 2 CC7.1"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-068: Baseline setting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CR-003: AUTONOMOUS AGENT ESCALATION CONFIGURATION
# Ascend Platform - Authored by Ascend Engineers
# © OW-kai Technologies Inc.
# ============================================================================

class EscalationConfigRequest(BaseModel):
    """CR-003: Escalation configuration for autonomous agents."""
    escalation_webhook_url: Optional[str] = Field(None, max_length=500, description="Webhook URL for escalation notifications")
    escalation_email: Optional[str] = Field(None, max_length=255, description="Email for escalation fallback")
    allow_queued_approval: bool = Field(False, description="Allow actions to be queued for human review")

    @field_validator('escalation_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator('escalation_webhook_url')
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate webhook URL if provided."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


@router.put("/agents/{agent_id}/escalation")
async def configure_escalation(
    agent_id: str,
    config: EscalationConfigRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    CR-003: Configure escalation path for autonomous agents.

    Enables autonomous agents to escalate high-risk actions instead of
    being blocked. Options include:
    - Webhook notification (real-time alerting)
    - Email notification (fallback)
    - Queued approval (async human review)

    Compliance: SOC 2 CC6.2, NIST AC-3
    """
    try:
        agent = agent_registry_service.get_agent(db, org_id, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        # Update escalation configuration
        agent.autonomous_escalation_webhook_url = config.escalation_webhook_url
        agent.autonomous_escalation_email = config.escalation_email
        agent.autonomous_allow_queued_approval = config.allow_queued_approval

        db.commit()

        logger.info(f"CR-003: Escalation configured for agent {agent_id} by {current_user.get('email')}")

        return {
            "success": True,
            "agent_id": agent_id,
            "escalation": {
                "webhook_url": config.escalation_webhook_url,
                "email": config.escalation_email,
                "allow_queued_approval": config.allow_queued_approval,
                "is_configured": bool(config.escalation_webhook_url or config.escalation_email or config.allow_queued_approval)
            },
            "configured_by": current_user.get("email"),
            "compliance": "CR-003 / SOC 2 CC6.2"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CR-003: Escalation configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
