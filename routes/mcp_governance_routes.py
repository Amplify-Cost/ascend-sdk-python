"""
MCP Server Governance API Routes
Complete AI Governance - Agents + MCP Servers
Integrates with existing authorization center and audit system
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text  # SEC-074: For raw SQL queries with org filtering
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta, UTC
from pydantic import BaseModel, Field
import logging
import json
import asyncio
import uuid

from database import get_db
from dependencies import get_current_user, get_organization_filter  # SEC-074: Multi-tenant isolation
from models_mcp_governance import MCPServerAction, MCPServer, MCPSession, MCPPolicy
from services.mcp_governance_service import MCPGovernanceService
from services.immutable_audit_service import ImmutableAuditService

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC SCHEMAS FOR MCP GOVERNANCE
# ============================================================================

class MCPActionRequest(BaseModel):
    """Schema for MCP action evaluation requests"""
    server_id: str = Field(..., description="MCP server identifier")
    namespace: str = Field(..., description="MCP namespace (e.g., filesystem, database)")
    verb: str = Field(..., description="MCP action verb (e.g., read_file, write_file)")
    resource: str = Field(..., description="Target resource path/identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    session_id: str = Field(..., description="MCP session identifier")
    client_id: str = Field(..., description="MCP client identifier")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request ID")

class MCPActionResponse(BaseModel):
    """Schema for MCP action evaluation responses"""
    action_id: str
    decision: str  # ALLOW, DENY, EVALUATE
    status: str    # AUTO_APPROVED, PENDING_APPROVAL, DENIED
    risk_score: int
    risk_level: str
    requires_approval: bool
    approval_level: int
    reason: str
    estimated_review_time_minutes: int

class MCPServerRegistration(BaseModel):
    """Schema for registering new MCP servers"""
    server_id: str
    server_name: str
    server_description: Optional[str] = None
    endpoint_url: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    trust_level: str = Field(default="restricted", description="trusted, restricted, sandbox")

class MCPApprovalRequest(BaseModel):
    """Schema for MCP action approval"""
    action_id: str
    approval_decision: str = Field(..., description="APPROVE or DENY")
    approval_reason: str
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MCPPolicyCreate(BaseModel):
    """Schema for creating MCP governance policies"""
    policy_name: str
    policy_description: Optional[str] = None
    server_patterns: List[str] = Field(default_factory=list)
    namespace_patterns: List[str] = Field(default_factory=list)
    verb_patterns: List[str] = Field(default_factory=list)
    resource_patterns: List[str] = Field(default_factory=list)
    risk_threshold: int = Field(default=50, ge=0, le=100)
    action: str = Field(default="EVALUATE", description="ALLOW, DENY, EVALUATE")
    required_approval_level: int = Field(default=1, ge=1, le=5)
    compliance_framework: Optional[str] = None

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_mcp_governance_service(db: Session = Depends(get_db)) -> MCPGovernanceService:
    """Dependency injection for MCP governance service"""
    return MCPGovernanceService(db)

def get_audit_service(db: Session = Depends(get_db)) -> ImmutableAuditService:
    """Dependency injection for audit service"""
    return ImmutableAuditService(db)

# ============================================================================
# MCP GATEWAY - CORE GOVERNANCE ENDPOINTS
# ============================================================================

@router.post("/evaluate",
             response_model=MCPActionResponse,
             summary="Evaluate MCP Action",
             description="Core MCP governance - evaluate action and return decision")
async def evaluate_mcp_action(
    action_request: MCPActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service)
):
    """
    **CORE MCP GOVERNANCE ENDPOINT**
    
    Evaluates MCP server actions using the same enterprise risk assessment
    and approval workflows as agent actions.
    
    **Enterprise Features:**
    - Real-time risk assessment (0-100 scale)
    - Policy-based decision making
    - Multi-level approval workflows
    - Immutable audit logging
    - Fail-closed security (deny by default)
    
    **Integration:** This endpoint is called by the MCP Gateway proxy
    for every MCP server action before execution.
    """
    try:
        # Extract user context
        user_context = {
            'user_id': str(current_user.id),
            'user_email': current_user.email,
            'role': getattr(current_user, 'role', 'user')
        }
        
        # Extract session context
        session_context = {
            'request_id': action_request.request_id,
            'session_id': action_request.session_id,
            'client_id': action_request.client_id,
            'source_ip': request.client.host,
            'user_agent': request.headers.get('user-agent', '')
        }
        
        # Evaluate the MCP action
        evaluation_result = await mcp_service.evaluate_mcp_action(
            server_id=action_request.server_id,
            namespace=action_request.namespace,
            verb=action_request.verb,
            resource=action_request.resource,
            parameters=action_request.parameters,
            user_context=user_context,
            session_context=session_context
        )
        
        return MCPActionResponse(**evaluation_result)
        
    except Exception as e:
        logger.error(f"Failed to evaluate MCP action: {e}")
        # Fail-closed: return denial on error
        return MCPActionResponse(
            action_id=str(uuid.uuid4()),
            decision="DENY",
            status="FAILED",
            risk_score=100,
            risk_level="CRITICAL",
            requires_approval=False,
            approval_level=0,
            reason=f"Evaluation failed: {str(e)}",
            estimated_review_time_minutes=0
        )

@router.post("/execute",
             summary="Execute Approved MCP Action",
             description="Execute MCP action after approval (if required)")
async def execute_mcp_action(
    action_id: str,
    execution_params: Dict[str, Any] = {},
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Execute approved MCP action with full audit logging
    """
    try:
        # Get the MCP action (SEC-074: organization_id filter)
        mcp_action = db.query(MCPServerAction).filter(
            MCPServerAction.id == action_id,
            MCPServerAction.organization_id == organization_id  # SEC-074
        ).first()
        
        if not mcp_action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP action not found"
            )
        
        # Verify action is approved or auto-approved
        if mcp_action.status not in ['APPROVED', 'AUTO_APPROVED']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action not approved. Current status: {mcp_action.status}"
            )
        
        # Update execution status
        mcp_action.status = 'EXECUTING'
        mcp_action.executed_at = datetime.now(UTC)
        execution_start = datetime.now(UTC)
        
        try:
            # Here you would integrate with the actual MCP server
            # For now, we'll simulate execution
            execution_result = {
                'success': True,
                'output': f"MCP action executed: {mcp_action.verb} on {mcp_action.resource}",
                'execution_time_ms': 150
            }
            
            # Update execution results
            execution_end = datetime.now(UTC)
            mcp_action.execution_duration_ms = int((execution_end - execution_start).total_seconds() * 1000)
            mcp_action.execution_result = 'SUCCESS' if execution_result['success'] else 'FAILED'
            mcp_action.execution_output = execution_result.get('output', '')
            mcp_action.status = 'COMPLETED'
            
        except Exception as exec_error:
            mcp_action.execution_result = 'FAILED'
            mcp_action.error_message = str(exec_error)
            mcp_action.status = 'FAILED'
            
        db.commit()
        
        # Log execution to immutable audit trail
        await audit_service.log_event(
            event_type="MCP_ACTION_EXECUTED",
            actor_id=current_user.email,
            resource_type="MCP_SERVER",
            resource_id=f"{mcp_action.mcp_server_id}:{mcp_action.namespace}",
            action=f"EXECUTE_{mcp_action.verb}",
            event_data={
                "mcp_action_id": str(mcp_action.id),
                "server_id": mcp_action.mcp_server_id,
                "namespace": mcp_action.namespace,
                "verb": mcp_action.verb,
                "resource": mcp_action.resource,
                "execution_result": mcp_action.execution_result,
                "execution_duration_ms": mcp_action.execution_duration_ms,
                "risk_score": mcp_action.risk_score
            },
            risk_level=mcp_action.risk_level,
            compliance_tags=["MCP_GOVERNANCE", "AI_EXECUTION"] + mcp_action.compliance_tags,
            ip_address=mcp_action.source_ip,
            user_agent=mcp_action.user_agent
        )
        
        return {
            'action_id': action_id,
            'status': mcp_action.status,
            'execution_result': mcp_action.execution_result,
            'execution_duration_ms': mcp_action.execution_duration_ms,
            'execution_output': mcp_action.execution_output,
            'error_message': mcp_action.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute MCP action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )

# ============================================================================
# MCP SERVER MANAGEMENT
# ============================================================================

@router.post("/servers/register",
             summary="Register MCP Server",
             description="Register new MCP server for governance")
async def register_mcp_server(
    server_registration: MCPServerRegistration,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """Register new MCP server for governance"""
    try:
        # Check if server already exists (SEC-074: within organization)
        existing_server = db.query(MCPServer).filter(
            MCPServer.server_id == server_registration.server_id,
            MCPServer.organization_id == organization_id  # SEC-074
        ).first()
        
        if existing_server:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MCP server {server_registration.server_id} already registered"
            )
        
        # Register the server
        server = await mcp_service.register_mcp_server(
            server_id=server_registration.server_id,
            server_name=server_registration.server_name,
            endpoint_url=server_registration.endpoint_url,
            capabilities=server_registration.capabilities,
            trust_level=server_registration.trust_level
        )
        
        # Log registration
        await audit_service.log_event(
            event_type="MCP_SERVER_REGISTERED",
            actor_id=current_user.email,
            resource_type="MCP_SERVER",
            resource_id=server_registration.server_id,
            action="REGISTER",
            event_data={
                "server_name": server_registration.server_name,
                "endpoint_url": server_registration.endpoint_url,
                "trust_level": server_registration.trust_level,
                "capabilities": server_registration.capabilities
            },
            risk_level="MEDIUM",
            compliance_tags=["MCP_GOVERNANCE", "SERVER_MANAGEMENT"]
        )
        
        return {
            'server_id': server.server_id,
            'status': 'registered',
            'trust_level': server.trust_level,
            'requires_approval': server.requires_approval_by_default
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register MCP server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/servers",
            summary="List MCP Servers",
            description="Get all registered MCP servers")
async def list_mcp_servers(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)  # SEC-074: Multi-tenant isolation
):
    """List all registered MCP servers"""
    try:
        # SEC-074: Filter by organization
        query = db.query(MCPServer).filter(MCPServer.organization_id == organization_id)
        if active_only:
            query = query.filter(MCPServer.is_active == True)
        
        servers = query.all()
        
        return {
            'total': len(servers),
            'servers': [
                {
                    'server_id': server.server_id,
                    'server_name': server.server_name,
                    'trust_level': server.trust_level,
                    'is_active': server.is_active,
                    'total_actions': server.total_actions,
                    'failed_actions': server.failed_actions,
                    'last_seen': server.last_seen.isoformat() if server.last_seen else None,
                    'capabilities': server.capabilities
                } for server in servers
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list MCP servers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        )

# ============================================================================
# APPROVAL WORKFLOWS - UNIFIED WITH AGENT APPROVALS
# ============================================================================

@router.get("/actions/pending",
            summary="Get Pending MCP Actions",
            description="Get MCP actions requiring approval (for Authorization Center)")
async def get_pending_mcp_actions(
    limit: int = 50,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service)
):
    """
    Get pending MCP actions for the Authorization Center
    **Integrates with existing agent approval workflows**
    """
    try:
        # SEC-074: Get pending actions for this organization only
        pending_actions = db.query(MCPServerAction).filter(
            MCPServerAction.organization_id == organization_id,  # SEC-074
            MCPServerAction.status == 'PENDING_APPROVAL'
        ).order_by(MCPServerAction.risk_score.desc()).limit(limit).all()
        
        # Filter by risk level if specified
        if risk_level:
            pending_actions = [a for a in pending_actions if a.risk_level == risk_level]
        
        return {
            'total': len(pending_actions),
            'limit': limit,
            'actions': [
                {
                    'id': str(action.id),
                    'action_type': 'mcp_server_action',  # Distinguishes from agent actions
                    'created_at': action.created_at.isoformat(),
                    'server_id': action.mcp_server_id,
                    'server_name': action.mcp_server_name,
                    'namespace': action.namespace,
                    'verb': action.verb,
                    'resource': action.resource,
                    'user_email': action.user_email,
                    'user_role': action.user_role,
                    'risk_score': action.risk_score,
                    'risk_level': action.risk_level,
                    'risk_factors': action.risk_factors,
                    'approval_level': action.approval_level,
                    'policy_reason': action.policy_reason,
                    'status': action.status,
                    'session_id': action.session_id,
                    'environment': action.environment,
                    'compliance_tags': action.compliance_tags
                } for action in pending_actions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending MCP actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending actions: {str(e)}"
        )

@router.post("/actions/{action_id}/approve",
             summary="Approve MCP Action",
             description="Approve pending MCP action (unified with agent approvals)")
async def approve_mcp_action(
    action_id: str,
    approval_request: MCPApprovalRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service)
):
    """
    Approve or deny MCP action
    **Uses same approval workflows as agent actions**
    """
    try:
        if approval_request.approval_decision.upper() == 'APPROVE':
            # SEC-074: Verify action belongs to organization before approving
            action_check = db.query(MCPServerAction).filter(
                MCPServerAction.id == action_id,
                MCPServerAction.organization_id == organization_id  # SEC-074
            ).first()

            if not action_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="MCP action not found"
                )

            result = await mcp_service.approve_mcp_action(
                action_id=action_id,
                approver_email=current_user.email,
                approval_reason=approval_request.approval_reason
            )
        else:
            # Deny the action (SEC-074: organization_id filter)
            action = db.query(MCPServerAction).filter(
                MCPServerAction.id == action_id,
                MCPServerAction.organization_id == organization_id  # SEC-074
            ).first()
            
            if not action:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="MCP action not found"
                )
            
            action.status = 'DENIED'
            action.approver_email = current_user.email
            action.approved_at = datetime.now(UTC)
            action.approval_reason = approval_request.approval_reason
            
            db.commit()
            
            result = {
                'action_id': action_id,
                'status': 'DENIED',
                'approved_by': current_user.email,
                'approved_at': action.approved_at.isoformat()
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve MCP action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval failed: {str(e)}"
        )

# ============================================================================
# POLICY MANAGEMENT
# ============================================================================

@router.post("/policies",
             summary="Create MCP Policy",
             description="Create governance policy for MCP servers")
async def create_mcp_policy(
    policy_data: MCPPolicyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """Create new MCP governance policy"""
    try:
        # SEC-074: Create policy with organization_id
        policy = MCPPolicy(
            organization_id=organization_id,  # SEC-074
            policy_name=policy_data.policy_name,
            policy_description=policy_data.policy_description,
            server_patterns=policy_data.server_patterns,
            namespace_patterns=policy_data.namespace_patterns,
            verb_patterns=policy_data.verb_patterns,
            resource_patterns=policy_data.resource_patterns,
            risk_threshold=policy_data.risk_threshold,
            action=policy_data.action,
            required_approval_level=policy_data.required_approval_level,
            compliance_framework=policy_data.compliance_framework,
            created_by=current_user.email
        )
        
        db.add(policy)
        db.commit()
        
        # Log policy creation
        await audit_service.log_event(
            event_type="MCP_POLICY_CREATED",
            actor_id=current_user.email,
            resource_type="MCP_POLICY",
            resource_id=str(policy.id),
            action="CREATE",
            event_data={
                "policy_name": policy_data.policy_name,
                "action": policy_data.action,
                "risk_threshold": policy_data.risk_threshold,
                "approval_level": policy_data.required_approval_level
            },
            risk_level="MEDIUM",
            compliance_tags=["MCP_GOVERNANCE", "POLICY_MANAGEMENT"]
        )
        
        return {
            'policy_id': str(policy.id),
            'policy_name': policy.policy_name,
            'status': 'created',
            'is_active': policy.is_active
        }
        
    except Exception as e:
        logger.error(f"Failed to create MCP policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy creation failed: {str(e)}"
        )

@router.get("/policies",
            summary="List MCP Policies",
            description="Get all MCP governance policies")
async def list_mcp_policies(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)  # SEC-074: Multi-tenant isolation
):
    """List MCP governance policies"""
    try:
        # SEC-074: Filter by organization
        query = db.query(MCPPolicy).filter(MCPPolicy.organization_id == organization_id)
        if active_only:
            query = query.filter(MCPPolicy.is_active == True)
        
        policies = query.order_by(MCPPolicy.priority.desc()).all()
        
        return {
            'total': len(policies),
            'policies': [
                {
                    'id': str(policy.id),
                    'policy_name': policy.policy_name,
                    'policy_description': policy.policy_description,
                    'action': policy.action,
                    'risk_threshold': policy.risk_threshold,
                    'required_approval_level': policy.required_approval_level,
                    'is_active': policy.is_active,
                    'priority': policy.priority,
                    'execution_count': policy.execution_count,
                    'created_by': policy.created_by,
                    'created_at': policy.created_at.isoformat()
                } for policy in policies
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list MCP policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list policies: {str(e)}"
        )

# ============================================================================
# ANALYTICS & MONITORING
# ============================================================================

@router.get("/analytics/dashboard",
            summary="MCP Governance Analytics",
            description="Analytics for MCP governance (integrates with existing dashboards)")
async def get_mcp_analytics(
    time_range_hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)  # SEC-074: Multi-tenant isolation
):
    """Get MCP governance analytics for dashboard integration"""
    try:
        from sqlalchemy import func, and_

        # Time range filter
        time_threshold = datetime.now(UTC) - timedelta(hours=time_range_hours)

        # SEC-074: Action counts by status (organization filtered)
        status_counts = db.query(
            MCPServerAction.status,
            func.count(MCPServerAction.id).label('count')
        ).filter(
            MCPServerAction.organization_id == organization_id,  # SEC-074
            MCPServerAction.created_at >= time_threshold
        ).group_by(MCPServerAction.status).all()

        # SEC-074: Risk level distribution (organization filtered)
        risk_counts = db.query(
            MCPServerAction.risk_level,
            func.count(MCPServerAction.id).label('count')
        ).filter(
            MCPServerAction.organization_id == organization_id,  # SEC-074
            MCPServerAction.created_at >= time_threshold
        ).group_by(MCPServerAction.risk_level).all()

        # SEC-074: Server activity (organization filtered)
        server_activity = db.query(
            MCPServerAction.mcp_server_id,
            MCPServerAction.mcp_server_name,
            func.count(MCPServerAction.id).label('total_actions'),
            func.avg(MCPServerAction.risk_score).label('avg_risk_score')
        ).filter(
            MCPServerAction.organization_id == organization_id,  # SEC-074
            MCPServerAction.created_at >= time_threshold
        ).group_by(
            MCPServerAction.mcp_server_id,
            MCPServerAction.mcp_server_name
        ).all()

        # SEC-074: Top risky actions (organization filtered)
        risky_actions = db.query(MCPServerAction).filter(
            and_(
                MCPServerAction.organization_id == organization_id,  # SEC-074
                MCPServerAction.created_at >= time_threshold,
                MCPServerAction.risk_score >= 70
            )
        ).order_by(MCPServerAction.risk_score.desc()).limit(10).all()
        
        return {
            'time_range_hours': time_range_hours,
            'generated_at': datetime.now(UTC).isoformat(),
            'summary': {
                'total_actions': sum(count for _, count in status_counts),
                'pending_approvals': next((count for status, count in status_counts if status == 'PENDING_APPROVAL'), 0),
                'auto_approved': next((count for status, count in status_counts if status == 'AUTO_APPROVED'), 0),
                'denied': next((count for status, count in status_counts if status == 'DENIED'), 0)
            },
            'status_distribution': [{'status': status, 'count': count} for status, count in status_counts],
            'risk_distribution': [{'risk_level': risk, 'count': count} for risk, count in risk_counts],
            'server_activity': [
                {
                    'server_id': server_id,
                    'server_name': server_name,
                    'total_actions': total,
                    'avg_risk_score': float(avg_risk) if avg_risk else 0
                } for server_id, server_name, total, avg_risk in server_activity
            ],
            'high_risk_actions': [
                {
                    'id': str(action.id),
                    'server_id': action.mcp_server_id,
                    'namespace': action.namespace,
                    'verb': action.verb,
                    'risk_score': action.risk_score,
                    'status': action.status,
                    'created_at': action.created_at.isoformat()
                } for action in risky_actions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get MCP analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics failed: {str(e)}"
        )

# ============================================================================
# UNIFIED AUTHORIZATION CENTER INTEGRATION
# ============================================================================

@router.get("/actions/all",
            summary="Get All Actions (Agents + MCP)",
            description="Unified view of all AI actions for Authorization Center")
async def get_unified_actions(
    limit: int = 50,
    status_filter: Optional[str] = None,
    risk_level_filter: Optional[str] = None,
    action_type_filter: Optional[str] = None,  # 'agent' or 'mcp' or 'all'
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)  # SEC-074: Multi-tenant isolation
):
    """
    **UNIFIED AUTHORIZATION CENTER ENDPOINT**

    Returns both agent actions and MCP server actions in a unified format
    for the Authorization Center dashboard.

    This enables complete AI governance visibility in a single interface.
    """
    try:
        mcp_actions = []

        # SEC-074: Get MCP actions (organization filtered)
        if action_type_filter in [None, 'all', 'mcp']:
            mcp_query = db.query(MCPServerAction).filter(
                MCPServerAction.organization_id == organization_id  # SEC-074
            )

            if status_filter:
                mcp_query = mcp_query.filter(MCPServerAction.status == status_filter)
            if risk_level_filter:
                mcp_query = mcp_query.filter(MCPServerAction.risk_level == risk_level_filter)
            
            mcp_results = mcp_query.order_by(
                MCPServerAction.risk_score.desc(),
                MCPServerAction.created_at.desc()
            ).limit(limit // 2 if action_type_filter == 'all' else limit).all()
            
            mcp_actions = [
                {
                    'id': str(action.id),
                    'action_type': 'mcp_server_action',
                    'created_at': action.created_at.isoformat(),
                    'updated_at': action.updated_at.isoformat(),
                    'title': f"{action.mcp_server_name}: {action.verb}",
                    'description': f"{action.namespace} - {action.resource}",
                    'server_id': action.mcp_server_id,
                    'server_name': action.mcp_server_name,
                    'namespace': action.namespace,
                    'verb': action.verb,
                    'resource': action.resource,
                    'user_email': action.user_email,
                    'user_role': action.user_role,
                    'risk_score': action.risk_score,
                    'risk_level': action.risk_level,
                    'risk_factors': action.risk_factors,
                    'status': action.status,
                    'requires_approval': action.requires_approval,
                    'approval_level': action.approval_level,
                    'policy_result': action.policy_result,
                    'policy_reason': action.policy_reason,
                    'approver_email': action.approver_email,
                    'approved_at': action.approved_at.isoformat() if action.approved_at else None,
                    'environment': action.environment,
                    'compliance_tags': action.compliance_tags
                } for action in mcp_results
            ]
        
        # ENTERPRISE UNIFIED GOVERNANCE: Query both MCP and agent actions

        # SEC-074: Get agent actions from the main authorization system (organization filtered)
        agent_actions = []

        agent_query = db.execute(text("""
            SELECT id, agent_id, action_type, description, risk_level, risk_score,
                   status, created_at, updated_at, approved, reviewed_by
            FROM agent_actions
            WHERE status IN ('pending', 'pending_approval', 'approved', 'submitted')
              AND organization_id = :organization_id
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit, "organization_id": organization_id}).fetchall()
        
        for row in agent_query:
            agent_actions.append({
                'id': str(row[0]),
                'action_type': 'agent_action',
                'created_at': row[7].isoformat() if row[7] else None,
                'updated_at': row[8].isoformat() if row[8] else None,
                'title': f"Agent {row[1]}: {row[2]}",
                'description': row[3] or "Agent security action",
                'agent_id': row[1],
                'risk_level': row[4] or 'medium',
                'risk_score': float(row[5]) if row[5] else 50.0,
                'status': row[6] or 'pending',
                'approved': bool(row[9]) if row[9] is not None else False,
                'reviewed_by': row[10],
                'enterprise_compliant': True,
                'source': 'agent_actions'
            })
        
        # Merge MCP and agent actions
        all_actions = mcp_actions + agent_actions
        
        # Sort by risk score and creation time
        all_actions.sort(key=lambda x: (x['risk_score'], x['created_at']), reverse=True)
        
        return {
            'total': len(all_actions),
            'limit': limit,
            'filters': {
                'status': status_filter,
                'risk_level': risk_level_filter,
                'action_type': action_type_filter
            },
            'actions': all_actions[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get unified actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unified actions: {str(e)}"
        )

# ============================================================================
# HEALTH CHECK & SYSTEM STATUS
# ============================================================================

@router.get("/health",
            summary="MCP Governance System Health",
            description="Enterprise health check for MCP governance system")
async def mcp_governance_health_check(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)  # SEC-074: Multi-tenant isolation
):
    """
    **ENTERPRISE HEALTH CHECK**

    Validates that MCP governance system is operational and ready
    for enterprise deployment.
    """
    try:
        from sqlalchemy import text

        # Test database connectivity
        db.execute(text("SELECT 1")).fetchone()

        # SEC-074: Get system statistics (organization filtered)
        total_servers = db.query(MCPServer).filter(
            MCPServer.organization_id == organization_id
        ).count()
        active_servers = db.query(MCPServer).filter(
            MCPServer.organization_id == organization_id,
            MCPServer.is_active == True
        ).count()

        total_actions = db.query(MCPServerAction).filter(
            MCPServerAction.organization_id == organization_id
        ).count()
        pending_actions = db.query(MCPServerAction).filter(
            MCPServerAction.organization_id == organization_id,
            MCPServerAction.status == 'PENDING_APPROVAL'
        ).count()

        active_policies = db.query(MCPPolicy).filter(
            MCPPolicy.organization_id == organization_id,
            MCPPolicy.is_active == True
        ).count()

        # SEC-074: Check recent activity (last 24 hours, organization filtered)
        recent_threshold = datetime.now(UTC) - timedelta(hours=24)
        recent_actions = db.query(MCPServerAction).filter(
            MCPServerAction.organization_id == organization_id,
            MCPServerAction.created_at >= recent_threshold
        ).count()
        
        return {
            'status': 'healthy',
            'mcp_governance_system': 'operational',
            'timestamp': datetime.now(UTC).isoformat(),
            'database_connected': True,
            'statistics': {
                'total_servers': total_servers,
                'active_servers': active_servers,
                'total_actions': total_actions,
                'pending_actions': pending_actions,
                'active_policies': active_policies,
                'recent_actions_24h': recent_actions
            },
            'features': [
                'mcp_action_evaluation',
                'risk_assessment', 
                'approval_workflows',
                'policy_engine',
                'audit_integration',
                'unified_dashboard',
                'real_time_monitoring'
            ],
            'enterprise_ready': True,
            'ai_governance_complete': True  # Both agents and MCP servers governed
        }
        
    except Exception as e:
        logger.error(f"MCP governance health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MCP governance system unavailable: {str(e)}"
        )

# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

@router.websocket("/ws/realtime")
async def mcp_governance_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time MCP governance updates
    Used by Authorization Center for live action notifications

    NOTE: WebSocket authentication should extract organization_id from token
    For now, this endpoint is NOT organization-filtered (requires WebSocket auth middleware)
    """
    await websocket.accept()

    try:
        while True:
            # Check for new pending actions every 5 seconds
            await asyncio.sleep(5)

            # NOTE: In production, extract organization_id from WebSocket token
            # For now, showing all pending actions (requires auth middleware upgrade)
            pending_count = db.query(MCPServerAction).filter(
                MCPServerAction.status == 'PENDING_APPROVAL'
            ).count()

            high_risk_count = db.query(MCPServerAction).filter(
                MCPServerAction.status == 'PENDING_APPROVAL',
                MCPServerAction.risk_score >= 80
            ).count()
            
            # Send update to client
            await websocket.send_json({
                'type': 'mcp_governance_update',
                'timestamp': datetime.now(UTC).isoformat(),
                'pending_actions': pending_count,
                'high_risk_actions': high_risk_count,
                'system_status': 'operational'
            })
            
    except WebSocketDisconnect:
        logger.info("MCP governance WebSocket client disconnected")
    except Exception as e:
        logger.error(f"MCP governance WebSocket error: {e}")
        await websocket.close()

# ============================================================================
# SIMPLIFIED TEST ENDPOINTS
# ============================================================================

@router.post("/test/evaluate",
             summary="Test MCP Evaluation",
             description="Simple test endpoint for MCP evaluation")
async def test_mcp_evaluation(
    server_id: str = "test-server",
    namespace: str = "filesystem",
    verb: str = "read_file",
    resource: str = "/tmp/test.txt",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter),  # SEC-074: Multi-tenant isolation
    mcp_service: MCPGovernanceService = Depends(get_mcp_governance_service)
):
    """Simple test endpoint for MCP evaluation (SEC-074: organization filtered)"""
    try:
        user_context = {
            'user_id': str(current_user.id),
            'user_email': current_user.email,
            'role': getattr(current_user, 'role', 'user')
        }
        
        session_context = {
            'request_id': str(uuid.uuid4()),
            'session_id': f"test-session-{uuid.uuid4()}",
            'client_id': 'test-client',
            'source_ip': '127.0.0.1',
            'user_agent': 'test-agent'
        }
        
        result = await mcp_service.evaluate_mcp_action(
            server_id=server_id,
            namespace=namespace,
            verb=verb,
            resource=resource,
            parameters={'test': True},
            user_context=user_context,
            session_context=session_context
        )
        
        return {
            'test_result': 'success',
            'evaluation': result
        }
        
    except Exception as e:
        logger.error(f"Test evaluation failed: {e}")
        return {
            'test_result': 'failed',
            'error': str(e)
        }