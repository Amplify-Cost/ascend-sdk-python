"""
Workflow Service
Handles workflow execution, stage transitions, and approval management
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
from datetime import datetime
import json

from core.logging import logger
from core.exceptions import ResourceNotFoundError, ValidationError


class WorkflowService:
    """Enterprise workflow service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_matching_workflows(self, risk_score: float) -> List:
        """Get active workflows that match risk score"""
        try:
            from models import Workflow
            workflows = self.db.query(Workflow).filter(
                Workflow.status == 'active'
            ).all()
            return [w for w in workflows if self._check_risk_match(w, risk_score)]
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []
    
    def trigger_workflow(self, workflow_id: str, action_id: int, triggered_by: str = "system") -> Dict:
        """Trigger a workflow execution"""
        try:
            result = self.db.execute(text("""
                INSERT INTO workflow_executions (
                    workflow_id, action_id, executed_by, execution_status,
                    current_stage, started_at
                )
                VALUES (:workflow_id, :action_id, :executed_by, 'in_progress', 0, :started_at)
                RETURNING id
            """), {
                "workflow_id": workflow_id,
                "action_id": action_id,
                "executed_by": triggered_by,
                "started_at": datetime.utcnow()
            })
            
            self.db.commit()
            execution_id = result.fetchone()[0]
            
            return {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "action_id": action_id,
                "status": "in_progress"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to trigger workflow: {e}")
            raise
    
    def _check_risk_match(self, workflow, risk_score: float) -> bool:
        """Check if workflow matches risk score"""
        try:
            conditions = workflow.trigger_conditions
            if isinstance(conditions, str):
                conditions = json.loads(conditions)
            if not conditions:
                return True
            min_risk = conditions.get('min_risk', 0)
            max_risk = conditions.get('max_risk', 100)
            return min_risk <= risk_score <= max_risk
        except:
            return False


def get_workflow_service(db: Session):
    return WorkflowService(db)
