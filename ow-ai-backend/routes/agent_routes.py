from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction, LogAuditTrail, Alert
from dependencies import get_current_user, require_admin
from schemas import AgentActionOut, AgentActionCreate
from datetime import datetime, UTC
from llm_utils import generate_summary, generate_smart_rule
from enrichment import evaluate_action_enrichment
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agent Actions"])

@router.post("/agent-action", response_model=AgentActionOut)
async def create_agent_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit a new agent action for security review"""
    try:
        data = await request.json()

        # Validate required fields
        required_fields = ["agent_id", "action_type", "description", "tool_name"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Parse timestamp
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp, UTC)
                else:
                    timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now(UTC)
        else:
            timestamp = datetime.now(UTC)

        # Generate AI summary (with fallback)
        try:
            summary = generate_summary(
                agent_id=data["agent_id"],
                action_type=data["action_type"],
                description=data["description"]
            )
        except Exception as e:
            logger.warning(f"OpenAI summary generation failed: {e}")
            summary = f"[FALLBACK] Agent '{data['agent_id']}' performed '{data['action_type']}' action."

        # Security enrichment (with fallback)
        try:
            enrichment = evaluate_action_enrichment(
                action_type=data["action_type"],
                description=data["description"]
            )
        except Exception as e:
            logger.warning(f"Security enrichment failed: {e}")
            enrichment = {
                "risk_level": "unknown",
                "mitre_tactic": "N/A",
                "mitre_technique": "N/A", 
                "nist_control": "N/A",
                "nist_description": "Manual review required",
                "recommendation": "Review this action manually for security implications."
            }

        # Create agent action record
        action = AgentAction(
            user_id=current_user["user_id"],
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            description=data["description"],
            tool_name=data["tool_name"],
            timestamp=timestamp,
            risk_level=enrichment["risk_level"],
            mitre_tactic=enrichment["mitre_tactic"],
            mitre_technique=enrichment["mitre_technique"],
            nist_control=enrichment["nist_control"],
            nist_description=enrichment["nist_description"],
            recommendation=enrichment["recommendation"],
            summary=summary,
            status="pending"
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        # Create alert if high risk
        if enrichment["risk_level"] == "high":
            alert = Alert(
                agent_action_id=action.id,
                alert_type="High Risk Agent Action",
                severity="high",
                message=f"Agent {data['agent_id']} performed high-risk action: {data['action_type']}",
                created_at=timestamp,
                timestamp=timestamp
            )
            db.add(alert)
            db.commit()

        logger.info(f"Agent action created: {action.id} (risk: {enrichment['risk_level']})")
        return action

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent action creation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent action"
        )

@router.get("/agent-actions", response_model=List[AgentActionOut])
def list_agent_actions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 100,
    skip: int = 0
):
    """List agent actions with pagination"""
    try:
        actions = (
            db.query(AgentAction)
            .order_by(AgentAction.timestamp.desc())
            .offset(skip)
            .limit(min(limit, 100))  # Max 100 items per request
            .all()
        )
        return actions
    except Exception as e:
        logger.error(f"Failed to list agent actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent actions"
        )

@router.get("/agent-activity", response_model=List[AgentActionOut])
def get_agent_activity(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    risk: str = None
):
    """Get recent agent activity, optionally filtered by risk level"""
    try:
        query = db.query(AgentAction).order_by(AgentAction.timestamp.desc())
        
        if risk and risk != "all":
            query = query.filter(AgentAction.risk_level == risk)
            
        actions = query.limit(50).all()
        return actions
    except Exception as e:
        logger.error(f"Failed to get agent activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent activity"
        )

# Admin-only endpoints
@router.post("/agent-action/{action_id}/approve")
def approve_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Approve an agent action (admin only)"""
    try:
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        action.status = "approved"
        action.approved = True
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # Create audit trail
        audit_log = LogAuditTrail(
            action_id=action_id,
            decision="approved",
            reviewed_by=admin_user["email"],
            timestamp=datetime.now(UTC)
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"Action {action_id} approved by {admin_user['email']}")
        return {"message": "Action approved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve action"
        )

@router.post("/agent-action/{action_id}/reject")
def reject_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Reject an agent action (admin only)"""
    try:
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        action.status = "rejected"
        action.approved = False
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # Create audit trail
        audit_log = LogAuditTrail(
            action_id=action_id,
            decision="rejected",
            reviewed_by=admin_user["email"],
            timestamp=datetime.now(UTC)
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"Action {action_id} rejected by {admin_user['email']}")
        return {"message": "Action rejected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject action"
        )

@router.post("/agent-action/{action_id}/false-positive")
def mark_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Mark an agent action as false positive (admin only)"""
    try:
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        action.status = "false_positive"
        action.is_false_positive = True
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # Create audit trail
        audit_log = LogAuditTrail(
            action_id=action_id,
            decision="false_positive",
            reviewed_by=admin_user["email"],
            timestamp=datetime.now(UTC)
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"Action {action_id} marked as false positive by {admin_user['email']}")
        return {"message": "Action marked as false positive"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark action {action_id} as false positive: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark as false positive"
        )

@router.get("/audit-trail")
def get_audit_trail(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get audit trail (admin only)"""
    try:
        logs = (
            db.query(LogAuditTrail)
            .order_by(LogAuditTrail.timestamp.desc())
            .limit(100)
            .all()
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get audit trail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit trail"
        )
