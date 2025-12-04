"""
SEC-065: Enterprise Executive Brief Model

Enterprise-grade executive briefing storage with full audit trail.

Following enterprise patterns:
- Datadog: Cached metrics with TTL
- Splunk: Scheduled report storage
- PagerDuty: Executive summary persistence
- Wiz.io: Security posture snapshots

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

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey,
    Index, Boolean, Float
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta

from database import Base


class ExecutiveBrief(Base):
    """
    Enterprise Executive Brief Storage

    Banking-Level Security:
    - Multi-tenant isolation via organization_id
    - Full audit trail for compliance
    - Immutable historical records
    - Snapshot of data at generation time

    Performance:
    - Composite indexes for fast retrieval
    - Cached brief lookup < 100ms
    - TTL-based expiration
    """
    __tablename__ = "executive_briefs"

    # ==========================================================================
    # PRIMARY KEY
    # ==========================================================================
    id = Column(Integer, primary_key=True, index=True)

    # ==========================================================================
    # MULTI-TENANT ISOLATION (Banking-Level Security)
    # Compliance: SOC 2 CC6.1, NIST AC-3, PCI-DSS 7.1
    # ==========================================================================
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    # ==========================================================================
    # BRIEF IDENTIFICATION
    # ==========================================================================
    brief_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique identifier: exec-brief-{timestamp}"
    )

    # ==========================================================================
    # TIME CONFIGURATION
    # ==========================================================================
    time_period = Column(
        String(20),
        default="24h",
        nullable=False,
        comment="Analysis period: 24h, 7d, 30d"
    )

    generated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Brief validity expiration (typically 1 hour after generation)"
    )

    generated_by = Column(
        String(255),
        nullable=False,
        comment="User email or 'system' for scheduled generation"
    )

    # ==========================================================================
    # BRIEF CONTENT
    # Compliance: SOC 2 AU-7 - Audit reduction and report generation
    # ==========================================================================
    summary = Column(
        Text,
        nullable=False,
        comment="AI-generated or fallback executive summary"
    )

    key_metrics = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Structured metrics: threats_detected, prevented, cost_savings, accuracy"
    )

    recommendations = Column(
        JSONB,
        default=list,
        comment="Prioritized action recommendations"
    )

    risk_assessment = Column(
        String(20),
        nullable=False,
        default="NO_DATA",
        index=True,
        comment="Overall risk: NO_DATA, LOW, MEDIUM, HIGH, CRITICAL"
    )

    # ==========================================================================
    # ALERT SNAPSHOT (Audit Trail)
    # Compliance: SOC 2 AU-6 - Audit record review
    # ==========================================================================
    alert_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    high_priority_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    critical_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    alert_snapshot = Column(
        JSONB,
        nullable=True,
        comment="Frozen alert IDs and summary at generation time for audit"
    )

    # ==========================================================================
    # GENERATION METADATA
    # For cost tracking and performance monitoring
    # ==========================================================================
    generation_method = Column(
        String(50),
        default="llm",
        nullable=False,
        comment="Generation method: llm, fallback, scheduled"
    )

    generation_time_ms = Column(
        Integer,
        nullable=True,
        comment="Time taken to generate brief in milliseconds"
    )

    llm_model = Column(
        String(100),
        nullable=True,
        comment="LLM model used: gpt-4, gpt-3.5-turbo, claude-3, etc."
    )

    llm_tokens_used = Column(
        Integer,
        nullable=True,
        comment="Total tokens consumed for cost tracking"
    )

    llm_cost_usd = Column(
        Float,
        nullable=True,
        comment="Estimated cost in USD for this generation"
    )

    # ==========================================================================
    # VERSION CONTROL (Audit Trail)
    # Compliance: SOX - Immutable audit logs
    # ==========================================================================
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Brief version within same time period"
    )

    superseded_by_id = Column(
        Integer,
        ForeignKey("executive_briefs.id"),
        nullable=True,
        comment="Points to newer brief that replaced this one"
    )

    is_current = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="True if this is the current valid brief for the org"
    )

    # ==========================================================================
    # DISTRIBUTION TRACKING
    # ==========================================================================
    distribution_list = Column(
        JSONB,
        default=list,
        comment="List of roles/users who should receive this brief"
    )

    viewed_by = Column(
        JSONB,
        default=list,
        comment="Audit trail of users who viewed this brief"
    )

    # ==========================================================================
    # COMPOSITE INDEXES FOR PERFORMANCE
    # Optimized for common query patterns
    # ==========================================================================
    __table_args__ = (
        # Fast lookup: Get current brief for org
        Index(
            'ix_exec_brief_org_current',
            'organization_id',
            'is_current',
            postgresql_where=(is_current == True)
        ),
        # Fast lookup: Get briefs by org and time
        Index(
            'ix_exec_brief_org_generated',
            'organization_id',
            'generated_at'
        ),
        # Cleanup: Find expired briefs
        Index(
            'ix_exec_brief_expires',
            'expires_at'
        ),
        # Audit: Find briefs by risk level
        Index(
            'ix_exec_brief_org_risk',
            'organization_id',
            'risk_assessment'
        ),
    )

    # ==========================================================================
    # RELATIONSHIPS
    # ==========================================================================
    organization = relationship("Organization", backref="executive_briefs")
    superseded_by = relationship(
        "ExecutiveBrief",
        remote_side=[id],
        backref="supersedes"
    )

    def __repr__(self):
        return (
            f"<ExecutiveBrief(id={self.id}, org={self.organization_id}, "
            f"risk={self.risk_assessment}, alerts={self.alert_count})>"
        )

    def is_expired(self) -> bool:
        """Check if brief has expired"""
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        """Check if brief is current and not expired"""
        return self.is_current and not self.is_expired()

    def to_api_response(self) -> dict:
        """Convert to API response format"""
        return {
            "brief_id": self.brief_id,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "generated_by": self.generated_by,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "time_period": self.time_period,
            "alert_count": self.alert_count,
            "high_priority_count": self.high_priority_count,
            "critical_count": self.critical_count,
            "summary": self.summary,
            "key_metrics": self.key_metrics or {},
            "recommendations": self.recommendations or [],
            "risk_assessment": self.risk_assessment,
            "distribution_list": self.distribution_list or [],
            "generation_method": self.generation_method,
            "is_expired": self.is_expired(),
            "is_current": self.is_current,
            "version": self.version,
            "meta": {
                "organization_id": self.organization_id,
                "has_activity": self.alert_count > 0,
                "llm_model": self.llm_model,
                "generation_time_ms": self.generation_time_ms
            }
        }
