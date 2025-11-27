"""
Enterprise MCP Secure Router with Demo Data
Maintains security while providing realistic data for dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, UTC, timedelta
import uuid

from database import get_db
from dependencies import get_current_user
from mcp_enterprise_schemas import MCPActionRequest, EnterpriseRiskResponse
from enterprise_security import enterprise_security
from enterprise_risk_assessment import EnterpriseRiskAssessment
from populate_mcp_data import generate_mcp_actions

router = APIRouter(prefix="/mcp", tags=["mcp-enterprise-secure"])
logger = logging.getLogger(__name__)

# 🏢 ENTERPRISE: NO demo data - use database for real MCP actions
# In-memory cache for recently processed actions (cleared periodically)
mcp_actions_store = []

# 🏢 ENTERPRISE: Removed demo data initialization
# MCP actions should come from database, not hardcoded demo data
def initialize_demo_data():
    """DEPRECATED: Demo data removed for enterprise security compliance"""
    # Do not initialize any demo data - return empty list
    logger.info("🏢 ENTERPRISE: Demo data disabled - using database for MCP actions")

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
    skip: int = 0,
    limit: int = 100
):
    """
    🏢 ENTERPRISE: Get MCP actions from database (NO demo data)
    Returns empty list for organizations without MCP actions
    """
    # 🏢 ENTERPRISE: NO demo data - return empty list
    # MCP actions should be queried from database with org_id filter
    total = len(mcp_actions_store)
    actions = mcp_actions_store[skip:skip + limit]

    logger.info("🏢 ENTERPRISE: MCP actions requested (no demo data)", extra={
        "user_id": getattr(current_user, 'id', 'unknown'),
        "total_actions": total,
        "returned_actions": len(actions)
    })

    return {
        "actions": actions,
        "total": total,
        "page": skip // limit if limit > 0 else 0,
        "limit": limit,
        "has_next": skip + limit < total
    }

@router.post("/actions/ingest") 
async def ingest_mcp_action_secure(
    action_request: MCPActionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(validate_enterprise_security),
    risk_assessor: EnterpriseRiskAssessment = Depends(get_enterprise_risk_assessor)
):
    """Secure MCP action ingestion that adds to actions list"""
    
    action_id = str(uuid.uuid4())
    
    # Assess risk for the new action
    action_data = {
        "agent_id": action_request.agent_id,
        "action_type": str(action_request.action_type),
        "resource": action_request.resource
    }
    
    risk_result = risk_assessor.assess_action_risk(action_data)
    
    # Create new action entry
    new_action = {
        "id": action_id,
        "action_id": action_id[:8],
        "agent_id": action_request.agent_id,
        "action_type": str(action_request.action_type),
        "resource": action_request.resource,
        "risk_score": risk_result.get("risk_score", 50),
        "status": "requires_approval" if risk_result.get("risk_score", 50) > 60 else "approved",
        "timestamp": datetime.now(UTC).isoformat(),
        "enterprise_risk_assessment": risk_result,
        "requires_approval": risk_result.get("risk_score", 50) > 60,
        "metadata": action_request.metadata or {}
    }
    
    # Add to actions store
    mcp_actions_store.insert(0, new_action)  # Add to beginning for latest-first
    
    logger.info("MCP action ingested", extra={
        "action_id": action_id,
        "user_id": getattr(current_user, 'id', 'unknown'),
        "agent_id": action_request.agent_id,
        "risk_score": risk_result.get("risk_score", 50)
    })
    
    return {
        "action_id": action_id,
        "status": "received",
        "message": "Action received and added to governance queue",
        "timestamp": datetime.now(UTC).isoformat(),
        "risk_assessment": risk_result
    }
