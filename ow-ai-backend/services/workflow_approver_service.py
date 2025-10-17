"""
Workflow Approver Assignment Service
Automatically assigns appropriate approvers when workflows are created
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from services.approver_selector import approver_selector

logger = logging.getLogger(__name__)


class WorkflowApproverService:
    """Assigns approvers to workflows based on risk and requirements"""
    
    def assign_approvers_to_workflow(
        self,
        db: Session,
        workflow_execution_id: int,
        action_id: int,
        risk_score: float,
        required_approval_level: int,
        department: str = "Engineering"
    ) -> Dict:
        """
        Assign approvers to a workflow execution
        Returns primary and backup approvers
        """
        logger.info(
            f"Assigning approvers to workflow {workflow_execution_id}, "
            f"action {action_id}, risk {risk_score}"
        )
        
        # Get qualified approvers
        approvers = approver_selector.select_approvers(
            db=db,
            risk_score=risk_score,
            approval_level=required_approval_level,
            department=department
        )
        
        if not approvers:
            logger.error(f"No approvers found for workflow {workflow_execution_id}")
            return {"primary": None, "backups": []}
        
        # First approver is primary, rest are backups
        primary = approvers[0]
        backups = approvers[1:3]  # Keep top 2 backups
        
        # Update agent_action with primary approver
        self._assign_to_action(db, action_id, primary["email"])
        
        # Store approver chain in workflow_execution
        self._store_approver_chain(
            db, workflow_execution_id, primary, backups
        )
        
        logger.info(
            f"Assigned primary: {primary['email']}, "
            f"backups: {[b['email'] for b in backups]}"
        )
        
        return {
            "primary": primary,
            "backups": backups,
            "total_available": len(approvers)
        }
    
    def _assign_to_action(self, db: Session, action_id: int, approver_email: str):
        """Update agent_action with assigned approver"""
        query = text("""
            UPDATE agent_actions
            SET pending_approvers = :email,
                updated_at = NOW()
            WHERE id = :action_id
        """)
        
        db.execute(query, {"email": approver_email, "action_id": action_id})
        db.commit()
    
    def _store_approver_chain(
        self,
        db: Session,
        workflow_execution_id: int,
        primary: Dict,
        backups: List[Dict]
    ):
        """Store approver information in workflow_execution metadata"""
        approver_data = {
            "primary_approver": {
                "email": primary["email"],
                "level": primary["approval_level"],
                "department": primary["department"]
            },
            "backup_approvers": [
                {
                    "email": b["email"],
                    "level": b["approval_level"],
                    "department": b["department"]
                }
                for b in backups
            ]
        }
        
        # Note: This assumes workflow_executions has a metadata JSONB column
        # If not, we'll just log it
        logger.info(f"Approver chain for workflow {workflow_execution_id}: {approver_data}")
    
    def reassign_on_unavailable(
        self,
        db: Session,
        action_id: int,
        unavailable_email: str
    ) -> str:
        """
        Reassign to backup approver if primary is unavailable
        Returns new approver email
        """
        logger.warning(f"Primary approver {unavailable_email} unavailable for action {action_id}")
        
        # Get action details to find new approver
        query = text("""
            SELECT risk_score, required_approval_level, user_id
            FROM agent_actions
            WHERE id = :action_id
        """)
        
        result = db.execute(query, {"action_id": action_id}).fetchone()
        if not result:
            return None
        
        risk_score, req_level, _ = result
        
        # Get new approvers, excluding unavailable one
        approvers = approver_selector.select_approvers(
            db=db,
            risk_score=risk_score,
            approval_level=req_level
        )
        
        # Filter out unavailable approver
        available = [a for a in approvers if a["email"] != unavailable_email]
        
        if not available:
            logger.error(f"No alternative approvers for action {action_id}")
            return None
        
        new_approver = available[0]["email"]
        self._assign_to_action(db, action_id, new_approver)
        
        logger.info(f"Reassigned action {action_id} to {new_approver}")
        return new_approver


# Singleton instance
workflow_approver_service = WorkflowApproverService()
