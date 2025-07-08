from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction, LogAuditTrail
from dependencies import verify_token
from datetime import datetime, UTC
from llm_utils import generate_summary, generate_smart_rule
from .enrichment import evaluate_action_enrichment
from schemas import AgentActionOut
from typing import List

router = APIRouter()

@router.post("/agent-action", response_model=AgentActionOut)
async def receive_agent_action(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    data = await request.json()

    required_fields = ["agent_id", "action_type", "description", "tool_name", "timestamp"]
    raise_if_missing = [field for field in required_fields if field not in data]
    if raise_if_missing:
        raise HTTPException(status_code=422, detail=f"Missing fields: {raise_if_missing}")

    # ✅ Generate summary (fallback if OpenAI quota exceeded)
    try:
        summary = generate_summary(
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            description=data["description"]
        )
    except Exception as e:
        print(f"OpenAI summary generation failed: {e}")
        summary = f"Agent {data['agent_id']} performed '{data['action_type']}' action."

    # ✅ Try enrichment logic — fallback if enrichment fails
    try:
        enrichment = evaluate_action_enrichment(
            action_type=data["action_type"],
            description=data["description"]
        )
    except Exception as e:
        print(f"⚠️ Enrichment failed: {e}")
        enrichment = {
            "risk_level": "unknown",
            "mitre_tactic": "N/A",
            "mitre_technique": "N/A",
            "nist_control": "N/A",
            "nist_description": "N/A",
            "recommendation": "Manual review required."
        }

    # ✅ Create and store agent action
    try:
        action = AgentAction(
            user_id=user["user_id"],
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            description=data["description"],
            tool_name=data["tool_name"],
            risk_level=enrichment["risk_level"],
            mitre_tactic=enrichment["mitre_tactic"],
            mitre_technique=enrichment["mitre_technique"],
            nist_control=enrichment["nist_control"],
            nist_description=enrichment["nist_description"],
            recommendation=enrichment["recommendation"],
            summary=summary,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status="pending"
        )

        db.add(action)
        db.commit()
        db.refresh(action)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error saving action: {str(e)}")

    # ✅ Try to generate smart rule — ignore if OpenAI fails
    try:
        smart_rule = generate_smart_rule(data["agent_id"], data["action_type"], data["description"])
        db.execute(
            """
            INSERT INTO smart_rules (id, agent_id, action_type, description, condition, action, risk_level, recommendation)
            VALUES (:id, :agent_id, :action_type, :description, :condition, :action, :risk_level, :recommendation)
            ON CONFLICT (id) DO NOTHING
            """,
            smart_rule
        )
        db.commit()
    except Exception as e:
        print(f"Smart rule generation failed: {e}")

    return action

@router.get("/agent-actions", response_model=List[AgentActionOut])
def get_all_agent_actions(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    return db.query(AgentAction).order_by(AgentAction.timestamp.desc()).limit(100).all()

@router.post("/agent-action/{action_id}/approve")
def approve_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")

    action.status = "approved"
    action.reviewed_by = user["email"]
    action.reviewed_at = datetime.now(UTC)

    db.add(LogAuditTrail(
        action_id=action_id,
        decision="approved",
        reviewed_by=user["email"],
        timestamp=datetime.now(UTC)
    ))

    db.commit()
    return {"message": "✅ Action approved"}

@router.post("/agent-action/{action_id}/reject")
def reject_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")

    action.status = "rejected"
    action.reviewed_by = user["email"]
    action.reviewed_at = datetime.now(UTC)

    db.add(LogAuditTrail(
        action_id=action_id,
        decision="rejected",
        reviewed_by=user["email"],
        timestamp=datetime.now(UTC)
    ))

    db.commit()
    return {"message": "✅ Action rejected"}

@router.post("/agent-action/{action_id}/false-positive")
def mark_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    action = db.query(AgentAction).filter(AgentAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")

    action.status = "false_positive"
    action.is_false_positive = True
    action.reviewed_by = user["email"]
    action.reviewed_at = datetime.now(UTC)

    db.add(LogAuditTrail(
        action_id=action_id,
        decision="false_positive",
        reviewed_by=user["email"],
        timestamp=datetime.now(UTC)
    ))

    db.commit()
    return {"message": "✅ Marked as false positive"}

@router.get("/audit-trail")
def get_audit_trail(
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return db.query(LogAuditTrail).order_by(LogAuditTrail.timestamp.desc()).limit(100).all()

@router.post("/alerts/summary")
def generate_alert_summary(payload: dict):
    alerts = payload.get("alerts", [])

    if not alerts:
        return {"summary": "No alerts to summarize."}

    high_risk = [a for a in alerts if "high" in a.lower()]
    medium_risk = [a for a in alerts if "medium" in a.lower()]
    low_risk = [a for a in alerts if "low" in a.lower()]

    summary = f"""
🧠 Alert Summary:
- Total alerts: {len(alerts)}
- High risk: {len(high_risk)}
- Medium risk: {len(medium_risk)}
- Low risk: {len(low_risk)}

Focus first on high-risk alerts involving port scans or script execution.
"""
    return {"summary": summary.strip()}
