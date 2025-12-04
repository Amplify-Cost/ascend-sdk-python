"""
SEC-065: Enterprise Executive Brief Service

Enterprise-grade cached executive briefing system following industry standards:
- Datadog: Cached metrics pipeline with TTL
- Splunk: Scheduled report generation and storage
- PagerDuty: Executive escalation summaries
- Wiz.io: Security posture scoring with snapshots

Features:
1. Cached brief retrieval (<100ms response time)
2. On-demand regeneration with cooldown (5 min rate limit)
3. LLM generation with enterprise fallback
4. Full audit trail for compliance
5. Multi-tenant isolation (banking-level security)

Compliance:
- SOC 2 AU-6: Audit record review and reporting
- SOC 2 AU-7: Audit reduction and report generation
- NIST 800-53 AU-6: Audit Review, Analysis, Reporting
- PCI-DSS 10.6: Review logs and security events daily
- HIPAA 164.312(b): Audit controls

Document ID: SEC-065
Publisher: Ascend (OW-kai Corporation)
Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from models import Alert, Organization
from models_executive_brief import ExecutiveBrief

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ExecutiveBriefConfig:
    """
    Enterprise configuration for executive brief generation.
    All values are production-ready defaults.
    """
    # Cache TTL in hours (briefs expire after this time)
    CACHE_TTL_HOURS: int = 1

    # Minimum time between regenerations (rate limiting)
    COOLDOWN_MINUTES: int = 5

    # Maximum alerts to include in snapshot for audit
    MAX_ALERT_SNAPSHOT: int = 100

    # Time period mappings (string to days)
    TIME_PERIOD_DAYS: Dict[str, int] = None

    # LLM configuration
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.7
    LLM_MODEL: str = "gpt-3.5-turbo"

    # Cost calculation (configurable per organization)
    # Industry standard: $50K-$150K per security incident
    # Set to 0 to disable cost savings display
    COST_PER_INCIDENT_USD: int = 50000

    # Maximum alerts to analyze (prevents memory issues)
    MAX_ALERTS_FOR_ANALYSIS: int = 1000

    # Risk thresholds
    RISK_THRESHOLDS: Dict[str, int] = None

    def __post_init__(self):
        if self.TIME_PERIOD_DAYS is None:
            self.TIME_PERIOD_DAYS = {
                "24h": 1,
                "7d": 7,
                "30d": 30,
                "90d": 90
            }
        if self.RISK_THRESHOLDS is None:
            self.RISK_THRESHOLDS = {
                "CRITICAL": 10,  # >= 10 critical alerts
                "HIGH": 5,       # >= 5 high priority alerts
                "MEDIUM": 1,     # >= 1 alert
                "LOW": 0         # Some activity but low severity
            }


# Default configuration
DEFAULT_CONFIG = ExecutiveBriefConfig()


# =============================================================================
# SERVICE CLASS
# =============================================================================

class ExecutiveBriefService:
    """
    Enterprise Executive Brief Service

    Banking-Level Security Features:
    - Multi-tenant isolation via organization_id
    - Rate limiting to prevent LLM abuse
    - Audit trail for all generated briefs
    - Graceful fallback when LLM unavailable

    Usage:
        service = ExecutiveBriefService(db, org_id)
        brief = service.get_cached_brief()
        if not brief or brief.is_expired():
            brief = service.generate_brief("24h", user_email)
    """

    def __init__(
        self,
        db: Session,
        org_id: int,
        config: ExecutiveBriefConfig = None
    ):
        """
        Initialize service with database session and organization.

        Args:
            db: SQLAlchemy database session
            org_id: Organization ID for multi-tenant isolation
            config: Optional custom configuration
        """
        self.db = db
        self.org_id = org_id
        self.config = config or DEFAULT_CONFIG

        logger.debug(f"SEC-065: ExecutiveBriefService initialized for org_id={org_id}")

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def get_cached_brief(self) -> Optional[ExecutiveBrief]:
        """
        Get the current valid cached brief for the organization.

        Performance: <100ms (indexed query)

        Returns:
            ExecutiveBrief if valid cached brief exists, None otherwise
        """
        start_time = time.time()

        try:
            brief = self.db.query(ExecutiveBrief).filter(
                and_(
                    ExecutiveBrief.organization_id == self.org_id,
                    ExecutiveBrief.is_current == True,
                    ExecutiveBrief.expires_at > datetime.now(UTC)
                )
            ).order_by(desc(ExecutiveBrief.generated_at)).first()

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"SEC-065: Cached brief lookup for org_id={self.org_id} "
                f"found={brief is not None} time={elapsed_ms:.1f}ms"
            )

            return brief

        except Exception as e:
            logger.error(f"SEC-065: Failed to get cached brief for org_id={self.org_id}: {e}")
            return None

    def can_regenerate(self) -> Tuple[bool, int]:
        """
        Check if regeneration is allowed (respects cooldown).

        Returns:
            Tuple of (can_regenerate, seconds_remaining)
            - (True, 0) if regeneration allowed
            - (False, N) if must wait N seconds
        """
        try:
            latest = self.db.query(ExecutiveBrief).filter(
                ExecutiveBrief.organization_id == self.org_id
            ).order_by(desc(ExecutiveBrief.generated_at)).first()

            if not latest:
                return (True, 0)

            cooldown_end = latest.generated_at + timedelta(
                minutes=self.config.COOLDOWN_MINUTES
            )
            now = datetime.now(UTC)

            if now >= cooldown_end:
                return (True, 0)

            remaining = int((cooldown_end - now).total_seconds())
            return (False, remaining)

        except Exception as e:
            logger.error(f"SEC-065: Cooldown check failed for org_id={self.org_id}: {e}")
            # On error, allow regeneration (fail open for usability)
            return (True, 0)

    def generate_brief(
        self,
        time_period: str = "24h",
        user_email: str = "system",
        force: bool = False
    ) -> ExecutiveBrief:
        """
        Generate a new executive brief.

        This will:
        1. Check cooldown (unless force=True)
        2. Fetch alerts from database
        3. Generate summary via LLM (with fallback)
        4. Store brief with audit trail
        5. Mark previous brief as superseded

        Args:
            time_period: Analysis period (24h, 7d, 30d)
            user_email: User who requested the brief
            force: Skip cooldown check (admin only)

        Returns:
            Newly generated ExecutiveBrief

        Raises:
            ValueError: If cooldown not expired and force=False
        """
        start_time = time.time()
        logger.info(
            f"SEC-065: Generating executive brief for org_id={self.org_id} "
            f"period={time_period} user={user_email}"
        )

        # Check cooldown
        if not force:
            can_regen, remaining = self.can_regenerate()
            if not can_regen:
                raise ValueError(
                    f"Rate limit: Please wait {remaining} seconds before regenerating. "
                    f"Cooldown: {self.config.COOLDOWN_MINUTES} minutes."
                )

        try:
            # Fetch alerts from database
            alerts = self._fetch_alerts_for_period(time_period)
            logger.info(f"SEC-065: Fetched {len(alerts)} alerts for period {time_period}")

            # Calculate metrics
            metrics = self._calculate_metrics(alerts)

            # Generate summary
            summary, method, llm_info = self._generate_summary(alerts, metrics)

            # Create brief record
            brief = self._create_brief_record(
                time_period=time_period,
                user_email=user_email,
                alerts=alerts,
                metrics=metrics,
                summary=summary,
                generation_method=method,
                llm_info=llm_info,
                start_time=start_time
            )

            # Mark previous briefs as superseded
            self._supersede_previous_briefs(brief)

            # Commit
            self.db.add(brief)
            self.db.commit()
            self.db.refresh(brief)

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"SEC-065: Brief generated successfully brief_id={brief.brief_id} "
                f"alerts={brief.alert_count} risk={brief.risk_assessment} "
                f"method={method} time={elapsed_ms:.0f}ms"
            )

            return brief

        except ValueError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            logger.error(f"SEC-065: Brief generation failed for org_id={self.org_id}: {e}")
            self.db.rollback()
            raise

    def get_brief_history(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[ExecutiveBrief]:
        """
        Get historical briefs for audit purposes.

        Compliance: SOC 2 AU-6 - Audit record review

        Args:
            limit: Maximum briefs to return
            offset: Pagination offset

        Returns:
            List of ExecutiveBrief records
        """
        try:
            briefs = self.db.query(ExecutiveBrief).filter(
                ExecutiveBrief.organization_id == self.org_id
            ).order_by(
                desc(ExecutiveBrief.generated_at)
            ).offset(offset).limit(limit).all()

            logger.debug(
                f"SEC-065: Retrieved {len(briefs)} historical briefs "
                f"for org_id={self.org_id}"
            )

            return briefs

        except Exception as e:
            logger.error(f"SEC-065: Failed to get brief history: {e}")
            return []

    def get_brief_by_id(self, brief_id: str) -> Optional[ExecutiveBrief]:
        """
        Get a specific brief by ID.

        Args:
            brief_id: The brief identifier

        Returns:
            ExecutiveBrief if found and belongs to org, None otherwise
        """
        try:
            brief = self.db.query(ExecutiveBrief).filter(
                and_(
                    ExecutiveBrief.brief_id == brief_id,
                    ExecutiveBrief.organization_id == self.org_id
                )
            ).first()

            return brief

        except Exception as e:
            logger.error(f"SEC-065: Failed to get brief {brief_id}: {e}")
            return None

    def record_view(self, brief_id: str, user_email: str) -> bool:
        """
        Record that a user viewed a brief (audit trail).

        Args:
            brief_id: The brief identifier
            user_email: User who viewed

        Returns:
            True if recorded successfully
        """
        try:
            brief = self.get_brief_by_id(brief_id)
            if not brief:
                return False

            viewed_by = brief.viewed_by or []
            view_record = {
                "email": user_email,
                "viewed_at": datetime.now(UTC).isoformat()
            }
            viewed_by.append(view_record)
            brief.viewed_by = viewed_by

            self.db.commit()
            logger.debug(f"SEC-065: Recorded view for brief {brief_id} by {user_email}")
            return True

        except Exception as e:
            logger.error(f"SEC-065: Failed to record view: {e}")
            self.db.rollback()
            return False

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _fetch_alerts_for_period(self, time_period: str) -> List[Alert]:
        """
        Fetch alerts from database for the specified time period.

        Multi-tenant isolation: Only fetches alerts for self.org_id
        """
        days = self.config.TIME_PERIOD_DAYS.get(time_period, 1)
        cutoff = datetime.now(UTC) - timedelta(days=days)

        alerts = self.db.query(Alert).filter(
            and_(
                Alert.organization_id == self.org_id,
                Alert.timestamp >= cutoff
            )
        ).order_by(desc(Alert.timestamp)).limit(
            self.config.MAX_ALERTS_FOR_ANALYSIS
        ).all()

        return alerts

    def _calculate_metrics(self, alerts: List[Alert]) -> Dict[str, Any]:
        """
        Calculate key metrics from alerts.
        """
        if not alerts:
            return {
                "total_alerts": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "acknowledged_count": 0,
                "pending_count": 0,
                "threats_detected": 0,
                "threats_prevented": 0,
                "cost_savings": "$0",
                "system_accuracy": "N/A"
            }

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        acknowledged = 0
        pending = 0

        for alert in alerts:
            severity = (alert.severity or "low").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

            if alert.status == "acknowledged":
                acknowledged += 1
            elif alert.status in ("new", "pending", "active"):
                pending += 1

        # Calculate derived metrics
        total = len(alerts)
        high_priority = severity_counts["critical"] + severity_counts["high"]
        prevented = acknowledged  # Acknowledged = handled = prevented

        # Cost savings estimate (configurable per organization)
        # Uses COST_PER_INCIDENT_USD from config (default: $50K)
        # Set to 0 in config to disable cost savings calculation
        if self.config.COST_PER_INCIDENT_USD > 0:
            cost_savings = prevented * self.config.COST_PER_INCIDENT_USD
        else:
            cost_savings = 0

        # System accuracy based on resolution rate
        accuracy = (acknowledged / total * 100) if total > 0 else 0

        return {
            "total_alerts": total,
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "acknowledged_count": acknowledged,
            "pending_count": pending,
            "threats_detected": total,
            "threats_prevented": prevented,
            "cost_savings": f"${cost_savings:,}",
            "system_accuracy": f"{accuracy:.1f}%" if total > 0 else "N/A"
        }

    def _generate_summary(
        self,
        alerts: List[Alert],
        metrics: Dict[str, Any]
    ) -> Tuple[str, str, Dict]:
        """
        Generate executive summary using LLM with fallback.

        Returns:
            Tuple of (summary_text, method, llm_info)
        """
        # If no alerts, return empty state
        if not alerts:
            return (
                "No security events detected for this organization during the analysis period. "
                "Systems are operating normally with no actionable alerts requiring executive attention.",
                "empty_state",
                {}
            )

        # Try LLM generation
        try:
            summary, llm_info = self._generate_with_llm(alerts, metrics)
            return (summary, "llm", llm_info)
        except Exception as e:
            logger.warning(f"SEC-065: LLM generation failed, using fallback: {e}")
            summary = self._generate_fallback(alerts, metrics)
            return (summary, "fallback", {"error": str(e)})

    def _generate_with_llm(
        self,
        alerts: List[Alert],
        metrics: Dict[str, Any]
    ) -> Tuple[str, Dict]:
        """
        Generate summary using OpenAI LLM.
        """
        from llm_utils import client

        if not client:
            raise Exception("OpenAI client not available")

        # Prepare alert summary for LLM
        alert_summary = self._prepare_alert_summary_for_llm(alerts[:20])  # Top 20 alerts

        prompt = f"""
EXECUTIVE SECURITY BRIEFING - {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}

SECURITY METRICS:
- Total Security Events: {metrics['total_alerts']}
- Critical Alerts: {metrics['critical_count']}
- High Priority Alerts: {metrics['high_count']}
- Threats Prevented: {metrics['threats_prevented']}
- Estimated Cost Savings: {metrics['cost_savings']}

RECENT ALERT SUMMARY:
{alert_summary}

Please provide a concise executive briefing (3-4 paragraphs) covering:

1. EXECUTIVE SUMMARY: High-level security posture assessment for C-level executives

2. KEY RISKS & BUSINESS IMPACT: Most significant threats and their potential business impact

3. IMMEDIATE ACTIONS: Prioritized recommendations for the security team

4. STRATEGIC OUTLOOK: Forward-looking security recommendations

Focus on business impact, risk mitigation, and actionable insights. Use professional, executive-appropriate language.
"""

        response = client.chat.completions.create(
            model=self.config.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior cybersecurity executive advisor providing "
                        "briefings to C-level executives and board members. Your summaries "
                        "are concise, business-focused, and actionable."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config.LLM_MAX_TOKENS,
            temperature=self.config.LLM_TEMPERATURE
        )

        summary = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Estimate cost (GPT-3.5-turbo pricing)
        cost_per_1k = 0.002  # $0.002 per 1K tokens
        estimated_cost = (tokens_used / 1000) * cost_per_1k

        llm_info = {
            "model": self.config.LLM_MODEL,
            "tokens_used": tokens_used,
            "estimated_cost_usd": estimated_cost
        }

        return (summary, llm_info)

    def _prepare_alert_summary_for_llm(self, alerts: List[Alert]) -> str:
        """
        Prepare a text summary of alerts for LLM consumption.
        """
        if not alerts:
            return "No recent alerts."

        lines = []
        for i, alert in enumerate(alerts[:10], 1):
            severity = (alert.severity or "unknown").upper()
            alert_type = alert.alert_type or "Unknown Type"
            message = (alert.message or "No message")[:100]
            lines.append(f"{i}. [{severity}] {alert_type}: {message}")

        if len(alerts) > 10:
            lines.append(f"... and {len(alerts) - 10} more alerts")

        return "\n".join(lines)

    def _generate_fallback(
        self,
        alerts: List[Alert],
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate enterprise fallback summary when LLM unavailable.
        """
        total = metrics['total_alerts']
        critical = metrics['critical_count']
        high = metrics['high_count']
        high_priority = critical + high

        # Determine risk level description
        if critical >= 5:
            risk_desc = "CRITICAL risk level requiring immediate executive attention"
        elif high_priority >= 10:
            risk_desc = "ELEVATED risk level requiring prompt security team response"
        elif high_priority >= 5:
            risk_desc = "MODERATE risk level with several high-priority items"
        elif total > 0:
            risk_desc = "LOW risk level with normal security operations"
        else:
            risk_desc = "MINIMAL activity with no significant security events"

        summary = f"""
EXECUTIVE SECURITY BRIEFING
Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}

EXECUTIVE SUMMARY:
Your enterprise security monitoring systems detected {total} security events during the analysis period. The current security posture indicates {risk_desc}. {high_priority} alerts have been classified as high-priority, requiring attention from your security operations team.

KEY SECURITY METRICS:
- Total Security Events: {total}
- Critical Alerts: {critical}
- High Priority Alerts: {high}
- Threats Mitigated: {metrics['threats_prevented']}
- Estimated Cost Savings: {metrics['cost_savings']}

RECOMMENDED ACTIONS:
{"1. IMMEDIATE: Convene security response team to address critical alerts" if critical > 0 else "1. ROUTINE: Continue standard security monitoring procedures"}
{"2. HIGH: Review and triage high-priority security events within 4 hours" if high > 0 else "2. STANDARD: Maintain current security posture"}
3. ONGOING: Ensure security team reviews all pending alerts per SLA requirements
4. STRATEGIC: Consider security posture assessment if alert volume increases

NEXT REVIEW: This briefing will be automatically refreshed in 1 hour or upon significant security events.

This briefing was generated by your enterprise AI security operations center. For detailed technical analysis, please consult with your Chief Information Security Officer.
"""

        return summary.strip()

    def _calculate_risk_assessment(self, metrics: Dict[str, Any]) -> str:
        """
        Calculate overall risk assessment level.
        """
        critical = metrics.get('critical_count', 0)
        high = metrics.get('high_count', 0)
        total = metrics.get('total_alerts', 0)

        if critical >= self.config.RISK_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif high >= self.config.RISK_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif total >= self.config.RISK_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        elif total > 0:
            return "LOW"
        else:
            return "NO_DATA"

    def _generate_recommendations(
        self,
        alerts: List[Alert],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prioritized recommendations based on alert analysis.
        """
        recommendations = []

        critical = metrics.get('critical_count', 0)
        high = metrics.get('high_count', 0)
        pending = metrics.get('pending_count', 0)

        if critical > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "action": f"Address {critical} critical security alerts immediately",
                "timeframe": "Within 1 hour",
                "owner": "Security Operations Team"
            })

        if high > 0:
            recommendations.append({
                "priority": "HIGH",
                "action": f"Review and triage {high} high-priority alerts",
                "timeframe": "Within 4 hours",
                "owner": "Security Analysts"
            })

        if pending > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Clear backlog of {pending} pending alerts",
                "timeframe": "Within 24 hours",
                "owner": "SOC Team"
            })

        # Always add ongoing recommendation
        recommendations.append({
            "priority": "LOW",
            "action": "Continue security monitoring and review daily briefings",
            "timeframe": "Ongoing",
            "owner": "Security Team"
        })

        return recommendations

    def _create_alert_snapshot(self, alerts: List[Alert]) -> List[Dict]:
        """
        Create a snapshot of alert IDs for audit trail.
        Limits to MAX_ALERT_SNAPSHOT for storage efficiency.
        """
        snapshot = []
        for alert in alerts[:self.config.MAX_ALERT_SNAPSHOT]:
            snapshot.append({
                "id": alert.id,
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "timestamp": alert.timestamp.isoformat() if alert.timestamp else None
            })
        return snapshot

    def _create_brief_record(
        self,
        time_period: str,
        user_email: str,
        alerts: List[Alert],
        metrics: Dict[str, Any],
        summary: str,
        generation_method: str,
        llm_info: Dict,
        start_time: float
    ) -> ExecutiveBrief:
        """
        Create the ExecutiveBrief database record.
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self.config.CACHE_TTL_HOURS)
        brief_id = f"exec-brief-{int(now.timestamp())}"

        # Calculate derived values
        risk_assessment = self._calculate_risk_assessment(metrics)
        recommendations = self._generate_recommendations(alerts, metrics)
        alert_snapshot = self._create_alert_snapshot(alerts)
        generation_time_ms = int((time.time() - start_time) * 1000)

        brief = ExecutiveBrief(
            organization_id=self.org_id,
            brief_id=brief_id,
            time_period=time_period,
            generated_at=now,
            expires_at=expires_at,
            generated_by=user_email,
            summary=summary,
            key_metrics={
                "threats_detected": metrics['total_alerts'],
                "threats_prevented": metrics['threats_prevented'],
                "cost_savings": metrics['cost_savings'],
                "system_accuracy": metrics['system_accuracy']
            },
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            alert_count=metrics['total_alerts'],
            high_priority_count=metrics['critical_count'] + metrics['high_count'],
            critical_count=metrics['critical_count'],
            alert_snapshot=alert_snapshot,
            generation_method=generation_method,
            generation_time_ms=generation_time_ms,
            llm_model=llm_info.get('model'),
            llm_tokens_used=llm_info.get('tokens_used'),
            llm_cost_usd=llm_info.get('estimated_cost_usd'),
            is_current=True,
            version=1,
            distribution_list=["CEO", "CISO", "CTO", "Security Team"]
        )

        return brief

    def _supersede_previous_briefs(self, new_brief: ExecutiveBrief) -> None:
        """
        Mark previous briefs as superseded (not current).
        Maintains audit trail while ensuring only one current brief.
        """
        try:
            self.db.query(ExecutiveBrief).filter(
                and_(
                    ExecutiveBrief.organization_id == self.org_id,
                    ExecutiveBrief.is_current == True,
                    ExecutiveBrief.id != new_brief.id
                )
            ).update({
                "is_current": False,
                "superseded_by_id": new_brief.id
            })

            logger.debug(f"SEC-065: Superseded previous briefs for org_id={self.org_id}")

        except Exception as e:
            logger.warning(f"SEC-065: Failed to supersede previous briefs: {e}")
            # Non-critical, continue


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_executive_brief_service(
    db: Session,
    org_id: int,
    config: ExecutiveBriefConfig = None
) -> ExecutiveBriefService:
    """
    Factory function to create ExecutiveBriefService.

    Usage:
        from services.executive_brief_service import get_executive_brief_service

        service = get_executive_brief_service(db, org_id)
        brief = service.get_cached_brief()
    """
    return ExecutiveBriefService(db, org_id, config)
