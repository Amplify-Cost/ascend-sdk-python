from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Alert, AgentAction
from schemas import AlertOut
from dependencies import get_current_user, require_csrf  
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ✅ Enriched /alerts endpoint used by frontend
@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get all alerts with enriched agent action data"""
    try:
        query = (
            db.query(Alert, AgentAction)
            .join(AgentAction, Alert.agent_action_id == AgentAction.id)
            .order_by(Alert.timestamp.desc())
            .limit(50)
            .all()
        )

        enriched_alerts = []
        for alert, action in query:
            enriched_alerts.append({
                "id": alert.id,
                "timestamp": alert.timestamp,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "agent_id": action.agent_id,
                "tool_name": action.tool_name,
                "risk_level": action.risk_level,
                "mitre_tactic": action.mitre_tactic,
                "mitre_technique": action.mitre_technique,
                "nist_control": action.nist_control,
                "nist_description": action.nist_description,
                "recommendation": action.recommendation,
                "status": getattr(alert, 'status', 'new')  # Add status field
            })
        
        logger.info(f"Retrieved {len(enriched_alerts)} alerts for user {user.get('email')}")
        return enriched_alerts
        
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {str(e)}")
        # Return empty array instead of crashing
        return []

@router.get("/alerts/count")
def alert_count(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get total count of alerts"""
    try:
        count = db.query(Alert).count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Failed to count alerts: {str(e)}")
        return {"count": 0}

@router.patch("/alerts/{alert_id}")
async def update_alert_status(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user), _=Depends(require_csrf)
):
    """Update alert status (admin only)"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update alerts")

    try:
        data = await request.json()
        status = data.get("status")
        if status not in ["new", "acknowledged", "resolved", "in_review"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Add status field if it doesn't exist
        if not hasattr(alert, 'status'):
            # We'll handle this in the database migration
            pass
        else:
            alert.status = status
        
        db.commit()
        logger.info(f"Alert {alert_id} status updated to {status} by {user['email']}")
        return {"message": f"Alert {alert_id} marked as {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update alert status")

# ✅ NEW: Add endpoint to create test alerts
@router.post("/alerts/create-test-data")
async def create_test_alerts(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user), _=Depends(require_csrf)
):
    """Create test alert data (admin only)"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create test data")
    
    try:
        # First, get or create some agent actions
        agent_actions = db.query(AgentAction).limit(5).all()
        
        if not agent_actions:
            # Create test agent actions first
            from datetime import datetime, UTC
            test_actions = [
                AgentAction(
                    agent_id="agent-076",
                    action_type="data_exfiltration",
                    description="Suspicious data transfer detected",
                    tool_name="file_transfer",
                    risk_level="high",
                    nist_control="SI-4",
                    nist_description="Information System Monitoring",
                    mitre_tactic="Exfiltration",
                    mitre_technique="T1041",
                    recommendation="Investigate immediately",
                    status="pending",
                    timestamp=datetime.now(UTC)
                ),
                AgentAction(
                    agent_id="agent-001",
                    action_type="authentication_failure",
                    description="Multiple failed login attempts",
                    tool_name="login_monitor",
                    risk_level="medium",
                    nist_control="AC-7",
                    nist_description="Unsuccessful Login Attempts",
                    mitre_tactic="Initial Access",
                    mitre_technique="T1078",
                    recommendation="Monitor user account",
                    status="pending",
                    timestamp=datetime.now(UTC)
                )
            ]
            
            for action in test_actions:
                db.add(action)
            db.commit()
            agent_actions = test_actions
        
        # Now create alerts linked to these actions
        test_alerts = []
        for i, action in enumerate(agent_actions[:2]):  # Create 2 test alerts
            alert = Alert(
    agent_action_id=action.id,
    alert_type="High Risk Agent Action",
    severity="high",
    message=f"Enterprise Alert: Agent {data['agent_id']} performed high-risk action: {data['action_type']}",
    timestamp=timestamp
)
            db.add(alert)
            test_alerts.append(alert)
        
        db.commit()
        
        logger.info(f"Created {len(test_alerts)} test alerts")
        return {
            "message": f"✅ Created {len(test_alerts)} test alerts",
            "alerts_created": len(test_alerts),
            "agent_actions_used": len(agent_actions)
        }
        
    except Exception as e:
        logger.error(f"Failed to create test alerts: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test data: {str(e)}")