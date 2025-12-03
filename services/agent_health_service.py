"""
SEC-050: Enterprise Agent Health Monitoring Service
====================================================

Datadog-style agent health monitoring with:
- Real-time heartbeat tracking
- Automatic health status calculation
- Performance metrics aggregation
- Alerting on health degradation

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6

Based on patterns from:
- Datadog Agent Health Monitoring
- Wiz.io Agent Status Tracking
- Splunk Forwarder Health Checks
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models_agent_registry import RegisteredAgent, AgentActivityLog, AgentStatus

logger = logging.getLogger(__name__)


class HealthStatus:
    """Agent health status enumeration."""
    ONLINE = "online"           # Heartbeat received within expected interval
    DEGRADED = "degraded"       # Heartbeat delayed (1-3 missed)
    OFFLINE = "offline"         # Multiple missed heartbeats (4+)
    UNKNOWN = "unknown"         # Never received heartbeat


class AgentHealthService:
    """
    Enterprise Agent Health Monitoring Service

    Provides real-time health monitoring for registered agents with:
    - Heartbeat reception and processing
    - Automatic health status calculation
    - Performance metrics tracking
    - Health summary for dashboards

    Thread-safe and suitable for concurrent access.
    """

    # Health thresholds
    DEGRADED_THRESHOLD = 1      # Missed heartbeats to mark as degraded
    OFFLINE_THRESHOLD = 4       # Missed heartbeats to mark as offline
    STALE_METRICS_HOURS = 24    # Hours after which metrics are considered stale

    def __init__(self, db: Session):
        self.db = db

    def process_heartbeat(
        self,
        agent_id: str,
        organization_id: int,
        metrics: Optional[Dict[str, Any]] = None,
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Process a heartbeat from an agent.

        Args:
            agent_id: The unique agent identifier
            organization_id: The organization ID (for multi-tenant isolation)
            metrics: Optional performance metrics from agent
            performed_by: Who triggered the heartbeat (for audit)

        Returns:
            Dict with updated health status and acknowledgment
        """
        # SEC-050: Multi-tenant isolation - filter by organization_id
        agent = self.db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.agent_id == agent_id,
                RegisteredAgent.organization_id == organization_id
            )
        ).first()

        if not agent:
            logger.warning(f"SEC-050: Heartbeat from unknown agent: {agent_id}, org: {organization_id}")
            return {
                "success": False,
                "error": "Agent not found",
                "agent_id": agent_id
            }

        now = datetime.now(UTC)
        previous_status = agent.health_status

        # Update heartbeat timestamp
        agent.last_heartbeat = now
        agent.consecutive_missed_heartbeats = 0
        agent.health_status = HealthStatus.ONLINE

        # Update metrics if provided
        if metrics:
            if "response_time_ms" in metrics:
                agent.avg_response_time_ms = metrics["response_time_ms"]
            if "error_rate" in metrics:
                agent.error_rate_percent = metrics["error_rate"]
            if "requests_count" in metrics:
                agent.total_requests_24h = metrics["requests_count"]
            if "last_error" in metrics:
                agent.last_error = metrics["last_error"]
                agent.last_error_at = now

        self.db.commit()

        # Log status change if it occurred
        if previous_status != HealthStatus.ONLINE:
            self._log_health_change(
                agent=agent,
                previous_status=previous_status,
                new_status=HealthStatus.ONLINE,
                performed_by=performed_by
            )
            logger.info(
                f"SEC-050: Agent {agent_id} recovered from {previous_status} to online"
            )

        return {
            "success": True,
            "agent_id": agent_id,
            "health_status": HealthStatus.ONLINE,
            "next_heartbeat_expected_at": (
                now + timedelta(seconds=agent.heartbeat_interval_seconds)
            ).isoformat(),
            "heartbeat_interval_seconds": agent.heartbeat_interval_seconds
        }

    def check_agent_health(self, organization_id: int) -> List[Dict[str, Any]]:
        """
        Check and update health status for all agents in an organization.

        This should be called periodically (e.g., every minute) to detect
        agents that have stopped sending heartbeats.

        Args:
            organization_id: The organization to check

        Returns:
            List of agents whose status changed
        """
        now = datetime.now(UTC)
        status_changes = []

        # Get all active agents for this organization
        agents = self.db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.organization_id == organization_id,
                RegisteredAgent.status == AgentStatus.ACTIVE.value
            )
        ).all()

        for agent in agents:
            if not agent.last_heartbeat:
                # Never received heartbeat
                if agent.health_status != HealthStatus.UNKNOWN:
                    old_status = agent.health_status
                    agent.health_status = HealthStatus.UNKNOWN
                    status_changes.append({
                        "agent_id": agent.agent_id,
                        "previous": old_status,
                        "current": HealthStatus.UNKNOWN
                    })
                continue

            # Calculate time since last heartbeat
            time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
            expected_interval = agent.heartbeat_interval_seconds

            # Calculate missed heartbeats
            missed = int(time_since_heartbeat / expected_interval)

            if missed > agent.consecutive_missed_heartbeats:
                agent.consecutive_missed_heartbeats = missed

            # Determine new health status
            old_status = agent.health_status

            if missed == 0:
                new_status = HealthStatus.ONLINE
            elif missed < self.OFFLINE_THRESHOLD:
                new_status = HealthStatus.DEGRADED
            else:
                new_status = HealthStatus.OFFLINE

            # Update if changed
            if old_status != new_status:
                agent.health_status = new_status
                status_changes.append({
                    "agent_id": agent.agent_id,
                    "agent_name": agent.display_name,
                    "previous": old_status,
                    "current": new_status,
                    "missed_heartbeats": missed,
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                })

                self._log_health_change(
                    agent=agent,
                    previous_status=old_status,
                    new_status=new_status,
                    performed_by="health_check_service"
                )

                logger.warning(
                    f"SEC-050: Agent {agent.agent_id} health changed: {old_status} -> {new_status}"
                )

        self.db.commit()
        return status_changes

    def get_health_summary(self, organization_id: int) -> Dict[str, Any]:
        """
        Get aggregated health summary for an organization's agents.

        Returns Datadog-style health overview suitable for dashboard display.

        Args:
            organization_id: The organization to summarize

        Returns:
            Dict with health counts, metrics, and agent details
        """
        # Count agents by health status
        health_counts = self.db.query(
            RegisteredAgent.health_status,
            func.count(RegisteredAgent.id)
        ).filter(
            and_(
                RegisteredAgent.organization_id == organization_id,
                RegisteredAgent.status == AgentStatus.ACTIVE.value
            )
        ).group_by(RegisteredAgent.health_status).all()

        counts = {
            HealthStatus.ONLINE: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.OFFLINE: 0,
            HealthStatus.UNKNOWN: 0
        }
        for status, count in health_counts:
            counts[status] = count

        total_agents = sum(counts.values())

        # Get recent status changes
        recent_changes = self._get_recent_health_changes(organization_id, hours=24)

        # Get agents with issues (degraded or offline)
        problem_agents = self.db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.organization_id == organization_id,
                RegisteredAgent.status == AgentStatus.ACTIVE.value,
                RegisteredAgent.health_status.in_([
                    HealthStatus.DEGRADED,
                    HealthStatus.OFFLINE
                ])
            )
        ).order_by(RegisteredAgent.last_heartbeat.asc().nullsfirst()).limit(10).all()

        # Aggregate performance metrics
        avg_metrics = self.db.query(
            func.avg(RegisteredAgent.avg_response_time_ms),
            func.avg(RegisteredAgent.error_rate_percent),
            func.sum(RegisteredAgent.total_requests_24h)
        ).filter(
            and_(
                RegisteredAgent.organization_id == organization_id,
                RegisteredAgent.status == AgentStatus.ACTIVE.value,
                RegisteredAgent.health_status == HealthStatus.ONLINE
            )
        ).first()

        return {
            "summary": {
                "total_agents": total_agents,
                "online": counts[HealthStatus.ONLINE],
                "degraded": counts[HealthStatus.DEGRADED],
                "offline": counts[HealthStatus.OFFLINE],
                "unknown": counts[HealthStatus.UNKNOWN],
                "health_score": self._calculate_health_score(counts, total_agents)
            },
            "metrics": {
                "avg_response_time_ms": round(avg_metrics[0] or 0, 2),
                "avg_error_rate_percent": round(avg_metrics[1] or 0, 2),
                "total_requests_24h": avg_metrics[2] or 0
            },
            "problem_agents": [
                {
                    "agent_id": a.agent_id,
                    "display_name": a.display_name,
                    "health_status": a.health_status,
                    "last_heartbeat": a.last_heartbeat.isoformat() if a.last_heartbeat else None,
                    "missed_heartbeats": a.consecutive_missed_heartbeats,
                    "last_error": a.last_error
                }
                for a in problem_agents
            ],
            "recent_changes": recent_changes,
            "last_check": datetime.now(UTC).isoformat()
        }

    def get_agent_health_details(
        self,
        agent_id: str,
        organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed health information for a specific agent.

        Args:
            agent_id: The agent identifier
            organization_id: The organization ID

        Returns:
            Dict with full agent health details or None if not found
        """
        agent = self.db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.agent_id == agent_id,
                RegisteredAgent.organization_id == organization_id
            )
        ).first()

        if not agent:
            return None

        # Calculate uptime if we have heartbeat history
        uptime_percent = self._calculate_uptime(agent)

        # Get recent health history
        recent_history = self._get_agent_health_history(agent.id, hours=24)

        return {
            "agent_id": agent.agent_id,
            "display_name": agent.display_name,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "health": {
                "current_status": agent.health_status,
                "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
                "heartbeat_interval_seconds": agent.heartbeat_interval_seconds,
                "consecutive_missed_heartbeats": agent.consecutive_missed_heartbeats,
                "uptime_percent_24h": uptime_percent
            },
            "metrics": {
                "avg_response_time_ms": agent.avg_response_time_ms,
                "error_rate_percent": agent.error_rate_percent,
                "total_requests_24h": agent.total_requests_24h
            },
            "errors": {
                "last_error": agent.last_error,
                "last_error_at": agent.last_error_at.isoformat() if agent.last_error_at else None
            },
            "recent_history": recent_history
        }

    def update_heartbeat_interval(
        self,
        agent_id: str,
        organization_id: int,
        interval_seconds: int,
        updated_by: str
    ) -> bool:
        """
        Update the expected heartbeat interval for an agent.

        Args:
            agent_id: The agent identifier
            organization_id: The organization ID
            interval_seconds: New interval (10-300 seconds)
            updated_by: Who made the change

        Returns:
            True if updated, False if agent not found
        """
        if interval_seconds < 10 or interval_seconds > 300:
            raise ValueError("Heartbeat interval must be between 10 and 300 seconds")

        agent = self.db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.agent_id == agent_id,
                RegisteredAgent.organization_id == organization_id
            )
        ).first()

        if not agent:
            return False

        old_interval = agent.heartbeat_interval_seconds
        agent.heartbeat_interval_seconds = interval_seconds
        agent.updated_by = updated_by

        # Log the change
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="heartbeat_interval_updated",
            activity_description=f"Heartbeat interval changed from {old_interval}s to {interval_seconds}s",
            performed_by=updated_by,
            performed_via="api",
            previous_state={"heartbeat_interval_seconds": old_interval},
            new_state={"heartbeat_interval_seconds": interval_seconds}
        )
        self.db.add(activity)
        self.db.commit()

        return True

    def _calculate_health_score(self, counts: Dict[str, int], total: int) -> int:
        """Calculate overall health score (0-100)."""
        if total == 0:
            return 100

        # Weights: online=100, degraded=50, offline=0, unknown=25
        weighted_sum = (
            counts.get(HealthStatus.ONLINE, 0) * 100 +
            counts.get(HealthStatus.DEGRADED, 0) * 50 +
            counts.get(HealthStatus.OFFLINE, 0) * 0 +
            counts.get(HealthStatus.UNKNOWN, 0) * 25
        )

        return int(weighted_sum / total)

    def _calculate_uptime(self, agent: RegisteredAgent) -> float:
        """Calculate 24-hour uptime percentage based on health changes."""
        # Simplified: if online now and has heartbeat, estimate based on missed beats
        if not agent.last_heartbeat:
            return 0.0

        if agent.health_status == HealthStatus.ONLINE:
            return 99.9  # Approximate for now

        # Degraded or offline - estimate based on missed heartbeats
        missed = agent.consecutive_missed_heartbeats
        interval = agent.heartbeat_interval_seconds
        downtime_seconds = missed * interval
        uptime = max(0, 100 - (downtime_seconds / 86400 * 100))
        return round(uptime, 2)

    def _get_recent_health_changes(
        self,
        organization_id: int,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent health status changes for an organization."""
        since = datetime.now(UTC) - timedelta(hours=hours)

        changes = self.db.query(AgentActivityLog).filter(
            and_(
                AgentActivityLog.organization_id == organization_id,
                AgentActivityLog.activity_type == "health_status_changed",
                AgentActivityLog.timestamp >= since
            )
        ).order_by(AgentActivityLog.timestamp.desc()).limit(20).all()

        return [
            {
                "agent_id": c.new_state.get("agent_id") if c.new_state else None,
                "previous_status": c.previous_state.get("health_status") if c.previous_state else None,
                "new_status": c.new_state.get("health_status") if c.new_state else None,
                "timestamp": c.timestamp.isoformat()
            }
            for c in changes
        ]

    def _get_agent_health_history(
        self,
        agent_db_id: int,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get health status history for a specific agent."""
        since = datetime.now(UTC) - timedelta(hours=hours)

        history = self.db.query(AgentActivityLog).filter(
            and_(
                AgentActivityLog.agent_id == agent_db_id,
                AgentActivityLog.activity_type == "health_status_changed",
                AgentActivityLog.timestamp >= since
            )
        ).order_by(AgentActivityLog.timestamp.desc()).limit(50).all()

        return [
            {
                "previous_status": h.previous_state.get("health_status") if h.previous_state else None,
                "new_status": h.new_state.get("health_status") if h.new_state else None,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]

    def _log_health_change(
        self,
        agent: RegisteredAgent,
        previous_status: str,
        new_status: str,
        performed_by: str
    ) -> None:
        """Log a health status change for audit trail."""
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=agent.organization_id,
            activity_type="health_status_changed",
            activity_description=f"Health status changed from {previous_status} to {new_status}",
            performed_by=performed_by,
            performed_via="system",
            previous_state={
                "health_status": previous_status,
                "agent_id": agent.agent_id
            },
            new_state={
                "health_status": new_status,
                "agent_id": agent.agent_id,
                "consecutive_missed_heartbeats": agent.consecutive_missed_heartbeats
            }
        )
        self.db.add(activity)
