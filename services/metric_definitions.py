"""
SEC-066: OW-kai Common Information Model (CIM)
Enterprise-grade standardized metric definitions

Aligned with industry leaders:
- Splunk Common Information Model (CIM)
- Datadog Unified Service Tagging
- Wiz Unified Risk Engine

Compliance:
- SOC 2 PI-1: Processing Integrity
- PCI-DSS 10.6: Consistent reporting
- NIST AU-6: Reliable audit metrics

All platform components MUST use these standardized definitions.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


# =============================================================================
# METRIC CATEGORIES
# =============================================================================

class MetricCategory(str, Enum):
    """Standard metric categories aligned with Splunk CIM domains"""
    ALERTS = "alerts"
    THREATS = "threats"
    FINANCIAL = "financial"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    RISK = "risk"
    AUTOMATION = "automation"


class MetricUnit(str, Enum):
    """Standard units for metric values"""
    COUNT = "count"
    PERCENTAGE = "percentage"
    CURRENCY_USD = "currency_usd"
    MINUTES = "minutes"
    HOURS = "hours"
    SCORE = "score"
    RATIO = "ratio"


class MetricValueType(str, Enum):
    """Data types for metric values"""
    INTEGER = "integer"
    FLOAT = "float"
    CURRENCY = "currency"
    STRING = "string"


# =============================================================================
# COMMON INFORMATION MODEL - STANDARDIZED FIELD NAMES
# =============================================================================

class MetricCIM:
    """
    OW-kai Common Information Model

    Standardized field names across ALL platform components.
    Modeled after Splunk CIM for enterprise consistency.

    Usage:
        from services.metric_definitions import MetricCIM

        # All components use same field names
        metrics[MetricCIM.THREATS_PREVENTED] = prevented_count
        metrics[MetricCIM.COST_SAVINGS] = savings_amount
    """

    # =========================================================================
    # ALERT METRICS - Core security event counts
    # =========================================================================
    ALERTS_TOTAL = "alerts.total"
    ALERTS_CRITICAL = "alerts.severity.critical"
    ALERTS_HIGH = "alerts.severity.high"
    ALERTS_MEDIUM = "alerts.severity.medium"
    ALERTS_LOW = "alerts.severity.low"
    ALERTS_ACKNOWLEDGED = "alerts.status.acknowledged"
    ALERTS_PENDING = "alerts.status.pending"
    ALERTS_DISMISSED = "alerts.status.dismissed"
    ALERTS_ESCALATED = "alerts.status.escalated"

    # =========================================================================
    # THREAT METRICS - Standardized threat terminology
    # =========================================================================
    THREATS_DETECTED = "threats.detected"           # Total threats identified
    THREATS_PREVENTED = "threats.prevented"         # Successfully mitigated
    THREATS_PENDING = "threats.pending"             # Awaiting action
    THREATS_MISSED = "threats.missed"               # False negatives

    # =========================================================================
    # FINANCIAL METRICS - Cost and savings calculations
    # =========================================================================
    COST_SAVINGS = "financial.cost_savings"         # Total estimated savings
    COST_SAVINGS_MONTHLY = "financial.cost_savings_monthly"
    COST_SAVINGS_ANNUAL = "financial.cost_savings_annual"
    COST_PER_INCIDENT = "financial.cost_per_incident"
    ROI_PERCENTAGE = "financial.roi_percentage"
    TIME_SAVINGS_HOURS = "financial.time_savings_hours"

    # =========================================================================
    # PERFORMANCE METRICS - System effectiveness
    # =========================================================================
    ACCURACY_RATE = "performance.accuracy_rate"
    FALSE_POSITIVE_RATE = "performance.false_positive_rate"
    FALSE_NEGATIVE_RATE = "performance.false_negative_rate"
    MTTR_MINUTES = "performance.mttr_minutes"       # Mean Time To Resolve
    MTTD_MINUTES = "performance.mttd_minutes"       # Mean Time To Detect
    SLA_COMPLIANCE = "performance.sla_compliance"
    AUTOMATION_RATE = "performance.automation_rate"
    PROCESSING_TIME_MS = "performance.processing_time_ms"

    # =========================================================================
    # RISK METRICS - Risk scoring and assessment
    # =========================================================================
    RISK_SCORE = "risk.score"                       # 0-100 composite score
    RISK_LEVEL = "risk.level"                       # CRITICAL/HIGH/MEDIUM/LOW
    RISK_TREND = "risk.trend"                       # increasing/stable/decreasing
    CVSS_SCORE = "risk.cvss_score"                  # 0-10 CVSS v3.1

    # =========================================================================
    # COMPLIANCE METRICS - Regulatory compliance
    # =========================================================================
    COMPLIANCE_SCORE = "compliance.score"
    COMPLIANCE_VIOLATIONS = "compliance.violations"
    POLICY_ADHERENCE = "compliance.policy_adherence"

    # =========================================================================
    # AUTOMATION METRICS - Workflow automation
    # =========================================================================
    AUTOMATION_EXECUTIONS = "automation.executions"
    AUTOMATION_SUCCESS_RATE = "automation.success_rate"
    AUTO_APPROVED = "automation.auto_approved"
    MANUAL_REVIEW = "automation.manual_review"


# =============================================================================
# METRIC DEFINITION SCHEMA
# =============================================================================

@dataclass
class MetricDefinition:
    """
    Immutable metric definition with validation rules.

    Aligned with Datadog metric metadata pattern.
    Each metric has explicit bounds to prevent invalid values
    (e.g., negative cost savings).
    """
    metric_id: str                          # CIM field name
    display_name: str                       # Human-readable name
    description: str                        # Detailed description
    category: MetricCategory                # Metric category
    unit: MetricUnit                        # Unit of measurement
    value_type: MetricValueType             # Data type
    calculation: str                        # Formula/SQL reference
    min_value: Optional[float] = None       # Validation: minimum allowed
    max_value: Optional[float] = None       # Validation: maximum allowed
    version: int = 1                        # Schema version
    deprecated: bool = False                # Deprecation flag

    def validate(self, value: float) -> bool:
        """Validate a value against this definition's constraints"""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def clamp(self, value: float) -> float:
        """Clamp value to valid range"""
        if self.min_value is not None:
            value = max(self.min_value, value)
        if self.max_value is not None:
            value = min(self.max_value, value)
        return value


# =============================================================================
# STANDARD METRIC DEFINITIONS
# =============================================================================

METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    # -------------------------------------------------------------------------
    # ALERT METRICS
    # -------------------------------------------------------------------------
    MetricCIM.ALERTS_TOTAL: MetricDefinition(
        metric_id=MetricCIM.ALERTS_TOTAL,
        display_name="Total Alerts",
        description="Total number of security alerts in the analysis period",
        category=MetricCategory.ALERTS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE timestamp >= period_start)",
        min_value=0
    ),

    MetricCIM.ALERTS_CRITICAL: MetricDefinition(
        metric_id=MetricCIM.ALERTS_CRITICAL,
        display_name="Critical Alerts",
        description="Alerts with critical severity requiring immediate attention",
        category=MetricCategory.ALERTS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE severity='critical')",
        min_value=0
    ),

    MetricCIM.ALERTS_HIGH: MetricDefinition(
        metric_id=MetricCIM.ALERTS_HIGH,
        display_name="High Severity Alerts",
        description="Alerts with high severity",
        category=MetricCategory.ALERTS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE severity='high')",
        min_value=0
    ),

    MetricCIM.ALERTS_ACKNOWLEDGED: MetricDefinition(
        metric_id=MetricCIM.ALERTS_ACKNOWLEDGED,
        display_name="Acknowledged Alerts",
        description="Alerts that have been reviewed and acknowledged",
        category=MetricCategory.ALERTS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE acknowledged_at IS NOT NULL)",
        min_value=0
    ),

    # -------------------------------------------------------------------------
    # THREAT METRICS
    # -------------------------------------------------------------------------
    MetricCIM.THREATS_DETECTED: MetricDefinition(
        metric_id=MetricCIM.THREATS_DETECTED,
        display_name="Threats Detected",
        description="Total security threats identified by the system",
        category=MetricCategory.THREATS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="= alerts.total (threats are surfaced as alerts)",
        min_value=0
    ),

    MetricCIM.THREATS_PREVENTED: MetricDefinition(
        metric_id=MetricCIM.THREATS_PREVENTED,
        display_name="Threats Prevented",
        description="Security threats successfully mitigated through acknowledgment/resolution",
        category=MetricCategory.THREATS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE acknowledged_at IS NOT NULL)",
        min_value=0
    ),

    MetricCIM.THREATS_PENDING: MetricDefinition(
        metric_id=MetricCIM.THREATS_PENDING,
        display_name="Threats Pending",
        description="Security threats awaiting review or action",
        category=MetricCategory.THREATS,
        unit=MetricUnit.COUNT,
        value_type=MetricValueType.INTEGER,
        calculation="COUNT(alerts WHERE acknowledged_at IS NULL)",
        min_value=0
    ),

    # -------------------------------------------------------------------------
    # FINANCIAL METRICS
    # -------------------------------------------------------------------------
    MetricCIM.COST_SAVINGS: MetricDefinition(
        metric_id=MetricCIM.COST_SAVINGS,
        display_name="Cost Savings",
        description="Estimated cost savings from prevented security incidents",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.CURRENCY_USD,
        value_type=MetricValueType.CURRENCY,
        calculation="threats.prevented × organization.cost_per_incident_usd",
        min_value=0,  # CRITICAL: Never negative
        max_value=None
    ),

    MetricCIM.COST_SAVINGS_MONTHLY: MetricDefinition(
        metric_id=MetricCIM.COST_SAVINGS_MONTHLY,
        display_name="Monthly Cost Savings",
        description="Estimated monthly cost savings extrapolated from current period",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.CURRENCY_USD,
        value_type=MetricValueType.CURRENCY,
        calculation="cost_savings × (30 / period_days)",
        min_value=0
    ),

    MetricCIM.COST_SAVINGS_ANNUAL: MetricDefinition(
        metric_id=MetricCIM.COST_SAVINGS_ANNUAL,
        display_name="Annual Cost Savings",
        description="Projected annual cost savings",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.CURRENCY_USD,
        value_type=MetricValueType.CURRENCY,
        calculation="cost_savings_monthly × 12",
        min_value=0
    ),

    MetricCIM.COST_PER_INCIDENT: MetricDefinition(
        metric_id=MetricCIM.COST_PER_INCIDENT,
        display_name="Cost Per Incident",
        description="Estimated cost of a single security incident (configurable per org)",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.CURRENCY_USD,
        value_type=MetricValueType.CURRENCY,
        calculation="organization.cost_per_incident_usd (default: $50,000)",
        min_value=0
    ),

    MetricCIM.ROI_PERCENTAGE: MetricDefinition(
        metric_id=MetricCIM.ROI_PERCENTAGE,
        display_name="ROI Percentage",
        description="Return on investment percentage for security operations",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.PERCENTAGE,
        value_type=MetricValueType.FLOAT,
        calculation="(cost_savings / operational_cost) × 100",
        min_value=0
    ),

    MetricCIM.TIME_SAVINGS_HOURS: MetricDefinition(
        metric_id=MetricCIM.TIME_SAVINGS_HOURS,
        display_name="Time Savings (Hours)",
        description="Analyst hours saved through automation",
        category=MetricCategory.FINANCIAL,
        unit=MetricUnit.HOURS,
        value_type=MetricValueType.FLOAT,
        calculation="automated_resolutions × avg_manual_resolution_time",
        min_value=0
    ),

    # -------------------------------------------------------------------------
    # PERFORMANCE METRICS
    # -------------------------------------------------------------------------
    MetricCIM.ACCURACY_RATE: MetricDefinition(
        metric_id=MetricCIM.ACCURACY_RATE,
        display_name="System Accuracy",
        description="Percentage of alerts correctly identified and resolved",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.PERCENTAGE,
        value_type=MetricValueType.FLOAT,
        calculation="(acknowledged / total) × 100",
        min_value=0,
        max_value=100
    ),

    MetricCIM.FALSE_POSITIVE_RATE: MetricDefinition(
        metric_id=MetricCIM.FALSE_POSITIVE_RATE,
        display_name="False Positive Rate",
        description="Percentage of alerts that were false positives",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.PERCENTAGE,
        value_type=MetricValueType.FLOAT,
        calculation="(dismissed / total) × 100",
        min_value=0,
        max_value=100
    ),

    MetricCIM.MTTR_MINUTES: MetricDefinition(
        metric_id=MetricCIM.MTTR_MINUTES,
        display_name="Mean Time to Resolve",
        description="Average time in minutes to acknowledge/resolve an alert",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.MINUTES,
        value_type=MetricValueType.FLOAT,
        calculation="AVG(acknowledged_at - timestamp) in minutes",
        min_value=0
    ),

    MetricCIM.SLA_COMPLIANCE: MetricDefinition(
        metric_id=MetricCIM.SLA_COMPLIANCE,
        display_name="SLA Compliance",
        description="Percentage of alerts resolved within SLA timeframes",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.PERCENTAGE,
        value_type=MetricValueType.FLOAT,
        calculation="(resolved_within_sla / total_resolved) × 100",
        min_value=0,
        max_value=100
    ),

    MetricCIM.AUTOMATION_RATE: MetricDefinition(
        metric_id=MetricCIM.AUTOMATION_RATE,
        display_name="Automation Rate",
        description="Percentage of alerts handled automatically without manual intervention",
        category=MetricCategory.PERFORMANCE,
        unit=MetricUnit.PERCENTAGE,
        value_type=MetricValueType.FLOAT,
        calculation="(auto_resolved / total) × 100",
        min_value=0,
        max_value=100
    ),

    # -------------------------------------------------------------------------
    # RISK METRICS
    # -------------------------------------------------------------------------
    MetricCIM.RISK_SCORE: MetricDefinition(
        metric_id=MetricCIM.RISK_SCORE,
        display_name="Risk Score",
        description="Composite security risk score (0-100, higher = more risk)",
        category=MetricCategory.RISK,
        unit=MetricUnit.SCORE,
        value_type=MetricValueType.FLOAT,
        calculation="Weighted composite of severity, volume, and trend factors",
        min_value=0,
        max_value=100
    ),

    MetricCIM.CVSS_SCORE: MetricDefinition(
        metric_id=MetricCIM.CVSS_SCORE,
        display_name="CVSS Score",
        description="Common Vulnerability Scoring System score (0-10)",
        category=MetricCategory.RISK,
        unit=MetricUnit.SCORE,
        value_type=MetricValueType.FLOAT,
        calculation="CVSS v3.1 base score calculation",
        min_value=0,
        max_value=10
    ),
}


# =============================================================================
# ORGANIZATION CONFIGURATION
# =============================================================================

@dataclass
class OrgMetricConfig:
    """
    Organization-specific metric configuration.
    Allows enterprises to customize calculations per their risk model.

    H-003: All values are validated in __post_init__ to prevent:
    - Fraudulent ROI inflation via extreme cost_per_incident
    - Invalid SLA configurations
    - Data integrity issues
    """
    organization_id: int

    # Financial configuration
    cost_per_incident_usd: float = 50000.0      # Default: $50K per incident
    hourly_analyst_rate_usd: float = 75.0       # Default: $75/hour

    # Time configuration
    default_analysis_period_hours: int = 24     # Default: 24 hours
    sla_critical_minutes: int = 15              # Critical SLA: 15 min
    sla_high_minutes: int = 30                  # High SLA: 30 min
    sla_medium_minutes: int = 60                # Medium SLA: 1 hour
    sla_low_minutes: int = 120                  # Low SLA: 2 hours

    # Feature flags
    include_dismissed_in_accuracy: bool = False  # Whether dismissed counts as resolved

    def __post_init__(self):
        """
        H-003: Validate all configuration values.

        Prevents:
        - Fraudulent cost_per_incident values
        - Invalid analyst rates
        - Zero or negative SLA values
        """
        # Financial validation (reasonable business ranges)
        if not (100 <= self.cost_per_incident_usd <= 10_000_000):
            raise ValueError(
                f"SEC-066: cost_per_incident_usd must be between $100-$10M, "
                f"got ${self.cost_per_incident_usd:,.2f}"
            )

        if not (10 <= self.hourly_analyst_rate_usd <= 1000):
            raise ValueError(
                f"SEC-066: hourly_analyst_rate_usd must be between $10-$1000, "
                f"got ${self.hourly_analyst_rate_usd:,.2f}"
            )

        # Time configuration validation
        if not (1 <= self.default_analysis_period_hours <= 8760):
            raise ValueError(
                f"SEC-066: default_analysis_period_hours must be 1-8760, "
                f"got {self.default_analysis_period_hours}"
            )

        # SLA validation (must be positive and in ascending order)
        sla_fields = [
            ('sla_critical_minutes', self.sla_critical_minutes),
            ('sla_high_minutes', self.sla_high_minutes),
            ('sla_medium_minutes', self.sla_medium_minutes),
            ('sla_low_minutes', self.sla_low_minutes)
        ]

        for field_name, value in sla_fields:
            if value <= 0:
                raise ValueError(
                    f"SEC-066: {field_name} must be > 0, got {value}"
                )
            if value > 1440:  # Max 24 hours
                raise ValueError(
                    f"SEC-066: {field_name} must be <= 1440 (24 hours), got {value}"
                )

        # SLA hierarchy validation (critical should be shorter than low)
        if not (self.sla_critical_minutes <= self.sla_high_minutes <=
                self.sla_medium_minutes <= self.sla_low_minutes):
            raise ValueError(
                f"SEC-066: SLA values must be in ascending order: "
                f"critical({self.sla_critical_minutes}) <= high({self.sla_high_minutes}) <= "
                f"medium({self.sla_medium_minutes}) <= low({self.sla_low_minutes})"
            )

    def get_sla_minutes(self, severity: str) -> int:
        """Get SLA threshold for a severity level"""
        sla_map = {
            "critical": self.sla_critical_minutes,
            "high": self.sla_high_minutes,
            "medium": self.sla_medium_minutes,
            "low": self.sla_low_minutes
        }
        return sla_map.get(severity.lower(), self.sla_medium_minutes)


# =============================================================================
# METRIC SNAPSHOT - Immutable calculation result
# =============================================================================

@dataclass
class MetricSnapshot:
    """
    Immutable snapshot of all calculated metrics.

    This is the standard output from UnifiedMetricsEngine.
    All platform components consume this snapshot for consistency.
    """
    # Metadata
    organization_id: int
    period_hours: int
    generated_at: datetime
    engine_version: str = "1.0.0"
    cim_version: str = "1.0.0"

    # Alert metrics
    alerts_total: int = 0
    alerts_critical: int = 0
    alerts_high: int = 0
    alerts_medium: int = 0
    alerts_low: int = 0
    alerts_acknowledged: int = 0
    alerts_pending: int = 0
    alerts_dismissed: int = 0

    # Threat metrics
    threats_detected: int = 0
    threats_prevented: int = 0
    threats_pending: int = 0

    # Financial metrics
    cost_savings: float = 0.0
    cost_savings_monthly: float = 0.0
    cost_savings_annual: float = 0.0
    cost_per_incident: float = 50000.0
    roi_percentage: float = 0.0
    time_savings_hours: float = 0.0

    # Performance metrics
    accuracy_rate: float = 0.0
    false_positive_rate: float = 0.0
    mttr_minutes: float = 0.0
    sla_compliance: float = 0.0
    automation_rate: float = 0.0

    # Risk metrics
    risk_score: float = 0.0
    risk_level: str = "LOW"
    risk_trend: str = "stable"

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary for API responses"""
        return {
            # Metadata
            "meta": {
                "organization_id": self.organization_id,
                "period_hours": self.period_hours,
                "generated_at": self.generated_at.isoformat(),
                "engine_version": self.engine_version,
                "cim_version": self.cim_version
            },
            # Alert metrics
            MetricCIM.ALERTS_TOTAL: self.alerts_total,
            MetricCIM.ALERTS_CRITICAL: self.alerts_critical,
            MetricCIM.ALERTS_HIGH: self.alerts_high,
            MetricCIM.ALERTS_MEDIUM: self.alerts_medium,
            MetricCIM.ALERTS_LOW: self.alerts_low,
            MetricCIM.ALERTS_ACKNOWLEDGED: self.alerts_acknowledged,
            MetricCIM.ALERTS_PENDING: self.alerts_pending,
            MetricCIM.ALERTS_DISMISSED: self.alerts_dismissed,
            # Threat metrics
            MetricCIM.THREATS_DETECTED: self.threats_detected,
            MetricCIM.THREATS_PREVENTED: self.threats_prevented,
            MetricCIM.THREATS_PENDING: self.threats_pending,
            # Financial metrics
            MetricCIM.COST_SAVINGS: self.cost_savings,
            MetricCIM.COST_SAVINGS_MONTHLY: self.cost_savings_monthly,
            MetricCIM.COST_SAVINGS_ANNUAL: self.cost_savings_annual,
            MetricCIM.COST_PER_INCIDENT: self.cost_per_incident,
            MetricCIM.ROI_PERCENTAGE: self.roi_percentage,
            MetricCIM.TIME_SAVINGS_HOURS: self.time_savings_hours,
            # Performance metrics
            MetricCIM.ACCURACY_RATE: self.accuracy_rate,
            MetricCIM.FALSE_POSITIVE_RATE: self.false_positive_rate,
            MetricCIM.MTTR_MINUTES: self.mttr_minutes,
            MetricCIM.SLA_COMPLIANCE: self.sla_compliance,
            MetricCIM.AUTOMATION_RATE: self.automation_rate,
            # Risk metrics
            MetricCIM.RISK_SCORE: self.risk_score,
            MetricCIM.RISK_LEVEL: self.risk_level,
            MetricCIM.RISK_TREND: self.risk_trend
        }

    def format_for_display(self) -> dict:
        """Format metrics for UI display with proper formatting"""
        return {
            "threats": {
                "detected": self.threats_detected,
                "prevented": self.threats_prevented,
                "pending": self.threats_pending
            },
            "financial": {
                "cost_savings": f"${self.cost_savings:,.0f}",
                "cost_savings_monthly": f"${self.cost_savings_monthly:,.0f}",
                "cost_savings_annual": f"${self.cost_savings_annual:,.0f}",
                "roi_percentage": f"{self.roi_percentage:.1f}%",
                "time_savings": f"{self.time_savings_hours:.1f} hours"
            },
            "performance": {
                "accuracy_rate": f"{self.accuracy_rate:.1f}%",
                "false_positive_rate": f"{self.false_positive_rate:.1f}%",
                "mttr": f"{self.mttr_minutes:.1f} min",
                "sla_compliance": f"{self.sla_compliance:.1f}%",
                "automation_rate": f"{self.automation_rate:.1f}%"
            },
            "risk": {
                "score": self.risk_score,
                "level": self.risk_level,
                "trend": self.risk_trend
            }
        }
