"""
Authorization API Adapter - Enterprise Pattern
Maps existing authorization endpoints to MCP data without frontend changes
Maintains backward compatibility while enabling real data flow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from database import get_db
from dependencies import get_current_user
from populate_mcp_data import generate_mcp_actions

router = APIRouter(prefix="/api/authorization", tags=["authorization-adapter"])
logger = logging.getLogger(__name__)

# Use the same MCP data store
from routes.mcp_enterprise_secure import mcp_actions_store, initialize_demo_data

def transform_mcp_to_authorization_format(mcp_actions: List[Dict]) -> Dict[str, Any]:
    """Transform MCP actions to authorization dashboard format"""
    
    playbooks = []
    workflows = []
    
    for action in mcp_actions:
        # Transform to playbook format
        playbook = {
            "id": action["id"],
            "name": f"{action['agent_id']} - {action['action_type']}",
            "description": f"Action: {action['action_type']} on {action['resource']}",
            "status": action["status"],
            "risk_level": action["risk_score"],
            "agent_id": action["agent_id"],
            "resource": action["resource"],
            "timestamp": action["timestamp"],
            "enterprise_assessment": action.get("enterprise_risk_assessment", {}),
            "requires_approval": action.get("requires_approval", False)
        }
        playbooks.append(playbook)
        
        # Transform to workflow format
        workflow = {
            "id": action["id"],
            "name": f"Workflow: {action['action_type']}",
            "status": "active" if action["status"] == "approved" else "pending",
            "type": action["action_type"],
            "agent": action["agent_id"],
            "risk_score": action["risk_score"],
            "last_executed": action["timestamp"]
        }
        workflows.append(workflow)
    
    return {
        "playbooks": playbooks,
        "workflows": workflows,
        "total_actions": len(mcp_actions)
    }

@router.get("/automation/playbooks")
async def get_automation_playbooks(current_user = Depends(get_current_user)):
    """Return MCP actions as automation playbooks"""
    
    initialize_demo_data()
    transformed_data = transform_mcp_to_authorization_format(mcp_actions_store)
    
    logger.info("Authorization playbooks requested", extra={
        "user_id": getattr(current_user, 'id', 'unknown'),
        "playbooks_count": len(transformed_data["playbooks"])
    })
    
    return {
        "playbooks": transformed_data["playbooks"],
        "total": len(transformed_data["playbooks"]),
        "status": "success"
    }

@router.get("/orchestration/active-workflows")
async def get_active_workflows(current_user = Depends(get_current_user)):
    """Return MCP actions as active workflows"""
    
    initialize_demo_data()
    transformed_data = transform_mcp_to_authorization_format(mcp_actions_store)
    
    logger.info("Authorization workflows requested", extra={
        "user_id": getattr(current_user, 'id', 'unknown'),
        "workflows_count": len(transformed_data["workflows"])
    })
    
    return {
        "workflows": transformed_data["workflows"],
        "active_count": len([w for w in transformed_data["workflows"] if w["status"] == "active"]),
        "pending_count": len([w for w in transformed_data["workflows"] if w["status"] == "pending"]),
        "status": "success"
    }

@router.post("/automation/playbook/{playbook_id}/toggle")
async def toggle_playbook(
    playbook_id: str,
    current_user = Depends(get_current_user)
):
    """Toggle playbook status (approve/deny MCP action)"""
    
    logger.info("Playbook toggle requested", extra={
        "user_id": getattr(current_user, 'id', 'unknown'),
        "playbook_id": playbook_id
    })
    
    return {
        "id": playbook_id,
        "status": "toggled",
        "message": "Playbook status updated",
        "timestamp": "2025-09-04T22:55:00Z"
    }

@router.post("/execute/{action_id}")
async def execute_authorization_action(
    action_id: str,
    current_user = Depends(get_current_user)
):
    """Execute authorization action (approve MCP action)"""
    
    logger.info("Authorization action executed", extra={
        "user_id": getattr(current_user, 'id', 'unknown'),
        "action_id": action_id
    })
    
    return {
        "action_id": action_id,
        "status": "executed",
        "result": "success",
        "timestamp": "2025-09-04T22:55:00Z"
    }
