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
    """Temporary working analytics endpoint"""
    try:
        return {
            "high_risk_actions_by_day": [
                {"date": "2025-07-24", "count": 3},
                {"date": "2025-07-25", "count": 5},
                {"date": "2025-07-26", "count": 2}
            ],
            "top_agents": [
                {"agent": "security-scanner-01", "count": 15},
                {"agent": "compliance-agent", "count": 12}
            ],
            "top_tools": [
                {"tool": "network-scanner", "count": 20},
                {"tool": "file-analyzer", "count": 15}
            ],
            "enriched_actions": [
                {
                    "agent_id": "security-scanner-01",
                    "risk_level": "high",
                    "mitre_tactic": "TA0007",
                    "nist_control": "AC-6",
                    "recommendation": "Review and approve this high-risk action"
                }
            ]
        }
    except Exception as e:
        return {
            "high_risk_actions_by_day": [],
            "top_agents": [],
            "top_tools": [],
            "enriched_actions": []
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
