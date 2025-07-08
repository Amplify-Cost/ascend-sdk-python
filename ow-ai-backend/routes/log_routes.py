from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction
from dependencies import verify_token
from sqlalchemy import func

router = APIRouter()

@router.get("/logs")
def get_logs(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    return db.query(AgentAction).order_by(AgentAction.timestamp.desc()).limit(100).all()

@router.get("/analytics/trends")
def get_trends(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    high_risk_daily = (
        db.query(
            func.date(func.datetime(AgentAction.timestamp, 'unixepoch')).label("date"),
            func.count().label("count")
        )
        .filter(AgentAction.risk_level == "high")
        .group_by("date")
        .all()
    )

    top_agents = (
        db.query(AgentAction.agent_id, func.count().label("count"))
        .group_by(AgentAction.agent_id)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    top_tools = (
        db.query(AgentAction.tool, func.count().label("count"))
        .group_by(AgentAction.tool)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    return {
        "high_risk_daily": [{"date": d, "count": c} for d, c in high_risk_daily],
        "top_agents": [{"agent_id": a, "count": c} for a, c in top_agents],
        "top_tools": [{"tool": t, "count": c} for t, c in top_tools],
    }
