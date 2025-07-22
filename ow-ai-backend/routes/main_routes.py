from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction, Alert, Log
from schemas import AgentActionOut, AlertOut
from dependencies import get_current_user
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Main"])

# ✅ REMOVED DUPLICATE ENDPOINTS - These are now in agent_routes.py and alert_routes.py

@router.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get application logs"""
    try:
        logs = (
            db.query(Log)
            .order_by(Log.timestamp.desc())
            .limit(min(limit, 100))
            .all()
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@router.get("/security-findings")
def get_security_findings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get security findings summary"""
    try:
        # Get total counts
        total_actions = db.query(AgentAction).count()
        total_alerts = db.query(Alert).count()
        
        # Get risk distribution
        high_risk = db.query(AgentAction).filter(AgentAction.risk_level == "high").count()
        medium_risk = db.query(AgentAction).filter(AgentAction.risk_level == "medium").count()
        low_risk = db.query(AgentAction).filter(AgentAction.risk_level == "low").count()
        
        # Get recent high-risk actions
        recent_alerts = (
            db.query(AgentAction)
            .filter(AgentAction.risk_level == "high")
            .order_by(AgentAction.timestamp.desc())
            .limit(5)
            .all()
        )
        
        return {
            "total_actions": total_actions,
            "total_alerts": total_alerts,
            "risk_distribution": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk
            },
            "recent_alerts": [
                {
                    "id": action.id,
                    "agent_id": action.agent_id,
                    "action_type": action.action_type,
                    "description": action.description,
                    "risk_level": action.risk_level,
                    "timestamp": action.timestamp
                }
                for action in recent_alerts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get security findings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security findings")

@router.post("/debug/seed-test-data")
def seed_test_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Seed test data for development (remove in production)"""
    try:
        from models import AgentAction, Alert
        from datetime import datetime, UTC
        
        # Create test agent actions
        test_actions = [
            AgentAction(
                user_id=current_user["user_id"],
                agent_id="test-agent-001",
                action_type="data_access",
                description="Agent accessed sensitive customer data",
                tool_name="DataReader",
                timestamp=datetime.now(UTC),
                risk_level="high",
                nist_control="AC-6",
                nist_description="Least Privilege Access Control",
                mitre_tactic="Collection",
                mitre_technique="T1005",
                recommendation="Review data access patterns and implement additional controls",
                summary="High-risk data access detected",
                status="pending"
            ),
            AgentAction(
                user_id=current_user["user_id"],
                agent_id="test-agent-002",
                action_type="network_scan",
                description="Agent performed network discovery scan",
                tool_name="NetworkScanner",
                timestamp=datetime.now(UTC),
                risk_level="medium",
                nist_control="SI-4",
                nist_description="Information System Monitoring",
                mitre_tactic="Discovery",
                mitre_technique="T1046",
                recommendation="Monitor network scanning activities",
                summary="Network reconnaissance activity detected",
                status="pending"
            ),
            AgentAction(
                user_id=current_user["user_id"],
                agent_id="test-agent-003",
                action_type="file_operation",
                description="Agent performed standard file operations",
                tool_name="FileManager",
                timestamp=datetime.now(UTC),
                risk_level="low",
                nist_control="AU-6",
                nist_description="Audit Review and Analysis",
                mitre_tactic="Execution",
                mitre_technique="T1059",
                recommendation="Continue monitoring file operations",
                summary="Normal file operations detected",
                status="approved"
            )
        ]
        
        db.add_all(test_actions)
        db.commit()
        
        # Create corresponding alerts for high-risk actions
        for action in test_actions:
            if action.risk_level == "high":
                alert = Alert(
                    agent_action_id=action.id,
                    alert_type="High Risk Activity",
                    severity="high",
                    message=f"High-risk activity detected: {action.description}",
                    created_at=action.timestamp,
                    timestamp=action.timestamp
                )
                db.add(alert)
        
        db.commit()
        
        logger.info(f"Test data seeded by {current_user['email']}")
        return {"message": f"✅ {len(test_actions)} test actions created"}
    
    except Exception as e:
        logger.error(f"Failed to seed test data: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create test data"
        )

