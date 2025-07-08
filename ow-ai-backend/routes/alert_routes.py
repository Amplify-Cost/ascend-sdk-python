from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Alert, AgentAction
from schemas import AlertOut
from dependencies import verify_token

router = APIRouter()

# ✅ Enriched /alerts endpoint used by frontend
@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
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
            "recommendation": action.recommendation
        })
    return enriched_alerts

@router.get("/alerts/count")
def alert_count(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    count = db.query(Alert).count()
    return {"count": count}

@router.patch("/alerts/{alert_id}")
async def update_alert_status(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update alerts")

    data = await request.json()
    status = data.get("status")
    if status not in ["acknowledged", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = status
    db.commit()
    return {"message": f"Alert {alert_id} marked as {status}"}
