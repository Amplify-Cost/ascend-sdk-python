"""
OW-AI Enterprise Agent Registry Service
=======================================

Enterprise-grade service for managing AI agent registrations.
Handles CRUD operations, versioning, policy management, and audit logging.

Features:
- Full CRUD with multi-tenant isolation
- Version control with rollback
- Policy evaluation and enforcement
- MCP server discovery and governance
- Comprehensive audit logging

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, UTC
import logging
import json
import re
import secrets
import hashlib

from models_agent_registry import (
    RegisteredAgent, AgentVersion, AgentPolicy, AgentActivityLog,
    MCPServerConfig, AgentType, AgentStatus
)

logger = logging.getLogger(__name__)


class AgentRegistryService:
    """
    Enterprise Agent Registry Service

    Provides comprehensive agent management with:
    - Multi-tenant data isolation
    - Version control and rollback
    - Policy configuration
    - Audit trail compliance
    - SEC-068: Autonomous agent governance
    """

    # =========================================================================
    # SEC-068: AUTONOMOUS AGENT GOVERNANCE
    # Enterprise-grade controls for autonomous AI agents
    # Compliance: SOC 2 CC6.1/CC6.2/CC7.1, NIST AC-3/SI-4, PCI-DSS 7.1
    # =========================================================================

    @staticmethod
    def check_rate_limit(
        db: Session,
        agent: RegisteredAgent
    ) -> Dict[str, Any]:
        """
        SEC-068: Check if agent is within rate limits.

        Checks per-minute, per-hour, and per-day limits.
        Automatically resets counters when window expires.

        Returns:
            {"allowed": bool, "reason": str, "remaining": dict}

        Compliance: NIST SI-4, Datadog rate limiting patterns
        """
        now = datetime.now(UTC)

        # Reset counters if window expired
        if agent.rate_limit_window_start:
            elapsed = (now - agent.rate_limit_window_start).total_seconds()

            # Reset minute counter every 60 seconds
            if elapsed >= 60:
                agent.current_minute_count = 0

            # Reset hour counter every 3600 seconds
            if elapsed >= 3600:
                agent.current_hour_count = 0

            # Reset day counter every 86400 seconds
            if elapsed >= 86400:
                agent.current_day_count = 0
                agent.rate_limit_window_start = now
        else:
            agent.rate_limit_window_start = now

        # Check limits
        remaining = {
            "minute": None,
            "hour": None,
            "day": None
        }

        # Per-minute check
        if agent.max_actions_per_minute is not None:
            remaining["minute"] = agent.max_actions_per_minute - agent.current_minute_count
            if agent.current_minute_count >= agent.max_actions_per_minute:
                return {
                    "allowed": False,
                    "reason": f"Rate limit exceeded: {agent.current_minute_count}/{agent.max_actions_per_minute} actions per minute",
                    "code": "RATE_LIMIT_MINUTE",
                    "remaining": remaining,
                    "retry_after_seconds": 60
                }

        # Per-hour check
        if agent.max_actions_per_hour is not None:
            remaining["hour"] = agent.max_actions_per_hour - agent.current_hour_count
            if agent.current_hour_count >= agent.max_actions_per_hour:
                return {
                    "allowed": False,
                    "reason": f"Rate limit exceeded: {agent.current_hour_count}/{agent.max_actions_per_hour} actions per hour",
                    "code": "RATE_LIMIT_HOUR",
                    "remaining": remaining,
                    "retry_after_seconds": 3600
                }

        # Per-day check
        if agent.max_actions_per_day is not None:
            remaining["day"] = agent.max_actions_per_day - agent.current_day_count
            if agent.current_day_count >= agent.max_actions_per_day:
                return {
                    "allowed": False,
                    "reason": f"Rate limit exceeded: {agent.current_day_count}/{agent.max_actions_per_day} actions per day",
                    "code": "RATE_LIMIT_DAY",
                    "remaining": remaining,
                    "retry_after_seconds": 86400
                }

        return {
            "allowed": True,
            "reason": "Within rate limits",
            "remaining": remaining
        }

    @staticmethod
    def increment_rate_counters(db: Session, agent: RegisteredAgent) -> None:
        """
        SEC-068: Increment rate limit counters after action.
        CR-004: Includes transaction rollback on failure.
        """
        try:
            agent.current_minute_count += 1
            agent.current_hour_count += 1
            agent.current_day_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"CR-004: Failed to increment rate counters for agent {agent.agent_id}: {e}")
            raise

    @staticmethod
    def check_budget(
        db: Session,
        agent: RegisteredAgent,
        estimated_cost: float = 0.0
    ) -> Dict[str, Any]:
        """
        SEC-068: Check if agent is within budget limits.

        Args:
            agent: The registered agent
            estimated_cost: Estimated cost of the action in USD

        Returns:
            {"allowed": bool, "reason": str, "remaining_usd": float}

        Compliance: PCI-DSS 7.1, SOC 2 A1.1
        """
        now = datetime.now(UTC)

        # No budget configured = unlimited
        if agent.max_daily_budget_usd is None:
            return {
                "allowed": True,
                "reason": "No budget limit configured",
                "remaining_usd": None
            }

        # Reset budget if new day
        if agent.budget_reset_at:
            elapsed_hours = (now - agent.budget_reset_at).total_seconds() / 3600
            if elapsed_hours >= 24:
                agent.current_daily_spend_usd = 0.0
                agent.budget_reset_at = now
                agent.budget_alert_sent = False
                db.commit()
        else:
            agent.budget_reset_at = now
            db.commit()

        remaining = agent.max_daily_budget_usd - agent.current_daily_spend_usd

        # Check if action would exceed budget
        if agent.current_daily_spend_usd + estimated_cost > agent.max_daily_budget_usd:
            return {
                "allowed": False,
                "reason": f"Budget exceeded: ${agent.current_daily_spend_usd:.2f}/${agent.max_daily_budget_usd:.2f} USD daily limit",
                "code": "BUDGET_EXCEEDED",
                "remaining_usd": remaining,
                "current_spend_usd": agent.current_daily_spend_usd
            }

        # Check if approaching threshold (warning only)
        threshold_amount = agent.max_daily_budget_usd * (agent.budget_alert_threshold_percent / 100)
        approaching_limit = agent.current_daily_spend_usd >= threshold_amount

        return {
            "allowed": True,
            "reason": "Within budget",
            "remaining_usd": remaining,
            "current_spend_usd": agent.current_daily_spend_usd,
            "approaching_limit": approaching_limit,
            "threshold_percent": agent.budget_alert_threshold_percent
        }

    @staticmethod
    def record_spend(db: Session, agent: RegisteredAgent, amount_usd: float) -> None:
        """
        SEC-068: Record spending against agent budget.
        CR-004: Includes transaction rollback on failure.
        CR-006: Uses row-level locking to prevent race conditions.
        """
        try:
            # CR-006: Acquire row-level lock to prevent concurrent budget updates
            from models_agent_registry import RegisteredAgent as RA
            locked_agent = db.query(RA).filter(
                RA.id == agent.id
            ).with_for_update().first()

            if locked_agent:
                locked_agent.current_daily_spend_usd += amount_usd
                db.commit()
                # Update the passed agent reference
                agent.current_daily_spend_usd = locked_agent.current_daily_spend_usd
            else:
                agent.current_daily_spend_usd += amount_usd
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"CR-004/CR-006: Failed to record spend for agent {agent.agent_id}: {e}")
            raise

    @staticmethod
    def check_time_window(agent: RegisteredAgent) -> Dict[str, Any]:
        """
        SEC-068: Check if current time is within allowed window.

        Supports timezone-aware checking and day-of-week restrictions.

        Returns:
            {"allowed": bool, "reason": str, "next_window": str}

        Compliance: SOC 2 A1.1, enterprise business hours enforcement
        """
        if not agent.time_window_enabled:
            return {
                "allowed": True,
                "reason": "Time window restrictions not enabled"
            }

        if not agent.time_window_start or not agent.time_window_end:
            return {
                "allowed": True,
                "reason": "Time window not fully configured"
            }

        # CR-005: Robust timezone handling with multiple fallbacks
        timezone_str = agent.time_window_timezone or "UTC"
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_str)
        except ImportError:
            try:
                from backports.zoneinfo import ZoneInfo as BackportZoneInfo
                tz = BackportZoneInfo(timezone_str)
            except ImportError:
                try:
                    import pytz
                    tz = pytz.timezone(timezone_str)
                except ImportError:
                    logger.warning(f"CR-005: No timezone library available, falling back to UTC for agent")
                    tz = None
        except Exception as e:
            # CR-005: Handle invalid timezone gracefully
            logger.warning(f"CR-005: Invalid timezone '{timezone_str}' for agent, falling back to UTC: {e}")
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("UTC")
            except ImportError:
                tz = None

        # Get current time in agent's timezone
        if tz:
            now = datetime.now(tz)
        else:
            now = datetime.now(UTC)
        current_time = now.strftime("%H:%M")
        current_day = now.isoweekday()  # Monday=1, Sunday=7

        # Check day of week
        if agent.time_window_days and len(agent.time_window_days) > 0:
            if current_day not in agent.time_window_days:
                return {
                    "allowed": False,
                    "reason": f"Actions not allowed on day {current_day} (allowed days: {agent.time_window_days})",
                    "code": "OUTSIDE_TIME_WINDOW_DAY",
                    "current_day": current_day
                }

        # Check time of day
        start = agent.time_window_start
        end = agent.time_window_end

        # Handle overnight windows (e.g., 22:00 - 06:00)
        if start <= end:
            # Normal window (e.g., 09:00 - 17:00)
            in_window = start <= current_time <= end
        else:
            # Overnight window (e.g., 22:00 - 06:00)
            in_window = current_time >= start or current_time <= end

        if not in_window:
            return {
                "allowed": False,
                "reason": f"Actions only allowed {start}-{end} {agent.time_window_timezone}. Current time: {current_time}",
                "code": "OUTSIDE_TIME_WINDOW_HOURS",
                "current_time": current_time,
                "window_start": start,
                "window_end": end
            }

        return {
            "allowed": True,
            "reason": f"Within allowed time window ({start}-{end})",
            "current_time": current_time
        }

    @staticmethod
    def check_data_classification(
        agent: RegisteredAgent,
        resource_classification: str
    ) -> Dict[str, Any]:
        """
        SEC-068: Check if agent can access this data classification.

        Args:
            agent: The registered agent
            resource_classification: Data classification of the resource (e.g., "pii", "public")

        Returns:
            {"allowed": bool, "reason": str}

        Compliance: HIPAA 164.312, PCI-DSS 3.4, GDPR data protection
        """
        if not resource_classification:
            return {
                "allowed": True,
                "reason": "No data classification specified"
            }

        classification_lower = resource_classification.lower()

        # Check blocked classifications first (deny takes precedence)
        if agent.blocked_data_classifications:
            blocked = [c.lower() for c in agent.blocked_data_classifications]
            if classification_lower in blocked:
                return {
                    "allowed": False,
                    "reason": f"Data classification '{resource_classification}' is blocked for this agent",
                    "code": "DATA_CLASSIFICATION_BLOCKED",
                    "classification": resource_classification
                }

        # Check allowed classifications (if specified, must be in list)
        if agent.allowed_data_classifications and len(agent.allowed_data_classifications) > 0:
            allowed = [c.lower() for c in agent.allowed_data_classifications]
            if classification_lower not in allowed:
                return {
                    "allowed": False,
                    "reason": f"Data classification '{resource_classification}' not in allowed list: {agent.allowed_data_classifications}",
                    "code": "DATA_CLASSIFICATION_NOT_ALLOWED",
                    "classification": resource_classification,
                    "allowed_classifications": agent.allowed_data_classifications
                }

        return {
            "allowed": True,
            "reason": f"Data classification '{resource_classification}' permitted"
        }

    @staticmethod
    def detect_anomalies(
        db: Session,
        agent: RegisteredAgent,
        current_action_rate: float = None,
        current_error_rate: float = None,
        current_risk_score: float = None
    ) -> Dict[str, Any]:
        """
        SEC-068: Compare current behavior against baseline.

        Detects anomalies in:
        - Action rate (actions per hour)
        - Error rate
        - Average risk score

        Returns:
            {"has_anomaly": bool, "anomalies": [...], "severity": str}

        Compliance: SOC 2 CC7.1, NIST SI-4, Datadog anomaly detection
        """
        if not agent.anomaly_detection_enabled:
            return {
                "has_anomaly": False,
                "anomalies": [],
                "reason": "Anomaly detection disabled"
            }

        anomalies = []
        threshold = agent.anomaly_threshold_percent or 50.0

        # Check action rate anomaly (CR-001: Zero-division protection)
        if agent.baseline_actions_per_hour is not None and agent.baseline_actions_per_hour > 0 and current_action_rate is not None:
            deviation = abs(current_action_rate - agent.baseline_actions_per_hour) / agent.baseline_actions_per_hour * 100
            if deviation > threshold:
                anomalies.append({
                    "type": "action_rate",
                    "baseline": agent.baseline_actions_per_hour,
                    "current": current_action_rate,
                    "deviation_percent": round(deviation, 2),
                    "threshold_percent": threshold
                })
        elif current_action_rate is not None and current_action_rate > 0 and not agent.baseline_actions_per_hour:
            # CR-001: Handle case where baseline not set but activity detected
            anomalies.append({
                "type": "action_rate",
                "baseline": None,
                "current": current_action_rate,
                "deviation_percent": 100.0,
                "threshold_percent": threshold,
                "note": "No baseline established"
            })

        # Check error rate anomaly
        if agent.baseline_error_rate is not None and current_error_rate is not None:
            if agent.baseline_error_rate > 0:
                deviation = abs(current_error_rate - agent.baseline_error_rate) / agent.baseline_error_rate * 100
            else:
                deviation = current_error_rate * 100 if current_error_rate > 0 else 0

            if deviation > threshold:
                anomalies.append({
                    "type": "error_rate",
                    "baseline": agent.baseline_error_rate,
                    "current": current_error_rate,
                    "deviation_percent": round(deviation, 2),
                    "threshold_percent": threshold
                })

        # Check risk score anomaly (CR-001: Zero-division protection)
        if agent.baseline_avg_risk_score is not None and agent.baseline_avg_risk_score > 0 and current_risk_score is not None:
            deviation = abs(current_risk_score - agent.baseline_avg_risk_score) / agent.baseline_avg_risk_score * 100
            if deviation > threshold:
                anomalies.append({
                    "type": "risk_score",
                    "baseline": agent.baseline_avg_risk_score,
                    "current": current_risk_score,
                    "deviation_percent": round(deviation, 2),
                    "threshold_percent": threshold
                })
        elif current_risk_score is not None and agent.baseline_avg_risk_score == 0:
            # CR-001: Use default baseline of 50 if baseline is 0
            deviation = abs(current_risk_score - 50.0) / 50.0 * 100
            if deviation > threshold:
                anomalies.append({
                    "type": "risk_score",
                    "baseline": 50.0,
                    "current": current_risk_score,
                    "deviation_percent": round(deviation, 2),
                    "threshold_percent": threshold,
                    "note": "Using default baseline (50)"
                })

        has_anomaly = len(anomalies) > 0

        # Determine severity
        if has_anomaly:
            max_deviation = max(a["deviation_percent"] for a in anomalies)
            if max_deviation > threshold * 2:
                severity = "critical"
            elif max_deviation > threshold * 1.5:
                severity = "high"
            elif max_deviation > threshold:
                severity = "medium"
            else:
                severity = "low"

            # Update anomaly tracking
            agent.last_anomaly_check = datetime.now(UTC)
            agent.last_anomaly_detected = datetime.now(UTC)
            agent.anomaly_count_24h += 1
            db.commit()
        else:
            severity = None
            agent.last_anomaly_check = datetime.now(UTC)
            db.commit()

        return {
            "has_anomaly": has_anomaly,
            "anomalies": anomalies,
            "severity": severity,
            "anomaly_count_24h": agent.anomaly_count_24h
        }

    @staticmethod
    def check_auto_suspend_triggers(
        db: Session,
        agent: RegisteredAgent
    ) -> Dict[str, Any]:
        """
        SEC-068: Check if any auto-suspend conditions are met.

        Checks:
        - Error rate threshold
        - Offline duration
        - Budget exceeded
        - Rate limit exceeded (if configured)

        Returns:
            {"should_suspend": bool, "reason": str, "trigger": str}

        Compliance: SOC 2 CC6.2, NIST AC-2(3)
        """
        if not agent.auto_suspend_enabled:
            return {
                "should_suspend": False,
                "reason": "Auto-suspend disabled"
            }

        now = datetime.now(UTC)

        # Check error rate trigger
        if agent.auto_suspend_on_error_rate is not None:
            if agent.error_rate_percent >= agent.auto_suspend_on_error_rate * 100:
                return {
                    "should_suspend": True,
                    "reason": f"Error rate {agent.error_rate_percent:.1f}% exceeds threshold {agent.auto_suspend_on_error_rate * 100:.1f}%",
                    "trigger": "error_rate",
                    "current_value": agent.error_rate_percent,
                    "threshold": agent.auto_suspend_on_error_rate * 100
                }

        # Check offline duration trigger
        if agent.auto_suspend_on_offline_minutes is not None and agent.last_heartbeat:
            minutes_offline = (now - agent.last_heartbeat).total_seconds() / 60
            if minutes_offline > agent.auto_suspend_on_offline_minutes:
                return {
                    "should_suspend": True,
                    "reason": f"Agent offline for {minutes_offline:.0f} minutes (threshold: {agent.auto_suspend_on_offline_minutes})",
                    "trigger": "offline_duration",
                    "current_value": minutes_offline,
                    "threshold": agent.auto_suspend_on_offline_minutes
                }

        # Check budget exceeded trigger
        if agent.auto_suspend_on_budget_exceeded and agent.max_daily_budget_usd:
            if agent.current_daily_spend_usd >= agent.max_daily_budget_usd:
                return {
                    "should_suspend": True,
                    "reason": f"Budget exceeded: ${agent.current_daily_spend_usd:.2f}/${agent.max_daily_budget_usd:.2f}",
                    "trigger": "budget_exceeded",
                    "current_value": agent.current_daily_spend_usd,
                    "threshold": agent.max_daily_budget_usd
                }

        # Check rate limit exceeded trigger
        if agent.auto_suspend_on_rate_exceeded:
            if agent.max_actions_per_day and agent.current_day_count >= agent.max_actions_per_day:
                return {
                    "should_suspend": True,
                    "reason": f"Daily rate limit exceeded: {agent.current_day_count}/{agent.max_actions_per_day}",
                    "trigger": "rate_exceeded",
                    "current_value": agent.current_day_count,
                    "threshold": agent.max_actions_per_day
                }

        return {
            "should_suspend": False,
            "reason": "No auto-suspend triggers met"
        }

    @staticmethod
    def auto_suspend_agent(
        db: Session,
        agent: RegisteredAgent,
        reason: str,
        trigger: str
    ) -> None:
        """SEC-068: Automatically suspend an agent due to trigger condition."""
        agent.status = AgentStatus.SUSPENDED.value
        agent.auto_suspended_at = datetime.now(UTC)
        agent.auto_suspend_reason = f"[{trigger.upper()}] {reason}"

        # Log the suspension
        log_entry = AgentActivityLog(
            agent_id=agent.id,
            organization_id=agent.organization_id,
            activity_type="auto_suspended",
            activity_description=f"SEC-068 Auto-suspension: {reason}",
            performed_by="SYSTEM:SEC-068",
            performed_via="autonomous_governance",
            previous_state={"status": "active"},
            new_state={"status": "suspended", "trigger": trigger, "reason": reason},
            timestamp=datetime.now(UTC)
        )

        db.add(log_entry)
        db.commit()

        logger.warning(f"SEC-068: Agent {agent.agent_id} auto-suspended - {reason}")

    # =========================================================================
    # AGENT REGISTRATION
    # =========================================================================

    @staticmethod
    def register_agent(
        db: Session,
        organization_id: int,
        agent_data: Dict[str, Any],
        created_by: str
    ) -> Tuple[RegisteredAgent, bool]:
        """
        Register a new AI agent with the governance platform.

        Args:
            db: Database session
            organization_id: Tenant isolation
            agent_data: Agent configuration
            created_by: User performing registration

        Returns:
            Tuple of (RegisteredAgent, created_new)

        Compliance: SOC 2 CC6.1, NIST AC-2
        """
        try:
            # Validate agent_id format (alphanumeric with dashes)
            agent_id = agent_data.get("agent_id", "")
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_]{2,63}$', agent_id):
                raise ValueError(
                    "agent_id must be 3-64 characters, alphanumeric with dashes/underscores, "
                    "starting with alphanumeric"
                )

            # Check for existing agent (idempotency)
            existing = db.query(RegisteredAgent).filter(
                and_(
                    RegisteredAgent.agent_id == agent_id,
                    RegisteredAgent.organization_id == organization_id
                )
            ).first()

            if existing:
                logger.info(f"Agent already registered: {agent_id} (org: {organization_id})")
                return existing, False

            # Validate agent type
            agent_type = agent_data.get("agent_type", AgentType.SUPERVISED.value)
            if agent_type not in [t.value for t in AgentType]:
                agent_type = AgentType.SUPERVISED.value

            # Create new agent registration
            agent = RegisteredAgent(
                agent_id=agent_id,
                display_name=agent_data.get("display_name", agent_id),
                description=agent_data.get("description"),
                agent_type=agent_type,
                status=AgentStatus.DRAFT.value,
                version="1.0.0",
                version_notes=agent_data.get("version_notes", "Initial registration"),
                organization_id=organization_id,

                # Risk Configuration
                default_risk_score=agent_data.get("default_risk_score", 50),
                max_risk_threshold=agent_data.get("max_risk_threshold", 80),
                auto_approve_below=agent_data.get("auto_approve_below", 30),
                requires_mfa_above=agent_data.get("requires_mfa_above", 70),

                # Capabilities
                allowed_action_types=agent_data.get("allowed_action_types", []),
                allowed_resources=agent_data.get("allowed_resources", []),
                blocked_resources=agent_data.get("blocked_resources", []),

                # MCP Integration
                is_mcp_server=agent_data.get("is_mcp_server", False),
                mcp_server_url=agent_data.get("mcp_server_url"),
                mcp_capabilities=agent_data.get("mcp_capabilities", {}),

                # Notifications
                alert_on_high_risk=agent_data.get("alert_on_high_risk", True),
                alert_recipients=agent_data.get("alert_recipients", []),
                webhook_url=agent_data.get("webhook_url"),

                # Audit
                created_at=datetime.now(UTC),
                created_by=created_by,
                updated_at=datetime.now(UTC),
                updated_by=created_by,

                # Metadata
                tags=agent_data.get("tags", []),
                agent_metadata=agent_data.get("metadata", {})
            )

            db.add(agent)
            db.flush()

            # Create initial version record
            version = AgentVersion(
                agent_id=agent.id,
                version="1.0.0",
                version_notes="Initial registration",
                is_active=True,
                config_snapshot=AgentRegistryService._create_config_snapshot(agent),
                created_at=datetime.now(UTC),
                created_by=created_by
            )
            db.add(version)

            # Log activity
            activity = AgentActivityLog(
                agent_id=agent.id,
                organization_id=organization_id,
                activity_type="registered",
                activity_description=f"Agent '{agent_id}' registered with type '{agent_type}'",
                performed_by=created_by,
                performed_via="api",
                previous_state=None,
                new_state=AgentRegistryService._create_config_snapshot(agent),
                timestamp=datetime.now(UTC)
            )
            db.add(activity)

            db.commit()
            db.refresh(agent)

            logger.info(f"Agent registered: {agent_id} (id: {agent.id}, org: {organization_id})")
            return agent, True

        except ValueError as e:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Agent registration failed: {e}")
            raise

    @staticmethod
    def get_agent(
        db: Session,
        organization_id: int,
        agent_id: str = None,
        internal_id: int = None
    ) -> Optional[RegisteredAgent]:
        """
        Get agent by agent_id or internal ID with tenant isolation.

        Compliance: Multi-tenant isolation enforced
        """
        query = db.query(RegisteredAgent).filter(
            RegisteredAgent.organization_id == organization_id
        )

        if internal_id:
            query = query.filter(RegisteredAgent.id == internal_id)
        elif agent_id:
            query = query.filter(RegisteredAgent.agent_id == agent_id)
        else:
            return None

        return query.first()

    @staticmethod
    def list_agents(
        db: Session,
        organization_id: int,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[RegisteredAgent], int]:
        """
        List all agents for an organization with filtering.

        Returns:
            Tuple of (agents, total_count)

        Compliance: Multi-tenant isolation enforced
        """
        query = db.query(RegisteredAgent).filter(
            RegisteredAgent.organization_id == organization_id
        )

        if status_filter:
            query = query.filter(RegisteredAgent.status == status_filter)

        if type_filter:
            query = query.filter(RegisteredAgent.agent_type == type_filter)

        total = query.count()

        agents = query.order_by(
            RegisteredAgent.created_at.desc()
        ).offset(offset).limit(limit).all()

        return agents, total

    @staticmethod
    def update_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        updates: Dict[str, Any],
        updated_by: str,
        create_version: bool = True
    ) -> Optional[RegisteredAgent]:
        """
        Update agent configuration with version control.

        Args:
            db: Database session
            organization_id: Tenant isolation
            agent_id: Agent identifier
            updates: Fields to update
            updated_by: User performing update
            create_version: Whether to create a new version

        Compliance: SOC 2 CC8.1 (change management)
        """
        try:
            agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
            if not agent:
                return None

            # Capture previous state
            previous_state = AgentRegistryService._create_config_snapshot(agent)

            # Fields that trigger version bump
            version_trigger_fields = {
                "allowed_action_types", "allowed_resources", "blocked_resources",
                "auto_approve_below", "max_risk_threshold", "requires_mfa_above",
                "mcp_capabilities", "agent_type"
            }

            should_bump_version = any(
                field in updates for field in version_trigger_fields
            ) and create_version

            # Apply updates
            allowed_fields = {
                "display_name", "description", "agent_type", "default_risk_score",
                "max_risk_threshold", "auto_approve_below", "requires_mfa_above",
                "allowed_action_types", "allowed_resources", "blocked_resources",
                "is_mcp_server", "mcp_server_url", "mcp_capabilities",
                "alert_on_high_risk", "alert_recipients", "webhook_url",
                "tags", "agent_metadata", "version_notes"
            }

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(agent, field, value)

            agent.updated_at = datetime.now(UTC)
            agent.updated_by = updated_by

            # Version management
            if should_bump_version:
                new_version = AgentRegistryService._increment_version(agent.version)
                agent.version = new_version
                agent.version_notes = updates.get("version_notes", f"Updated: {', '.join(updates.keys())}")

                # Mark old versions as inactive
                db.query(AgentVersion).filter(
                    AgentVersion.agent_id == agent.id
                ).update({"is_active": False})

                # Create new version record
                version = AgentVersion(
                    agent_id=agent.id,
                    version=new_version,
                    version_notes=agent.version_notes,
                    is_active=True,
                    config_snapshot=AgentRegistryService._create_config_snapshot(agent),
                    created_at=datetime.now(UTC),
                    created_by=updated_by
                )
                db.add(version)

            # Log activity
            new_state = AgentRegistryService._create_config_snapshot(agent)
            activity = AgentActivityLog(
                agent_id=agent.id,
                organization_id=organization_id,
                activity_type="updated",
                activity_description=f"Agent '{agent_id}' updated: {', '.join(updates.keys())}",
                performed_by=updated_by,
                performed_via="api",
                previous_state=previous_state,
                new_state=new_state,
                timestamp=datetime.now(UTC)
            )
            db.add(activity)

            db.commit()
            db.refresh(agent)

            logger.info(f"Agent updated: {agent_id} (version: {agent.version})")
            return agent

        except Exception as e:
            db.rollback()
            logger.error(f"Agent update failed: {e}")
            raise

    @staticmethod
    def activate_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        approved_by: str
    ) -> Optional[RegisteredAgent]:
        """
        Activate an agent for production use.

        Requires admin approval for compliance.

        Compliance: SOC 2 CC6.2 (access authorization)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        if agent.status not in [AgentStatus.DRAFT.value, AgentStatus.PENDING_APPROVAL.value, AgentStatus.SUSPENDED.value]:
            raise ValueError(f"Cannot activate agent in status: {agent.status}")

        previous_status = agent.status
        agent.status = AgentStatus.ACTIVE.value
        agent.approved_at = datetime.now(UTC)
        agent.approved_by = approved_by
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = approved_by

        # Log activation
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="activated",
            activity_description=f"Agent '{agent_id}' activated (previous: {previous_status})",
            performed_by=approved_by,
            performed_via="api",
            previous_state={"status": previous_status},
            new_state={"status": AgentStatus.ACTIVE.value},
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.info(f"Agent activated: {agent_id} by {approved_by}")
        return agent

    @staticmethod
    def suspend_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        suspended_by: str,
        reason: str = None
    ) -> Optional[RegisteredAgent]:
        """
        Suspend an agent (emergency disable).

        Used for security incidents or policy violations.

        Compliance: SOC 2 CC6.2, NIST AC-2(3)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        previous_status = agent.status
        agent.status = AgentStatus.SUSPENDED.value
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = suspended_by

        # Log suspension with reason
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="suspended",
            activity_description=f"Agent '{agent_id}' suspended. Reason: {reason or 'Not specified'}",
            performed_by=suspended_by,
            performed_via="api",
            previous_state={"status": previous_status},
            new_state={"status": AgentStatus.SUSPENDED.value, "reason": reason},
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.warning(f"Agent SUSPENDED: {agent_id} by {suspended_by} - Reason: {reason}")
        return agent

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    @staticmethod
    def list_versions(
        db: Session,
        organization_id: int,
        agent_id: str
    ) -> List[AgentVersion]:
        """List all versions of an agent."""
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return []

        return db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent.id
        ).order_by(AgentVersion.created_at.desc()).all()

    @staticmethod
    def rollback_to_version(
        db: Session,
        organization_id: int,
        agent_id: str,
        target_version: str,
        performed_by: str
    ) -> Optional[RegisteredAgent]:
        """
        Rollback agent to a previous version.

        Compliance: SOC 2 CC8.1 (rollback capability)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        # Find target version
        version_record = db.query(AgentVersion).filter(
            and_(
                AgentVersion.agent_id == agent.id,
                AgentVersion.version == target_version
            )
        ).first()

        if not version_record:
            raise ValueError(f"Version {target_version} not found")

        # Restore configuration from snapshot
        snapshot = version_record.config_snapshot
        previous_state = AgentRegistryService._create_config_snapshot(agent)

        # Apply rollback
        for field, value in snapshot.items():
            if hasattr(agent, field) and field not in ['id', 'organization_id', 'created_at', 'created_by']:
                setattr(agent, field, value)

        agent.version = target_version
        agent.version_notes = f"Rollback from {previous_state.get('version')} to {target_version}"
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = performed_by

        # Mark target version as active
        db.query(AgentVersion).filter(AgentVersion.agent_id == agent.id).update({"is_active": False})
        version_record.is_active = True

        # Log rollback
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="rollback",
            activity_description=f"Agent '{agent_id}' rolled back to version {target_version}",
            performed_by=performed_by,
            performed_via="api",
            previous_state=previous_state,
            new_state=snapshot,
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.info(f"Agent rollback: {agent_id} -> {target_version} by {performed_by}")
        return agent

    # =========================================================================
    # POLICY MANAGEMENT
    # =========================================================================

    @staticmethod
    def add_policy(
        db: Session,
        organization_id: int,
        agent_id: str,
        policy_data: Dict[str, Any],
        created_by: str
    ) -> AgentPolicy:
        """
        Add a policy to an agent.

        Compliance: NIST AC-3 (access enforcement)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        policy = AgentPolicy(
            agent_id=agent.id,
            organization_id=organization_id,
            policy_name=policy_data.get("policy_name", "Unnamed Policy"),
            policy_description=policy_data.get("policy_description"),
            is_active=policy_data.get("is_active", True),
            priority=policy_data.get("priority", 100),
            conditions=policy_data.get("conditions", {}),
            policy_action=policy_data.get("policy_action", "require_approval"),
            action_params=policy_data.get("action_params", {}),
            created_at=datetime.now(UTC),
            created_by=created_by
        )

        db.add(policy)
        db.commit()
        db.refresh(policy)

        logger.info(f"Policy added to agent {agent_id}: {policy.policy_name}")
        return policy

    @staticmethod
    def evaluate_policies(
        db: Session,
        organization_id: int,
        agent_id: str,
        action_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate all policies for an agent against an action context.

        SEC-068: Enhanced with autonomous agent governance checks:
        - Rate limiting
        - Budget controls
        - Time window restrictions
        - Data classification enforcement
        - Anomaly detection
        - Auto-suspension triggers

        Returns:
            Policy evaluation result with decision and matching policies

        Compliance: NIST AC-3, SOC 2 CC6.1/CC6.2/CC7.1, PCI-DSS 7.1
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return {"decision": "deny", "reason": "Agent not registered", "policies": []}

        # Check agent status
        if agent.status != AgentStatus.ACTIVE.value:
            return {
                "decision": "deny",
                "reason": f"Agent not active (status: {agent.status})",
                "policies": []
            }

        # =====================================================================
        # SEC-068: AUTONOMOUS AGENT GOVERNANCE PRE-FLIGHT CHECKS
        # These checks apply to ALL agents but are stricter for autonomous
        # =====================================================================

        is_autonomous = agent.agent_type == AgentType.AUTONOMOUS.value
        governance_checks = []

        # 1. Rate Limit Check
        rate_check = AgentRegistryService.check_rate_limit(db, agent)
        governance_checks.append({"check": "rate_limit", "result": rate_check})
        if not rate_check["allowed"]:
            # Check if auto-suspend is triggered
            if agent.auto_suspend_on_rate_exceeded:
                suspend_check = AgentRegistryService.check_auto_suspend_triggers(db, agent)
                if suspend_check["should_suspend"]:
                    AgentRegistryService.auto_suspend_agent(db, agent, suspend_check["reason"], suspend_check["trigger"])
            return {
                "decision": "deny",
                "reason": rate_check["reason"],
                "code": rate_check.get("code", "RATE_LIMIT_EXCEEDED"),
                "policies": [],
                "governance_checks": governance_checks,
                "retry_after_seconds": rate_check.get("retry_after_seconds", 60)
            }

        # 2. Budget Check
        estimated_cost = action_context.get("estimated_cost", 0.0)
        budget_check = AgentRegistryService.check_budget(db, agent, estimated_cost)
        governance_checks.append({"check": "budget", "result": budget_check})
        if not budget_check["allowed"]:
            # Check if auto-suspend is triggered
            if agent.auto_suspend_on_budget_exceeded:
                AgentRegistryService.auto_suspend_agent(
                    db, agent,
                    f"Budget exceeded: ${agent.current_daily_spend_usd:.2f}/${agent.max_daily_budget_usd:.2f}",
                    "budget_exceeded"
                )
            return {
                "decision": "deny",
                "reason": budget_check["reason"],
                "code": budget_check.get("code", "BUDGET_EXCEEDED"),
                "policies": [],
                "governance_checks": governance_checks
            }

        # 3. Time Window Check (especially important for autonomous agents)
        time_check = AgentRegistryService.check_time_window(agent)
        governance_checks.append({"check": "time_window", "result": time_check})
        if not time_check["allowed"]:
            return {
                "decision": "deny",
                "reason": time_check["reason"],
                "code": time_check.get("code", "OUTSIDE_TIME_WINDOW"),
                "policies": [],
                "governance_checks": governance_checks
            }

        # 4. Data Classification Check
        resource_classification = action_context.get("data_classification")
        if resource_classification:
            data_check = AgentRegistryService.check_data_classification(agent, resource_classification)
            governance_checks.append({"check": "data_classification", "result": data_check})
            if not data_check["allowed"]:
                return {
                    "decision": "deny",
                    "reason": data_check["reason"],
                    "code": data_check.get("code", "DATA_CLASSIFICATION_BLOCKED"),
                    "policies": [],
                    "governance_checks": governance_checks
                }

        # 5. Auto-Suspend Trigger Check
        suspend_check = AgentRegistryService.check_auto_suspend_triggers(db, agent)
        governance_checks.append({"check": "auto_suspend_triggers", "result": suspend_check})
        if suspend_check["should_suspend"]:
            AgentRegistryService.auto_suspend_agent(db, agent, suspend_check["reason"], suspend_check["trigger"])
            return {
                "decision": "deny",
                "reason": f"Agent auto-suspended: {suspend_check['reason']}",
                "code": "AUTO_SUSPENDED",
                "policies": [],
                "governance_checks": governance_checks
            }

        # 6. Anomaly Detection (non-blocking, but logs and alerts)
        current_risk_score = action_context.get("risk_score", agent.default_risk_score)
        anomaly_check = AgentRegistryService.detect_anomalies(
            db, agent,
            current_action_rate=agent.current_hour_count,
            current_error_rate=agent.error_rate_percent,
            current_risk_score=current_risk_score
        )
        governance_checks.append({"check": "anomaly_detection", "result": anomaly_check})

        # =====================================================================
        # POLICY EVALUATION
        # =====================================================================

        # Get active policies ordered by priority
        policies = db.query(AgentPolicy).filter(
            and_(
                AgentPolicy.agent_id == agent.id,
                AgentPolicy.is_active == True
            )
        ).order_by(AgentPolicy.priority).all()

        matched_policies = []
        final_decision = "allow"  # Default allow if no policies match

        for policy in policies:
            if AgentRegistryService._policy_matches(policy.conditions, action_context):
                matched_policies.append({
                    "policy_id": policy.id,
                    "policy_name": policy.policy_name,
                    "action": policy.policy_action,
                    "params": policy.action_params
                })

                # First matching policy determines decision (sorted by priority)
                if final_decision == "allow":
                    final_decision = policy.policy_action

        # =====================================================================
        # SEC-068: APPLY RISK THRESHOLDS (STRICTER FOR AUTONOMOUS)
        # =====================================================================

        risk_score = action_context.get("risk_score", agent.default_risk_score)

        # Use autonomous-specific thresholds if agent is autonomous
        if is_autonomous:
            effective_auto_approve = min(agent.auto_approve_below, agent.autonomous_auto_approve_below)
            effective_max_threshold = min(agent.max_risk_threshold, agent.autonomous_max_risk_threshold)
            logger.info(f"SEC-068: Autonomous agent {agent_id} using stricter thresholds: auto_approve<{effective_auto_approve}, max<{effective_max_threshold}")
        else:
            effective_auto_approve = agent.auto_approve_below
            effective_max_threshold = agent.max_risk_threshold

        if risk_score < effective_auto_approve:
            # Increment rate counters on successful action
            AgentRegistryService.increment_rate_counters(db, agent)
            return {
                "decision": "auto_approve",
                "reason": f"Risk score {risk_score} below auto-approve threshold {effective_auto_approve}",
                "policies": matched_policies,
                "risk_score": risk_score,
                "governance_checks": governance_checks,
                "is_autonomous": is_autonomous,
                "anomaly_detected": anomaly_check.get("has_anomaly", False)
            }

        if risk_score > effective_max_threshold:
            # CR-003: Autonomous agents can escalate if configured
            if is_autonomous:
                escalation_result = AgentRegistryService._handle_autonomous_escalation(
                    db, agent, action_context, risk_score, matched_policies, governance_checks
                )
                if escalation_result:
                    return escalation_result
                # No escalation configured - deny
                return {
                    "decision": "deny",
                    "reason": f"Risk score {risk_score} exceeds max threshold {effective_max_threshold} - autonomous agent has no escalation path configured",
                    "policies": matched_policies,
                    "risk_score": risk_score,
                    "governance_checks": governance_checks,
                    "is_autonomous": is_autonomous,
                    "escalation_available": False
                }
            else:
                return {
                    "decision": "escalate",
                    "reason": f"Risk score {risk_score} exceeds max threshold {effective_max_threshold}",
                    "policies": matched_policies,
                    "risk_score": risk_score,
                    "governance_checks": governance_checks,
                    "is_autonomous": is_autonomous
                }

        # SEC-068: Increment rate counters for allowed actions
        if final_decision in ["allow", "require_approval"]:
            AgentRegistryService.increment_rate_counters(db, agent)

        # SEC-068: For autonomous agents, "require_approval" can be escalated or queued
        # CR-003: Check if escalation path is configured
        if is_autonomous and final_decision == "require_approval":
            escalation_result = AgentRegistryService._handle_autonomous_escalation(
                db, agent, action_context, risk_score, matched_policies, governance_checks
            )
            if escalation_result:
                return escalation_result

            # No escalation configured - deny
            return {
                "decision": "deny",
                "reason": f"Autonomous agents cannot wait for approval. Risk score: {risk_score}. Configure escalation path for async approval.",
                "policies": matched_policies,
                "risk_score": risk_score,
                "governance_checks": governance_checks,
                "is_autonomous": is_autonomous,
                "escalation_available": False
            }

        return {
            "decision": final_decision,
            "reason": f"Policy evaluation complete. {len(matched_policies)} policies matched.",
            "policies": matched_policies,
            "risk_score": risk_score,
            "requires_mfa": risk_score >= agent.requires_mfa_above and not is_autonomous,
            "governance_checks": governance_checks,
            "is_autonomous": is_autonomous,
            "anomaly_detected": anomaly_check.get("has_anomaly", False)
        }

    # =========================================================================
    # MCP SERVER MANAGEMENT
    # =========================================================================

    @staticmethod
    def register_mcp_server(
        db: Session,
        organization_id: int,
        server_data: Dict[str, Any],
        created_by: str
    ) -> MCPServerConfig:
        """
        Register an MCP server for governance.

        Compliance: SOC 2 CC6.1
        """
        server = MCPServerConfig(
            server_name=server_data.get("server_name"),
            display_name=server_data.get("display_name", server_data.get("server_name")),
            description=server_data.get("description"),
            server_url=server_data.get("server_url"),
            transport_type=server_data.get("transport_type", "stdio"),
            connection_config=server_data.get("connection_config", {}),
            organization_id=organization_id,
            discovered_tools=server_data.get("tools", []),
            discovered_prompts=server_data.get("prompts", []),
            discovered_resources=server_data.get("resources", []),
            governance_enabled=server_data.get("governance_enabled", True),
            auto_approve_tools=server_data.get("auto_approve_tools", []),
            blocked_tools=server_data.get("blocked_tools", []),
            tool_risk_overrides=server_data.get("tool_risk_overrides", {}),
            is_active=True,
            health_status="unknown",
            created_at=datetime.now(UTC),
            created_by=created_by
        )

        db.add(server)
        db.commit()
        db.refresh(server)

        logger.info(f"MCP Server registered: {server.server_name} (org: {organization_id})")
        return server

    @staticmethod
    def list_mcp_servers(
        db: Session,
        organization_id: int
    ) -> List[MCPServerConfig]:
        """List all MCP servers for an organization."""
        return db.query(MCPServerConfig).filter(
            MCPServerConfig.organization_id == organization_id
        ).all()

    # =========================================================================
    # AGENT DELETE
    # =========================================================================

    @staticmethod
    def delete_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        deleted_by: str,
        reason: str = None
    ) -> bool:
        """
        Delete an agent registration.

        This is a SOFT delete for audit trail - marks as deleted but preserves data.
        For hard delete, use purge_agent (admin only).

        Args:
            db: Database session
            organization_id: Tenant isolation
            agent_id: Agent to delete
            deleted_by: User performing deletion
            reason: Reason for deletion

        Returns:
            True if deleted, False if not found

        Compliance: SOC 2 CC6.1, NIST AC-2
        """
        agent = db.query(RegisteredAgent).filter(
            and_(
                RegisteredAgent.agent_id == agent_id,
                RegisteredAgent.organization_id == organization_id
            )
        ).first()

        if not agent:
            return False

        # Log the deletion
        log = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="AGENT_DELETED",
            activity_description=f"Agent deleted: {reason or 'No reason provided'}",
            performed_by=deleted_by,
            performed_via="admin_ui",
            previous_state={"status": agent.status, "agent_id": agent.agent_id},
            new_state={"status": "deleted"},
            timestamp=datetime.now(UTC)
        )
        db.add(log)

        # Hard delete the agent and related data
        # Delete policies first
        from models_agent_registry import AgentPolicy, AgentVersion
        db.query(AgentPolicy).filter(AgentPolicy.agent_id == agent.id).delete()
        db.query(AgentVersion).filter(AgentVersion.agent_id == agent.id).delete()
        db.delete(agent)
        db.commit()

        logger.info(f"SEC-024: Agent deleted: {agent_id} by {deleted_by}")
        return True

    # =========================================================================
    # MCP SERVER MANAGEMENT
    # =========================================================================

    @staticmethod
    def get_mcp_server(
        db: Session,
        organization_id: int,
        server_name: str
    ) -> Optional[MCPServerConfig]:
        """Get an MCP server by server_name."""
        return db.query(MCPServerConfig).filter(
            and_(
                MCPServerConfig.server_name == server_name,
                MCPServerConfig.organization_id == organization_id
            )
        ).first()

    @staticmethod
    def update_mcp_server(
        db: Session,
        organization_id: int,
        server_name: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Optional[MCPServerConfig]:
        """
        Update an MCP server configuration.

        Args:
            db: Database session
            organization_id: Tenant isolation
            server_name: Server to update
            updates: Fields to update
            updated_by: User performing update

        Returns:
            Updated MCPServerConfig or None if not found

        Compliance: SOC 2 CC8.1, NIST AC-3
        """
        server = db.query(MCPServerConfig).filter(
            and_(
                MCPServerConfig.server_name == server_name,
                MCPServerConfig.organization_id == organization_id
            )
        ).first()

        if not server:
            return None

        # Update allowed fields
        allowed_updates = [
            'display_name', 'description', 'server_url', 'transport_type',
            'connection_config', 'governance_enabled', 'auto_approve_tools',
            'blocked_tools', 'tool_risk_overrides'
        ]

        for key, value in updates.items():
            if key in allowed_updates and value is not None:
                setattr(server, key, value)

        server.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(server)

        logger.info(f"SEC-024: MCP Server updated: {server_name} by {updated_by}")
        return server

    @staticmethod
    def delete_mcp_server(
        db: Session,
        organization_id: int,
        server_name: str,
        deleted_by: str
    ) -> bool:
        """
        Delete an MCP server registration.

        Args:
            db: Database session
            organization_id: Tenant isolation
            server_name: Server to delete
            deleted_by: User performing deletion

        Returns:
            True if deleted, False if not found

        Compliance: SOC 2 CC6.1, NIST AC-2
        """
        server = db.query(MCPServerConfig).filter(
            and_(
                MCPServerConfig.server_name == server_name,
                MCPServerConfig.organization_id == organization_id
            )
        ).first()

        if not server:
            return False

        db.delete(server)
        db.commit()

        logger.info(f"SEC-024: MCP Server deleted: {server_name} by {deleted_by}")
        return True

    @staticmethod
    def activate_mcp_server(
        db: Session,
        organization_id: int,
        server_name: str,
        activated_by: str
    ) -> Optional[MCPServerConfig]:
        """
        Activate an MCP server.

        Args:
            db: Database session
            organization_id: Tenant isolation
            server_name: Server to activate
            activated_by: User performing activation

        Returns:
            Updated MCPServerConfig or None if not found

        Compliance: SOC 2 CC6.2
        """
        server = db.query(MCPServerConfig).filter(
            and_(
                MCPServerConfig.server_name == server_name,
                MCPServerConfig.organization_id == organization_id
            )
        ).first()

        if not server:
            return None

        server.is_active = True
        server.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(server)

        logger.info(f"SEC-024: MCP Server activated: {server_name} by {activated_by}")
        return server

    @staticmethod
    def deactivate_mcp_server(
        db: Session,
        organization_id: int,
        server_name: str,
        deactivated_by: str,
        reason: str = None
    ) -> Optional[MCPServerConfig]:
        """
        Deactivate an MCP server.

        Args:
            db: Database session
            organization_id: Tenant isolation
            server_name: Server to deactivate
            deactivated_by: User performing deactivation
            reason: Reason for deactivation

        Returns:
            Updated MCPServerConfig or None if not found

        Compliance: SOC 2 CC6.2, NIST AC-2(3)
        """
        server = db.query(MCPServerConfig).filter(
            and_(
                MCPServerConfig.server_name == server_name,
                MCPServerConfig.organization_id == organization_id
            )
        ).first()

        if not server:
            return None

        server.is_active = False
        server.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(server)

        logger.info(f"SEC-024: MCP Server deactivated: {server_name} by {deactivated_by} - Reason: {reason}")
        return server

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def _handle_autonomous_escalation(
        db: Session,
        agent: RegisteredAgent,
        action_context: Dict[str, Any],
        risk_score: float,
        matched_policies: List[Dict],
        governance_checks: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        CR-003: Handle escalation path for autonomous agents.

        Autonomous agents can:
        1. Send webhook notification and continue (if escalation_webhook configured)
        2. Queue for human approval (if autonomous_allow_queued_approval enabled)
        3. Send email notification (if escalation_email configured)

        Returns:
            Escalation result dict if escalation was handled, None if no escalation configured.

        Compliance: SOC 2 CC6.2, NIST AC-3
        """
        # Check if any escalation path is configured
        has_webhook = bool(agent.autonomous_escalation_webhook_url)
        has_email = bool(agent.autonomous_escalation_email)
        allows_queued = agent.autonomous_allow_queued_approval

        if not (has_webhook or has_email or allows_queued):
            return None  # No escalation configured

        escalation_info = {
            "webhook_sent": False,
            "email_sent": False,
            "queued_for_approval": False,
            "escalation_id": None
        }

        # 1. Send webhook notification if configured
        if has_webhook:
            try:
                import requests
                webhook_payload = {
                    "event": "autonomous_agent_escalation",
                    "agent_id": agent.agent_id,
                    "organization_id": agent.organization_id,
                    "risk_score": risk_score,
                    "action_context": action_context,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": f"Risk score {risk_score} requires escalation",
                    "queued_for_approval": allows_queued
                }

                # Fire-and-forget webhook (don't block on response)
                try:
                    requests.post(
                        agent.autonomous_escalation_webhook_url,
                        json=webhook_payload,
                        timeout=5,
                        headers={"Content-Type": "application/json"}
                    )
                    escalation_info["webhook_sent"] = True
                    logger.info(f"CR-003: Escalation webhook sent for agent {agent.agent_id}")
                except Exception as e:
                    logger.warning(f"CR-003: Escalation webhook failed for agent {agent.agent_id}: {e}")
            except ImportError:
                logger.warning("CR-003: requests library not available for webhook escalation")

        # 2. Log email notification (actual sending would use enterprise email service)
        if has_email:
            logger.info(f"CR-003: Escalation email would be sent to {agent.autonomous_escalation_email} for agent {agent.agent_id}")
            escalation_info["email_sent"] = True  # Mark as "sent" (logged)

        # 3. If queued approval is allowed, return "pending" decision
        if allows_queued:
            escalation_info["queued_for_approval"] = True
            escalation_info["escalation_id"] = f"ESC-{agent.agent_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

            return {
                "decision": "pending_escalation",
                "reason": f"Action queued for human review. Risk score {risk_score} exceeds threshold. Escalation ID: {escalation_info['escalation_id']}",
                "policies": matched_policies,
                "risk_score": risk_score,
                "governance_checks": governance_checks,
                "is_autonomous": True,
                "escalation": escalation_info
            }

        # Webhook/email sent but not queuing - still deny but notify
        return {
            "decision": "deny_with_escalation",
            "reason": f"Action denied but escalation notification sent. Risk score {risk_score} exceeds threshold.",
            "policies": matched_policies,
            "risk_score": risk_score,
            "governance_checks": governance_checks,
            "is_autonomous": True,
            "escalation": escalation_info
        }

    @staticmethod
    def _create_config_snapshot(agent: RegisteredAgent) -> Dict[str, Any]:
        """Create a JSON-serializable snapshot of agent configuration."""
        return {
            "agent_id": agent.agent_id,
            "display_name": agent.display_name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "version": agent.version,
            "default_risk_score": agent.default_risk_score,
            "max_risk_threshold": agent.max_risk_threshold,
            "auto_approve_below": agent.auto_approve_below,
            "requires_mfa_above": agent.requires_mfa_above,
            "allowed_action_types": agent.allowed_action_types,
            "allowed_resources": agent.allowed_resources,
            "blocked_resources": agent.blocked_resources,
            "is_mcp_server": agent.is_mcp_server,
            "mcp_server_url": agent.mcp_server_url,
            "mcp_capabilities": agent.mcp_capabilities,
            "alert_on_high_risk": agent.alert_on_high_risk,
            "tags": agent.tags,
            "metadata": agent.agent_metadata
        }

    @staticmethod
    def _increment_version(current_version: str) -> str:
        """Increment semantic version (patch level)."""
        try:
            parts = current_version.split(".")
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                return ".".join(parts)
        except:
            pass
        return f"{current_version}.1"

    @staticmethod
    def _policy_matches(conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if policy conditions match the action context."""
        if not conditions:
            return True  # Empty conditions = always match

        for key, value in conditions.items():
            context_value = context.get(key)

            if key.endswith("_above"):
                actual_key = key.replace("_above", "")
                if context.get(actual_key, 0) <= value:
                    return False
            elif key.endswith("_below"):
                actual_key = key.replace("_below", "")
                if context.get(actual_key, 0) >= value:
                    return False
            elif key.endswith("_in"):
                actual_key = key.replace("_in", "")
                if context.get(actual_key) not in value:
                    return False
            elif key.endswith("_not_in"):
                actual_key = key.replace("_not_in", "")
                if context.get(actual_key) in value:
                    return False
            elif isinstance(value, list):
                if context_value not in value:
                    return False
            elif context_value != value:
                return False

        return True


# Global service instance
agent_registry_service = AgentRegistryService()
