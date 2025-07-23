# Create routes/authorization_routes.py

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import PendingAgentAction, AgentAction
from dependencies import verify_token
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-control", tags=["Agent Authorization"])

# 1. AGENT REQUEST FOR ACTION AUTHORIZATION
@router.post("/request-authorization")
async def request_action_authorization(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Agent requests authorization to perform an action"""
    try:
        data = await request.json()
        
        # Extract agent and action details
        agent_id = data.get("agent_id")
        action_type = data.get("action_type")
        description = data.get("description", "")
        risk_level = data.get("risk_level", "medium")
        action_payload = json.dumps(data.get("action_payload", {}))
        tenant_id = data.get("tenant_id", "default")
        
        if not agent_id or not action_type:
            raise HTTPException(status_code=400, detail="agent_id and action_type required")
        
        # AI Risk Assessment
        risk_score = await assess_action_risk(data)
        
        # Auto-authorization rules
        authorization_status = await determine_authorization_status(data, risk_score)
        
        # Set expiration time (15 minutes for human review)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        # Create pending action record
        pending_action = PendingAgentAction(
            tenant_id=tenant_id,
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            tool_name=data.get("tool_name"),
            risk_level=risk_level,
            action_payload=action_payload,
            target_system=data.get("target_system"),
            authorization_status=authorization_status,
            expires_at=expires_at,
            ai_risk_score=risk_score,
            nist_control=map_to_nist_control(action_type),
            mitre_tactic=map_to_mitre_tactic(action_type),
            mitre_technique=map_to_mitre_technique(action_type)
        )
        
        db.add(pending_action)
        db.commit()
        db.refresh(pending_action)
        
        # If requires human review, send alert to security team (background task)
        if authorization_status == "pending":
            background_tasks.add_task(notify_security_team, pending_action.id, risk_score, tenant_id)
        
        logger.info(f"Authorization requested: {pending_action.id} - Status: {authorization_status}")
        
        return {
            "authorization_id": pending_action.id,
            "status": authorization_status,
            "expires_at": expires_at.isoformat(),
            "risk_score": risk_score,
            "requires_human_review": authorization_status == "pending",
            "estimated_review_time": "5-15 minutes" if authorization_status == "pending" else "immediate"
        }
        
    except Exception as e:
        logger.error(f"Authorization request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authorization request failed: {str(e)}")

# 2. CHECK AUTHORIZATION STATUS
@router.get("/authorization-status/{authorization_id}")
async def check_authorization_status(
    authorization_id: int,
    db: Session = Depends(get_db)
):
    """Agent checks if action is authorized"""
    try:
        pending_action = db.query(PendingAgentAction).filter(
            PendingAgentAction.id == authorization_id
        ).first()
        
        if not pending_action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        # Check if expired
        if pending_action.expires_at < datetime.utcnow() and pending_action.authorization_status == "pending":
            pending_action.authorization_status = "expired"
            db.commit()
        
        return {
            "authorization_id": authorization_id,
            "status": pending_action.authorization_status,
            "reviewed_by": pending_action.reviewed_by,
            "reviewed_at": pending_action.reviewed_at.isoformat() if pending_action.reviewed_at else None,
            "review_notes": pending_action.review_notes,
            "expires_at": pending_action.expires_at.isoformat(),
            "can_execute": pending_action.authorization_status in ["approved", "auto_approved"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Status check failed")

# 3. GET PENDING AUTHORIZATIONS (for dashboard)
@router.get("/pending-authorizations")
async def get_pending_authorizations(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Get all pending actions requiring human authorization"""
    try:
        tenant_id = user.get("tenant_id", "default")
        
        pending_actions = db.query(PendingAgentAction).filter(
            PendingAgentAction.tenant_id == tenant_id,
            PendingAgentAction.authorization_status == "pending",
            PendingAgentAction.expires_at > datetime.utcnow()
        ).order_by(PendingAgentAction.ai_risk_score.desc()).all()
        
        return {
            "pending_count": len(pending_actions),
            "actions": [
                {
                    "id": action.id,
                    "agent_id": action.agent_id,
                    "action_type": action.action_type,
                    "description": action.description,
                    "risk_level": action.risk_level,
                    "ai_risk_score": action.ai_risk_score,
                    "target_system": action.target_system,
                    "requested_at": action.requested_at.isoformat(),
                    "expires_at": action.expires_at.isoformat(),
                    "nist_control": action.nist_control,
                    "mitre_tactic": action.mitre_tactic,
                    "action_payload": json.loads(action.action_payload) if action.action_payload else {}
                }
                for action in pending_actions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending authorizations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending authorizations")

# 4. APPROVE/DENY ACTIONS
@router.post("/authorize/{authorization_id}")
async def authorize_action(
    authorization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Human approves or denies a pending action"""
    try:
        data = await request.json()
        decision = data.get("decision")  # "approve" or "deny"
        notes = data.get("notes", "")
        
        if decision not in ["approve", "deny"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'deny'")
        
        pending_action = db.query(PendingAgentAction).filter(
            PendingAgentAction.id == authorization_id
        ).first()
        
        if not pending_action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        if pending_action.authorization_status != "pending":
            raise HTTPException(status_code=400, detail="Action already processed")
        
        # Update authorization
        pending_action.authorization_status = "approved" if decision == "approve" else "denied"
        pending_action.reviewed_by = user.get("email", "unknown")
        pending_action.reviewed_at = datetime.utcnow()
        pending_action.review_notes = notes
        
        db.commit()
        
        logger.info(f"Action {authorization_id} {decision}d by {user.get('email')} - Notes: {notes}")
        
        # If approved, create the actual agent action record for your existing system
        if decision == "approve":
            agent_action = AgentAction(
                agent_id=pending_action.agent_id,
                action_type=pending_action.action_type,
                description=pending_action.description,
                tool_name=pending_action.tool_name,
                risk_level=pending_action.risk_level,
                nist_control=pending_action.nist_control,
                mitre_tactic=pending_action.mitre_tactic,
                mitre_technique=pending_action.mitre_technique,
                status="approved",
                reviewed_by=user.get("email"),
                reviewed_at=datetime.utcnow(),
                tenant_id=pending_action.tenant_id
            )
            db.add(agent_action)
            db.commit()
        
        return {
            "status": "success",
            "decision": decision,
            "authorization_id": authorization_id,
            "message": f"Action {decision}d successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Authorization failed")

# Helper functions
async def assess_action_risk(action_data: dict) -> int:
    """AI-powered risk assessment of the requested action"""
    risk_score = 50  # Base risk
    
    action_type = action_data.get("action_type", "").lower()
    target_system = action_data.get("target_system", "").lower()
    
    # High-risk actions
    high_risk_actions = [
        "delete", "format", "shutdown", "reboot", "kill_process",
        "modify_firewall", "change_permissions", "escalate_privilege",
        "install_software", "modify_registry", "access_credentials"
    ]
    
    if any(risky in action_type for risky in high_risk_actions):
        risk_score += 30
    
    # Critical systems
    if any(critical in target_system for critical in ["production", "database", "domain_controller"]):
        risk_score += 25
    
    # Time-based risk (higher risk outside business hours)
    current_hour = datetime.utcnow().hour
    if current_hour < 7 or current_hour > 19:  # Outside 7 AM - 7 PM UTC
        risk_score += 15
    
    return min(risk_score, 100)

async def determine_authorization_status(action_data: dict, risk_score: int) -> str:
    """Determine if action should be auto-approved, auto-denied, or require human review"""
    action_type = action_data.get("action_type", "").lower()
    
    # Auto-deny conditions
    if risk_score > 90:
        return "auto_denied"
    
    if any(dangerous in action_type for dangerous in ["format", "delete_system", "shutdown_production"]):
        return "auto_denied"
    
    # Auto-approve conditions
    if risk_score < 30 and action_type in ["health_check", "log_write", "status_report"]:
        return "auto_approved"
    
    # Everything else requires human review
    return "pending"

async def notify_security_team(authorization_id: int, risk_score: int, tenant_id: str):
    """Send notification to security team about pending authorization"""
    # In production, this would send Slack/Teams/email notifications
    logger.info(f"🚨 URGENT: Action authorization required - ID: {authorization_id}, Risk: {risk_score}")

def map_to_nist_control(action_type: str) -> str:
    """Map action type to NIST control"""
    mapping = {
        "file_access": "AC-6",
        "network_connection": "SI-4", 
        "process_execution": "SI-7",
        "privilege_escalation": "AC-6",
        "authentication": "IA-2"
    }
    return mapping.get(action_type.lower(), "SI-4")

def map_to_mitre_tactic(action_type: str) -> str:
    """Map action type to MITRE tactic"""
    mapping = {
        "privilege_escalation": "Privilege Escalation",
        "network_connection": "Command and Control", 
        "process_execution": "Execution",
        "file_access": "Collection"
    }
    return mapping.get(action_type.lower(), "Discovery")

def map_to_mitre_technique(action_type: str) -> str:
    """Map action type to MITRE technique"""
    mapping = {
        "privilege_escalation": "T1068",
        "network_connection": "T1071",
        "process_execution": "T1059",
        "file_access": "T1005"
    }
    return mapping.get(action_type.lower(), "T1082")
