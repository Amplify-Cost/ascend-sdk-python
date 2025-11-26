from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction
from dependencies import verify_token, get_organization_filter
from sqlalchemy import func

router = APIRouter()

@router.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)  # 🏢 ENTERPRISE: Multi-tenant isolation
):
    query = db.query(AgentAction)
    # 🏢 ENTERPRISE: Multi-tenant isolation - filter by organization
    if org_id is not None:
        query = query.filter(AgentAction.organization_id == org_id)
    return query.order_by(AgentAction.timestamp.desc()).limit(100).all()

@router.get("/analytics/trends")
def get_trends(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)  # 🏢 ENTERPRISE: Multi-tenant isolation
):
    # 🏢 ENTERPRISE: Multi-tenant isolation - base query with organization filter
    base_query = db.query(AgentAction)
    if org_id is not None:
        base_query = base_query.filter(AgentAction.organization_id == org_id)

    high_risk_daily = (
        base_query.with_entities(
            func.date(func.datetime(AgentAction.timestamp, 'unixepoch')).label("date"),
            func.count().label("count")
        )
        .filter(AgentAction.risk_level == "high")
        .group_by("date")
        .all()
    )

    base_query2 = db.query(AgentAction)
    if org_id is not None:
        base_query2 = base_query2.filter(AgentAction.organization_id == org_id)

    top_agents = (
        base_query2.with_entities(AgentAction.agent_id, func.count().label("count"))
        .group_by(AgentAction.agent_id)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    base_query3 = db.query(AgentAction)
    if org_id is not None:
        base_query3 = base_query3.filter(AgentAction.organization_id == org_id)

    top_tools = (
        base_query3.with_entities(AgentAction.tool, func.count().label("count"))
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