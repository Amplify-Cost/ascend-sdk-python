"""
SLA Monitor Service - Enterprise Background Job
Monitors workflow SLA deadlines and auto-escalates overdue approvals
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import AgentAction, WorkflowExecution, Workflow

logger = logging.getLogger(__name__)


class SLAMonitor:
    """
    Monitors and enforces SLA deadlines for approval workflows.
    Runs as background job every 15 minutes.
    """

    def __init__(self):
        self.escalation_count = 0
        self.alert_count = 0

    def run_check(self, db: Session) -> Dict[str, int]:
        """
        Main entry point - finds and escalates overdue workflows.
        
        Returns:
            Dict with counts: {'overdue': int, 'escalated': int, 'alerted': int}
        """
        logger.info("🔍 SLA Monitor: Starting check for overdue workflows")
        
        try:
            overdue_actions = self.find_overdue_workflows(db)
            
            if not overdue_actions:
                logger.info("✅ No overdue workflows found")
                return {'overdue': 0, 'escalated': 0, 'alerted': 0}
            
            logger.warning(f"⚠️  Found {len(overdue_actions)} overdue workflows")
            
            escalated = 0
            alerted = 0
            
            for action in overdue_actions:
                result = self.escalate_workflow(action, db)
                if result == 'escalated':
                    escalated += 1
                elif result == 'alerted':
                    alerted += 1
            
            db.commit()
            
            logger.info(f"✅ SLA Monitor completed: {escalated} escalated, {alerted} executive alerts")
            
            return {
                'overdue': len(overdue_actions),
                'escalated': escalated,
                'alerted': alerted
            }
            
        except Exception as e:
            logger.error(f"❌ SLA Monitor error: {str(e)}", exc_info=True)
            db.rollback()
            raise

    def find_overdue_workflows(self, db: Session) -> List[AgentAction]:
        """
        Find all workflows past their SLA deadline.
        
        Returns:
            List of AgentAction objects that are overdue and still pending
        """
        now = datetime.now(timezone.utc)
        
        overdue_actions = db.query(AgentAction).filter(
            and_(
                AgentAction.sla_deadline.isnot(None),
                AgentAction.sla_deadline < now,
                AgentAction.workflow_stage.notin_(['approved', 'denied', 'cancelled'])
            )
        ).all()
        
        logger.info(f"Found {len(overdue_actions)} overdue workflows")
        
        for action in overdue_actions:
            hours_overdue = (now - action.sla_deadline).total_seconds() / 3600
            logger.warning(
                f"Action #{action.id}: {hours_overdue:.1f}h overdue, "
                f"stage={action.workflow_stage}, "
                f"approval_level={action.current_approval_level}/{action.required_approval_level}"
            )
        
        return overdue_actions

    def escalate_workflow(self, action: AgentAction, db: Session) -> str:
        """
        Escalate an overdue workflow to next approval level or send executive alert.
        
        Args:
            action: AgentAction that is overdue
            db: Database session
            
        Returns:
            'escalated' if approval level increased, 'alerted' if at max level, 'skipped' if already handled
        """
        # Check if already escalated recently (within last hour)
        if self._recently_escalated(action):
            logger.info(f"Action #{action.id}: Already escalated recently, skipping")
            return 'skipped'
        
        # Check if we can escalate to next level
        if action.current_approval_level < action.required_approval_level:
            return self._escalate_approval_level(action, db)
        else:
            return self._send_executive_alert(action, db)

    def _escalate_approval_level(self, action: AgentAction, db: Session) -> str:
        """
        Increase the approval level for an overdue workflow.
        """
        old_level = action.current_approval_level
        new_level = old_level + 1
        
        # Update approval level
        action.current_approval_level = new_level
        
        # Determine new stage
        if new_level == 1:
            action.workflow_stage = 'stage_1'
        elif new_level == 2:
            action.workflow_stage = 'stage_2'
        elif new_level >= 3:
            action.workflow_stage = 'stage_3'
        
        # Log escalation to approval chain
        self._log_escalation(
            action=action,
            escalation_type='level_increase',
            details={
                'old_level': old_level,
                'new_level': new_level,
                'reason': 'SLA deadline exceeded',
                'hours_overdue': (datetime.now(timezone.utc) - action.sla_deadline).total_seconds() / 3600
            },
            db=db
        )
        
        logger.warning(
            f"⬆️  Action #{action.id}: Escalated from level {old_level} → {new_level}"
        )
        
        return 'escalated'

    def _send_executive_alert(self, action: AgentAction, db: Session) -> str:
        """
        Send executive alert for workflows already at maximum approval level.
        """
        # Log executive alert to approval chain
        self._log_escalation(
            action=action,
            escalation_type='executive_alert',
            details={
                'current_level': action.current_approval_level,
                'max_level': action.required_approval_level,
                'reason': 'At maximum approval level but still overdue',
                'hours_overdue': (datetime.now(timezone.utc) - action.sla_deadline).total_seconds() / 3600
            },
            db=db
        )
        
        logger.critical(
            f"🚨 Action #{action.id}: EXECUTIVE ALERT - At max approval level but {action.current_approval_level}h overdue"
        )
        
        # TODO: Send actual email/Slack notification to executives
        # For now, just log it
        
        return 'alerted'

    def _log_escalation(
        self, 
        action: AgentAction, 
        escalation_type: str, 
        details: Dict,
        db: Session
    ):
        """
        Add escalation entry to approval_chain audit trail.
        """
        escalation_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'sla_escalation',
            'escalation_type': escalation_type,
            'automated': True,
            'details': details
        }
        
        # Get existing approval chain or initialize
        if action.approval_chain is None:
            action.approval_chain = []
        
        # Append escalation entry
        approval_chain = action.approval_chain.copy() if isinstance(action.approval_chain, list) else []
        approval_chain.append(escalation_entry)
        
        # Update with flag_modified for JSONB persistence
        action.approval_chain = approval_chain
        try:
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(action, 'approval_chain')
        except (ImportError, AttributeError):
            # In tests, flag_modified might not work with mocks
            pass
        
        logger.info(f"📝 Action #{action.id}: Logged {escalation_type} to approval chain")

    def _recently_escalated(self, action: AgentAction) -> bool:
        """
        Check if action was escalated in the last hour to prevent duplicate escalations.
        """
        if not action.approval_chain:
            return False
        
        one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
        
        for entry in action.approval_chain:
            if entry.get('event_type') == 'sla_escalation':
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')).timestamp()
                if entry_time > one_hour_ago:
                    return True
        
        return False

    def get_sla_metrics(self, db: Session) -> Dict:
        """
        Get SLA compliance metrics for dashboard.
        
        Returns:
            Dict with SLA statistics
        """
        now = datetime.now(timezone.utc)
        
        # Total workflows with SLA
        total = db.query(AgentAction).filter(
            AgentAction.sla_deadline.isnot(None)
        ).count()
        
        # Overdue workflows
        overdue = db.query(AgentAction).filter(
            and_(
                AgentAction.sla_deadline.isnot(None),
                AgentAction.sla_deadline < now,
                AgentAction.workflow_stage.notin_(['approved', 'denied', 'cancelled'])
            )
        ).count()
        
        # On-time workflows
        on_time = db.query(AgentAction).filter(
            and_(
                AgentAction.sla_deadline.isnot(None),
                AgentAction.sla_deadline >= now,
                AgentAction.workflow_stage.notin_(['approved', 'denied', 'cancelled'])
            )
        ).count()
        
        # Completed workflows
        completed = db.query(AgentAction).filter(
            and_(
                AgentAction.sla_deadline.isnot(None),
                AgentAction.workflow_stage.in_(['approved', 'denied'])
            )
        ).count()
        
        # Calculate compliance rate
        compliance_rate = ((total - overdue) / total * 100) if total > 0 else 100.0
        
        return {
            'total_workflows': total,
            'overdue': overdue,
            'on_time': on_time,
            'completed': completed,
            'compliance_rate': round(compliance_rate, 2)
        }
