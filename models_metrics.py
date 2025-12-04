"""
SEC-066: Enterprise Metric Models
SQLAlchemy models for metric audit and configuration

Compliance:
- SOC 2 AU-6: Audit record review
- SOC 2 PI-1: Processing Integrity
- PCI-DSS 10.2: Implement audit trails
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class MetricCalculationAudit(Base):
    """
    SEC-066: Audit trail for all metric calculations.

    Every metric calculation is logged for SOC 2 compliance.
    Enables reproducibility and investigation of metric values.
    """
    __tablename__ = "metric_calculation_audit"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Calculation identification
    calculation_id = Column(String(100), unique=True, nullable=False, index=True)
    calculation_type = Column(String(50), nullable=False, default="unified_metrics")

    # Timing
    calculated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    period_hours = Column(Integer, nullable=False)
    calculation_duration_ms = Column(Integer, nullable=True)

    # Input tracking (for reproducibility)
    input_data_hash = Column(String(64), nullable=False)
    config_snapshot = Column(JSONB, nullable=False, default={})

    # Results
    metrics_snapshot = Column(JSONB, nullable=False)

    # Version tracking
    engine_version = Column(String(20), nullable=False)
    cim_version = Column(String(20), nullable=False)

    # Audit metadata
    triggered_by = Column(String(100), nullable=False, default="system")
    trigger_source = Column(String(50), nullable=False, default="api")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Validation results
    validation_passed = Column(Boolean, nullable=False, default=True)
    validation_warnings = Column(JSONB, default=[])

    # Relationships
    organization = relationship("Organization", back_populates="metric_audits")
    user = relationship("User", back_populates="metric_audits")

    def __repr__(self):
        return f"<MetricCalculationAudit(id={self.id}, org={self.organization_id}, type={self.calculation_type})>"


class OrgMetricConfig(Base):
    """
    SEC-066: Organization-specific metric configuration.

    Allows enterprises to customize calculations per their risk model.
    For example, different industries have different cost-per-incident values.
    """
    __tablename__ = "org_metric_configs"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Multi-tenant isolation (unique per org)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Financial configuration
    cost_per_incident_usd = Column(Float, nullable=False, default=50000.0)
    hourly_analyst_rate_usd = Column(Float, nullable=False, default=75.0)

    # Time configuration
    default_analysis_period_hours = Column(Integer, nullable=False, default=24)
    sla_critical_minutes = Column(Integer, nullable=False, default=15)
    sla_high_minutes = Column(Integer, nullable=False, default=30)
    sla_medium_minutes = Column(Integer, nullable=False, default=60)
    sla_low_minutes = Column(Integer, nullable=False, default=120)

    # Feature flags
    include_dismissed_in_accuracy = Column(Boolean, nullable=False, default=False)

    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_by = Column(String(255), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="metric_config")

    def __repr__(self):
        return f"<OrgMetricConfig(org={self.organization_id}, cost_per_incident=${self.cost_per_incident_usd:,.0f})>"

    def to_config_object(self):
        """Convert to OrgMetricConfig dataclass for use with UnifiedMetricsEngine"""
        from services.metric_definitions import OrgMetricConfig as ConfigDataclass

        return ConfigDataclass(
            organization_id=self.organization_id,
            cost_per_incident_usd=self.cost_per_incident_usd,
            hourly_analyst_rate_usd=self.hourly_analyst_rate_usd,
            default_analysis_period_hours=self.default_analysis_period_hours,
            sla_critical_minutes=self.sla_critical_minutes,
            sla_high_minutes=self.sla_high_minutes,
            sla_medium_minutes=self.sla_medium_minutes,
            sla_low_minutes=self.sla_low_minutes,
            include_dismissed_in_accuracy=self.include_dismissed_in_accuracy
        )
