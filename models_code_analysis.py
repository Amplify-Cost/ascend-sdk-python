"""
ASCEND Code Analysis Models - Phase 9 Option C
===============================================

Enterprise-grade code pattern detection following CrowdStrike/Palo Alto pattern:
1. GlobalCodePattern - Vendor-managed patterns (ASCEND maintains)
2. OrgCodeAnalysisConfig - Per-org settings and thresholds (NO HARDCODED VALUES)
3. OrgPatternOverride - Customer can disable/modify with approval trail
4. OrgCustomPattern - Customer can add their own patterns
5. CodePatternAuditLog - Immutable audit trail for all changes

Key Design Principles:
- NO hardcoded values in application code
- All thresholds from OrgCodeAnalysisConfig
- All severity scores from OrgCodeAnalysisConfig.severity_scores
- Patterns from database, not YAML files
- Respects RegisteredAgent.max_risk_threshold per-agent

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10

Author: OW-kai Enterprise Security Team
Version: 1.0.0
Created: 2025-12-17
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base


# ============================================================================
# TABLE 1: GlobalCodePattern
# ============================================================================
# Vendor-managed patterns maintained by ASCEND (like CrowdStrike signatures)
# No organization_id - these are global to all tenants


class GlobalCodePattern(Base):
    """
    Global code patterns maintained by ASCEND (vendor).

    These are the "out of box" patterns shipped with the product.
    Customers can override or disable them per-org, but cannot modify directly.

    Similar to:
    - CrowdStrike detection rules
    - Palo Alto threat signatures
    - Snort/Suricata rules
    """
    __tablename__ = "global_code_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(50), unique=True, nullable=False, index=True)

    # Pattern classification
    language = Column(String(20), nullable=False, index=True)  # sql, python, shell, javascript, any
    category = Column(String(50), nullable=False, index=True)  # data_destruction, injection, rce, etc.
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low, info

    # Pattern definition
    pattern_type = Column(String(20), nullable=False, default='regex')  # regex, ast, semantic
    pattern_value = Column(Text, nullable=False)  # The actual regex/pattern
    pattern_flags = Column(String(50), nullable=True)  # IGNORECASE, MULTILINE, etc.

    # Documentation
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)

    # Compliance mappings
    cwe_ids = Column(ARRAY(String(20)), default=[])  # CWE-89, CWE-78, etc.
    mitre_techniques = Column(ARRAY(String(20)), default=[])  # T1485, T1059.004, etc.

    # CVSS scoring
    cvss_base_score = Column(Numeric(3, 1), nullable=True)  # 0.0 - 10.0
    cvss_vector = Column(String(100), nullable=True)  # CVSS:3.1/AV:N/AC:L/...

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "pattern_id": self.pattern_id,
            "language": self.language,
            "category": self.category,
            "severity": self.severity,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "pattern_flags": self.pattern_flags,
            "description": self.description,
            "recommendation": self.recommendation,
            "cwe_ids": self.cwe_ids or [],
            "mitre_techniques": self.mitre_techniques or [],
            "cvss_base_score": float(self.cvss_base_score) if self.cvss_base_score else None,
            "cvss_vector": self.cvss_vector,
            "is_active": self.is_active,
            "version": self.version,
        }


# ============================================================================
# TABLE 2: OrgCodeAnalysisConfig
# ============================================================================
# Per-organization configuration - NO HARDCODED VALUES IN CODE


class OrgCodeAnalysisConfig(Base):
    """
    Per-organization code analysis configuration.

    ALL thresholds and settings come from this table, NOT hardcoded in code.

    Default values are only set in database migrations, not in application code.
    Application code reads from this table for all configuration.
    """
    __tablename__ = "org_code_analysis_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )

    # Feature toggles
    enabled = Column(Boolean, default=True, nullable=False)
    mode = Column(String(20), default='enforce', nullable=False)  # enforce, monitor, off

    # Per-org severity scores (NOT HARDCODED IN CODE)
    # These override the default risk score calculation
    severity_scores = Column(
        JSONB,
        default={"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}
    )

    # Per-org thresholds (NOT HARDCODED IN CODE)
    block_threshold = Column(Integer, default=90, nullable=False)  # Block if risk >= this
    escalate_threshold = Column(Integer, default=70, nullable=False)  # Escalate if risk >= this
    alert_threshold = Column(Integer, default=50, nullable=False)  # Alert if risk >= this

    # CVSS threshold for auto-block
    cvss_block_threshold = Column(Numeric(3, 1), default=9.0)

    # Filtering options (empty = all)
    enabled_languages = Column(ARRAY(String(20)), default=[])  # Empty = all languages
    enabled_categories = Column(ARRAY(String(50)), default=[])  # Empty = all categories

    # Globally disabled patterns for this org
    disabled_pattern_ids = Column(ARRAY(String(50)), default=[])

    # Notification settings
    notify_on_block = Column(Boolean, default=True)
    notify_on_critical = Column(Boolean, default=True)
    notification_emails = Column(ARRAY(String(255)), default=[])

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationship
    organization = relationship("Organization", backref="code_analysis_config")

    def get_severity_score(self, severity: str) -> int:
        """Get risk score for a severity level from org config."""
        default_scores = {"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}
        scores = self.severity_scores or default_scores
        return scores.get(severity, scores.get("medium", 50))

    def is_pattern_disabled(self, pattern_id: str) -> bool:
        """Check if a pattern is disabled for this org."""
        return pattern_id in (self.disabled_pattern_ids or [])

    def is_language_enabled(self, language: str) -> bool:
        """Check if a language is enabled (empty = all enabled)."""
        if not self.enabled_languages:
            return True
        return language in self.enabled_languages or language == "any"

    def is_category_enabled(self, category: str) -> bool:
        """Check if a category is enabled (empty = all enabled)."""
        if not self.enabled_categories:
            return True
        return category in self.enabled_categories

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "enabled": self.enabled,
            "mode": self.mode,
            "severity_scores": self.severity_scores,
            "block_threshold": self.block_threshold,
            "escalate_threshold": self.escalate_threshold,
            "alert_threshold": self.alert_threshold,
            "cvss_block_threshold": float(self.cvss_block_threshold) if self.cvss_block_threshold else None,
            "enabled_languages": self.enabled_languages or [],
            "enabled_categories": self.enabled_categories or [],
            "disabled_pattern_ids": self.disabled_pattern_ids or [],
            "notify_on_block": self.notify_on_block,
            "notify_on_critical": self.notify_on_critical,
        }


# ============================================================================
# TABLE 3: OrgPatternOverride
# ============================================================================
# Customer can disable/modify global patterns for their org


class OrgPatternOverride(Base):
    """
    Per-organization overrides for global patterns.

    Allows customers to:
    - Disable patterns that cause false positives in their environment
    - Adjust severity for their risk tolerance
    - Override risk scores

    All changes require justification and optional approval for SOC 2 compliance.
    """
    __tablename__ = "org_pattern_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pattern_id = Column(String(50), nullable=False, index=True)  # References global_code_patterns.pattern_id

    # Override options
    is_disabled = Column(Boolean, default=False, nullable=False)
    severity_override = Column(String(20), nullable=True)  # Override global severity
    risk_score_override = Column(Integer, nullable=True)  # Override calculated risk score

    # Approval trail (required for SOC 2)
    modified_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    modification_reason = Column(Text, nullable=False)  # Required justification
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_required = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('organization_id', 'pattern_id', name='uq_org_pattern_override'),
    )

    # Relationships
    modifier = relationship("User", foreign_keys=[modified_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "pattern_id": self.pattern_id,
            "is_disabled": self.is_disabled,
            "severity_override": self.severity_override,
            "risk_score_override": self.risk_score_override,
            "modification_reason": self.modification_reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approval_required": self.approval_required,
        }


# ============================================================================
# TABLE 4: OrgCustomPattern
# ============================================================================
# Customer can add their own patterns for org-specific risks


class OrgCustomPattern(Base):
    """
    Custom patterns created by customers for org-specific risks.

    Allows customers to add detection for:
    - Internal APIs that shouldn't be called
    - Org-specific sensitive data patterns
    - Custom compliance requirements

    Pattern IDs are prefixed with "CUSTOM-" to distinguish from global patterns.
    """
    __tablename__ = "org_custom_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pattern_id = Column(String(50), nullable=False)  # Customer-defined ID, prefixed with CUSTOM-

    # Pattern classification
    language = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)

    # Pattern definition
    pattern_type = Column(String(20), default='regex', nullable=False)
    pattern_value = Column(Text, nullable=False)
    pattern_flags = Column(String(50), nullable=True)

    # Documentation
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)

    # Compliance mappings (optional for custom)
    cwe_ids = Column(ARRAY(String(20)), default=[])
    mitre_techniques = Column(ARRAY(String(20)), default=[])
    cvss_base_score = Column(Numeric(3, 1), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Creator info
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('organization_id', 'pattern_id', name='uq_org_custom_pattern'),
    )

    # Relationship
    creator = relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "pattern_id": self.pattern_id,
            "language": self.language,
            "category": self.category,
            "severity": self.severity,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "pattern_flags": self.pattern_flags,
            "description": self.description,
            "recommendation": self.recommendation,
            "cwe_ids": self.cwe_ids or [],
            "mitre_techniques": self.mitre_techniques or [],
            "cvss_base_score": float(self.cvss_base_score) if self.cvss_base_score else None,
            "is_active": self.is_active,
        }


# ============================================================================
# TABLE 5: CodePatternAuditLog
# ============================================================================
# Immutable audit trail for all pattern changes


class CodePatternAuditLog(Base):
    """
    Immutable audit trail for all code pattern changes.

    Required for SOC 2 compliance. Records all:
    - Pattern creations
    - Pattern modifications
    - Pattern disabling/enabling
    - Config changes
    - Override changes

    This table is append-only - no updates or deletes allowed.
    """
    __tablename__ = "code_pattern_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = Column(String(255), nullable=True)  # Denormalized for audit trail

    # What changed
    action = Column(String(50), nullable=False, index=True)  # created, updated, deleted, disabled, enabled
    resource_type = Column(String(50), nullable=False)  # global_pattern, org_config, org_override, org_custom
    resource_id = Column(String(100), nullable=False)  # pattern_id or config id

    # Change details
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    change_reason = Column(Text, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    correlation_id = Column(String(100), nullable=True)

    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @classmethod
    def log_change(
        cls,
        db,
        organization_id: int,
        user_id: int,
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: dict = None,
        new_value: dict = None,
        change_reason: str = None,
        ip_address: str = None,
        user_agent: str = None,
        correlation_id: str = None
    ):
        """Create an audit log entry."""
        entry = cls(
            organization_id=organization_id,
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id
        )
        db.add(entry)
        return entry

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_reason": self.change_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
