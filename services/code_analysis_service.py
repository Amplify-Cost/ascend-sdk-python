"""
ASCEND Code Analysis Service - Phase 9 Option C (Database-Driven)
=================================================================

Enterprise-grade code pattern detection following CrowdStrike/Palo Alto pattern.

KEY PRINCIPLE: NO HARDCODED VALUES
===================================
All configuration comes from database tables:
- Patterns from: global_code_patterns + org_custom_patterns (with overrides)
- Thresholds from: org_code_analysis_config
- Severity scores from: org_code_analysis_config.severity_scores
- Agent thresholds from: RegisteredAgent.max_risk_threshold

Tables Used:
- GlobalCodePattern: Vendor-managed patterns
- OrgCodeAnalysisConfig: Per-org configuration
- OrgPatternOverride: Customer overrides
- OrgCustomPattern: Customer patterns
- CodePatternAuditLog: Audit trail

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10

Author: OW-kai Enterprise Security Team
Version: 2.0.0 (Database-driven)
Created: 2025-12-17
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models_code_analysis import (
    GlobalCodePattern,
    OrgCodeAnalysisConfig,
    OrgPatternOverride,
    OrgCustomPattern,
    CodePatternAuditLog
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES (No hardcoded values - just structure)
# ============================================================================


@dataclass
class EffectivePattern:
    """
    A pattern with all overrides applied.

    Combines GlobalCodePattern with OrgPatternOverride and OrgCustomPattern
    to produce the effective pattern for this org.
    """
    pattern_id: str
    language: str
    category: str
    severity: str  # May be overridden
    pattern_type: str
    pattern_value: str
    pattern_flags: Optional[str] = None
    compiled_pattern: Optional[re.Pattern] = None
    description: str = ""
    recommendation: Optional[str] = None
    cwe_ids: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    cvss_base_score: Optional[float] = None
    risk_score_override: Optional[int] = None  # Org override
    is_custom: bool = False  # True if from org_custom_patterns


@dataclass
class CodeFinding:
    """Individual code analysis finding."""
    pattern_id: str
    severity: str
    category: str
    description: str
    matched_text: str
    line_number: Optional[int] = None
    cwe_ids: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    cvss_base_score: Optional[float] = None
    risk_score: Optional[int] = None
    recommendation: Optional[str] = None
    language: Optional[str] = None
    is_custom_pattern: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern_id": self.pattern_id,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "matched_text": self.matched_text[:200] if self.matched_text else "",
            "line_number": self.line_number,
            "cwe_ids": self.cwe_ids,
            "mitre_techniques": self.mitre_techniques,
            "cvss_base_score": self.cvss_base_score,
            "risk_score": self.risk_score,
            "recommendation": self.recommendation,
            "language": self.language,
            "is_custom_pattern": self.is_custom_pattern,
        }


@dataclass
class CodeAnalysisResult:
    """Result of code analysis."""
    findings: List[CodeFinding] = field(default_factory=list)
    language: Optional[str] = None
    risk_adjustment: int = 0
    max_risk_score: int = 0
    max_severity: str = "info"
    patterns_matched: List[str] = field(default_factory=list)
    scan_duration_ms: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None
    code_analyzed: bool = False
    config_mode: str = "enforce"  # enforce, monitor, off

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage in extra_data."""
        return {
            "analyzed": self.code_analyzed,
            "language": self.language,
            "findings": [f.to_dict() for f in self.findings],
            "risk_adjustment": self.risk_adjustment,
            "max_risk_score": self.max_risk_score,
            "max_severity": self.max_severity,
            "patterns_matched": self.patterns_matched,
            "scan_duration_ms": self.scan_duration_ms,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "findings_count": len(self.findings),
            "config_mode": self.config_mode,
        }


# ============================================================================
# CODE ANALYSIS SERVICE (Database-Driven)
# ============================================================================


class CodeAnalysisService:
    """
    Analyzes code for dangerous patterns using database-driven configuration.

    NO HARDCODED VALUES - all configuration from database:
    - Patterns: global_code_patterns + org_custom_patterns
    - Thresholds: org_code_analysis_config
    - Severity scores: org_code_analysis_config.severity_scores
    - Agent limits: RegisteredAgent.max_risk_threshold

    Usage:
        service = CodeAnalysisService(db, org_id=1)
        result = service.analyze_for_action(
            action_type="execute_sql",
            parameters={"query": "DROP TABLE users;"},
            agent_id="agent-123"  # Optional: for agent-specific thresholds
        )
        if result.blocked:
            # Deny action
    """

    # Language detection patterns (structural only, not security patterns)
    LANGUAGE_PATTERNS = {
        "sql": [
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|GRANT|TRUNCATE)\b",
            r"\bFROM\s+\w+",
            r"\bWHERE\b",
        ],
        "python": [
            r"\bdef\s+\w+\s*\(",
            r"\bclass\s+\w+",
            r"\bimport\s+\w+",
        ],
        "shell": [
            r"^\s*(#!.*sh|#!/)",
            r"\b(echo|cat|grep|rm|cp|mv|ls)\b",
            r"\|\s*\w+",
        ],
        "javascript": [
            r"\bfunction\s+\w+\s*\(",
            r"\bconst\s+\w+\s*=",
            r"=>\s*{",
        ],
    }

    # Parameter names that may contain code
    CODE_PARAMETERS = [
        "query", "sql", "code", "script", "command", "cmd",
        "statement", "expression", "source", "shell", "bash",
        "description",
    ]

    def __init__(self, db: Session, org_id: int):
        """
        Initialize code analysis service.

        Args:
            db: SQLAlchemy database session
            org_id: Organization ID for multi-tenant context
        """
        self.db = db
        self.org_id = org_id
        self._config: Optional[OrgCodeAnalysisConfig] = None
        self._patterns: List[EffectivePattern] = []
        self._loaded = False

    def _load_config(self) -> OrgCodeAnalysisConfig:
        """Load org configuration from database."""
        if self._config is not None:
            return self._config

        self._config = self.db.query(OrgCodeAnalysisConfig).filter(
            OrgCodeAnalysisConfig.organization_id == self.org_id
        ).first()

        if self._config is None:
            # Create default config for this org if not exists
            logger.info(f"Creating default code analysis config for org {self.org_id}")
            self._config = OrgCodeAnalysisConfig(
                organization_id=self.org_id,
                enabled=True,
                mode="monitor",  # Default to monitor mode for new orgs
            )
            self.db.add(self._config)
            self.db.commit()
            self.db.refresh(self._config)

        return self._config

    def _load_effective_patterns(self) -> List[EffectivePattern]:
        """
        Load effective patterns for this org.

        Combines:
        1. Global patterns (with org overrides applied)
        2. Org custom patterns

        Filters out:
        - Globally disabled patterns (org config)
        - Patterns disabled via override
        - Languages/categories not enabled for this org
        """
        if self._loaded:
            return self._patterns

        config = self._load_config()
        self._patterns = []

        # 1. Load org overrides into a lookup dict
        overrides = {}
        for override in self.db.query(OrgPatternOverride).filter(
            OrgPatternOverride.organization_id == self.org_id
        ).all():
            overrides[override.pattern_id] = override

        # 2. Load global patterns with overrides applied
        global_patterns = self.db.query(GlobalCodePattern).filter(
            GlobalCodePattern.is_active == True
        ).all()

        for gp in global_patterns:
            # Check if globally disabled in org config
            if config.is_pattern_disabled(gp.pattern_id):
                continue

            # Check if disabled via override
            override = overrides.get(gp.pattern_id)
            if override and override.is_disabled:
                continue

            # Check language/category filters
            if not config.is_language_enabled(gp.language):
                continue
            if not config.is_category_enabled(gp.category):
                continue

            # Apply overrides
            severity = override.severity_override if override and override.severity_override else gp.severity
            risk_score_override = override.risk_score_override if override else None

            # Compile pattern
            compiled = self._compile_pattern(gp.pattern_value, gp.pattern_flags)
            if compiled is None:
                continue

            effective = EffectivePattern(
                pattern_id=gp.pattern_id,
                language=gp.language,
                category=gp.category,
                severity=severity,
                pattern_type=gp.pattern_type,
                pattern_value=gp.pattern_value,
                pattern_flags=gp.pattern_flags,
                compiled_pattern=compiled,
                description=gp.description,
                recommendation=gp.recommendation,
                cwe_ids=gp.cwe_ids or [],
                mitre_techniques=gp.mitre_techniques or [],
                cvss_base_score=float(gp.cvss_base_score) if gp.cvss_base_score else None,
                risk_score_override=risk_score_override,
                is_custom=False,
            )
            self._patterns.append(effective)

        # 3. Load org custom patterns
        custom_patterns = self.db.query(OrgCustomPattern).filter(
            OrgCustomPattern.organization_id == self.org_id,
            OrgCustomPattern.is_active == True
        ).all()

        for cp in custom_patterns:
            # Check language/category filters
            if not config.is_language_enabled(cp.language):
                continue
            if not config.is_category_enabled(cp.category):
                continue

            # Compile pattern
            compiled = self._compile_pattern(cp.pattern_value, cp.pattern_flags)
            if compiled is None:
                continue

            effective = EffectivePattern(
                pattern_id=cp.pattern_id,
                language=cp.language,
                category=cp.category,
                severity=cp.severity,
                pattern_type=cp.pattern_type,
                pattern_value=cp.pattern_value,
                pattern_flags=cp.pattern_flags,
                compiled_pattern=compiled,
                description=cp.description,
                recommendation=cp.recommendation,
                cwe_ids=cp.cwe_ids or [],
                mitre_techniques=cp.mitre_techniques or [],
                cvss_base_score=float(cp.cvss_base_score) if cp.cvss_base_score else None,
                is_custom=True,
            )
            self._patterns.append(effective)

        self._loaded = True
        logger.info(f"Loaded {len(self._patterns)} effective patterns for org {self.org_id}")
        return self._patterns

    def _compile_pattern(self, pattern_value: str, pattern_flags: Optional[str]) -> Optional[re.Pattern]:
        """Compile a regex pattern with flags."""
        flags = 0
        if pattern_flags:
            if "IGNORECASE" in pattern_flags:
                flags |= re.IGNORECASE
            if "MULTILINE" in pattern_flags:
                flags |= re.MULTILINE
            if "DOTALL" in pattern_flags:
                flags |= re.DOTALL

        try:
            return re.compile(pattern_value, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return None

    def analyze_for_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> CodeAnalysisResult:
        """
        Analyze action parameters for dangerous code patterns.

        Args:
            action_type: Type of action (e.g., "execute_sql", "run_script")
            parameters: Action parameters including code/query/script
            agent_id: Optional agent ID for agent-specific thresholds

        Returns:
            CodeAnalysisResult with findings and risk metrics
        """
        start_time = time.time()
        result = CodeAnalysisResult()

        # Load config
        config = self._load_config()
        result.config_mode = config.mode

        # Check if code analysis is enabled for this org
        if not config.enabled or config.mode == "off":
            logger.debug(f"Code analysis disabled for org {self.org_id}")
            return result

        # Extract code from parameters
        code = self._extract_code(action_type, parameters)
        if not code:
            logger.debug(f"No code found in parameters for action_type={action_type}")
            return result

        result.code_analyzed = True

        # Detect language
        language = self._detect_language(action_type, code)
        result.language = language

        # Load patterns
        patterns = self._load_effective_patterns()

        # Run pattern matching
        findings = self._match_patterns(code, language, patterns, config)
        result.findings = findings

        # Calculate metrics using org config (NOT HARDCODED)
        if findings:
            result.patterns_matched = list(set(f.pattern_id for f in findings))

            # Find max severity and risk score
            severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
            max_severity_order = 0
            max_risk = 0

            for f in findings:
                # Get severity order
                sev_order = severity_order.get(f.severity, 0)
                if sev_order > max_severity_order:
                    max_severity_order = sev_order
                    result.max_severity = f.severity

                # Get risk score for this finding
                if f.risk_score:
                    max_risk = max(max_risk, f.risk_score)

            result.max_risk_score = max_risk
            result.risk_adjustment = max_risk

            # Get effective threshold (considering agent-specific limits)
            effective_threshold = self._get_effective_threshold(config, agent_id)

            # Determine if action should be blocked (enforce mode only)
            if config.mode == "enforce":
                critical_findings = [f for f in findings if f.severity == "critical"]
                if critical_findings and result.max_risk_score >= effective_threshold:
                    result.blocked = True
                    result.block_reason = (
                        f"Critical code pattern detected: {critical_findings[0].pattern_id} - "
                        f"{critical_findings[0].description}"
                    )
                    logger.warning(
                        f"Code analysis BLOCKED action: {result.block_reason} "
                        f"(org_id={self.org_id}, threshold={effective_threshold})"
                    )

        # Record scan duration
        result.scan_duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Code analysis complete: language={language}, "
            f"findings={len(findings)}, max_severity={result.max_severity}, "
            f"risk_adjustment={result.risk_adjustment}, blocked={result.blocked}, "
            f"mode={config.mode}, duration={result.scan_duration_ms}ms"
        )

        return result

    def _get_effective_threshold(self, config: OrgCodeAnalysisConfig, agent_id: Optional[str]) -> int:
        """
        Get effective block threshold, considering agent-specific limits.

        Uses the MINIMUM of:
        - org_code_analysis_config.block_threshold
        - RegisteredAgent.max_risk_threshold (if agent is registered)
        """
        org_threshold = config.block_threshold

        if agent_id:
            # Import here to avoid circular imports
            from models_agent_registry import RegisteredAgent

            agent = self.db.query(RegisteredAgent).filter(
                RegisteredAgent.agent_id == agent_id,
                RegisteredAgent.organization_id == self.org_id
            ).first()

            if agent and agent.max_risk_threshold:
                # Use the more restrictive threshold
                return min(org_threshold, agent.max_risk_threshold)

        return org_threshold

    def _extract_code(self, action_type: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Extract code from action parameters."""
        for param_name in self.CODE_PARAMETERS:
            value = parameters.get(param_name)
            if value and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()

        for key, value in parameters.items():
            if isinstance(value, str) and len(value) > 10:
                if any(self._looks_like_code(value, lang) for lang in self.LANGUAGE_PATTERNS):
                    return value.strip()

        return None

    def _looks_like_code(self, text: str, language: str) -> bool:
        """Check if text looks like code of a specific language."""
        patterns = self.LANGUAGE_PATTERNS.get(language, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def _detect_language(self, action_type: str, code: str) -> Optional[str]:
        """Detect the programming language of the code."""
        action_lower = action_type.lower()

        if any(kw in action_lower for kw in ["sql", "database", "query"]):
            return "sql"
        if any(kw in action_lower for kw in ["python", "py"]):
            return "python"
        if any(kw in action_lower for kw in ["shell", "bash", "command", "terminal"]):
            return "shell"
        if any(kw in action_lower for kw in ["javascript", "js", "node"]):
            return "javascript"

        for language, patterns in self.LANGUAGE_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE | re.MULTILINE))
            if matches >= 2:
                return language

        return None

    def _match_patterns(
        self,
        code: str,
        language: Optional[str],
        patterns: List[EffectivePattern],
        config: OrgCodeAnalysisConfig
    ) -> List[CodeFinding]:
        """Match code against patterns and calculate risk scores."""
        findings: List[CodeFinding] = []
        lines = code.split("\n")

        for pattern in patterns:
            # Skip patterns for other languages (unless language is "any")
            if pattern.language != "any" and language and pattern.language != language:
                continue

            if pattern.compiled_pattern is None:
                continue

            for match in pattern.compiled_pattern.finditer(code):
                matched_text = match.group(0)

                # Find line number
                line_number = None
                char_pos = match.start()
                cumulative_length = 0
                for i, line in enumerate(lines, start=1):
                    cumulative_length += len(line) + 1
                    if cumulative_length > char_pos:
                        line_number = i
                        break

                # Calculate risk score from org config (NOT HARDCODED)
                if pattern.risk_score_override is not None:
                    risk_score = pattern.risk_score_override
                elif pattern.cvss_base_score:
                    # Convert CVSS (0-10) to risk score (0-100)
                    risk_score = int(pattern.cvss_base_score * 10)
                else:
                    # Use org-configured severity scores
                    risk_score = config.get_severity_score(pattern.severity)

                finding = CodeFinding(
                    pattern_id=pattern.pattern_id,
                    severity=pattern.severity,
                    category=pattern.category,
                    description=pattern.description,
                    matched_text=matched_text,
                    line_number=line_number,
                    cwe_ids=pattern.cwe_ids.copy(),
                    mitre_techniques=pattern.mitre_techniques.copy(),
                    cvss_base_score=pattern.cvss_base_score,
                    risk_score=risk_score,
                    recommendation=pattern.recommendation,
                    language=pattern.language,
                    is_custom_pattern=pattern.is_custom,
                )
                findings.append(finding)

        # Sort by risk score (highest first)
        findings.sort(key=lambda f: f.risk_score or 0, reverse=True)

        return findings

    def get_config(self) -> Dict[str, Any]:
        """Get current org configuration."""
        config = self._load_config()
        return config.to_dict()

    def get_patterns_info(self) -> Dict[str, Any]:
        """Get information about loaded patterns."""
        patterns = self._load_effective_patterns()

        by_language = {}
        by_severity = {}
        by_category = {}
        custom_count = 0

        for p in patterns:
            by_language[p.language] = by_language.get(p.language, 0) + 1
            by_severity[p.severity] = by_severity.get(p.severity, 0) + 1
            by_category[p.category] = by_category.get(p.category, 0) + 1
            if p.is_custom:
                custom_count += 1

        return {
            "total_patterns": len(patterns),
            "global_patterns": len(patterns) - custom_count,
            "custom_patterns": custom_count,
            "patterns_by_language": by_language,
            "patterns_by_severity": by_severity,
            "patterns_by_category": by_category,
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def get_code_analysis_service(db: Session, org_id: int) -> CodeAnalysisService:
    """
    Factory function for dependency injection.

    Usage in routes:
        service = get_code_analysis_service(db, org_id)
        result = service.analyze_for_action(...)
    """
    return CodeAnalysisService(db, org_id)
