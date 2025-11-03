"""
Alert Service
Handles all alert CRUD operations, correlation, and threat intelligence
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from core.logging import logger
from core.exceptions import ResourceNotFoundError, ValidationError


class AlertService:
    """
    Enterprise alert service for security alert management
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        source: str = "system",
        agent_action_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Create a new alert
        
        Returns:
            Alert ID
        """
        try:
            # Validate severity
            valid_severities = ["low", "medium", "high", "critical"]
            if severity not in valid_severities:
                raise ValidationError(f"Invalid severity: {severity}")
            
            result = self.db.execute(text("""
                INSERT INTO alerts (
                    alert_type, severity, message, status, source,
                    agent_action_id, agent_id, timestamp, metadata
                )
                VALUES (
                    :alert_type, :severity, :message, 'new', :source,
                    :agent_action_id, :agent_id, :timestamp, :metadata
                )
                RETURNING id
            """), {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "source": source,
                "agent_action_id": agent_action_id,
                "agent_id": agent_id,
                "timestamp": datetime.utcnow(),
                "metadata": json.dumps(metadata) if metadata else None
            })
            
            self.db.commit()
            alert_id = result.fetchone()[0]
            
            logger.info(f"✅ Created alert {alert_id}: {severity} - {alert_type}")
            return alert_id
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create alert: {e}")
            raise
    
    def create_for_action(
        self,
        action_id: int,
        risk_level: str,
        action_type: str = "Unknown"
    ) -> Dict:
        """
        Create alert specifically for a high-risk action
        Convenience method used by orchestration
        """
        alert_id = self.create_alert(
            alert_type="High Risk Agent Action",
            severity=risk_level,
            message=f"High-risk action detected: {action_type} (Action ID: {action_id})",
            source="orchestration_service",
            agent_action_id=action_id
        )
        
        return {
            "alert_id": alert_id,
            "action_id": action_id,
            "severity": risk_level
        }
    
    def update_status(
        self,
        alert_id: int,
        new_status: str,
        updated_by: Optional[int] = None,
        resolution_notes: Optional[str] = None
    ):
        """
        Update alert status
        
        Valid statuses: new, investigating, resolved, dismissed
        """
        try:
            valid_statuses = ["new", "investigating", "resolved", "dismissed", "escalated"]
            if new_status not in valid_statuses:
                raise ValidationError(f"Invalid status: {new_status}")
            
            update_data = {
                "status": new_status,
                "updated_at": datetime.utcnow(),
                "alert_id": alert_id
            }
            
            if resolution_notes:
                update_data["resolution_notes"] = resolution_notes
            
            query = """
                UPDATE alerts
                SET status = :status,
                    updated_at = :updated_at
            """
            
            if resolution_notes:
                query += ", resolution_notes = :resolution_notes"
            
            if new_status in ["resolved", "dismissed"]:
                query += ", resolved_at = :updated_at"
            
            query += " WHERE id = :alert_id"
            
            self.db.execute(text(query), update_data)
            self.db.commit()
            
            logger.info(f"✅ Updated alert {alert_id} status to {new_status}")
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update alert: {e}")
            raise
    
    def get_by_id(self, alert_id: int) -> Dict:
        """Get alert by ID with full details"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, alert_type, severity, message, status, source,
                    agent_action_id, agent_id, timestamp, resolved_at,
                    resolution_notes, metadata
                FROM alerts
                WHERE id = :alert_id
            """), {"alert_id": alert_id})
            
            row = result.fetchone()
            if not row:
                raise ResourceNotFoundError("Alert", alert_id)
            
            return {
                "id": row[0],
                "alert_type": row[1],
                "severity": row[2],
                "message": row[3],
                "status": row[4],
                "source": row[5],
                "agent_action_id": row[6],
                "agent_id": row[7],
                "timestamp": row[8],
                "resolved_at": row[9],
                "resolution_notes": row[10],
                "metadata": json.loads(row[11]) if row[11] else None
            }
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get alert: {e}")
            raise
    
    def get_active_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get active (unresolved) alerts"""
        try:
            query = """
                SELECT 
                    id, alert_type, severity, message, status,
                    agent_action_id, agent_id, timestamp
                FROM alerts
                WHERE status NOT IN ('resolved', 'dismissed')
            """
            
            params = {"limit": limit}
            
            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            
            result = self.db.execute(text(query), params)
            
            alerts = []
            for row in result:
                alerts.append({
                    "id": row[0],
                    "alert_type": row[1],
                    "severity": row[2],
                    "message": row[3],
                    "status": row[4],
                    "agent_action_id": row[5],
                    "agent_id": row[6],
                    "timestamp": row[7]
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def get_by_action(self, action_id: int) -> List[Dict]:
        """Get all alerts for a specific action"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, alert_type, severity, message, status, timestamp
                FROM alerts
                WHERE agent_action_id = :action_id
                ORDER BY timestamp DESC
            """), {"action_id": action_id})
            
            alerts = []
            for row in result:
                alerts.append({
                    "id": row[0],
                    "alert_type": row[1],
                    "severity": row[2],
                    "message": row[3],
                    "status": row[4],
                    "timestamp": row[5]
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts for action: {e}")
            return []
    
    def get_statistics(self, days: int = 7) -> Dict:
        """Get alert statistics for dashboard"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium,
                    COUNT(CASE WHEN severity = 'low' THEN 1 END) as low,
                    COUNT(CASE WHEN status = 'new' THEN 1 END) as new,
                    COUNT(CASE WHEN status = 'investigating' THEN 1 END) as investigating,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                    COUNT(CASE WHEN status = 'dismissed' THEN 1 END) as dismissed
                FROM alerts
                WHERE timestamp >= :since
            """), {"since": since})
            
            row = result.fetchone()
            
            return {
                "period_days": days,
                "total_alerts": row[0],
                "by_severity": {
                    "critical": row[1],
                    "high": row[2],
                    "medium": row[3],
                    "low": row[4]
                },
                "by_status": {
                    "new": row[5],
                    "investigating": row[6],
                    "resolved": row[7],
                    "dismissed": row[8]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            return {"error": str(e)}
    
    def correlate_alerts(self, alert_id: int) -> List[Dict]:
        """
        Find correlated alerts (same agent, similar time, related actions)
        """
        try:
            # Get the source alert
            source_alert = self.get_by_id(alert_id)
            
            # Find correlated alerts within 1 hour
            time_window = timedelta(hours=1)
            
            result = self.db.execute(text("""
                SELECT 
                    id, alert_type, severity, message, timestamp
                FROM alerts
                WHERE id != :alert_id
                  AND (
                      agent_id = :agent_id
                      OR agent_action_id IN (
                          SELECT id FROM agent_actions 
                          WHERE agent_id = :agent_id
                      )
                  )
                  AND timestamp BETWEEN :start_time AND :end_time
                ORDER BY timestamp DESC
                LIMIT 10
            """), {
                "alert_id": alert_id,
                "agent_id": source_alert.get("agent_id"),
                "start_time": source_alert["timestamp"] - time_window,
                "end_time": source_alert["timestamp"] + time_window
            })
            
            correlated = []
            for row in result:
                correlated.append({
                    "id": row[0],
                    "alert_type": row[1],
                    "severity": row[2],
                    "message": row[3],
                    "timestamp": row[4]
                })
            
            return correlated
            
        except Exception as e:
            logger.error(f"Failed to correlate alerts: {e}")
            return []


def get_alert_service(db: Session):
    """Dependency injection factory"""
    return AlertService(db)
