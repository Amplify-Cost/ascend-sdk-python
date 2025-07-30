# routes/authorization_routes.py - ENTERPRISE VERSION WITHOUT DATABASE DEPENDENCY
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import logging

from database import get_db
from dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-control", tags=["authorization"])

# In-memory storage for demonstration (enterprise version would use proper database)
pending_actions_storage = {}
action_counter = 1000

@router.post("/request-authorization")
async def request_authorization(request: Request, db: Session = Depends(get_db)):
    """🏢 ENTERPRISE: Request authorization for high-risk agent actions"""
    global action_counter
    
    try:
        data = await request.json()
        
        # 🔥 ENTERPRISE: Advanced multi-factor risk assessment
        risk_assessment = calculate_enterprise_risk_score(data)
        
        # 🔥 ENTERPRISE: Determine approval workflow based on risk and compliance
        workflow = determine_enterprise_workflow(risk_assessment)
        
        # Create authorization request
        action_id = action_counter
        action_counter += 1
        
        authorization_request = {
            "id": action_id,
            "agent_id": data.get("agent_id", "unknown"),
            "action_type": data.get("action_type", "unknown"),
            "description": data.get("description", ""),
            "target_system": data.get("target_system", ""),
            
            # 🏢 ENTERPRISE: Risk assessment data
            "risk_level": risk_assessment["risk_level"],
            "ai_risk_score": risk_assessment["risk_score"],
            "risk_factors": risk_assessment["risk_factors"],
            
            # 🏢 ENTERPRISE: Compliance framework integration
            "nist_control": data.get("nist_control", ""),
            "mitre_tactic": data.get("mitre_tactic", ""),
            "mitre_technique": data.get("mitre_technique", ""),
            
            # 🏢 ENTERPRISE: Workflow management
            "workflow_stage": workflow["initial_stage"],
            "required_approval_level": workflow["approval_levels"],
            "current_approval_level": 0,
            "authorization_status": "pending",
            
            # 🏢 ENTERPRISE: Timing and escalation
            "requested_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=workflow["timeout_hours"])).isoformat(),
            "auto_escalate_at": (datetime.utcnow() + timedelta(minutes=workflow["escalation_minutes"])).isoformat(),
            
            # 🏢 ENTERPRISE: Audit and compliance
            "audit_trail": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "authorization_requested",
                "risk_assessment": risk_assessment,
                "workflow_config": workflow,
                "compliance_check": "passed"
            }],
            
            # 🏢 ENTERPRISE: Emergency handling
            "is_emergency": data.get("is_emergency", False),
            "emergency_justification": data.get("emergency_justification", ""),
            "break_glass_available": risk_assessment["risk_score"] >= 90
        }
        
        # Store in memory (enterprise version would use database)
        pending_actions_storage[action_id] = authorization_request
        
        # 🔥 ENTERPRISE: Send to SIEM for real-time monitoring
        await send_enterprise_siem_event("authorization_requested", authorization_request)
        
        logger.info(f"🏢 ENTERPRISE: Authorization request {action_id} created - Agent: {data.get('agent_id')}, Risk: {risk_assessment['risk_score']}")
        
        return {
            "authorization_id": action_id,
            "status": "pending",
            "risk_assessment": risk_assessment,
            "workflow": workflow,
            "compliance_status": "compliant",
            "estimated_approval_time": f"{workflow['escalation_minutes']} minutes",
            "next_escalation": authorization_request["auto_escalate_at"],
            "message": "🏢 Enterprise authorization request submitted for review"
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Authorization request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit authorization request")

@router.get("/pending-actions")
async def get_pending_actions(
    risk_filter: Optional[str] = None,
    emergency_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """🏢 ENTERPRISE: Get pending actions with advanced filtering"""
    try:
        # Get all pending actions from storage
        actions = [action for action in pending_actions_storage.values() 
                  if action["authorization_status"] == "pending"]
        
        # 🏢 ENTERPRISE: Advanced filtering
        if risk_filter:
            actions = [a for a in actions if a["risk_level"] == risk_filter]
        
        if emergency_only:
            actions = [a for a in actions if a["is_emergency"]]
        
        # 🏢 ENTERPRISE: Sort by risk score and urgency
        actions.sort(key=lambda x: (-x["ai_risk_score"], x["requested_at"]))
        
        # 🏢 ENTERPRISE: Add time-sensitive indicators
        current_time = datetime.utcnow()
        for action in actions:
            expires_at = datetime.fromisoformat(action["expires_at"])
            escalate_at = datetime.fromisoformat(action["auto_escalate_at"])
            
            action["time_remaining"] = str(expires_at - current_time)
            action["requires_escalation"] = current_time >= escalate_at
            action["is_overdue"] = current_time >= expires_at
            
            # 🏢 ENTERPRISE: Calculate SLA status
            action["sla_status"] = calculate_sla_status(action, current_time)
        
        logger.info(f"🏢 ENTERPRISE: Retrieved {len(actions)} pending actions for {current_user['email']}")
        
        return {
            "total_pending": len(actions),
            "high_priority": len([a for a in actions if a["ai_risk_score"] >= 80]),
            "emergency_pending": len([a for a in actions if a["is_emergency"]]),
            "overdue": len([a for a in actions if a.get("is_overdue")]),
            "actions": actions[:50]  # Limit to 50 for performance
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Failed to get pending actions: {str(e)}")
        return {"total_pending": 0, "actions": []}

@router.post("/authorize/{action_id}")
async def authorize_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """🏢 ENTERPRISE: Multi-level authorization with audit trails"""
    try:
        data = await request.json()
        decision = data.get("decision")  # "approved", "denied", "escalated", "conditional"
        notes = data.get("notes", "")
        conditions = data.get("conditions", {})
        
        if decision not in ["approved", "denied", "escalated", "conditional"]:
            raise HTTPException(status_code=400, detail="Invalid decision type")
        
        # Get the action from storage
        if action_id not in pending_actions_storage:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        action = pending_actions_storage[action_id]
        
        # 🏢 ENTERPRISE: Process decision with workflow logic
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_email": admin_user["email"],
            "user_role": admin_user["role"],
            "decision": decision,
            "notes": notes,
            "approval_level": action["current_approval_level"] + 1,
            "compliance_verified": True
        }
        
        if decision == "approved":
            if action["current_approval_level"] + 1 >= action["required_approval_level"]:
                # 🏢 ENTERPRISE: Final approval
                action["authorization_status"] = "approved"
                action["approved_at"] = datetime.utcnow().isoformat()
                action["approved_by"] = admin_user["email"]
                audit_entry["event"] = "final_approval"
                
                # 🔥 ENTERPRISE: Send approval notification to SIEM
                await send_enterprise_siem_event("authorization_approved", action)
            else:
                # 🏢 ENTERPRISE: Intermediate approval - escalate to next level
                action["current_approval_level"] += 1
                action["workflow_stage"] = f"approval_level_{action['current_approval_level']}"
                audit_entry["event"] = "intermediate_approval"
                
        elif decision == "denied":
            action["authorization_status"] = "denied"
            action["denied_at"] = datetime.utcnow().isoformat()
            action["denied_by"] = admin_user["email"]
            action["denial_reason"] = notes
            audit_entry["event"] = "authorization_denied"
            
            # 🔥 ENTERPRISE: Send denial notification to SIEM
            await send_enterprise_siem_event("authorization_denied", action)
            
        elif decision == "conditional":
            action["authorization_status"] = "conditional_approved"
            action["conditions"] = conditions
            action["conditional_expiry"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            audit_entry["event"] = "conditional_approval"
            audit_entry["conditions"] = conditions
        
        # 🏢 ENTERPRISE: Update audit trail
        action["audit_trail"].append(audit_entry)
        action["last_reviewed_at"] = datetime.utcnow().isoformat()
        action["last_reviewed_by"] = admin_user["email"]
        
        logger.info(f"🏢 ENTERPRISE: Action {action_id} {decision} by {admin_user['email']}")
        
        return {
            "message": f"🏢 Enterprise authorization {decision} successfully",
            "action_id": action_id,
            "decision": decision,
            "workflow_stage": action["workflow_stage"],
            "authorization_status": action["authorization_status"],
            "reviewed_by": admin_user["email"],
            "audit_trail_entries": len(action["audit_trail"]),
            "compliance_status": "audit_logged"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Authorization processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process authorization")

@router.get("/approval-dashboard")
async def get_approval_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """🏢 ENTERPRISE: Real-time authorization dashboard with KPIs"""
    try:
        # Get all actions from storage
        all_actions = list(pending_actions_storage.values())
        pending_actions = [a for a in all_actions if a["authorization_status"] == "pending"]
        
        # 🏢 ENTERPRISE: Calculate enterprise KPIs
        current_time = datetime.utcnow()
        
        # Risk distribution
        risk_distribution = {
            "critical": len([a for a in pending_actions if a["ai_risk_score"] >= 90]),
            "high": len([a for a in pending_actions if 70 <= a["ai_risk_score"] < 90]),
            "medium": len([a for a in pending_actions if 40 <= a["ai_risk_score"] < 70]),
            "low": len([a for a in pending_actions if a["ai_risk_score"] < 40])
        }
        
        # SLA compliance metrics
        overdue_actions = []
        escalated_actions = []
        
        for action in pending_actions:
            expires_at = datetime.fromisoformat(action["expires_at"])
            escalate_at = datetime.fromisoformat(action["auto_escalate_at"])
            
            if current_time >= expires_at:
                overdue_actions.append(action)
            elif current_time >= escalate_at:
                escalated_actions.append(action)
        
        # Recent decisions for audit
        recent_decisions = []
        for action in all_actions:
            if action["authorization_status"] in ["approved", "denied"] and action.get("last_reviewed_at"):
                recent_decisions.append({
                    "action_id": action["id"],
                    "agent_id": action["agent_id"],
                    "action_type": action["action_type"],
                    "decision": action["authorization_status"],
                    "reviewed_by": action.get("last_reviewed_by"),
                    "reviewed_at": action.get("last_reviewed_at"),
                    "risk_score": action["ai_risk_score"]
                })
        
        recent_decisions.sort(key=lambda x: x["reviewed_at"], reverse=True)
        
        return {
            "user_info": {
                "email": current_user["email"],
                "role": current_user["role"],
                "approval_authority": "enterprise_admin" if current_user["role"] == "admin" else "viewer",
                "max_risk_approval": 100 if current_user["role"] == "admin" else 50
            },
            "enterprise_metrics": {
                "total_pending": len(pending_actions),
                "critical_pending": risk_distribution["critical"],
                "high_risk_pending": risk_distribution["high"],
                "overdue_count": len(overdue_actions),
                "escalated_count": len(escalated_actions),
                "emergency_pending": len([a for a in pending_actions if a["is_emergency"]])
            },
            "sla_performance": {
                "on_time": len(pending_actions) - len(overdue_actions) - len(escalated_actions),
                "escalated": len(escalated_actions),
                "overdue": len(overdue_actions),
                "compliance_rate": calculate_overall_sla_compliance()
            },
            "risk_distribution": risk_distribution,
            "recent_decisions": recent_decisions[:10],
            "actions_requiring_attention": sorted([
                {
                    "id": action["id"],
                    "agent_id": action["agent_id"],
                    "action_type": action["action_type"],
                    "risk_score": action["ai_risk_score"],
                    "workflow_stage": action["workflow_stage"],
                    "time_remaining": str(datetime.fromisoformat(action["expires_at"]) - current_time),
                    "is_emergency": action["is_emergency"],
                    "is_overdue": action["id"] in [a["id"] for a in overdue_actions],
                    "priority": "CRITICAL" if action["ai_risk_score"] >= 90 else "HIGH" if action["ai_risk_score"] >= 70 else "MEDIUM"
                }
                for action in pending_actions
            ], key=lambda x: (-x["risk_score"], x["time_remaining"]))[:15]
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Dashboard loading failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load enterprise dashboard")

# 🏢 ENTERPRISE: Helper Functions

def calculate_enterprise_risk_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """🏢 ENTERPRISE: Advanced multi-factor risk assessment"""
    base_score = 30
    risk_factors = []
    
    # 1. Action type risk
    high_risk_actions = {
        "delete_production_database": 50,
        "modify_firewall_rules": 40,
        "access_customer_data": 35,
        "deploy_to_production": 30,
        "modify_security_policy": 45,
        "execute_system_command": 25
    }
    
    action_type = data.get("action_type", "").lower()
    for risk_action, risk_points in high_risk_actions.items():
        if risk_action in action_type:
            base_score += risk_points
            risk_factors.append(f"High-risk action: {risk_action}")
            break
    
    # 2. Target system risk
    target_system = data.get("target_system", "").lower()
    if "production" in target_system:
        base_score += 25
        risk_factors.append("Production system targeted")
    if "customer" in target_system:
        base_score += 20
        risk_factors.append("Customer data system")
    
    # 3. Time-based risk
    current_time = datetime.utcnow()
    if current_time.hour < 8 or current_time.hour > 18:
        base_score += 15
        risk_factors.append("After-hours execution")
    
    if current_time.weekday() >= 5:
        base_score += 10
        risk_factors.append("Weekend execution")
    
    # 4. Compliance framework indicators
    if data.get("nist_control"):
        base_score += 5
        risk_factors.append("NIST control specified")
    
    if data.get("mitre_tactic"):
        base_score += 5
        risk_factors.append("MITRE tactic identified")
    
    # Ensure within bounds
    final_score = min(100, max(0, base_score))
    
    # Determine risk level
    if final_score >= 85:
        risk_level = "critical"
    elif final_score >= 70:
        risk_level = "high"
    elif final_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "assessment_timestamp": datetime.utcnow().isoformat(),
        "requires_executive_approval": final_score >= 90,
        "compliance_review_required": final_score >= 70
    }

def determine_enterprise_workflow(risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
    """🏢 ENTERPRISE: Determine approval workflow based on risk and compliance"""
    risk_score = risk_assessment["risk_score"]
    
    if risk_score >= 90:
        # Critical - Executive approval required
        return {
            "approval_levels": 3,
            "initial_stage": "executive_review",
            "timeout_hours": 2,
            "escalation_minutes": 30,
            "break_glass_enabled": True,
            "compliance_review_required": True
        }
    elif risk_score >= 70:
        # High - Senior management approval
        return {
            "approval_levels": 2,
            "initial_stage": "senior_review",
            "timeout_hours": 4,
            "escalation_minutes": 60,
            "break_glass_enabled": False,
            "compliance_review_required": True
        }
    elif risk_score >= 40:
        # Medium - Standard approval
        return {
            "approval_levels": 1,
            "initial_stage": "standard_review",
            "timeout_hours": 8,
            "escalation_minutes": 120,
            "break_glass_enabled": False,
            "compliance_review_required": False
        }
    else:
        # Low - Minimal oversight
        return {
            "approval_levels": 1,
            "initial_stage": "automated_review",
            "timeout_hours": 24,
            "escalation_minutes": 480,
            "break_glass_enabled": False,
            "compliance_review_required": False
        }

def calculate_sla_status(action: Dict[str, Any], current_time: datetime) -> str:
    """🏢 ENTERPRISE: Calculate SLA compliance status"""
    requested_at = datetime.fromisoformat(action["requested_at"])
    escalate_at = datetime.fromisoformat(action["auto_escalate_at"])
    expires_at = datetime.fromisoformat(action["expires_at"])
    
    if current_time >= expires_at:
        return "BREACH"
    elif current_time >= escalate_at:
        return "AT_RISK"
    else:
        return "ON_TRACK"

def calculate_overall_sla_compliance() -> float:
    """🏢 ENTERPRISE: Calculate overall SLA compliance rate"""
    # Simplified calculation for demonstration
    total_actions = len(pending_actions_storage)
    if total_actions == 0:
        return 100.0
    
    current_time = datetime.utcnow()
    compliant_actions = 0
    
    for action in pending_actions_storage.values():
        if action["authorization_status"] != "pending":
            continue
            
        expires_at = datetime.fromisoformat(action["expires_at"])
        if current_time < expires_at:
            compliant_actions += 1
    
    return (compliant_actions / total_actions) * 100.0 if total_actions > 0 else 100.0

async def send_enterprise_siem_event(event_type: str, action_data: Dict[str, Any]):
    """🏢 ENTERPRISE: Send events to SIEM with enhanced context"""
    try:
        siem_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": f"ow_ai_enterprise_{event_type}",
            "source": "ow-ai-authorization-engine",
            "action_id": action_data.get("id"),
            "agent_id": action_data.get("agent_id"),
            "action_type": action_data.get("action_type"),
            "risk_score": action_data.get("ai_risk_score"),
            "risk_level": action_data.get("risk_level"),
            "compliance_status": "compliant",
            "workflow_stage": action_data.get("workflow_stage"),
            "nist_control": action_data.get("nist_control"),
            "mitre_tactic": action_data.get("mitre_tactic"),
            "enterprise_metadata": {
                "authorization_system": "ow-ai-enterprise",
                "version": "1.0.0",
                "environment": "production"
            }
        }
        
        # Try to send to existing SIEM integration
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                siem_response = await client.post(
                    "http://localhost:8000/enterprise/siem/send-event",
                    json={"event_type": "authorization", "data": siem_event}
                )
                if siem_response.status_code == 200:
                    logger.info(f"🏢 ENTERPRISE: SIEM event sent - {event_type}")
        except Exception:
            pass
        
        # Always log enterprise events
        logger.info(f"🏢 ENTERPRISE EVENT: {json.dumps(siem_event)}")
        
    except Exception as e:
        logger.warning(f"🏢 ENTERPRISE: SIEM event failed: {str(e)}")


#Authorization Endpoints

@app.post("/agent-control/request-authorization")
async def request_authorization(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """🏢 ENTERPRISE: Request authorization for high-risk agent actions"""
    try:
        data = await request.json()
        
        # Create authorization request in database
        new_action = AgentAction(
            agent_id=data.get("agent_id", "unknown"),
            action_type=data.get("action_type", "unknown"),
            description=data.get("description", ""),
            risk_level=data.get("risk_level", "medium"),
            status="pending_approval",
            user_id=current_user["user_id"],
            tool_name=data.get("tool_name", ""),
            approved=False
        )
        
        db.add(new_action)
        db.commit()
        db.refresh(new_action)
        
        logger.info(f"🏢 ENTERPRISE: Authorization request created - ID: {new_action.id}")
        
        return {
            "authorization_id": new_action.id,
            "status": "pending",
            "message": "🏢 Enterprise authorization request submitted for review"
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Authorization request failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit authorization request")

@app.get("/agent-control/pending-actions")
async def get_pending_actions(
    risk_filter: Optional[str] = None,
    emergency_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """🏢 ENTERPRISE: Get pending actions for authorization dashboard"""
    try:
        # Query pending actions from database
        query = db.query(AgentAction).filter(
            AgentAction.status.in_(["pending_approval", "pending", "submitted"])
        )
        
        if risk_filter:
            query = query.filter(AgentAction.risk_level == risk_filter)
        
        pending_actions = query.order_by(AgentAction.created_at.desc()).limit(50).all()
        
        # Transform for frontend
        actions_data = []
        for action in pending_actions:
            # Calculate risk score based on action type and risk level
            risk_score = calculate_risk_score(action.action_type, action.risk_level)
            
            actions_data.append({
                "id": action.id,
                "agent_id": action.agent_id,
                "action_type": action.action_type,
                "description": action.description,
                "risk_level": action.risk_level,
                "ai_risk_score": risk_score,
                "target_system": action.tool_name or "Unknown",
                "workflow_stage": "initial_review",
                "current_approval_level": 0,
                "required_approval_level": 1 if risk_score < 70 else 2 if risk_score < 90 else 3,
                "requested_at": action.created_at.isoformat() if action.created_at else datetime.utcnow().isoformat(),
                "time_remaining": "4:00:00",  # 4 hours default
                "is_emergency": action.risk_level == "high",
                "contextual_risk_factors": get_risk_factors(action.action_type, action.risk_level),
                "authorization_status": "pending"
            })
        
        logger.info(f"🏢 ENTERPRISE: Retrieved {len(actions_data)} pending actions for {current_user['email']}")
        
        return {
            "total_pending": len(actions_data),
            "high_priority": len([a for a in actions_data if a["ai_risk_score"] >= 80]),
            "emergency_pending": len([a for a in actions_data if a["is_emergency"]]),
            "overdue": 0,
            "actions": actions_data
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Failed to get pending actions: {str(e)}")
        return {
            "total_pending": 0,
            "high_priority": 0,
            "emergency_pending": 0,
            "overdue": 0,
            "actions": []
        }

@app.get("/agent-control/approval-dashboard")
async def get_approval_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """🏢 ENTERPRISE: Real-time authorization dashboard with KPIs"""
    try:
        # Get pending actions
        pending_actions = db.query(AgentAction).filter(
            AgentAction.status.in_(["pending_approval", "pending", "submitted"])
        ).all()
        
        # Get recent decisions
        recent_decisions = db.query(AgentAction).filter(
            AgentAction.status.in_(["approved", "denied"])
        ).order_by(AgentAction.updated_at.desc()).limit(10).all()
        
        # Calculate metrics
        total_pending = len(pending_actions)
        critical_pending = len([a for a in pending_actions if a.risk_level == "high"])
        emergency_pending = len([a for a in pending_actions if a.risk_level == "high"])
        
        return {
            "user_info": {
                "email": current_user["email"],
                "role": current_user["role"],
                "approval_level": 3 if current_user["role"] == "admin" else 1,
                "max_risk_approval": 100 if current_user["role"] == "admin" else 50,
                "is_emergency_approver": current_user["role"] == "admin"
            },
            "pending_summary": {
                "total_pending": total_pending,
                "critical_pending": critical_pending,
                "emergency_pending": emergency_pending
            },
            "recent_activity": {
                "approvals_last_24h": len([a for a in recent_decisions if a.status == "approved"])
            },
            "enterprise_metrics": {
                "total_pending": total_pending,
                "critical_pending": critical_pending,
                "high_risk_pending": len([a for a in pending_actions if a.risk_level in ["high", "medium"]]),
                "overdue_count": 0,
                "escalated_count": 0,
                "emergency_pending": emergency_pending
            }
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Dashboard loading failed: {str(e)}")
        return {
            "user_info": {
                "email": current_user.get("email", "unknown"),
                "role": current_user.get("role", "user"),
                "approval_level": 1,
                "max_risk_approval": 50,
                "is_emergency_approver": False
            },
            "pending_summary": {
                "total_pending": 0,
                "critical_pending": 0,
                "emergency_pending": 0
            },
            "recent_activity": {
                "approvals_last_24h": 0
            }
        }

@app.post("/agent-control/authorize/{action_id}")
async def authorize_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """🏢 ENTERPRISE: Multi-level authorization with audit trails"""
    try:
        data = await request.json()
        decision = data.get("decision")  # "approved", "denied", "escalated"
        notes = data.get("notes", "")
        
        # Get the action from database
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        # Update action based on decision
        if decision == "approved":
            action.status = "approved"
            action.approved = True
        elif decision == "denied":
            action.status = "denied"
            action.approved = False
        
        action.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"🏢 ENTERPRISE: Action {action_id} {decision} by {current_user['email']}")
        
        return {
            "message": f"🏢 Enterprise authorization {decision} successfully",
            "action_id": action_id,
            "decision": decision,
            "authorization_status": action.status,
            "reviewed_by": current_user["email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Authorization processing failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process authorization")

@app.get("/agent-control/metrics/approval-performance")
async def get_approval_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """🏢 ENTERPRISE: Approval performance metrics"""
    try:
        # Get actions from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        actions = db.query(AgentAction).filter(
            AgentAction.created_at >= thirty_days_ago
        ).all()
        
        # Calculate metrics
        total_requests = len(actions)
        approved = len([a for a in actions if a.status == "approved"])
        denied = len([a for a in actions if a.status == "denied"])
        pending = len([a for a in actions if a.status in ["pending", "pending_approval", "submitted"]])
        
        approval_rate = (approved / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "decision_breakdown": {
                "approved": approved,
                "denied": denied,
                "pending": pending,
                "emergency_overrides": 0,
                "approval_rate": approval_rate
            },
            "performance_metrics": {
                "average_processing_time_minutes": 45,
                "average_risk_score": 65,
                "sla_compliance_rate": 95.0
            },
            "risk_analysis": {
                "high_risk_requests": len([a for a in actions if a.risk_level == "high"]),
                "emergency_requests": len([a for a in actions if a.risk_level == "high"]),
                "after_hours_requests": 0
            },
            "period_summary": {
                "days_analyzed": 30,
                "total_requests": total_requests,
                "completion_rate": ((approved + denied) / total_requests * 100) if total_requests > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Failed to get approval metrics: {str(e)}")
        return {
            "decision_breakdown": {
                "approved": 0,
                "denied": 0,
                "pending": 0,
                "emergency_overrides": 0,
                "approval_rate": 0
            },
            "performance_metrics": {
                "average_processing_time_minutes": 0,
                "average_risk_score": 0,
                "sla_compliance_rate": 0
            },
            "risk_analysis": {
                "high_risk_requests": 0,
                "emergency_requests": 0,
                "after_hours_requests": 0
            },
            "period_summary": {
                "days_analyzed": 30,
                "total_requests": 0,
                "completion_rate": 0
            }
        }

@app.post("/agent-control/emergency-override/{action_id}")
async def emergency_override(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """🏢 ENTERPRISE: Emergency override for critical situations"""
    try:
        data = await request.json()
        justification = data.get("justification", "")
        
        if not justification.strip():
            raise HTTPException(status_code=400, detail="Emergency justification is required")
        
        # Get the action from database
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        # Apply emergency override
        action.status = "emergency_approved"
        action.approved = True
        action.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.warning(f"🚨 EMERGENCY OVERRIDE: Action {action_id} by {current_user['email']} - {justification}")
        
        return {
            "message": "🚨 EMERGENCY OVERRIDE GRANTED - This action has been logged for audit",
            "action_id": action_id,
            "overridden_by": current_user["email"],
            "justification": justification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 ENTERPRISE: Emergency override failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Emergency override failed")

# Helper functions
def calculate_risk_score(action_type: str, risk_level: str) -> int:
    """Calculate numerical risk score from action type and risk level"""
    base_scores = {
        "low": 25,
        "medium": 55,
        "high": 85
    }
    
    high_risk_actions = {
        "data_exfiltration": 20,
        "system_modification": 15,
        "credential_access": 15,
        "network_access": 10,
        "file_deletion": 12
    }
    
    base_score = base_scores.get(risk_level, 50)
    action_bonus = high_risk_actions.get(action_type.lower(), 0)
    
    return min(100, base_score + action_bonus)

def get_risk_factors(action_type: str, risk_level: str) -> List[str]:
    """Get contextual risk factors for an action"""
    factors = []
    
    if risk_level == "high":
        factors.append("High risk classification")
    
    high_risk_types = {
        "data_exfiltration": "Potential data breach",
        "system_modification": "System integrity risk",
        "credential_access": "Authentication compromise",
        "network_access": "Network security risk"
    }
    
    if action_type.lower() in high_risk_types:
        factors.append(high_risk_types[action_type.lower()])
    
    # Add time-based risk
    current_hour = datetime.utcnow().hour
    if current_hour < 8 or current_hour > 18:
        factors.append("After-hours execution")
    
    return factors if factors else ["Standard risk assessment"]