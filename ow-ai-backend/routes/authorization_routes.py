# routes/authorization_routes.py - COMPATIBLE VERSION WITHOUT AUTH DEPENDENCIES
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging

from database import get_db
from models import PendingAgentAction, User, Alert, AgentAction
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-control", tags=["authorization"])

# Enhanced Pydantic Models
class AuthorizationRequest(BaseModel):
    agent_id: str
    action_type: str
    description: str
    tool_name: Optional[str] = None
    target_system: Optional[str] = None
    risk_level: str
    risk_score: Optional[int] = None
    affected_resources: Optional[List[str]] = None
    action_payload: Optional[Dict[str, Any]] = None
    is_emergency: Optional[bool] = False
    emergency_justification: Optional[str] = None
    compliance_frameworks: Optional[List[str]] = None
    nist_control: Optional[str] = None
    mitre_tactic: Optional[str] = None

class ApprovalDecision(BaseModel):
    decision: str  # approved, denied, escalated, conditional_approved
    notes: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    approval_duration: Optional[int] = None
    escalate_to_level: Optional[int] = None

# ENHANCED: Risk Assessment Engine
class RiskAssessmentEngine:
    @staticmethod
    def calculate_comprehensive_risk(
        action_type: str, 
        target_system: str, 
        time_context: datetime, 
        agent_history: dict,
        affected_resources: List[str] = None
    ) -> Dict[str, Any]:
        """Advanced risk calculation with multiple factors"""
        
        base_risk = 30  # Base risk score
        risk_factors = []
        
        # 1. Action Type Risk
        high_risk_actions = [
            "delete_production_database", "modify_firewall_rules", 
            "access_customer_data", "execute_system_command",
            "modify_security_policy", "deploy_to_production"
        ]
        
        if action_type.lower() in [a.lower() for a in high_risk_actions]:
            base_risk += 40
            risk_factors.append("High-risk action type")
        
        # 2. Time-based Risk (after hours, weekends)
        if time_context.hour < 8 or time_context.hour > 18:
            base_risk += 15
            risk_factors.append("After-hours execution")
        
        if time_context.weekday() >= 5:  # Weekend
            base_risk += 10
            risk_factors.append("Weekend execution")
        
        # 3. Target System Risk
        critical_systems = ["production", "customer", "financial", "security"]
        if target_system and any(sys in target_system.lower() for sys in critical_systems):
            base_risk += 25
            risk_factors.append("Critical system targeted")
        
        # 4. Resource Impact
        if affected_resources and len(affected_resources) > 10:
            base_risk += 15
            risk_factors.append("Large resource impact")
        
        # 5. Agent Historical Behavior
        if agent_history.get("recent_failures", 0) > 2:
            base_risk += 20
            risk_factors.append("Recent agent failures")
        
        # Cap at 100
        final_risk = min(base_risk, 100)
        
        # Determine risk level
        if final_risk >= 80:
            risk_level = "critical"
        elif final_risk >= 60:
            risk_level = "high"
        elif final_risk >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": final_risk,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "assessment_timestamp": datetime.utcnow().isoformat(),
            "requires_escalation": final_risk >= 70
        }

# ENHANCED: Workflow Engine
class ApprovalWorkflowEngine:
    @staticmethod
    def determine_approval_workflow(risk_score: int, action_type: str, db: Session) -> Dict[str, Any]:
        """Determine the appropriate approval workflow based on risk and rules"""
        
        # Default workflow configuration
        workflow = {
            "approval_levels": 1,
            "required_approvers_per_level": {1: 1},
            "escalation_timeout": 60,
            "auto_deny_timeout": 1440,
            "allows_emergency": True,
            "break_glass_enabled": False
        }
        
        # Risk-based workflow determination
        if risk_score >= 90:
            # Critical - Requires executive approval
            workflow.update({
                "approval_levels": 3,
                "required_approvers_per_level": {1: 1, 2: 1, 3: 1},
                "escalation_timeout": 30,
                "break_glass_enabled": True
            })
        elif risk_score >= 70:
            # High - Requires senior approval
            workflow.update({
                "approval_levels": 2,
                "required_approvers_per_level": {1: 1, 2: 1},
                "escalation_timeout": 45
            })
        elif risk_score >= 50:
            # Medium - Requires standard approval
            workflow.update({
                "approval_levels": 1,
                "required_approvers_per_level": {1: 2}  # Two approvers
            })
        
        # Action-specific overrides
        if "production" in action_type.lower() or "delete" in action_type.lower():
            workflow["approval_levels"] = max(workflow["approval_levels"], 2)
        
        return workflow

# MAIN ENDPOINTS

@router.post("/request-authorization")
async def request_authorization(
    request: AuthorizationRequest,
    db: Session = Depends(get_db)
):
    """Enhanced authorization request with sophisticated workflow routing"""
    try:
        logger.info(f"Authorization request from agent {request.agent_id} for {request.action_type}")
        
        # 1. Enhanced Risk Assessment
        risk_assessment = RiskAssessmentEngine.calculate_comprehensive_risk(
            action_type=request.action_type,
            target_system=request.target_system or "unknown",
            time_context=datetime.utcnow(),
            agent_history={},  # TODO: Fetch real agent history
            affected_resources=request.affected_resources or []
        )
        
        # 2. Determine Approval Workflow
        workflow_config = ApprovalWorkflowEngine.determine_approval_workflow(
            risk_score=risk_assessment["risk_score"],
            action_type=request.action_type,
            db=db
        )
        
        # 3. Create Enhanced Pending Action
        pending_action = PendingAgentAction(
            # Basic info
            agent_id=request.agent_id,
            action_type=request.action_type,
            description=request.description,
            tool_name=request.tool_name,
            target_system=request.target_system,
            
            # Enhanced risk data
            risk_level=risk_assessment["risk_level"],
            ai_risk_score=risk_assessment["risk_score"],
            contextual_risk_factors=risk_assessment["risk_factors"],
            
            # Workflow configuration
            required_approval_level=workflow_config["approval_levels"],
            current_approval_level=0,
            workflow_stage="initial",
            
            # Timing
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=workflow_config["auto_deny_timeout"]),
            
            # Data storage
            action_payload=json.dumps(request.action_payload) if request.action_payload else None,
            affected_resources=request.affected_resources,
            
            # Emergency handling
            is_emergency=request.is_emergency,
            emergency_justification=request.emergency_justification,
            
            # Compliance
            nist_control=request.nist_control,
            mitre_tactic=request.mitre_tactic,
            compliance_frameworks=request.compliance_frameworks or [],
            
            # Audit trail initialization
            audit_trail=[{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "authorization_requested",
                "risk_assessment": risk_assessment,
                "workflow_config": workflow_config
            }]
        )
        
        # 4. Emergency Fast-Track
        if request.is_emergency and risk_assessment["risk_score"] < 95:
            pending_action.auto_approve_at = datetime.utcnow() + timedelta(minutes=15)
            pending_action.workflow_stage = "emergency_queue"
        
        # 5. Save to database
        db.add(pending_action)
        db.commit()
        db.refresh(pending_action)
        
        # 6. Create Alert for High-Risk Actions
        if risk_assessment["risk_score"] >= 70:
            alert = Alert(
                pending_action_id=pending_action.id,
                alert_type="high_risk_authorization_request",
                severity="high" if risk_assessment["risk_score"] < 90 else "critical",
                message=f"High-risk authorization request: {request.action_type} by {request.agent_id}",
                auto_escalate_minutes=30 if risk_assessment["risk_score"] >= 90 else 60
            )
            db.add(alert)
            db.commit()
        
        logger.info(f"Authorization request created with ID {pending_action.id}, risk score: {risk_assessment['risk_score']}")
        
        return {
            "status": "success",
            "authorization_id": pending_action.id,
            "risk_assessment": risk_assessment,
            "workflow_stage": pending_action.workflow_stage,
            "required_approval_level": pending_action.required_approval_level,
            "estimated_approval_time": f"{workflow_config['escalation_timeout'] * workflow_config['approval_levels']} minutes",
            "message": "Authorization request submitted for review"
        }
        
    except Exception as e:
        logger.error(f"Failed to request authorization: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit authorization request"
        )

@router.get("/pending-actions")
async def get_pending_actions(
    status_filter: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get pending authorization actions with enhanced filtering"""
    try:
        query = db.query(PendingAgentAction).filter(
            PendingAgentAction.authorization_status == "pending"
        )
        
        if status_filter:
            query = query.filter(PendingAgentAction.workflow_stage == status_filter)
        
        if risk_level:
            query = query.filter(PendingAgentAction.risk_level == risk_level)
        
        pending_actions = query.order_by(
            PendingAgentAction.ai_risk_score.desc(),
            PendingAgentAction.requested_at.desc()
        ).limit(limit).all()
        
        # Enhanced response with workflow context
        enhanced_actions = []
        for action in pending_actions:
            enhanced_actions.append({
                "id": action.id,
                "agent_id": action.agent_id,
                "action_type": action.action_type,
                "description": action.description,
                "risk_level": action.risk_level,
                "ai_risk_score": action.ai_risk_score,
                "workflow_stage": action.workflow_stage,
                "required_approval_level": action.required_approval_level,
                "current_approval_level": action.current_approval_level,
                "requested_at": action.requested_at,
                "expires_at": action.expires_at,
                "is_emergency": action.is_emergency,
                "target_system": action.target_system,
                "contextual_risk_factors": action.contextual_risk_factors,
                "time_remaining": str(action.expires_at - datetime.utcnow()) if action.expires_at else None
            })
        
        return enhanced_actions
        
    except Exception as e:
        logger.error(f"Failed to fetch pending actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending actions"
        )

@router.post("/authorize/{action_id}")
async def process_authorization(
    action_id: int,
    decision: ApprovalDecision,
    db: Session = Depends(get_db)
):
    """Enhanced authorization processing with multi-level approval support"""
    try:
        # Get the pending action
        action = db.query(PendingAgentAction).filter(PendingAgentAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        # Process decision based on type
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_email": "system_user",  # Default for now
            "decision": decision.decision,
            "notes": decision.notes,
            "approval_level": 1  # Default level
        }
        
        if decision.decision == "approved":
            if action.current_approval_level + 1 >= action.required_approval_level:
                # Final approval
                action.authorization_status = "approved"
                action.reviewed_at = datetime.utcnow()
                audit_entry["event"] = "final_approval"
            else:
                # Intermediate approval - escalate to next level
                action.current_approval_level += 1
                action.workflow_stage = f"level_{action.current_approval_level + 1}"
                audit_entry["event"] = "level_approval"
                
        elif decision.decision == "conditional_approved":
            action.authorization_status = "conditional_approved"
            action.conditional_approval = True
            action.conditions = decision.conditions
            action.approval_duration = decision.approval_duration
            audit_entry["event"] = "conditional_approval"
            audit_entry["conditions"] = decision.conditions
            
        elif decision.decision == "denied":
            action.authorization_status = "denied"
            action.reviewed_at = datetime.utcnow()
            audit_entry["event"] = "denial"
            
        elif decision.decision == "escalated":
            action.workflow_stage = f"level_{decision.escalate_to_level}"
            action.current_approval_level = decision.escalate_to_level - 1
            audit_entry["event"] = "escalation"
            audit_entry["escalated_to_level"] = decision.escalate_to_level
        
        # Update audit trail
        current_trail = action.audit_trail or []
        current_trail.append(audit_entry)
        action.audit_trail = current_trail
        action.review_notes = decision.notes
        
        db.commit()
        
        logger.info(f"Authorization {action_id} {decision.decision} processed")
        
        return {
            "status": "success",
            "action_id": action_id,
            "decision": decision.decision,
            "new_status": action.authorization_status,
            "workflow_stage": action.workflow_stage,
            "message": f"Authorization {decision.decision} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process authorization {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process authorization"
        )

@router.post("/emergency-override/{action_id}")
async def emergency_override(
    action_id: int,
    justification: str,
    db: Session = Depends(get_db)
):
    """Emergency override for critical situations"""
    try:
        action = db.query(PendingAgentAction).filter(PendingAgentAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Authorization request not found")
        
        # Log emergency override
        emergency_audit = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "emergency_override",
            "user_email": "emergency_user",  # Default for now
            "justification": justification,
            "original_risk_score": action.ai_risk_score,
            "original_workflow_stage": action.workflow_stage
        }
        
        # Apply emergency override
        action.authorization_status = "emergency_approved"
        action.break_glass_used = True
        action.emergency_justification = justification
        action.reviewed_at = datetime.utcnow()
        
        # Update audit trail
        current_trail = action.audit_trail or []
        current_trail.append(emergency_audit)
        action.audit_trail = current_trail
        
        # Create high-priority alert for emergency override
        alert = Alert(
            pending_action_id=action.id,
            alert_type="emergency_override_used",
            severity="critical",
            message=f"EMERGENCY OVERRIDE: {action.action_type} by {action.agent_id}",
            auto_escalate_minutes=5  # Immediate escalation
        )
        db.add(alert)
        
        db.commit()
        
        logger.warning(f"EMERGENCY OVERRIDE used for action {action_id}: {justification}")
        
        return {
            "status": "success",
            "action_id": action_id,
            "decision": "emergency_approved",
            "justification": justification,
            "warning": "Emergency override logged and will be audited",
            "message": "Emergency authorization granted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency override failed for action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Emergency override failed"
        )

@router.get("/approval-dashboard")
async def get_approval_dashboard(
    db: Session = Depends(get_db)
):
    """Enhanced dashboard with workflow metrics and real-time stats"""
    try:
        # Get all pending actions
        pending_actions = db.query(PendingAgentAction).filter(
            PendingAgentAction.authorization_status == "pending"
        ).all()
        
        # Calculate dashboard metrics
        total_pending = len(pending_actions)
        critical_pending = len([a for a in pending_actions if a.ai_risk_score >= 80])
        emergency_pending = len([a for a in pending_actions if a.is_emergency])
        overdue_pending = len([a for a in pending_actions if a.expires_at and a.expires_at < datetime.utcnow()])
        
        # Risk distribution
        risk_distribution = {
            "critical": len([a for a in pending_actions if a.ai_risk_score >= 80]),
            "high": len([a for a in pending_actions if 60 <= a.ai_risk_score < 80]),
            "medium": len([a for a in pending_actions if 40 <= a.ai_risk_score < 60]),
            "low": len([a for a in pending_actions if a.ai_risk_score < 40])
        }
        
        # Workflow stage distribution
        workflow_stages = {}
        for action in pending_actions:
            stage = action.workflow_stage
            workflow_stages[stage] = workflow_stages.get(stage, 0) + 1
        
        return {
            "user_info": {
                "email": "system_user",
                "approval_level": 3,  # Max level for now
                "max_risk_approval": 100,  # Max approval authority
                "is_emergency_approver": True
            },
            "pending_summary": {
                "total_pending": total_pending,
                "critical_pending": critical_pending,
                "emergency_pending": emergency_pending,
                "overdue_pending": overdue_pending
            },
            "risk_distribution": risk_distribution,
            "workflow_stages": workflow_stages,
            "recent_activity": {
                "approvals_last_24h": 0  # Default for now
            },
            "actions_requiring_attention": [
                {
                    "id": action.id,
                    "agent_id": action.agent_id,
                    "action_type": action.action_type,
                    "risk_score": action.ai_risk_score,
                    "workflow_stage": action.workflow_stage,
                    "time_remaining": str(action.expires_at - datetime.utcnow()) if action.expires_at else None,
                    "is_emergency": action.is_emergency,
                    "is_overdue": action.expires_at and action.expires_at < datetime.utcnow()
                }
                for action in sorted(pending_actions, key=lambda x: (-x.ai_risk_score, x.requested_at))[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get approval dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard"
        )

@router.get("/metrics/approval-performance")
async def get_approval_metrics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get approval performance metrics and trends"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all actions from the specified period
        actions = db.query(PendingAgentAction).filter(
            PendingAgentAction.requested_at >= start_date
        ).all()
        
        if not actions:
            return {"message": "No data available for the specified period"}
        
        # Calculate metrics
        total_requests = len(actions)
        approved = len([a for a in actions if a.authorization_status == "approved"])
        denied = len([a for a in actions if a.authorization_status == "denied"])
        emergency_overrides = len([a for a in actions if a.break_glass_used])
        pending = len([a for a in actions if a.authorization_status == "pending"])
        
        # Average processing time (for completed actions)
        completed_actions = [a for a in actions if a.reviewed_at and a.authorization_status != "pending"]
        avg_processing_time = None
        if completed_actions:
            processing_times = [(a.reviewed_at - a.requested_at).total_seconds() / 60 for a in completed_actions]
            avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Risk score distribution
        risk_scores = [a.ai_risk_score for a in actions if a.ai_risk_score]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # SLA compliance (actions completed within expected timeframes)
        sla_compliant = 0
        for action in completed_actions:
            processing_minutes = (action.reviewed_at - action.requested_at).total_seconds() / 60
            expected_time = 60  # Base expectation: 1 hour
            
            if action.ai_risk_score >= 80:
                expected_time = 30  # Critical: 30 minutes
            elif action.ai_risk_score >= 60:
                expected_time = 45  # High: 45 minutes
            
            if processing_minutes <= expected_time:
                sla_compliant += 1
        
        sla_compliance_rate = (sla_compliant / len(completed_actions)) * 100 if completed_actions else 0
        
        return {
            "period_summary": {
                "days_analyzed": days,
                "total_requests": total_requests,
                "completion_rate": ((approved + denied) / total_requests) * 100 if total_requests > 0 else 0
            },
            "decision_breakdown": {
                "approved": approved,
                "denied": denied,
                "emergency_overrides": emergency_overrides,
                "pending": pending,
                "approval_rate": (approved / total_requests) * 100 if total_requests > 0 else 0
            },
            "performance_metrics": {
                "average_processing_time_minutes": round(avg_processing_time, 2) if avg_processing_time else None,
                "average_risk_score": round(avg_risk_score, 2),
                "sla_compliance_rate": round(sla_compliance_rate, 2)
            },
            "risk_analysis": {
                "high_risk_requests": len([a for a in actions if a.ai_risk_score >= 70]),
                "emergency_requests": len([a for a in actions if a.is_emergency]),
                "after_hours_requests": len([a for a in actions if a.requested_at.hour < 8 or a.requested_at.hour > 18])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get approval metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval metrics"
        )