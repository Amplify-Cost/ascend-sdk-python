"""
Enterprise MCP Secure Router
SEC-089: Production implementation - queries real database
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, UTC, timedelta
import uuid

from database import get_db
from dependencies import get_current_user, get_organization_filter
from mcp_enterprise_schemas import MCPActionRequest, EnterpriseRiskResponse
from enterprise_security import enterprise_security
from enterprise_risk_assessment import EnterpriseRiskAssessment

router = APIRouter(prefix="/mcp", tags=["mcp-enterprise-secure"])
logger = logging.getLogger(__name__)

# SEC-089: REMOVED demo data initialization - production uses database only

# Security validation dependency
async def validate_enterprise_security(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Enterprise security validation dependency"""
    user_role = getattr(current_user, 'role', 'default')
    user_id = getattr(current_user, 'id', str(current_user))
    
    await enterprise_security.validate_request_security(request, str(user_id), user_role)
    return current_user

def get_enterprise_risk_assessor():
    """Get enterprise risk assessor instance"""
    return EnterpriseRiskAssessment()

@router.post("/actions/assess-risk-enterprise", response_model=EnterpriseRiskResponse)
async def assess_enterprise_risk_secure(
    action_request: MCPActionRequest,
    request: Request,
    current_user = Depends(validate_enterprise_security),
    risk_assessor: EnterpriseRiskAssessment = Depends(get_enterprise_risk_assessor)
):
    """Secure enterprise risk assessment endpoint"""
    
    try:
        action_data = {
            "agent_id": action_request.agent_id,
            "action_type": action_request.action_type.value if hasattr(action_request.action_type, 'value') else str(action_request.action_type),
            "resource": action_request.resource
        }
        
        if action_request.metadata:
            action_data.update(action_request.metadata)
        
        risk_result = risk_assessor.assess_action_risk(action_data)
        
        logger.info("Enterprise MCP risk assessment completed", extra={
            "user_id": getattr(current_user, 'id', 'unknown'),
            "user_email": getattr(current_user, 'email', 'unknown'),
            "agent_id": action_request.agent_id,
            "action_type": str(action_request.action_type),
            "risk_score": risk_result.get("risk_score", 0)
        })
        
        return EnterpriseRiskResponse(
            action_data=action_data,
            enterprise_risk_assessment=risk_result,
            assessed_by=getattr(current_user, 'email', 'system'),
            assessment_timestamp=datetime.now(UTC).isoformat(),
            enterprise_benefits=risk_result.get("enterprise_benefits", {
                "methodology_credibility": "Industry-standard CVSS v3.1 + NIST 800-30 + MITRE ATT&CK",
                "audit_ready": "Complete documentation for SOC2 compliance", 
                "threat_intelligence": f"Mapped to MITRE tactic {risk_result.get('mitre_tactic_id', 'N/A')}"
            })
        )
        
    except Exception as e:
        logger.error(f"Enterprise risk assessment failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Enterprise risk assessment temporarily unavailable"
        )

@router.get("/actions")
async def get_mcp_actions_secure(
    current_user = Depends(validate_enterprise_security),
    db: Session = Depends(get_db),
    org_id: int = Depends(get_organization_filter),
    skip: int = 0,
    limit: int = 100
):
    """SEC-089: Get MCP actions from real database"""

    # Query real MCP actions from database
    result = db.execute(text("""
        SELECT id, uuid, agent_id, action_type, namespace, verb, resource,
               status, risk_score, created_at, mcp_server_name
        FROM mcp_server_actions
        WHERE organization_id = :org_id
        ORDER BY created_at DESC
        OFFSET :skip LIMIT :limit
    """), {"org_id": org_id, "skip": skip, "limit": limit}).fetchall()

    # Get total count
    count_result = db.execute(text("""
        SELECT COUNT(*) FROM mcp_server_actions WHERE organization_id = :org_id
    """), {"org_id": org_id}).fetchone()
    total = count_result[0] if count_result else 0

    actions = []
    for row in result:
        actions.append({
            "id": str(row[1]) if row[1] else str(row[0]),  # Prefer UUID
            "action_id": str(row[0]),
            "agent_id": row[2] or "unknown",
            "action_type": row[3] or "mcp_action",
            "namespace": row[4],
            "verb": row[5],
            "resource": row[6],
            "status": row[7] or "pending",
            "risk_score": row[8] or 0,
            "timestamp": row[9].isoformat() if row[9] else None,
            "mcp_server_name": row[10]
        })

    logger.info(f"✅ SEC-089: MCP actions query - {len(actions)} results for org_id={org_id}")

    return {
        "actions": actions,
        "total": total,
        "page": skip // limit if limit > 0 else 0,
        "limit": limit,
        "has_next": skip + limit < total,
        "has_activity": total > 0,
        "message": None if total > 0 else "No MCP actions yet. Actions will appear when MCP servers are integrated."
    }

@router.post("/actions/ingest")
async def ingest_mcp_action_secure(
    action_request: MCPActionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_organization_filter),
    current_user = Depends(validate_enterprise_security),
    risk_assessor: EnterpriseRiskAssessment = Depends(get_enterprise_risk_assessor)
):
    """SEC-089: Secure MCP action ingestion - stores to database"""

    action_uuid = str(uuid.uuid4())
    request_id = f"req-{uuid.uuid4().hex[:8]}"

    # Assess risk for the new action
    action_data = {
        "agent_id": action_request.agent_id,
        "action_type": str(action_request.action_type),
        "resource": action_request.resource
    }

    risk_result = risk_assessor.assess_action_risk(action_data)
    risk_score = risk_result.get("risk_score", 50)
    status = "requires_approval" if risk_score > 60 else "approved"

    # SEC-089: Store to database instead of in-memory
    try:
        import json
        db.execute(text("""
            INSERT INTO mcp_server_actions
            (uuid, organization_id, agent_id, action_type, namespace, verb, resource,
             request_id, session_id, client_id, mcp_server_name, status, risk_score,
             context, created_at, updated_at)
            VALUES
            (:uuid, :org_id, :agent_id, :action_type, :namespace, :verb, :resource,
             :request_id, :session_id, :client_id, :mcp_server_name, :status, :risk_score,
             :context, NOW(), NOW())
        """), {
            "uuid": action_uuid,
            "org_id": org_id,
            "agent_id": action_request.agent_id,
            "action_type": str(action_request.action_type),
            "namespace": getattr(action_request, 'namespace', 'default'),
            "verb": getattr(action_request, 'verb', str(action_request.action_type)),
            "resource": action_request.resource,
            "request_id": request_id,
            "session_id": f"session-{uuid.uuid4().hex[:8]}",
            "client_id": getattr(current_user, 'id', 'unknown'),
            "mcp_server_name": action_request.agent_id,
            "status": status,
            "risk_score": risk_score,
            "context": json.dumps(action_request.metadata or {})
        })
        db.commit()

        logger.info(f"✅ SEC-089: MCP action stored to database", extra={
            "action_id": action_uuid,
            "org_id": org_id,
            "agent_id": action_request.agent_id,
            "risk_score": risk_score
        })

    except Exception as e:
        logger.error(f"❌ SEC-089: Failed to store MCP action: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to store MCP action")

    return {
        "action_id": action_uuid,
        "status": "received",
        "message": "Action received and stored in governance queue",
        "timestamp": datetime.now(UTC).isoformat(),
        "risk_assessment": risk_result
    }
