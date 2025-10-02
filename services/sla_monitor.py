"""
SLA Monitor Service - Using Raw SQL (bypasses ORM caching issues)
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class SLAMonitor:
    """Monitors and enforces SLA deadlines using raw SQL"""
    
    def __init__(self):
        self.escalation_count = 0
        self.alert_count = 0
    
    def run_check(self, db: Session) -> Dict[str, int]:
        """Main entry point - finds and escalates overdue workflows"""
        try:
            logger.info("🔍 SLA Monitor: Starting check for overdue workflows")
            
            overdue_actions = self.find_overdue_workflows(db)
            logger.info(f"Found {len(overdue_actions)} overdue workflows")
            
            for action in overdue_actions:
                self.escalate_workflow(db, action)
            
            return {
                "checked": len(overdue_actions),
                "escalated": self.escalation_count,
                "alerted": self.alert_count
            }
            
        except Exception as e:
            logger.error(f"❌ SLA Monitor error: {e}", exc_info=True)
            raise
    
    def find_overdue_workflows(self, db: Session) -> List[tuple]:
        """Find workflows past SLA deadline using raw SQL"""
        query = text("""
            SELECT 
                id,
                workflow_stage,
                current_approval_level,
                required_approval_level,
                sla_deadline,
                EXTRACT(EPOCH FROM (NOW() - sla_deadline))/3600 as hours_overdue
            FROM agent_actions
            WHERE sla_deadline IS NOT NULL
              AND sla_deadline < NOW()
              AND workflow_stage NOT IN ('approved', 'denied', 'cancelled')
            ORDER BY sla_deadline
        """)
        
        result = db.execute(query)
        return result.fetchall()
    
    def escalate_workflow(self, db: Session, action: tuple):
        """Escalate a single workflow"""
        action_id = action[0]
        stage = action[1]
        current_level = action[2]
        required_level = action[3]
        sla_deadline = action[4]
        hours_overdue = action[5]
        
        # Don't escalate if already at required level
        if current_level >= required_level:
            logger.info(f"Action {action_id} already at max approval level {required_level}")
            return
        
        new_level = current_level + 1
        
        # Update using raw SQL
        update_query = text("""
            UPDATE agent_actions
            SET current_approval_level = :new_level,
                updated_at = NOW()
            WHERE id = :action_id
        """)
        
        db.execute(update_query, {
            "new_level": new_level,
            "action_id": action_id
        })
        db.commit()
        
        self.escalation_count += 1
        logger.info(
            f"✅ Escalated action {action_id} from level {current_level} to {new_level} "
            f"(overdue by {hours_overdue:.1f} hours)"
        )
        
        # Alert if approaching max level
        if new_level >= required_level:
            self.alert_count += 1
            logger.warning(
                f"⚠️ Action {action_id} reached required approval level {required_level}. "
                f"Needs immediate attention!"
            )
