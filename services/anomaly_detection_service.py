"""
SEC-077: Enterprise Anomaly Detection Service
=============================================

Statistical anomaly detection for AI agent behavior monitoring.
Uses Z-score algorithm with configurable sensitivity thresholds.

Industry Alignment:
- Datadog Anomaly Detection monitors
- Splunk Machine Learning Toolkit (MLTK)
- AWS CloudWatch Anomaly Detection

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6

Created: 2025-12-04
"""

from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging
import math

logger = logging.getLogger(__name__)


class AnomalySeverity:
    """Severity levels for detected anomalies."""
    LOW = "low"           # 1-2 std deviations
    MEDIUM = "medium"     # 2-3 std deviations
    HIGH = "high"         # 3-4 std deviations
    CRITICAL = "critical" # >4 std deviations


class AnomalyType:
    """Types of anomalies detected."""
    ACTION_RATE = "action_rate"       # Unusual action frequency
    ERROR_RATE = "error_rate"         # Unusual error rate
    RISK_SCORE = "risk_score"         # Unusual risk pattern
    COMBINED = "combined"             # Multiple anomaly indicators


class AnomalyDetectionService:
    """
    Enterprise Anomaly Detection for Agent Governance

    Implements statistical anomaly detection to:
    1. Establish behavioral baselines for each agent
    2. Calculate rolling statistics (EMA, SMA, std dev)
    3. Detect deviations using Z-score algorithm
    4. Trigger alerts and auto-suspension on critical anomalies

    Algorithm: Z-score based detection
    - z = (x - μ) / σ
    - |z| > threshold indicates anomaly
    - Default threshold: 2.0 (95% confidence)

    Compliance:
    - SOC 2 CC7.1: Monitoring for unauthorized changes
    - NIST SI-4: Information system monitoring
    - PCI-DSS 10.6: Review security events
    """

    # EMA smoothing factor (0.1 = slow adaptation, 0.3 = fast adaptation)
    EMA_ALPHA = 0.2

    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id

    def check_agent_anomalies(self, agent_id: int) -> Dict[str, Any]:
        """
        Check agent for anomalous behavior across all metrics.

        Args:
            agent_id: Registered agent ID

        Returns:
            dict: Anomaly detection results
        """
        from models_agent_registry import RegisteredAgent

        agent = self._get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found", "agent_id": agent_id}

        if not agent.anomaly_detection_enabled:
            return {
                "agent_id": agent_id,
                "enabled": False,
                "message": "Anomaly detection is disabled for this agent",
            }

        now = datetime.now(UTC)
        anomalies = []

        # Get current metrics
        current_metrics = self._get_current_metrics(agent)

        # Check action rate anomaly
        if agent.rolling_avg_actions_24h and agent.rolling_std_actions:
            action_result = self._check_zscore_anomaly(
                current_value=current_metrics["actions_per_hour"],
                mean=agent.rolling_avg_actions_24h,
                std_dev=agent.rolling_std_actions,
                threshold=agent.anomaly_sensitivity,
                metric_name="action_rate"
            )
            if action_result["is_anomaly"]:
                anomalies.append(action_result)

        # Check error rate anomaly
        if agent.rolling_avg_error_rate_24h and agent.rolling_std_error_rate:
            error_result = self._check_zscore_anomaly(
                current_value=current_metrics["error_rate"],
                mean=agent.rolling_avg_error_rate_24h,
                std_dev=agent.rolling_std_error_rate,
                threshold=agent.anomaly_sensitivity,
                metric_name="error_rate"
            )
            if error_result["is_anomaly"]:
                anomalies.append(error_result)

        # Check risk score anomaly
        if agent.rolling_avg_risk_24h and agent.rolling_std_risk:
            risk_result = self._check_zscore_anomaly(
                current_value=current_metrics["avg_risk_score"],
                mean=agent.rolling_avg_risk_24h,
                std_dev=agent.rolling_std_risk,
                threshold=agent.anomaly_sensitivity,
                metric_name="risk_score"
            )
            if risk_result["is_anomaly"]:
                anomalies.append(risk_result)

        # Update agent anomaly tracking
        if anomalies:
            max_severity = self._get_max_severity(anomalies)
            agent.consecutive_anomalies += 1
            agent.last_anomaly_detected = now
            agent.last_anomaly_severity = max_severity
            agent.anomaly_count_24h += 1

            # Check for escalation
            should_escalate = agent.consecutive_anomalies >= agent.anomaly_escalation_threshold
            should_suspend = (
                agent.anomaly_auto_suspend and
                max_severity == AnomalySeverity.CRITICAL
            )

            if should_suspend:
                agent.status = "suspended"
                agent.auto_suspended_at = now
                agent.auto_suspend_reason = f"SEC-077: Critical anomaly detected - {anomalies[0]['metric']}"
                logger.warning(
                    f"SEC-077: Agent {agent.agent_id} AUTO-SUSPENDED due to critical anomaly"
                )

            self.db.commit()

            return {
                "agent_id": agent_id,
                "agent_name": agent.display_name,
                "anomaly_detected": True,
                "anomalies": anomalies,
                "severity": max_severity,
                "consecutive_anomalies": agent.consecutive_anomalies,
                "escalation_triggered": should_escalate,
                "auto_suspended": should_suspend,
                "threshold": agent.anomaly_sensitivity,
                "checked_at": now.isoformat(),
            }
        else:
            # No anomaly - reset consecutive count
            agent.consecutive_anomalies = 0
            agent.last_anomaly_check = now
            self.db.commit()

            return {
                "agent_id": agent_id,
                "agent_name": agent.display_name,
                "anomaly_detected": False,
                "current_metrics": current_metrics,
                "checked_at": now.isoformat(),
            }

    def update_rolling_statistics(self, agent_id: int) -> Dict[str, Any]:
        """
        Update rolling statistics for an agent based on historical data.
        Should be called periodically (e.g., hourly) or after significant activity.

        Args:
            agent_id: Registered agent ID

        Returns:
            dict: Updated statistics
        """
        agent = self._get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found", "agent_id": agent_id}

        now = datetime.now(UTC)
        window_hours = agent.baseline_window_hours or 168  # Default 1 week

        # Get historical metrics
        historical = self._get_historical_metrics(agent, window_hours)

        if not historical or len(historical) < 24:  # Need at least 24 hours of data
            return {
                "agent_id": agent_id,
                "status": "insufficient_data",
                "data_points": len(historical) if historical else 0,
                "required": 24,
            }

        # Calculate rolling statistics
        actions_data = [h["actions"] for h in historical]
        error_data = [h["error_rate"] for h in historical]
        risk_data = [h["avg_risk"] for h in historical]

        # Update agent statistics
        agent.rolling_avg_actions_24h = self._calculate_sma(actions_data[-24:])
        agent.rolling_avg_actions_1h = self._calculate_ema(actions_data, self.EMA_ALPHA)
        agent.rolling_std_actions = self._calculate_std(actions_data)

        agent.rolling_avg_error_rate_24h = self._calculate_sma(error_data[-24:])
        agent.rolling_avg_error_rate_1h = self._calculate_ema(error_data, self.EMA_ALPHA)
        agent.rolling_std_error_rate = self._calculate_std(error_data)

        agent.rolling_avg_risk_24h = self._calculate_sma(risk_data[-24:])
        agent.rolling_avg_risk_1h = self._calculate_ema(risk_data, self.EMA_ALPHA)
        agent.rolling_std_risk = self._calculate_std(risk_data)

        # Update baseline if enough deviation
        if not agent.baseline_actions_per_hour or self._should_update_baseline(agent):
            agent.baseline_actions_per_hour = agent.rolling_avg_actions_24h
            agent.baseline_error_rate = agent.rolling_avg_error_rate_24h
            agent.baseline_avg_risk_score = agent.rolling_avg_risk_24h

        agent.last_baseline_update = now
        self.db.commit()

        return {
            "agent_id": agent_id,
            "agent_name": agent.display_name,
            "updated_at": now.isoformat(),
            "data_points": len(historical),
            "statistics": {
                "actions": {
                    "avg_24h": agent.rolling_avg_actions_24h,
                    "avg_1h": agent.rolling_avg_actions_1h,
                    "std_dev": agent.rolling_std_actions,
                },
                "error_rate": {
                    "avg_24h": agent.rolling_avg_error_rate_24h,
                    "avg_1h": agent.rolling_avg_error_rate_1h,
                    "std_dev": agent.rolling_std_error_rate,
                },
                "risk_score": {
                    "avg_24h": agent.rolling_avg_risk_24h,
                    "avg_1h": agent.rolling_avg_risk_1h,
                    "std_dev": agent.rolling_std_risk,
                },
            },
        }

    def get_anomaly_history(
        self,
        agent_id: Optional[int] = None,
        hours: int = 24,
        severity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get anomaly detection history for analysis.

        Args:
            agent_id: Optional filter by specific agent
            hours: Lookback period in hours
            severity_filter: Optional filter by severity level

        Returns:
            list: Historical anomaly events
        """
        from models_agent_registry import RegisteredAgent

        query = self.db.query(RegisteredAgent).filter(
            RegisteredAgent.organization_id == self.organization_id,
            RegisteredAgent.anomaly_detection_enabled == True,
            RegisteredAgent.last_anomaly_detected.isnot(None)
        )

        if agent_id:
            query = query.filter(RegisteredAgent.id == agent_id)

        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        query = query.filter(RegisteredAgent.last_anomaly_detected >= cutoff)

        if severity_filter:
            query = query.filter(RegisteredAgent.last_anomaly_severity == severity_filter)

        agents = query.all()

        return [
            {
                "agent_id": a.id,
                "agent_name": a.display_name,
                "last_anomaly": a.last_anomaly_detected.isoformat() if a.last_anomaly_detected else None,
                "severity": a.last_anomaly_severity,
                "consecutive_count": a.consecutive_anomalies,
                "anomaly_count_24h": a.anomaly_count_24h,
                "status": a.status,
                "auto_suspended": a.auto_suspended_at is not None,
            }
            for a in agents
        ]

    def configure_agent_detection(
        self,
        agent_id: int,
        enabled: Optional[bool] = None,
        sensitivity: Optional[float] = None,
        auto_suspend: Optional[bool] = None,
        escalation_threshold: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Configure anomaly detection settings for an agent.

        Args:
            agent_id: Registered agent ID
            enabled: Enable/disable detection
            sensitivity: Z-score threshold (1.0-4.0)
            auto_suspend: Auto-suspend on critical anomaly
            escalation_threshold: Consecutive anomalies before escalation

        Returns:
            dict: Updated configuration
        """
        agent = self._get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found", "agent_id": agent_id}

        if enabled is not None:
            agent.anomaly_detection_enabled = enabled

        if sensitivity is not None:
            # Validate sensitivity range
            if not 1.0 <= sensitivity <= 4.0:
                return {"error": "Sensitivity must be between 1.0 and 4.0"}
            agent.anomaly_sensitivity = sensitivity

        if auto_suspend is not None:
            agent.anomaly_auto_suspend = auto_suspend

        if escalation_threshold is not None:
            if not 1 <= escalation_threshold <= 10:
                return {"error": "Escalation threshold must be between 1 and 10"}
            agent.anomaly_escalation_threshold = escalation_threshold

        self.db.commit()

        return {
            "agent_id": agent_id,
            "agent_name": agent.display_name,
            "configuration": {
                "enabled": agent.anomaly_detection_enabled,
                "sensitivity": agent.anomaly_sensitivity,
                "auto_suspend": agent.anomaly_auto_suspend,
                "escalation_threshold": agent.anomaly_escalation_threshold,
                "algorithm": agent.anomaly_algorithm,
            },
        }

    def _get_agent(self, agent_id: int):
        """Get agent with organization isolation."""
        from models_agent_registry import RegisteredAgent

        return self.db.query(RegisteredAgent).filter(
            RegisteredAgent.id == agent_id,
            RegisteredAgent.organization_id == self.organization_id
        ).first()

    def _get_current_metrics(self, agent) -> Dict[str, float]:
        """Get current hourly metrics for an agent."""
        # Use the real-time metrics from the agent model
        return {
            "actions_per_hour": float(agent.total_requests_24h or 0) / 24.0,
            "error_rate": float(agent.error_rate_percent or 0),
            "avg_risk_score": float(agent.baseline_avg_risk_score or 50),
        }

    def _get_historical_metrics(self, agent, window_hours: int) -> List[Dict[str, float]]:
        """
        Get historical hourly metrics for baseline calculation.
        Queries agent_actions or agent_activity_logs table.
        """
        # Query historical data from agent actions
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)

        result = self.db.execute(
            text("""
                SELECT
                    date_trunc('hour', created_at) as hour,
                    COUNT(*) as actions,
                    COALESCE(AVG(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) * 100, 0) as error_rate,
                    COALESCE(AVG(risk_score), 50) as avg_risk
                FROM agent_actions
                WHERE organization_id = :org_id
                  AND agent_id = :agent_id
                  AND created_at >= :cutoff
                GROUP BY date_trunc('hour', created_at)
                ORDER BY hour
            """),
            {
                "org_id": self.organization_id,
                "agent_id": agent.agent_id,
                "cutoff": cutoff,
            }
        )

        return [
            {
                "hour": row.hour,
                "actions": float(row.actions),
                "error_rate": float(row.error_rate),
                "avg_risk": float(row.avg_risk),
            }
            for row in result
        ]

    def _check_zscore_anomaly(
        self,
        current_value: float,
        mean: float,
        std_dev: float,
        threshold: float,
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Check if current value is anomalous using Z-score.

        Z-score = (x - μ) / σ
        """
        if std_dev == 0:
            # No variance - can't detect anomaly
            return {"is_anomaly": False, "metric": metric_name}

        z_score = abs(current_value - mean) / std_dev
        is_anomaly = z_score > threshold

        severity = AnomalySeverity.LOW
        if z_score > 4.0:
            severity = AnomalySeverity.CRITICAL
        elif z_score > 3.0:
            severity = AnomalySeverity.HIGH
        elif z_score > 2.0:
            severity = AnomalySeverity.MEDIUM

        return {
            "is_anomaly": is_anomaly,
            "metric": metric_name,
            "current_value": round(current_value, 2),
            "expected_value": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "z_score": round(z_score, 2),
            "threshold": threshold,
            "severity": severity if is_anomaly else None,
            "direction": "high" if current_value > mean else "low",
        }

    def _calculate_sma(self, data: List[float]) -> float:
        """Calculate Simple Moving Average."""
        if not data:
            return 0.0
        return sum(data) / len(data)

    def _calculate_ema(self, data: List[float], alpha: float) -> float:
        """Calculate Exponential Moving Average."""
        if not data:
            return 0.0
        ema = data[0]
        for value in data[1:]:
            ema = alpha * value + (1 - alpha) * ema
        return ema

    def _calculate_std(self, data: List[float]) -> float:
        """Calculate Standard Deviation."""
        if len(data) < 2:
            return 0.0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        return math.sqrt(variance)

    def _get_max_severity(self, anomalies: List[Dict]) -> str:
        """Get the highest severity from a list of anomalies."""
        severity_order = {
            AnomalySeverity.LOW: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.HIGH: 3,
            AnomalySeverity.CRITICAL: 4,
        }
        max_sev = AnomalySeverity.LOW
        for anomaly in anomalies:
            if anomaly.get("severity"):
                if severity_order.get(anomaly["severity"], 0) > severity_order.get(max_sev, 0):
                    max_sev = anomaly["severity"]
        return max_sev

    def _should_update_baseline(self, agent) -> bool:
        """Determine if baseline should be updated based on drift."""
        if not agent.last_baseline_update:
            return True
        # Update baseline weekly
        age = datetime.now(UTC) - agent.last_baseline_update
        return age > timedelta(days=7)


# Convenience function for dependency injection
def get_anomaly_detector(db: Session, organization_id: int) -> AnomalyDetectionService:
    """Factory function for dependency injection."""
    return AnomalyDetectionService(db, organization_id)
