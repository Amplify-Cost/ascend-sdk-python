"""
Enterprise Workflow Bridge - Policy to Workflow Integration

Connects policy enforcement decisions (REQUIRE_APPROVAL) to workflow execution system.
Maps risk scores to appropriate multi-stage approval workflows.
"""
from sqlalchemy.orm import attributes


from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List
import logging

from models import Workflow, WorkflowExecution, AgentAction

logger = logging.getLogger("enterprise.workflow_bridge")

class WorkflowBridgeError(Exception):
    """Custom exception for workflow bridge errors"""
    pass

class WorkflowBridge:
    """
    Enterprise workflow bridge connecting policy decisions to workflow execution.
    """
    
    WORKFLOW_TEMPLATES = {
        (90, 100): "risk_90_100",
        (70, 89): "risk_70_89",
        (50, 69): "risk_50_69",
        (0, 49): "risk_0_49"
    }
    
    def __init__(self, db: Session):
        self.db = db
        
    def select_workflow_template(self, risk_score: int) -> str:
        """Select appropriate workflow template based on risk score."""
        if not isinstance(risk_score, (int, float)) or risk_score < 0 or risk_score > 100:
            raise WorkflowBridgeError(f"Invalid risk score: {risk_score}. Must be 0-100.")
        
        for (min_score, max_score), template_id in self.WORKFLOW_TEMPLATES.items():
            if min_score <= risk_score <= max_score:
                logger.info(f"Selected workflow template '{template_id}' for risk score {risk_score}")
                return template_id
        
        logger.warning(f"No template found for risk score {risk_score}, using fallback")
        return "risk_0_49"
    
    def calculate_approval_levels(self, risk_score: int) -> int:
        """Calculate required approval levels based on risk score."""
        if risk_score >= 90:
            return 3
        elif risk_score >= 70:
            return 2
        elif risk_score >= 50:
            return 2
        else:
            return 1
    
    def calculate_sla_deadline(self, workflow_id: str) -> datetime:
        """Calculate SLA deadline based on workflow configuration."""
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow or not workflow.workflow_metadata:
            logger.warning(f"No workflow metadata for {workflow_id}, using default 24h SLA")
            return datetime.now(UTC) + timedelta(hours=24)
        
        sla_hours = workflow.workflow_metadata.get("sla_hours", 24)
        deadline = datetime.now(UTC) + timedelta(hours=sla_hours)
        
        logger.info(f"SLA deadline for workflow {workflow_id}: {deadline} ({sla_hours}h)")
        return deadline

    
    def create_workflow_execution(
        self,
        action_data: Dict[str, Any],
        risk_score: int,
        policies_triggered: List[Dict[str, Any]]
    ) -> WorkflowExecution:
        """Create workflow execution for action requiring approval."""
        try:
            workflow_id = self.select_workflow_template(risk_score)
            required_levels = self.calculate_approval_levels(risk_score)
            sla_deadline = self.calculate_sla_deadline(workflow_id)
            
            action_id = action_data.get("action_id")
            
            if not action_id:
                agent_action = self._create_pending_action(action_data, risk_score)
                action_id = agent_action.id
                self.db.refresh(agent_action)  # Ensure attached to session
            else:
                agent_action = self.db.query(AgentAction).filter(AgentAction.id == action_id).first()
                if not agent_action:
                    raise WorkflowBridgeError(f"Action {action_id} not found")
            
            

            workflow_execution = WorkflowExecution(
                workflow_id=workflow_id,
                action_id=action_id,
                executed_by=action_data.get("agent_id", "unknown"),
                execution_status="pending_stage_1",
                input_data={
                    "action_type": action_data.get("action_type"),
                    "target": action_data.get("target"),
                    "context": action_data.get("context", {}),
                    "risk_score": risk_score,
                    "policies_triggered": policies_triggered
                },
                current_stage="stage_1",
                approval_chain=[]
            )
            
            self.db.add(workflow_execution)
            self.db.flush()
            
            agent_action.workflow_id = workflow_id
            agent_action.workflow_execution_id = workflow_execution.id
            agent_action.workflow_stage = "stage_1"
            agent_action.current_approval_level = 0
            agent_action.required_approval_level = required_levels
            agent_action.sla_deadline = sla_deadline
            agent_action.status = "pending_approval"
            
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            # Mark workflow fields as modified to ensure they are saved
            attributes.flag_modified(agent_action, "workflow_id")
            attributes.flag_modified(agent_action, "workflow_stage")

            if workflow and workflow.steps:
                first_step = workflow.steps[0] if isinstance(workflow.steps, list) else {}

                approver_role = first_step.get("approver_role", "security")
                agent_action.pending_approvers = approver_role
            
            self.db.add(agent_action)  # Ensure updated fields are tracked

            self.db.commit()
            self.db.refresh(workflow_execution)
            
            logger.info(
                f"Created workflow execution {workflow_execution.id} "
                f"for action {action_id} using template {workflow_id}"
            )
            
            return workflow_execution
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create workflow execution: {str(e)}")
            raise WorkflowBridgeError(f"Workflow creation failed: {str(e)}")
    
    def _create_pending_action(self, action_data: Dict[str, Any], risk_score: int) -> AgentAction:
        """Create new pending action in database."""
        agent_action = AgentAction(
            agent_id=action_data.get("agent_id", "unknown"),
            action_type=action_data.get("action_type", "unknown"),
            description=action_data.get("description", ""),
            risk_score=risk_score,
            risk_level=self._risk_score_to_level(risk_score),
            status="pending_approval",
            target_system=action_data.get("target"),
            requires_approval=True,
            extra_data=action_data.get("context", {})
        )
        
        self.db.add(agent_action)
        self.db.flush()
        
        return agent_action
    
    @staticmethod
    def _risk_score_to_level(risk_score: int) -> str:
        """Convert numeric risk score to text level."""
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
