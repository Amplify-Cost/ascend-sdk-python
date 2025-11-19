"""
Orchestration Service
Handles automatic triggering of alerts and workflows based on action risk levels.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List
import json
from datetime import datetime

from core.logging import logger
from core.exceptions import OrchestrationError


class OrchestrationService:
    """Enterprise orchestration service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def orchestrate_action(
        self, 
        action_id: int, 
        risk_level: str, 
        risk_score: float,
        action_type: str
    ) -> Dict:
        """
        Main orchestration - triggers alerts and workflows
        """
        results = {
            "alert_created": False,
            "alert_id": None,
            "workflows_triggered": [],
            "orchestration_status": "success"
        }
        
        try:
            # Auto-create alert for high/critical risk
            if risk_level in ["high", "critical"]:
                alert_id = self._create_alert(action_id, risk_level, action_type)
                results["alert_created"] = True
                results["alert_id"] = alert_id
                logger.info(f"✅ Auto-created alert for action {action_id}")
            
            # Auto-trigger workflows
            triggered = self._trigger_workflows(action_id, risk_score, action_type)
            results["workflows_triggered"] = triggered
            
            if triggered:
                logger.info(f"✅ Triggered {len(triggered)} workflows")
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            results["orchestration_status"] = "failed"
            results["error"] = str(e)
        
        return results
    
    def _create_alert(self, action_id: int, risk_level: str, action_type: str) -> int:
        """Create alert for high-risk action"""
        try:
            result = self.db.execute(text("""
                INSERT INTO alerts (
                    agent_action_id, alert_type, severity, status,
                    message, timestamp
                )
                VALUES (
                    :action_id, 'High Risk Agent Action', :severity, 'new',
                    :message, :timestamp
                )
                RETURNING id
            """), {
                "action_id": action_id,
                "severity": risk_level,
                "message": f"High-risk action: {action_type} (ID: {action_id})",
                "timestamp": datetime.utcnow()
            })
            
            self.db.commit()
            return result.fetchone()[0]
            
        except Exception as e:
            self.db.rollback()
            raise OrchestrationError(f"Alert creation failed: {e}")
    
    def _trigger_workflows(self, action_id: int, risk_score: float, action_type: str) -> List[str]:
        """Trigger matching workflows"""
        triggered = []
        
        try:
            from models import Workflow
            
            workflows = self.db.query(Workflow).filter(
                Workflow.status == 'active'
            ).all()
            
            for workflow in workflows:
                trigger_conditions = workflow.trigger_conditions or {}
                if isinstance(trigger_conditions, str):
                    trigger_conditions = json.loads(trigger_conditions)
                
                if self._check_trigger_match(trigger_conditions, risk_score):
                    exec_id = self._create_workflow_execution(workflow.id, action_id, risk_score)
                    triggered.append(workflow.id)
            
        except Exception as e:
            logger.error(f"Workflow triggering failed: {e}")
        
        return triggered
    
    def _check_trigger_match(self, conditions: Dict, risk_score: float) -> bool:
        """Check if conditions match"""
        if conditions and 'min_risk' in conditions:
            min_risk = conditions.get('min_risk', 0)
            max_risk = conditions.get('max_risk', 100)
            return min_risk <= risk_score <= max_risk
        return not conditions
    
    def _create_workflow_execution(self, workflow_id: str, action_id: int, risk_score: float) -> int:
        """Create workflow execution"""
        try:
            result = self.db.execute(text("""
                INSERT INTO workflow_executions (
                    workflow_id, action_id, executed_by, execution_status,
                    current_stage, started_at, input_data
                )
                VALUES (
                    :workflow_id, :action_id, 'system', 'in_progress',
                    0, :started_at, :input_data
                )
                RETURNING id
            """), {
                "workflow_id": workflow_id,
                "action_id": action_id,
                "started_at": datetime.utcnow(),
                "input_data": json.dumps({"risk_score": risk_score})
            })
            
            self.db.commit()
            return result.fetchone()[0]
            
        except Exception as e:
            self.db.rollback()
            raise OrchestrationError(f"Execution creation failed: {e}")


def get_orchestration_service(db: Session) -> OrchestrationService:
    """Dependency injection factory"""
    return OrchestrationService(db)
