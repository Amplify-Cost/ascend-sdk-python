"""
ASCEND Prompt Security Models - Phase 10
=========================================

Enterprise-grade prompt injection detection and LLM-to-LLM governance.
Follows Phase 9 Code Analysis patterns exactly:

1. GlobalPromptPattern - Vendor-managed patterns (ASCEND maintains)
2. OrgPromptSecurityConfig - Per-org settings and thresholds (NO HARDCODED VALUES)
3. OrgPromptPatternOverride - Customer can disable/modify with approval trail
4. OrgCustomPromptPattern - Customer can add their own patterns
5. PromptSecurityAuditLog - Immutable audit trail for all changes
6. LLMChainAuditLog - LLM-to-LLM communication tracking

Key Design Principles:
- NO hardcoded values in application code
- All thresholds from OrgPromptSecurityConfig
- All severity scores from OrgPromptSecurityConfig.severity_scores
- Patterns from database, not YAML files
- OWASP LLM Top 10 compliance mappings

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10, OWASP LLM Top 10

Author: OW-kai Enterprise Security Team
Version: 1.0.0
Created: 2025-12-18
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric,
    ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base
import uuid


# ============================================================================
# TABLE 1: GlobalPromptPattern
# ============================================================================
# Vendor-managed prompt security patterns maintained by ASCEND


class GlobalPromptPattern(Base):
    """
    Global prompt security patterns maintained by ASCEND (vendor).

    These are the "out of box" patterns shipped with the product for detecting:
    - Prompt injection attacks
    - Jailbreak attempts
    - Role manipulation
    - Encoding-based evasion
    - Data exfiltration attempts
    - LLM chain attacks

    Similar to:
    - CrowdStrike detection rules
    - Palo Alto threat signatures
    - OWASP LLM Top 10 patterns
    """
    __tablename__ = "global_prompt_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(50), unique=True, nullable=False, index=True)

    # Pattern classification
    category = Column(String(50), nullable=False, index=True)
    # Categories: prompt_injection, jailbreak, role_manipulation, encoding_attack,
    #             delimiter_attack, data_exfiltration, chain_attack

    attack_vector = Column(String(50), nullable=False)
    # Attack vectors: direct, indirect, chain, encoded

    severity = Column(String(20), nullable=False, index=True)
    # Severities: critical, high, medium, low, info

    # Pattern definition
    pattern_type = Column(String(20), nullable=False, default='regex')
    # Types: regex, semantic, llm_classifier

    pattern_value = Column(Text, nullable=False)  # The actual regex/pattern
    pattern_flags = Column(String(50), nullable=True)  # IGNORECASE, MULTILINE, DOTALL

    # Scope: where to apply this pattern
    applies_to = Column(ARRAY(String(50)), default=[])
    # Values: system_prompt, user_prompt, agent_response, all

    # Documentation
    description = Column(Text, nullable=False)
    example_attack = Column(Text, nullable=True)  # Example of what this pattern detects
    recommendation = Column(Text, nullable=True)

    # Compliance mappings
    cwe_ids = Column(ARRAY(String(20)), default=[])  # CWE-77, CWE-94, etc.
    mitre_techniques = Column(ARRAY(String(20)), default=[])  # T1059, T1190, etc.
    nist_controls = Column(ARRAY(String(20)), default=[])  # SI-10, SC-7, etc.
    owasp_llm_top10 = Column(ARRAY(String(20)), default=[])  # LLM01, LLM02, etc.

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
            "category": self.category,
            "attack_vector": self.attack_vector,
            "severity": self.severity,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "pattern_flags": self.pattern_flags,
            "applies_to": self.applies_to or [],
            "description": self.description,
            "example_attack": self.example_attack,
            "recommendation": self.recommendation,
            "cwe_ids": self.cwe_ids or [],
            "mitre_techniques": self.mitre_techniques or [],
            "nist_controls": self.nist_controls or [],
            "owasp_llm_top10": self.owasp_llm_top10 or [],
            "cvss_base_score": float(self.cvss_base_score) if self.cvss_base_score else None,
            "cvss_vector": self.cvss_vector,
            "is_active": self.is_active,
            "version": self.version,
        }


# ============================================================================
# TABLE 2: OrgPromptSecurityConfig
# ============================================================================
# Per-organization configuration - NO HARDCODED VALUES IN CODE


class OrgPromptSecurityConfig(Base):
    """
    Per-organization prompt security configuration.

    ALL thresholds and settings come from this table, NOT hardcoded in code.

    Default values are only set in database migrations, not in application code.
    Application code reads from this table for all configuration.
    """
    __tablename__ = "org_prompt_security_config"

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
    mode = Column(String(20), default='monitor', nullable=False)  # enforce, monitor, off

    # Per-org severity scores (NOT HARDCODED IN CODE)
    severity_scores = Column(
        JSONB,
        default={"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}
    )

    # Per-org thresholds (NOT HARDCODED IN CODE)
    block_threshold = Column(Integer, default=90, nullable=False)  # Block if risk >= this
    escalate_threshold = Column(Integer, default=70, nullable=False)  # Escalate if risk >= this
    alert_threshold = Column(Integer, default=50, nullable=False)  # Alert if risk >= this

    # Scan settings - what to analyze
    scan_system_prompts = Column(Boolean, default=True, nullable=False)
    scan_user_prompts = Column(Boolean, default=True, nullable=False)
    scan_agent_responses = Column(Boolean, default=True, nullable=False)
    scan_llm_to_llm = Column(Boolean, default=True, nullable=False)

    # Encoding detection settings
    detect_base64 = Column(Boolean, default=True, nullable=False)
    detect_unicode_smuggling = Column(Boolean, default=True, nullable=False)
    detect_html_entities = Column(Boolean, default=True, nullable=False)
    max_decode_depth = Column(Integer, default=3, nullable=False)  # Max recursive decode levels

    # LLM-to-LLM governance (PROMPT-002)
    llm_chain_depth_limit = Column(Integer, default=5, nullable=False)
    require_chain_approval = Column(Boolean, default=False, nullable=False)

    # Filtering options (empty = all)
    enabled_categories = Column(ARRAY(String(50)), default=[])  # Empty = all categories
    disabled_pattern_ids = Column(ARRAY(String(50)), default=[])  # Explicitly disabled patterns

    # Notification settings
    notify_on_block = Column(Boolean, default=True)
    notify_on_critical = Column(Boolean, default=True)
    notification_emails = Column(ARRAY(String(255)), default=[])

    # ========================================================================
    # VAL-FIX-001: Multi-Signal Configuration
    # ========================================================================
    # These settings reduce false positives on business terminology while
    # maintaining security for actual injection attempts.
    # ========================================================================

    # Require 2+ pattern matches for HIGH risk (>=80)
    # When True, single pattern matches are capped at single_pattern_max_risk
    multi_signal_required = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='VAL-FIX-001: Require 2+ pattern matches for HIGH risk classification'
    )

    # Maximum risk score when only 1 pattern matches (if multi_signal_required=True)
    # Default 70 places single matches in MEDIUM tier, not HIGH
    single_pattern_max_risk = Column(
        Integer,
        default=70,
        nullable=False,
        comment='VAL-FIX-001: Max risk when only 1 pattern matches (default 70 = MEDIUM tier)'
    )

    # Enable pre-filter for common business terminology
    # Reduces false positives on reports, analytics, calculations, etc.
    business_context_filter = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='VAL-FIX-001: Enable business terminology pre-filter to reduce false positives'
    )

    # Critical patterns (PROMPT-001, 004, 008, 016, 018, 020) always use full risk
    # WARNING: Setting to False significantly reduces security
    critical_patterns_always_block = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='VAL-FIX-001: Critical injection patterns bypass multi-signal (SECURITY CRITICAL)'
    )

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationship
    organization = relationship("Organization", backref="prompt_security_config")

    def get_severity_score(self, severity: str) -> int:
        """Get risk score for a severity level from org config."""
        default_scores = {"critical": 95, "high": 75, "medium": 50, "low": 25, "info": 10}
        scores = self.severity_scores or default_scores
        return scores.get(severity, scores.get("medium", 50))

    def is_pattern_disabled(self, pattern_id: str) -> bool:
        """Check if a pattern is disabled for this org."""
        return pattern_id in (self.disabled_pattern_ids or [])

    def is_category_enabled(self, category: str) -> bool:
        """Check if a category is enabled (empty = all enabled)."""
        if not self.enabled_categories:
            return True
        return category in self.enabled_categories

    def should_scan(self, prompt_type: str) -> bool:
        """Check if a prompt type should be scanned based on config."""
        scan_map = {
            "system_prompt": self.scan_system_prompts,
            "user_prompt": self.scan_user_prompts,
            "agent_response": self.scan_agent_responses,
        }
        return scan_map.get(prompt_type, True)

    @property
    def multi_signal_config(self) -> dict:
        """
        VAL-FIX-001: Get multi-signal configuration as dictionary.

        Used by PromptSecurityService.analyze_prompt() for multi-signal scoring.
        """
        return {
            "multi_signal_required": self.multi_signal_required,
            "single_pattern_max_risk": self.single_pattern_max_risk,
            "business_context_filter": self.business_context_filter,
            "critical_patterns_always_block": self.critical_patterns_always_block,
        }

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
            "scan_system_prompts": self.scan_system_prompts,
            "scan_user_prompts": self.scan_user_prompts,
            "scan_agent_responses": self.scan_agent_responses,
            "scan_llm_to_llm": self.scan_llm_to_llm,
            "detect_base64": self.detect_base64,
            "detect_unicode_smuggling": self.detect_unicode_smuggling,
            "detect_html_entities": self.detect_html_entities,
            "max_decode_depth": self.max_decode_depth,
            "llm_chain_depth_limit": self.llm_chain_depth_limit,
            "require_chain_approval": self.require_chain_approval,
            "enabled_categories": self.enabled_categories or [],
            "disabled_pattern_ids": self.disabled_pattern_ids or [],
            "notify_on_block": self.notify_on_block,
            "notify_on_critical": self.notify_on_critical,
            # VAL-FIX-001: Multi-signal configuration
            "multi_signal_required": self.multi_signal_required,
            "single_pattern_max_risk": self.single_pattern_max_risk,
            "business_context_filter": self.business_context_filter,
            "critical_patterns_always_block": self.critical_patterns_always_block,
        }


# ============================================================================
# TABLE 3: OrgPromptPatternOverride
# ============================================================================
# Customer can disable/modify global patterns for their org


class OrgPromptPatternOverride(Base):
    """
    Per-organization overrides for global prompt patterns.

    Allows customers to:
    - Disable patterns that cause false positives in their environment
    - Adjust severity for their risk tolerance
    - Override risk scores

    All changes require justification and optional approval for SOC 2 compliance.
    """
    __tablename__ = "org_prompt_pattern_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pattern_id = Column(String(50), nullable=False, index=True)

    # Override options
    is_disabled = Column(Boolean, default=False, nullable=False)
    severity_override = Column(String(20), nullable=True)  # Override global severity
    risk_score_override = Column(Integer, nullable=True)  # Override calculated risk score

    # Approval trail (required for SOC 2)
    modified_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    modification_reason = Column(Text, nullable=False)  # Required justification
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('organization_id', 'pattern_id', name='uq_org_prompt_pattern_override'),
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
        }


# ============================================================================
# TABLE 4: OrgCustomPromptPattern
# ============================================================================
# Customer can add their own patterns for org-specific threats


class OrgCustomPromptPattern(Base):
    """
    Custom patterns created by customers for org-specific prompt threats.

    Allows customers to add detection for:
    - Company-specific jailbreak attempts
    - Industry-specific prompt patterns
    - Custom compliance requirements
    - Internal terms or phrases to monitor

    Pattern IDs are prefixed with "CUSTOM-PROMPT-" to distinguish from global patterns.
    """
    __tablename__ = "org_custom_prompt_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pattern_id = Column(String(50), nullable=False)

    # Pattern classification
    category = Column(String(50), nullable=False)
    attack_vector = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)

    # Pattern definition
    pattern_type = Column(String(20), default='regex', nullable=False)
    pattern_value = Column(Text, nullable=False)
    pattern_flags = Column(String(50), nullable=True)
    applies_to = Column(ARRAY(String(50)), default=[])

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
        UniqueConstraint('organization_id', 'pattern_id', name='uq_org_custom_prompt_pattern'),
    )

    # Relationship
    creator = relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "pattern_id": self.pattern_id,
            "category": self.category,
            "attack_vector": self.attack_vector,
            "severity": self.severity,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "pattern_flags": self.pattern_flags,
            "applies_to": self.applies_to or [],
            "description": self.description,
            "recommendation": self.recommendation,
            "cwe_ids": self.cwe_ids or [],
            "mitre_techniques": self.mitre_techniques or [],
            "cvss_base_score": float(self.cvss_base_score) if self.cvss_base_score else None,
            "is_active": self.is_active,
        }


# ============================================================================
# TABLE 5: PromptSecurityAuditLog
# ============================================================================
# Immutable audit trail for all prompt security changes and detections


class PromptSecurityAuditLog(Base):
    """
    Immutable audit trail for all prompt security changes and detections.

    Required for SOC 2 compliance. Records all:
    - Pattern creations/modifications
    - Config changes
    - Override changes
    - Detection events
    - Block events

    This table is append-only - no updates or deletes allowed.
    """
    __tablename__ = "prompt_security_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = Column(String(255), nullable=True)  # Denormalized for audit trail

    # What happened
    action = Column(String(50), nullable=False, index=True)
    # Actions: created, updated, deleted, disabled, enabled, detection, block, escalation

    resource_type = Column(String(50), nullable=False)
    # Types: global_pattern, org_config, org_override, org_custom, detection_event

    resource_id = Column(String(100), nullable=False)  # pattern_id or config id

    # Detection event fields (when action='detection' or 'block')
    agent_action_id = Column(Integer, nullable=True)  # Link to agent_actions table
    prompt_type = Column(String(50), nullable=True)  # system_prompt, user_prompt, agent_response
    detected_patterns = Column(ARRAY(String(50)), nullable=True)  # Patterns that matched
    risk_score = Column(Integer, nullable=True)
    blocked = Column(Boolean, nullable=True)

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

    # Indexes for common queries
    __table_args__ = (
        Index('ix_prompt_audit_org_action', 'organization_id', 'action'),
        Index('ix_prompt_audit_created', 'created_at'),
    )

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
        """Create an audit log entry for configuration changes."""
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

    @classmethod
    def log_detection(
        cls,
        db,
        organization_id: int,
        agent_action_id: int,
        prompt_type: str,
        detected_patterns: list,
        risk_score: int,
        blocked: bool,
        correlation_id: str = None
    ):
        """Create an audit log entry for a detection event."""
        action = "block" if blocked else "detection"
        entry = cls(
            organization_id=organization_id,
            action=action,
            resource_type="detection_event",
            resource_id=str(agent_action_id),
            agent_action_id=agent_action_id,
            prompt_type=prompt_type,
            detected_patterns=detected_patterns,
            risk_score=risk_score,
            blocked=blocked,
            correlation_id=correlation_id
        )
        db.add(entry)
        return entry

    def to_dict(self):
        """Convert to dictionary for API responses."""
        result = {
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
        # Include detection fields if present
        if self.agent_action_id:
            result.update({
                "agent_action_id": self.agent_action_id,
                "prompt_type": self.prompt_type,
                "detected_patterns": self.detected_patterns,
                "risk_score": self.risk_score,
                "blocked": self.blocked,
            })
        return result


# ============================================================================
# TABLE 6: LLMChainAuditLog
# ============================================================================
# LLM-to-LLM communication tracking (PROMPT-002)


class LLMChainAuditLog(Base):
    """
    Audit log for LLM-to-LLM (agent-to-agent) communication chains.

    Tracks when one AI agent passes prompts to another, detecting:
    - Chain depth violations
    - Injection propagation between agents
    - Policy bypass attempts through chaining

    Required for PROMPT-002: LLM-to-LLM Governance.
    """
    __tablename__ = "llm_chain_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Chain identification
    chain_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    parent_chain_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    depth = Column(Integer, default=1, nullable=False)

    # Source agent (who is sending)
    source_agent_id = Column(String(255), nullable=False, index=True)
    source_action_id = Column(Integer, nullable=True)  # Link to agent_actions

    # Target agent (who is receiving)
    target_agent_id = Column(String(255), nullable=False, index=True)
    target_action_id = Column(Integer, nullable=True)

    # Content hashes (for privacy - don't store actual prompts)
    prompt_content_hash = Column(String(64), nullable=False)  # SHA-256
    prompt_length = Column(Integer, nullable=True)
    response_content_hash = Column(String(64), nullable=True)
    response_length = Column(Integer, nullable=True)

    # Security analysis
    injection_detected = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    patterns_matched = Column(ARRAY(String(50)), default=[])

    # Governance decision
    status = Column(String(50), default='allowed', nullable=False)
    # Status: allowed, blocked, escalated, pending_approval
    block_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for chain traversal
    __table_args__ = (
        Index('ix_llm_chain_org_status', 'organization_id', 'status'),
        Index('ix_llm_chain_source', 'source_agent_id', 'created_at'),
        Index('ix_llm_chain_target', 'target_agent_id', 'created_at'),
    )

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "chain_id": str(self.chain_id),
            "parent_chain_id": str(self.parent_chain_id) if self.parent_chain_id else None,
            "depth": self.depth,
            "source_agent_id": self.source_agent_id,
            "source_action_id": self.source_action_id,
            "target_agent_id": self.target_agent_id,
            "target_action_id": self.target_action_id,
            "prompt_length": self.prompt_length,
            "response_length": self.response_length,
            "injection_detected": self.injection_detected,
            "risk_score": self.risk_score,
            "patterns_matched": self.patterns_matched or [],
            "status": self.status,
            "block_reason": self.block_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ============================================================================
# Helper Dataclass for Analysis Results
# ============================================================================


class PromptAnalysisResult:
    """
    Result of prompt security analysis.

    Not a database model - used for passing analysis results through the pipeline.
    """

    def __init__(
        self,
        analyzed: bool = False,
        findings: list = None,
        max_severity: str = None,
        max_risk_score: int = 0,
        blocked: bool = False,
        block_reason: str = None,
        encoding_detected: bool = False,
        decoded_layers: int = 0,
        config_mode: str = None,
        patterns_matched: list = None
    ):
        self.analyzed = analyzed
        self.findings = findings or []
        self.max_severity = max_severity
        self.max_risk_score = max_risk_score
        self.blocked = blocked
        self.block_reason = block_reason
        self.encoding_detected = encoding_detected
        self.decoded_layers = decoded_layers
        self.config_mode = config_mode
        self.patterns_matched = patterns_matched or []

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "analyzed": self.analyzed,
            "findings_count": len(self.findings),
            "max_severity": self.max_severity,
            "max_risk_score": self.max_risk_score,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "encoding_detected": self.encoding_detected,
            "decoded_layers": self.decoded_layers,
            "config_mode": self.config_mode,
            "patterns_matched": self.patterns_matched,
        }


class PromptFinding:
    """
    Individual finding from prompt analysis.

    Not a database model - used for passing finding details.
    """

    def __init__(
        self,
        pattern_id: str,
        category: str,
        severity: str,
        risk_score: int,
        description: str,
        match_text: str = None,
        match_position: tuple = None,
        cwe_ids: list = None,
        mitre_techniques: list = None,
        owasp_llm_top10: list = None
    ):
        self.pattern_id = pattern_id
        self.category = category
        self.severity = severity
        self.risk_score = risk_score
        self.description = description
        self.match_text = match_text
        self.match_position = match_position
        self.cwe_ids = cwe_ids or []
        self.mitre_techniques = mitre_techniques or []
        self.owasp_llm_top10 = owasp_llm_top10 or []

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "pattern_id": self.pattern_id,
            "category": self.category,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "description": self.description,
            "match_text": self.match_text[:100] if self.match_text else None,  # Truncate for safety
            "cwe_ids": self.cwe_ids,
            "mitre_techniques": self.mitre_techniques,
            "owasp_llm_top10": self.owasp_llm_top10,
        }
