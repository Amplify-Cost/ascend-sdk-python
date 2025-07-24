# routes/authorization_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import PendingAgentAction
from dependencies import get_current_user, require_admin
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-control", tags=["authorization"])

@router.get("/pending-actions")
async def get_pending_actions(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Get all pending agent actions requiring authorization"""
    try:
        pending_actions = (
            db.query(PendingAgentAction)
            .filter(PendingAgentAction.authorization_status == "pending")
            .order_by(PendingAgentAction.requested_at.desc())
            .limit(50)
            .all()
        )
        
        return [{
            "id": action.id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "description": action.description,
            "risk_level": action.risk_level,
            "ai_risk_score": action.ai_risk_score,
            "requested_at": action.requested_at,
            "expires_at": action.expires_at,
            "nist_control": action.nist_control,
            "mitre_tactic": action.mitre_tactic
        } for action in pending_actions]
        
    except Exception as e:
        logger.error(f"Failed to get pending actions: {str(e)}")
        return []

@router.post("/request-authorization")
async def request_authorization(
    request: Request,
    db: Session = Depends(get_db)
):
    """Request authorization for an agent action"""
    try:
        data = await request.json()
        
        # Create pending action record
        pending_action = PendingAgentAction(
            agent_id=data.get("agent_id", "unknown"),
            action_type=data.get("action_type", "unknown"),
            description=data.get("description", ""),
            risk_level=data.get("risk_level", "medium"),
            authorization_status="pending",
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ai_risk_score=data.get("risk_score", 50)
        )
        
        db.add(pending_action)
        db.commit()
        db.refresh(pending_action)
        
        logger.info(f"Authorization requested for {data.get('agent_id')}/{data.get('action_type')}")
        
        return {
            "id": pending_action.id,
            "status": "pending",
            "message": "Authorization request submitted"
        }
        
    except Exception as e:
        logger.error(f"Failed to request authorization: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit authorization request")

@router.post("/authorize/{action_id}")
async def authorize_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Approve or deny a pending action"""
    try:
        data = await request.json()
        decision = data.get("decision")  # "approved" or "denied"
        notes = data.get("notes", "")
        
        if decision not in ["approved", "denied"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'denied'")
        
        pending_action = db.query(PendingAgentAction).filter(
            PendingAgentAction.id == action_id
        ).first()
        
        if not pending_action:
            raise HTTPException(status_code=404, detail="Pending action not found")
        
        # Update the pending action
        pending_action.authorization_status = decision
        pending_action.reviewed_by = admin_user["email"]
        pending_action.reviewed_at = datetime.utcnow()
        pending_action.review_notes = notes
        
        db.commit()
        
        logger.info(f"Action {action_id} {decision} by {admin_user['email']}")
        
        return {
            "message": f"Action {decision} successfully",
            "action_id": action_id,
            "decision": decision
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to authorize action: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process authorization")