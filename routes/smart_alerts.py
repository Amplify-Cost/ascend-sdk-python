# routes/smart_alerts.py - Master Prompt Aligned Smart Alert Management
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from database import get_db
from models import SmartRule, AgentAction, User, AuditLog
from dependencies import get_current_user, require_admin, require_csrf, get_organization_filter
from datetime import datetime, UTC, timedelta
import json
import asyncio
import logging
from typing import Dict, Any, List
import psutil
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory alert store for real-time processing
active_alerts = {}
alert_subscribers = []

class AlertEngine:
    """Enterprise-grade alert processing engine"""
    
    @staticmethod
    async def evaluate_rules(metrics_data: Dict[str, Any], db: Session, org_id: int = None):
        """Evaluate all active smart rules against real-time metrics - ENTERPRISE: Multi-tenant isolated"""
        try:
            # SEC-082: Get active smart rules filtered by organization
            query = db.query(SmartRule).filter(SmartRule.is_active == True)

            if org_id is not None:
                query = query.filter(SmartRule.organization_id == org_id)

            active_rules = query.all()
            
            triggered_alerts = []
            
            for rule in active_rules:
                try:
                    rule_config = json.loads(rule.rule_definition) if isinstance(rule.rule_definition, str) else rule.rule_definition
                    
                    if AlertEngine._evaluate_rule_condition(rule_config, metrics_data):
                        alert = {
                            "id": f"alert_{rule.id}_{int(datetime.now(UTC).timestamp())}",
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "severity": rule_config.get("severity", "medium"),
                            "message": AlertEngine._generate_alert_message(rule, metrics_data),
                            "triggered_at": datetime.now(UTC).isoformat(),
                            "metrics_snapshot": metrics_data,
                            "status": "active",
                            # ONBOARD-018: Store org_id for tenant isolation
                            "organization_id": org_id
                        }
                        
                        triggered_alerts.append(alert)
                        active_alerts[alert["id"]] = alert
                        
                        # Log alert trigger
                        logger.info(f"🚨 Alert triggered: {alert['rule_name']} for severity {alert['severity']}")
                        
                except Exception as rule_error:
                    logger.error(f"Error evaluating rule {rule.id}: {rule_error}")
                    continue
            
            # Broadcast alerts to WebSocket subscribers
            if triggered_alerts:
                await AlertEngine._broadcast_alerts(triggered_alerts)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Alert evaluation error: {e}")
            return []
    
    @staticmethod
    def _evaluate_rule_condition(rule_config: Dict, metrics: Dict) -> bool:
        """Evaluate if rule condition is met based on metrics"""
        try:
            condition_type = rule_config.get("condition_type", "threshold")
            
            if condition_type == "threshold":
                metric_name = rule_config.get("metric")
                operator = rule_config.get("operator", ">")
                threshold = rule_config.get("threshold", 0)
                
                current_value = AlertEngine._get_nested_metric(metrics, metric_name)
                if current_value is None:
                    return False
                
                if operator == ">":
                    return current_value > threshold
                elif operator == "<":
                    return current_value < threshold
                elif operator == ">=":
                    return current_value >= threshold
                elif operator == "<=":
                    return current_value <= threshold
                elif operator == "==":
                    return current_value == threshold
                    
            elif condition_type == "anomaly":
                # Implement anomaly detection logic
                metric_name = rule_config.get("metric")
                sensitivity = rule_config.get("sensitivity", 0.8)
                current_value = AlertEngine._get_nested_metric(metrics, metric_name)
                
                # Simplified anomaly detection (in production, use proper ML)
                historical_avg = rule_config.get("historical_average", current_value)
                deviation_threshold = historical_avg * sensitivity
                
                return abs(current_value - historical_avg) > deviation_threshold
                
            elif condition_type == "pattern":
                # Pattern-based alerting
                pattern = rule_config.get("pattern", {})
                return AlertEngine._match_pattern(metrics, pattern)
            
            return False
            
        except Exception as e:
            logger.error(f"Rule condition evaluation error: {e}")
            return False
    
    @staticmethod
    def _get_nested_metric(metrics: Dict, metric_path: str):
        """Get nested metric value using dot notation (e.g., 'system.cpu_percent')"""
        try:
            keys = metric_path.split('.')
            value = metrics
            for key in keys:
                value = value.get(key)
                if value is None:
                    return None
            return value
        except:
            return None
    
    @staticmethod
    def _match_pattern(metrics: Dict, pattern: Dict) -> bool:
        """Match complex patterns in metrics"""
        # Implement pattern matching logic
        # This could include multiple metric conditions, time-based patterns, etc.
        return False
    
    @staticmethod
    def _generate_alert_message(rule: SmartRule, metrics: Dict) -> str:
        """Generate human-readable alert message"""
        rule_config = json.loads(rule.rule_definition) if isinstance(rule.rule_definition, str) else rule.rule_definition
        
        if rule_config.get("condition_type") == "threshold":
            metric_name = rule_config.get("metric", "unknown")
            current_value = AlertEngine._get_nested_metric(metrics, metric_name)
            threshold = rule_config.get("threshold", 0)
            operator = rule_config.get("operator", ">")
            
            return f"{rule.name}: {metric_name} is {current_value} (threshold: {operator} {threshold})"
        
        return f"{rule.name}: Alert condition met"
    
    @staticmethod
    async def _broadcast_alerts(alerts: List[Dict]):
        """Broadcast alerts to all WebSocket subscribers"""
        if not alert_subscribers:
            return
            
        message = {
            "type": "alerts",
            "data": alerts,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Send to all connected subscribers
        disconnected = []
        for websocket in alert_subscribers:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # Clean up disconnected subscribers
        for ws in disconnected:
            if ws in alert_subscribers:
                alert_subscribers.remove(ws)

@router.get("/active")
async def get_active_alerts(
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """
    Get all currently active alerts for the user's organization.

    ONBOARD-018: Fixed critical data leak - now filters by organization_id
    Security: Tenant-isolated via organization_id filter
    Compliance: SOC 2 CC6.1, HIPAA 164.312(a)(1)
    """
    try:
        logger.info(f"🚨 Active alerts requested by: {current_user.get('email')} [org_id={org_id}]")

        # ONBOARD-018: Filter alerts by organization_id for tenant isolation
        user_alerts = [
            alert for alert in active_alerts.values()
            if alert.get("organization_id") == org_id
        ]

        # Add alert statistics (tenant-scoped)
        stats = {
            "total_active": len(user_alerts),
            "by_severity": {
                "critical": len([a for a in user_alerts if a.get("severity") == "critical"]),
                "high": len([a for a in user_alerts if a.get("severity") == "high"]),
                "medium": len([a for a in user_alerts if a.get("severity") == "medium"]),
                "low": len([a for a in user_alerts if a.get("severity") == "low"])
            }
        }

        return {
            "alerts": user_alerts,
            "statistics": stats,
            "last_updated": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert - supports both database and demo alerts - ENTERPRISE: Multi-tenant isolated"""
    from sqlalchemy import text
    logger.info(f"🔔 Acknowledge request received for alert {alert_id} by {current_user.get('email')}")
    try:
        # Try database first with org filtering
        try:
            # SEC-082: Add organization_id filter to prevent cross-tenant manipulation
            result = db.execute(text("""
                UPDATE alerts
                SET status = 'acknowledged',
                    acknowledged_by = :user_email,
                    acknowledged_at = NOW()
                WHERE id = :alert_id AND organization_id = :org_id
                RETURNING id
            """), {"alert_id": alert_id, "user_email": current_user.get("email"), "org_id": org_id})

            if result.rowcount > 0:
                db.commit()
                logger.info(f"✅ Alert {alert_id} acknowledged by {current_user.get('email')}")
                return {"success": True, "message": "Alert acknowledged successfully"}
        except Exception as db_error:
            logger.error(f"Database update failed: {db_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

        # SEC-089: REMOVED demo alert handling (IDs 3001-3005 and in-memory fallback)
        # Production only handles real database alerts
        raise HTTPException(status_code=404, detail="Alert not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user), _=Depends(require_csrf),
    db: Session = Depends(get_db)
):

    """Resolve an alert"""
    try:
        if alert_id not in active_alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        active_alerts[alert_id]["status"] = "resolved"
        active_alerts[alert_id]["resolved_by"] = current_user.get('email')
        active_alerts[alert_id]["resolved_at"] = datetime.now(UTC).isoformat()
        
        logger.info(f"✅ Alert {alert_id} resolved by {current_user.get('email')}")
        
        # Remove from active alerts after marking as resolved
        del active_alerts[alert_id]
        
        return {"message": "Alert resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

async def get_alert_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: int = Depends(get_organization_filter)
):

    """SEC-089: Get alert history from real database"""
    try:
        logger.info(f"📊 Alert history requested by: {current_user.get('email')} for {days} days")

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        # SEC-089: Query real alert history from database
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT id, title, severity, timestamp, acknowledged_at, status
            FROM alerts
            WHERE organization_id = :org_id
              AND timestamp >= :start_date
            ORDER BY timestamp DESC
            LIMIT 100
        """), {"org_id": org_id, "start_date": start_date}).fetchall()

        history = []
        for row in result:
            history.append({
                "id": str(row[0]),
                "rule_name": row[1] or "Alert",
                "severity": row[2] or "medium",
                "triggered_at": row[3].isoformat() if row[3] else None,
                "resolved_at": row[4].isoformat() if row[4] else None,
                "status": row[5] or "pending"
            })

        return {
            "history": history,
            "total_count": len(history),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "has_activity": len(history) > 0,
            "message": None if history else "No alert history for this period"
        }
        
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alert history")

@router.websocket("/stream")
async def alert_stream(websocket: WebSocket, current_user: dict = Depends(get_current_user)):
    """WebSocket endpoint for real-time alert streaming"""
    await websocket.accept()
    alert_subscribers.append(websocket)
    logger.info(f"🔌 Alert stream connected: {current_user.get('email')}")
    
    try:
        # Send current active alerts on connection
        if active_alerts:
            initial_message = {
                "type": "initial_alerts",
                "data": list(active_alerts.values()),
                "timestamp": datetime.now(UTC).isoformat()
            }
            await websocket.send_text(json.dumps(initial_message))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"🔌 Alert stream disconnected: {current_user.get('email')}")
        if websocket in alert_subscribers:
            alert_subscribers.remove(websocket)
    except Exception as e:
        logger.error(f"Alert stream error: {e}")
        if websocket in alert_subscribers:
            alert_subscribers.remove(websocket)

# Background task to continuously evaluate rules against real-time metrics
async def start_alert_monitoring():
    """Background task to monitor and trigger alerts"""
    logger.info("🚨 Starting Smart Alert Monitoring Engine...")
    
    while True:
        try:
            # This would integrate with your analytics routes to get real-time metrics
            # For now, simulate with system metrics
            metrics_data = {
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            # Evaluate rules against metrics (you'd pass the db session here)
            # await AlertEngine.evaluate_rules(metrics_data, db)
            
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Alert monitoring error: {e}")
            await asyncio.sleep(60)  # Wait longer on error
@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf),
    db: Session = Depends(get_db)
):
    """Escalate alert to security team - supports both database and demo alerts - ENTERPRISE: Multi-tenant isolated"""
    from sqlalchemy import text
    logger.info(f"⚠️ Escalate request received for alert {alert_id} by {current_user.get('email')}")
    try:
        # Try database first with org filtering
        try:
            # SEC-082: Add organization_id filter to prevent cross-tenant manipulation
            result = db.execute(text("""
                UPDATE alerts
                SET status = 'escalated',
                    severity = 'high',
                    escalated_by = :user_email,
                    escalated_at = NOW()
                WHERE id = :alert_id AND organization_id = :org_id
                RETURNING id
            """), {"alert_id": alert_id, "user_email": current_user.get("email"), "org_id": org_id})

            if result.rowcount > 0:
                db.commit()
                logger.warning(f"⚠️ Alert {alert_id} escalated by {current_user.get('email')}")
                return {"success": True, "message": "Alert escalated to security team"}
        except Exception as db_error:
            logger.error(f"Database update failed: {db_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to escalate alert")

        # SEC-089: REMOVED demo alert handling (IDs 3001-3005 and in-memory fallback)
        # Production only handles real database alerts
        raise HTTPException(status_code=404, detail="Alert not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))
