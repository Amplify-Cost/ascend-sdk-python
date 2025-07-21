from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import AgentAction
from datetime import datetime, timedelta
from collections import defaultdict, Counter

router = APIRouter()

@router.get("/trends")
def get_trend_data(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    past_week = now - timedelta(days=7)

    raw_actions = (
        db.query(AgentAction)
        .filter(AgentAction.timestamp >= past_week)
        .order_by(AgentAction.timestamp.asc())
        .all()
    )

    daily_counts = defaultdict(int)
    agent_counter = Counter()
    tool_counter = Counter()

    for action in raw_actions:
        # 🔧 Fix: normalize risk_level comparison to lowercase
        if action.risk_level and action.risk_level.lower() == "high":
            date_str = action.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_str] += 1
        if action.agent_id:
            agent_counter[action.agent_id] += 1
        if action.tool_name:
            tool_counter[action.tool_name] += 1

    enriched_actions = (
        db.query(AgentAction)
        .filter(AgentAction.summary != None)
        .order_by(AgentAction.timestamp.desc())
        .limit(10)
        .all()
    )

    enriched_data = [
        {
            "agent_id": a.agent_id,
            "risk_level": a.risk_level,
            "mitre_tactic": a.mitre_tactic,
            "nist_control": a.nist_control,
            "recommendation": a.recommendation,
        }
        for a in enriched_actions
    ]

    return {
        "high_risk_actions_by_day": [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items())
        ],
        "top_agents": [
            {"agent": agent, "count": count}
            for agent, count in agent_counter.most_common(5)
        ],
        "top_tools": [
            {"tool": tool, "count": count}
            for tool, count in tool_counter.most_common(5)
        ],
        "enriched_actions": enriched_data
    }

@router.get("/debug")
def debug_enriched_actions(db: Session = Depends(get_db)):
    actions = (
        db.query(AgentAction)
        .order_by(AgentAction.timestamp.desc())
        .limit(5)
        .all()
    )
    return [
        {
            "id": a.id,
            "agent_id": a.agent_id,
            "risk_level": a.risk_level,
            "mitre_tactic": a.mitre_tactic,
            "nist_control": a.nist_control,
            "recommendation": a.recommendation,
            "summary": a.summary,
        }
        for a in actions
    ]
