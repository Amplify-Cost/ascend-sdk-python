"""
ENTERPRISE MIGRATION: Convert pending agent_actions to workflow_executions
This migrates from legacy authorization system to enterprise workflow orchestration
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AgentAction, WorkflowExecution
from services.workflow_bridge import WorkflowBridge
from database import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_pending_actions_to_workflows():
    """Migrate all pending actions to workflow system"""
    
    db = next(get_db())
    
    try:
        # Get all pending actions
        pending_actions = db.query(AgentAction).filter(
            AgentAction.status.in_(["pending_approval", "pending", "submitted"])
        ).all()
        
        logger.info(f"Found {len(pending_actions)} pending actions to migrate")
        
        if len(pending_actions) == 0:
            logger.warning("No pending actions found. Nothing to migrate.")
            return
        
        bridge = WorkflowBridge(db)
        migrated_count = 0
        
        for action in pending_actions:
            # Check if workflow already exists for this action
            existing = db.query(WorkflowExecution).filter(
                WorkflowExecution.action_id == action.id
            ).first()
            
            if existing:
                logger.info(f"Skipping action {action.id} - workflow already exists")
                continue
            
            # Prepare action data
            action_data = {
                "action_id": action.id,
                "action_type": action.action_type,
                "agent_id": action.agent_id,
                "target": action.target_system or "unknown",
                "context": {
                    "description": action.description,
                    "nist_control": action.nist_control,
                    "mitre_tactic": action.mitre_tactic
                }
            }
            
            # Use enterprise_risk_score if available, otherwise default
            risk_score = getattr(action, 'enterprise_risk_score', None) or 75
            
            # Create workflow execution
            try:
                workflow_execution = bridge.create_workflow_execution(
                    action_data=action_data,
                    risk_score=risk_score,
                    policies_triggered=[]
                )
                
                logger.info(f"✅ Created workflow {workflow_execution.id} for action {action.id}")
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to create workflow for action {action.id}: {e}")
                continue
        
        db.commit()
        logger.info(f"\n🎉 MIGRATION COMPLETE: {migrated_count} actions migrated to workflows")
        logger.info("Your enterprise workflow system is now active!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_pending_actions_to_workflows()
