"""
Action Service
Handles all agent action CRUD operations and validation
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
from datetime import datetime

from core.logging import logger
from core.exceptions import ValidationError, ResourceNotFoundError


class ActionService:
    """
    Enterprise action service for agent action management
    Handles creation, updates, status changes, and queries
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        user_id: int,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new agent action with validation
        
        Returns:
            Dict with action_id and details
        """
        try:
            # Validate input
            self._validate_action_data(agent_id, action_type, description)
            
            # Insert action
            result = self.db.execute(text("""
                INSERT INTO agent_actions (
                    agent_id, action_type, description, status,
                    created_by, created_at, risk_score, risk_level
                )
                VALUES (
                    :agent_id, :action_type, :description, 'pending_approval',
                    :user_id, :created_at, 50, 'medium'
                )
                RETURNING id
            """), {
                "agent_id": agent_id,
                "action_type": action_type,
                "description": description,
                "user_id": user_id,
                "created_at": datetime.utcnow()
            })
            
            self.db.commit()
            action_id = result.fetchone()[0]
            
            logger.info(f"✅ Created action {action_id} by user {user_id}")
            
            return {
                "action_id": action_id,
                "status": "pending_approval",
                "agent_id": agent_id,
                "action_type": action_type
            }
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create action: {e}")
            raise
    
    def update_status(
        self,
        action_id: int,
        new_status: str,
        updated_by: int,
        reason: Optional[str] = None
    ):
        """
        Update action status with audit trail
        
        Valid statuses: pending_approval, approved, denied, completed
        """
        try:
            # Validate status
            valid_statuses = ["pending_approval", "approved", "denied", "completed", "in_progress"]
            if new_status not in valid_statuses:
                raise ValidationError(f"Invalid status: {new_status}")
            
            # Update status
            self.db.execute(text("""
                UPDATE agent_actions
                SET status = :status,
                    updated_at = :updated_at,
                    updated_by = :updated_by
                WHERE id = :action_id
            """), {
                "status": new_status,
                "updated_at": datetime.utcnow(),
                "updated_by": updated_by,
                "action_id": action_id
            })
            
            # Log status change
            self.db.execute(text("""
                INSERT INTO action_audit_log (
                    action_id, changed_by, old_status, new_status,
                    change_reason, changed_at
                )
                SELECT 
                    :action_id, :changed_by, status, :new_status,
                    :reason, :changed_at
                FROM agent_actions WHERE id = :action_id
            """), {
                "action_id": action_id,
                "changed_by": updated_by,
                "new_status": new_status,
                "reason": reason,
                "changed_at": datetime.utcnow()
            })
            
            self.db.commit()
            logger.info(f"✅ Updated action {action_id} status to {new_status}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update action status: {e}")
            raise
    
    def update_risk_score(self, action_id: int, risk_score: float, risk_level: str):
        """Update risk score and level after assessment"""
        try:
            self.db.execute(text("""
                UPDATE agent_actions
                SET risk_score = :risk_score,
                    risk_level = :risk_level,
                    updated_at = :updated_at
                WHERE id = :action_id
            """), {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "updated_at": datetime.utcnow(),
                "action_id": action_id
            })
            
            self.db.commit()
            logger.info(f"✅ Updated action {action_id} risk: {risk_level} ({risk_score})")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update risk score: {e}")
            raise
    
    def get_by_id(self, action_id: int) -> Dict:
        """Get action by ID"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, agent_id, action_type, description, status,
                    risk_score, risk_level, created_at, created_by
                FROM agent_actions
                WHERE id = :action_id
            """), {"action_id": action_id})
            
            row = result.fetchone()
            if not row:
                raise ResourceNotFoundError("Action", action_id)
            
            return {
                "id": row[0],
                "agent_id": row[1],
                "action_type": row[2],
                "description": row[3],
                "status": row[4],
                "risk_score": row[5],
                "risk_level": row[6],
                "created_at": row[7],
                "created_by": row[8]
            }
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get action: {e}")
            raise
    
    def get_pending_approval(self, limit: int = 100) -> List[Dict]:
        """Get all actions pending approval"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, agent_id, action_type, description,
                    risk_score, risk_level, created_at
                FROM agent_actions
                WHERE status = 'pending_approval'
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"limit": limit})
            
            actions = []
            for row in result:
                actions.append({
                    "id": row[0],
                    "agent_id": row[1],
                    "action_type": row[2],
                    "description": row[3],
                    "risk_score": row[4],
                    "risk_level": row[5],
                    "created_at": row[6]
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to get pending actions: {e}")
            return []
    
    def get_by_agent(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get all actions for a specific agent"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, action_type, description, status,
                    risk_score, risk_level, created_at
                FROM agent_actions
                WHERE agent_id = :agent_id
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"agent_id": agent_id, "limit": limit})
            
            actions = []
            for row in result:
                actions.append({
                    "id": row[0],
                    "action_type": row[1],
                    "description": row[2],
                    "status": row[3],
                    "risk_score": row[4],
                    "risk_level": row[5],
                    "created_at": row[6]
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to get agent actions: {e}")
            return []
    
    def delete_action(self, action_id: int, deleted_by: int):
        """Soft delete an action"""
        try:
            self.db.execute(text("""
                UPDATE agent_actions
                SET status = 'deleted',
                    updated_at = :updated_at,
                    updated_by = :deleted_by
                WHERE id = :action_id
            """), {
                "updated_at": datetime.utcnow(),
                "deleted_by": deleted_by,
                "action_id": action_id
            })
            
            self.db.commit()
            logger.info(f"✅ Deleted action {action_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete action: {e}")
            raise
    
    def _validate_action_data(self, agent_id: str, action_type: str, description: str):
        """Validate action input data"""
        if not agent_id or len(agent_id) < 3:
            raise ValidationError("Agent ID must be at least 3 characters")
        
        if not action_type or len(action_type) < 3:
            raise ValidationError("Action type must be at least 3 characters")
        
        if not description or len(description) < 10:
            raise ValidationError("Description must be at least 10 characters")
        
        # Check for SQL injection attempts
        dangerous_patterns = ["DROP TABLE", "DELETE FROM", "INSERT INTO", "--", "/*"]
        for pattern in dangerous_patterns:
            if pattern.lower() in description.lower():
                raise ValidationError("Description contains potentially dangerous content")


def get_action_service(db: Session):
    """Dependency injection factory"""
    return ActionService(db)
