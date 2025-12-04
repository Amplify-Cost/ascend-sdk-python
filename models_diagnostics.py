"""
SEC-076: Enterprise Diagnostics Models
=======================================

Industry-aligned diagnostic audit logging for enterprise health monitoring.
Patterns from: Wiz.io, Splunk, Datadog

Compliance: SOC 2 CC7.2, PCI-DSS 10.2, HIPAA 164.312, NIST AU-6
Author: Ascend Engineer
Date: 2025-12-04
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from database import Base


class DiagnosticAuditLog(Base):
    """
    Enterprise Diagnostic Audit Log
    ================================

    Immutable audit trail for all system diagnostic operations.
    Aligned with Splunk CIM and Datadog monitoring patterns.

    Features:
    - Correlation ID for distributed tracing
    - SIEM-compatible export formats
    - Remediation suggestions with severity
    - Component-level health scoring
    - Multi-tenant isolation

    Compliance:
    - SOC 2 CC7.2: Security Monitoring
    - PCI-DSS 10.2: Audit Trail Requirements
    - HIPAA 164.312: Audit Controls
    - NIST AU-6: Audit Review, Analysis, Reporting
    """
    __tablename__ = "diagnostic_audit_logs"

    # Composite index for efficient organization + time queries
    __table_args__ = (
        Index('ix_diagnostic_audit_org_created', 'organization_id', 'created_at'),
        Index('ix_diagnostic_audit_correlation', 'correlation_id'),
        Index('ix_diagnostic_audit_severity', 'severity', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # SEC-076: Distributed tracing correlation
    # Format: diag_{org_id}_{timestamp}_{uuid4_short}
    correlation_id = Column(String(64), nullable=False, unique=True, index=True)

    # SEC-076: Multi-tenant isolation (required, not nullable)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Diagnostic classification
    diagnostic_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="api_health | database_status | integration_test | full_diagnostic | security_scan"
    )

    # Execution status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="success | warning | failure | critical | timeout"
    )

    # Health scoring (0-100, enterprise standard)
    health_score = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Composite health score 0-100"
    )

    # Severity classification (Splunk-compatible)
    severity = Column(
        String(20),
        nullable=False,
        default="INFO",
        index=True,
        comment="INFO | WARNING | ERROR | CRITICAL | EMERGENCY"
    )

    # Detailed results (JSONB for flexible schema)
    results = Column(
        JSONB,
        nullable=False,
        default={},
        comment="Full diagnostic results with component breakdown"
    )

    # Component-level health details
    component_details = Column(
        JSONB,
        nullable=True,
        comment="Individual component statuses: {api: {score: 98, status: 'healthy'}, ...}"
    )

    # AI-generated remediation suggestions
    remediation_suggestions = Column(
        JSONB,
        nullable=True,
        comment="Actionable remediation steps: [{priority: 1, action: '...', impact: '...'}, ...]"
    )

    # Execution metadata
    initiated_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    duration_ms = Column(
        Integer,
        nullable=True,
        comment="Execution duration in milliseconds"
    )

    # SIEM integration (Splunk, Datadog, Wiz)
    siem_export_format = Column(
        String(30),
        nullable=True,
        comment="splunk_cim | datadog_metrics | wiz_json | generic_syslog"
    )

    siem_exported_at = Column(DateTime, nullable=True)

    # Request context for debugging
    request_context = Column(
        JSONB,
        nullable=True,
        comment="Source IP, user agent, request ID for tracing"
    )

    # Timestamps (immutable audit trail)
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", backref="diagnostic_logs")
    initiator = relationship("User", foreign_keys=[initiated_by])

    @classmethod
    def generate_correlation_id(cls, org_id: int) -> str:
        """
        Generate Splunk-compatible correlation ID.

        Format: diag_{org_id}_{YYYYMMDD}_{HHMMSS}_{uuid4_short}
        Example: diag_4_20251204_143052_a1b2c3d4
        """
        now = datetime.now(UTC)
        short_uuid = str(uuid.uuid4())[:8]
        return f"diag_{org_id}_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}_{short_uuid}"

    def to_splunk_cim(self) -> dict:
        """
        Export to Splunk Common Information Model format.

        Returns:
            dict: Splunk-compatible event data
        """
        return {
            "event_id": self.correlation_id,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "source": "owkai_diagnostics",
            "sourcetype": f"owkai:diagnostic:{self.diagnostic_type}",
            "severity": self.severity.lower(),
            "status": self.status,
            "health_score": self.health_score,
            "organization_id": self.organization_id,
            "duration_ms": self.duration_ms,
            "component_count": len(self.component_details or {}),
            "remediation_count": len(self.remediation_suggestions or []),
            "details": self.results
        }

    def to_datadog_metrics(self) -> list:
        """
        Export to Datadog metrics format.

        Returns:
            list: Datadog metric points
        """
        timestamp = int(self.created_at.timestamp()) if self.created_at else None
        tags = [
            f"org_id:{self.organization_id}",
            f"diagnostic_type:{self.diagnostic_type}",
            f"status:{self.status}",
            f"severity:{self.severity.lower()}"
        ]

        return [
            {
                "metric": "owkai.diagnostics.health_score",
                "type": "gauge",
                "points": [[timestamp, self.health_score]],
                "tags": tags
            },
            {
                "metric": "owkai.diagnostics.duration_ms",
                "type": "gauge",
                "points": [[timestamp, self.duration_ms or 0]],
                "tags": tags
            },
            {
                "metric": "owkai.diagnostics.execution",
                "type": "count",
                "points": [[timestamp, 1]],
                "tags": tags
            }
        ]

    def __repr__(self):
        return (
            f"<DiagnosticAuditLog(id={self.id}, correlation_id='{self.correlation_id}', "
            f"type='{self.diagnostic_type}', status='{self.status}', score={self.health_score})>"
        )


class DiagnosticThreshold(Base):
    """
    Organization-specific diagnostic thresholds.

    Allows each organization to customize alert thresholds
    based on their risk tolerance and SLA requirements.

    Compliance: SOC 2 CC7.1, PCI-DSS 10.6
    """
    __tablename__ = "diagnostic_thresholds"

    id = Column(Integer, primary_key=True, index=True)

    # SEC-076: Multi-tenant isolation
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # API health thresholds
    api_response_time_warning_ms = Column(Integer, default=500)
    api_response_time_critical_ms = Column(Integer, default=2000)
    api_error_rate_warning_pct = Column(Float, default=1.0)
    api_error_rate_critical_pct = Column(Float, default=5.0)

    # Database health thresholds
    db_query_time_warning_ms = Column(Integer, default=100)
    db_query_time_critical_ms = Column(Integer, default=500)
    db_connection_pool_warning_pct = Column(Float, default=70.0)
    db_connection_pool_critical_pct = Column(Float, default=90.0)

    # Overall health score thresholds
    health_score_warning = Column(Float, default=80.0)
    health_score_critical = Column(Float, default=60.0)

    # Alerting configuration
    auto_alert_on_critical = Column(Boolean, default=True)
    alert_cooldown_minutes = Column(Integer, default=15)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization = relationship("Organization", backref="diagnostic_thresholds")

    def __repr__(self):
        return f"<DiagnosticThreshold(org_id={self.organization_id})>"
