from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction, Alert, Log
from schemas import AgentActionOut, AlertOut
from datetime import datetime
from fastapi.responses import JSONResponse
from typing import List

router = APIRouter()

@router.get("/agent-actions", response_model=List[AgentActionOut])
def list_agent_actions(db: Session = Depends(get_db)):
    actions = db.query(AgentAction).order_by(AgentAction.timestamp.desc()).all()
    return actions

@router.get("/agent-activity", response_model=List[AgentActionOut])
def get_agent_activity(db: Session = Depends(get_db)):
    actions = db.query(AgentAction).order_by(AgentAction.timestamp.desc()).limit(10).all()
    return actions

@router.get("/alerts", response_model=List[AlertOut])
def get_alerts(db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert, AgentAction)
        .join(AgentAction, Alert.agent_action_id == AgentAction.id)
        .order_by(Alert.timestamp.desc())
        .limit(10)
        .all()
    )
    return [
        AlertOut(
            id=a.id,
            timestamp=a.timestamp,
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            agent_id=aa.agent_id,
            tool_name=aa.tool_name,
            risk_level=aa.risk_level,
            mitre_tactic=aa.mitre_tactic,
            mitre_technique=aa.mitre_technique,
            nist_control=aa.nist_control,
            nist_description=aa.nist_description,
            recommendation=aa.recommendation,
        )
        for a, aa in alerts
    ]

@router.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(10).all()
    return logs

@router.post("/agent-activity")
def create_agent_action(action: dict, db: Session = Depends(get_db)):
    new_action = AgentAction(**action)
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    return new_action

@router.post("/alerts")
def create_alert(alert: dict, db: Session = Depends(get_db)):
    new_alert = Alert(**alert)
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

@router.post("/logs")
def create_log(log: dict, db: Session = Depends(get_db)):
    new_log = Log(**log)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@router.get("/agent-action/false-positive/{action_id}")
def mark_false_positive(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")

    action.is_false_positive = True
    action.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": f"Action {action_id} marked as false positive"}

@router.get("/agent-action/{action_id}")
def get_agent_action_status(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")
    return {"status": action.status}

@router.put("/agent-action/approve/{action_id}")
def approve_agent_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "approved"
    action.approved = True
    action.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": f"Action {action_id} approved"}

@router.put("/agent-action/reject/{action_id}")
def reject_agent_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "rejected"
    action.approved = False
    action.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": f"Action {action_id} rejected"}

@router.put("/agent-action/false-positive/{action_id}")
def mark_false_positive_put(action_id: int, db: Session = Depends(get_db)):
    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.is_false_positive = True
    db.commit()
    return {"message": f"Action {action_id} marked as false positive"}


@router.post("/debug/seed-agent-action")
def seed_test_action(db: Session = Depends(get_db)):
    from models import AgentAction
    from datetime import datetime

    action = AgentAction(
        agent_id="agent_test_001",
        tool_name="Tool-X",
        action_type="execute",
        description="Test high-risk agent action",
        timestamp=datetime.utcnow(),
        risk_level="high",
        mitre_tactic="TA0001",
        mitre_technique="T1003",
        nist_control="AC-6",
        nist_description="Least privilege",
        recommendation="Limit access privileges",
    )
    db.add(action)
    db.commit()
    return {"message": "✅ Test agent action added."}
