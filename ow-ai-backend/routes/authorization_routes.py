from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependencies import verify_token
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-control", tags=["Agent Authorization"])

# Temporary PendingAgentAction class until models are updated
class PendingAgentAction:
    def __init__(self, **kwargs):
        self.id = None
        self.tenant_id = kwargs.get('tenant_id', 'default')
        self.agent_id = kwargs.get('agent_id')
        self.action_type = kwargs.get('action_type')
        self.description = kwargs.get('description')
        self.tool_name = kwargs.get('tool_name')
        self.risk_level = kwargs.get('risk_level')
        self.action_payload = kwargs.get('action_payload')
        self.target_system = kwargs.get('target_system')
        self.authorization_status = kwargs.get('authorization_status', 'pending')
        self.requested_at = kwargs.get('requested_at', datetime.utcnow())
        self.expires_at = kwargs.get('expires_at')
        self.reviewed_by = kwargs.get('reviewed_by')
        self.reviewed_at = kwargs.get('reviewed_at')
        self.review_notes = kwargs.get('review_notes')
        self.ai_risk_score = kwargs.get('ai_risk_score')
        self.nist_control = kwargs.get('nist_control')
        self.mitre_tactic = kwargs.get('mitre_tactic')
        self.mitre_technique = kwargs.get('mitre_technique')

@router.post("/request-authorization")
async def request_action_authorization(request: Request, db: Session = Depends(get_db)):
    """Agent requests authorization to perform an action"""
    try:
        data = await request.json()
        
        agent_id = data.get("agent_id")
        action_type = data.get("action_type")
        description = data.get("description", "")
        risk_level = data.get("risk_level", "medium")
        target_system = data.get("target_system", "")
        tool_name = data.get("tool_name", "")
        action_payload = json.dumps(data.get("action_payload", {}))
        
        if not agent_id or not action_type:
            raise HTTPException(status_code=400, detail="agent_id and action_type required")
        
        # AI Risk Assessment
        risk_score = await assess_action_risk(data)
        
        # Auto-authorization logic
        authorization_status = await determine_authorization_status(data, risk_score)
        
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        # Insert into database using raw SQL since model might not exist yet
        from sqlalchemy import text
        result = db.execute(text("""
            INSERT INTO pending_agent_actions 
            (tenant_id, agent_id, action_type, description, tool_name, risk_level, 
             action_payload, target_system, authorization_status, expires_at, ai_risk_score,
             nist_control, mitre_tactic, mitre_technique, requested_at)
            VALUES (:tenant_id, :agent_id, :action_type, :description, :tool_name, :risk_level,
                    :action_payload, :target_system, :authorization_status, :expires_at, :ai_risk_score,
                    :nist_control, :mitre_tactic, :mitre_technique, :requested_at)
            RETURNING id
        """), {
            "tenant_id": "default",
            "agent_id": agent_id,
            "action_type": action_type,
            "description": description,
            "tool_name": tool_name,
            "risk_level": risk_level,
            "action_payload": action_payload,
            "target_system": target_system,
            "authorization_status": authorization_status,
            "expires_at": expires_at,
            "ai_risk_score": risk_score,
            "nist_control": map_to_nist_control(action_type),
            "mitre_tactic": map_to_mitre_tactic(action_type),
            "mitre_technique": map_to_mitre_technique(action_type),
            "requested_at": datetime.utcnow()
        })
        
        authorization_id = result.fetchone()[0]
        db.commit()
        
        logger.info(f"Authorization requested: {authorization_id} - Status: {authorization_status}")
        
        return {
            "authorization_id": authorization_id,
            "status": authorization_status,
            "expires_at": expires_at.isoformat(),
            "risk_score": risk_score,
            "requires_human_review": authorization_status == "pending",
            "estimated_review_time": "5-15 minutes" if authorization_status == "pending" else "immediate"
        }
        
    except Exception as e:
        logger.error(f"Authorization request failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Authorization request failed: {str(e)}")

@router.get("/authorization-status/{authorization_id}")
async def check_authorization_status(authorization_id: int, db: Session = Depends(get_db)):
    """Agent checks if action is authorized"""
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT authorization_status, reviewed_by, reviewed_at, review_notes, expires_at
            FROM pending_agent_actions 
            WHERE id = :auth_id
        """), {"auth_id": authorization_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        status, reviewed_by, reviewed_at, review_notes, expires_at = row
        
        # Check if expired
        if expires_at and expires_at < datetime.utcnow() and status == "pending":
            db.execute(text("""
                UPDATE pending_agent_actions 
                SET authorization_status = 'expired' 
                WHERE id = :auth_id
            """), {"auth_id": authorization_id})
            db.commit()
            status = "expired"
        
        return {
            "authorization_id": authorization_id,
            "status": status,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
            "review_notes": review_notes,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "can_execute": status in ["approved", "auto_approved"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Status check failed")

@router.get("/pending-authorizations")
async def get_pending_authorizations(db: Session = Depends(get_db), user: dict = Depends(verify_token)):
    """Get all pending actions requiring human authorization"""
    try:
        from sqlalchemy import text
        
        result = db.execute(text("""
            SELECT id, agent_id, action_type, description, risk_level, ai_risk_score,
                   target_system, requested_at, expires_at, nist_control, mitre_tactic,
                   action_payload
            FROM pending_agent_actions 
            WHERE authorization_status = 'pending' 
            AND expires_at > :now
            ORDER BY ai_risk_score DESC
        """), {"now": datetime.utcnow()})
        
        actions = []
        for row in result:
            action_payload = {}
            try:
                if row[11]:  # action_payload column
                    action_payload = json.loads(row[11])
            except:
                pass
            
            actions.append({
                "id": row[0],
                "agent_id": row[1],
                "action_type": row[2],
                "description": row[3],
                "risk_level": row[4],
                "ai_risk_score": row[5],
                "target_system": row[6],
                "requested_at": row[7].isoformat() if row[7] else None,
                "expires_at": row[8].isoformat() if row[8] else None,
                "nist_control": row[9],
                "mitre_tactic": row[10],
                "action_payload": action_payload
            })
        
        return {
            "pending_count": len(actions),
            "actions": actions
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending authorizations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending authorizations")

@router.post("/authorize/{authorization_id}")
async def authorize_action(authorization_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(verify_token)):
    """Human approves or denies a pending action"""
    try:
        data = await request.json()
        decision = data.get("decision")  # "approve" or "deny"
        notes = data.get("notes", "")
        
        if decision not in ["approve", "deny"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'deny'")
        
        from sqlalchemy import text
        
        # Check if action exists and is still pending
        result = db.execute(text("""
            SELECT authorization_status FROM pending_agent_actions WHERE id = :auth_id
        """), {"auth_id": authorization_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        if row[0] != "pending":
            raise HTTPException(status_code=400, detail="Action already processed")
        
        # Update authorization
        new_status = "approved" if decision == "approve" else "denied"
        db.execute(text("""
            UPDATE pending_agent_actions 
            SET authorization_status = :status,
                reviewed_by = :reviewed_by,
                reviewed_at = :reviewed_at,
                review_notes = :notes
            WHERE id = :auth_id
        """), {
            "status": new_status,
            "reviewed_by": user.get("email", "unknown"),
            "reviewed_at": datetime.utcnow(),
            "notes": notes,
            "auth_id": authorization_id
        })
        
        db.commit()
        
        logger.info(f"Action {authorization_id} {decision}d by {user.get('email')} - Notes: {notes}")
        
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
    risk_level = action_data.get("risk_level", "").lower()
    
    # High-risk actions
    high_risk_actions = [
        "delete", "format", "shutdown", "reboot", "kill_process",
        "modify_firewall", "change_permissions", "escalate_privilege",
        "install_software", "modify_registry", "access_credentials"
    ]
    
    if any(risky in action_type for risky in high_risk_actions):
        risk_score += 30
    
    # Risk level adjustment
    if "critical" in risk_level:
        risk_score += 25
    elif "high" in risk_level:
        risk_score += 15
    elif "low" in risk_level:
        risk_score -= 20
    
    # Critical systems
    if any(critical in target_system for critical in ["production", "database", "domain_controller"]):
        risk_score += 25
    
    # Time-based risk (higher risk outside business hours)
    current_hour = datetime.utcnow().hour
    if current_hour < 7 or current_hour > 19:  # Outside 7 AM - 7 PM UTC
        risk_score += 15
    
    return min(max(risk_score, 0), 100)

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

def map_to_nist_control(action_type: str) -> str:
    """Map action type to NIST control"""
    mapping = {
        "file_access": "AC-6",
        "network_connection": "SI-4", 
        "process_execution": "SI-7",
        "privilege_escalation": "AC-6",
        "authentication": "IA-2",
        "delete": "AC-6",
        "modify": "CM-5"
    }
    return mapping.get(action_type.lower(), "SI-4")

def map_to_mitre_tactic(action_type: str) -> str:
    """Map action type to MITRE tactic"""
    mapping = {
        "privilege_escalation": "Privilege Escalation",
        "network_connection": "Command and Control", 
        "process_execution": "Execution",
        "file_access": "Collection",
        "delete": "Impact",
        "modify": "Defense Evasion"
    }
    return mapping.get(action_type.lower(), "Discovery")

def map_to_mitre_technique(action_type: str) -> str:
    """Map action type to MITRE technique"""
    mapping = {
        "privilege_escalation": "T1068",
        "network_connection": "T1071",
        "process_execution": "T1059",
        "file_access": "T1005",
        "delete": "T1485",
        "modify": "T1562"
    }
    return mapping.get(action_type.lower(), "T1082")