"""
OW-AI Enterprise Agent Registry API Routes
==========================================

RESTful API for managing AI agent registrations.
Provides full CRUD operations with enterprise-grade security.

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

MCP Server Management:
- POST   /api/registry/mcp-servers         - Register MCP server
- GET    /api/registry/mcp-servers         - List MCP servers

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

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
                "requires_mfa_above": agent.requires_mfa_above
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
            "metadata": agent.metadata,

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
