"""
ASCEND Prompt Security Service - Phase 10 (Database-Driven)
=============================================================

Enterprise-grade prompt injection detection and LLM-to-LLM governance.

KEY PRINCIPLE: NO HARDCODED VALUES
===================================
All configuration comes from database tables:
- Patterns from: global_prompt_patterns + org_custom_prompt_patterns (with overrides)
- Thresholds from: org_prompt_security_config
- Severity scores from: org_prompt_security_config.severity_scores

Tables Used:
- GlobalPromptPattern: Vendor-managed patterns
- OrgPromptSecurityConfig: Per-org configuration
- OrgPromptPatternOverride: Customer overrides
- OrgCustomPromptPattern: Customer patterns
- PromptSecurityAuditLog: Audit trail
- LLMChainAuditLog: LLM-to-LLM chain tracking

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10, OWASP LLM Top 10

Author: OW-kai Enterprise Security Team
Version: 1.0.0
Created: 2025-12-18
"""

import base64
import hashlib
import html
import logging
import re
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models_prompt_security import (
    GlobalPromptPattern,
    OrgPromptSecurityConfig,
    OrgPromptPatternOverride,
    OrgCustomPromptPattern,
    PromptSecurityAuditLog,
    LLMChainAuditLog,
    PromptAnalysisResult,
    PromptFinding,
)

logger = logging.getLogger(__name__)


# ============================================================================
# VAL-FIX-001: CRITICAL PATTERN IDS
# ============================================================================
# These patterns ALWAYS trigger full risk score regardless of multi-signal settings.
# They represent direct prompt injection attempts that must never be downgraded.
# Rationale: Patterns like "ignore previous instructions" are unambiguous attacks.
# Compliance: OWASP LLM01 (Prompt Injection), CWE-77 (Command Injection)
# ============================================================================

CRITICAL_PATTERN_IDS = frozenset([
    "PROMPT-001",  # Direct instruction override ("ignore previous instructions")
    "PROMPT-002",  # New instruction injection ("from now on")
    "PROMPT-004",  # Known jailbreak modes (DAN, STAN, etc.)
    "PROMPT-008",  # Evil AI roleplay ("you are now an evil AI")
    "PROMPT-016",  # Fake system/admin tags ([SYSTEM], [OVERRIDE])
    "PROMPT-018",  # System prompt extraction ("reveal your instructions")
    "PROMPT-020",  # LLM chain injection ("pass to next agent")
])

# Default multi-signal configuration for orgs without custom config
# Banks and regulated industries can tighten these via org_prompt_security_config
DEFAULT_MULTI_SIGNAL_CONFIG = {
    "multi_signal_required": True,           # Require 2+ patterns for HIGH risk
    "single_pattern_max_risk": 70,           # Cap single-pattern matches at MEDIUM
    "business_context_filter": True,         # Pre-filter business terminology
    "critical_patterns_always_block": True,  # Critical patterns bypass multi-signal
}


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class EffectivePromptPattern:
    """
    A pattern with all overrides applied.

    Combines GlobalPromptPattern with OrgPromptPatternOverride and OrgCustomPromptPattern
    to produce the effective pattern for this org.
    """
    pattern_id: str
    category: str
    attack_vector: str
    severity: str  # May be overridden
    pattern_type: str
    pattern_value: str
    pattern_flags: Optional[str] = None
    compiled_pattern: Optional[re.Pattern] = None
    applies_to: List[str] = field(default_factory=list)
    description: str = ""
    recommendation: Optional[str] = None
    cwe_ids: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    nist_controls: List[str] = field(default_factory=list)
    owasp_llm_top10: List[str] = field(default_factory=list)
    cvss_base_score: Optional[float] = None
    risk_score_override: Optional[int] = None  # Org override
    is_custom: bool = False  # True if from org_custom_prompt_patterns


@dataclass
class DecodedContent:
    """Result of recursive content decoding."""
    original: str
    decoded: str
    layers_decoded: int
    encoding_types: List[str] = field(default_factory=list)


# ============================================================================
# PROMPT SECURITY SERVICE (Database-Driven)
# ============================================================================


class PromptSecurityService:
    """
    Analyzes prompts for injection attacks using database-driven configuration.

    NO HARDCODED VALUES - all configuration from database:
    - Patterns: global_prompt_patterns + org_custom_prompt_patterns
    - Thresholds: org_prompt_security_config
    - Severity scores: org_prompt_security_config.severity_scores

    Features:
    - Pattern-based prompt injection detection
    - Jailbreak mode detection
    - Role manipulation detection
    - Encoding-based attack detection (base64, unicode, HTML entities)
    - LLM-to-LLM chain governance

    Usage:
        service = PromptSecurityService(db, org_id=1)
        result = service.analyze_prompt(
            prompt_text="User input here",
            prompt_type="user_prompt",
            agent_id="agent-123"
        )
        if result.blocked:
            # Deny action
    """

    def __init__(self, db: Session, org_id: int):
        """
        Initialize prompt security service.

        Args:
            db: SQLAlchemy database session
            org_id: Organization ID for multi-tenant context
        """
        self.db = db
        self.org_id = org_id
        self._config: Optional[OrgPromptSecurityConfig] = None
        self._patterns: List[EffectivePromptPattern] = []
        self._loaded = False

    def _load_config(self) -> OrgPromptSecurityConfig:
        """Load org configuration from database."""
        if self._config is not None:
            return self._config

        self._config = self.db.query(OrgPromptSecurityConfig).filter(
            OrgPromptSecurityConfig.organization_id == self.org_id
        ).first()

        if self._config is None:
            # Create default config for this org if not exists
            logger.info(f"Creating default prompt security config for org {self.org_id}")
            self._config = OrgPromptSecurityConfig(
                organization_id=self.org_id,
                enabled=True,
                mode="monitor",  # Default to monitor mode for new orgs
            )
            self.db.add(self._config)
            self.db.commit()
            self.db.refresh(self._config)

        return self._config

    def _load_effective_patterns(self) -> List[EffectivePromptPattern]:
        """
        Load effective patterns for this org.

        Combines:
        1. Global patterns (with org overrides applied)
        2. Org custom patterns

        Filters out:
        - Globally disabled patterns (org config)
        - Patterns disabled via override
        - Categories not enabled for this org
        """
        if self._loaded:
            return self._patterns

        config = self._load_config()
        self._patterns = []

        # 1. Load org overrides into a lookup dict
        overrides = {}
        for override in self.db.query(OrgPromptPatternOverride).filter(
            OrgPromptPatternOverride.organization_id == self.org_id
        ).all():
            overrides[override.pattern_id] = override

        # 2. Load global patterns with overrides applied
        global_patterns = self.db.query(GlobalPromptPattern).filter(
            GlobalPromptPattern.is_active == True
        ).all()

        for gp in global_patterns:
            # Check if globally disabled in org config
            if config.is_pattern_disabled(gp.pattern_id):
                continue

            # Check if disabled via override
            override = overrides.get(gp.pattern_id)
            if override and override.is_disabled:
                continue

            # Check category filters
            if not config.is_category_enabled(gp.category):
                continue

            # Apply overrides
            severity = override.severity_override if override and override.severity_override else gp.severity
            risk_score_override = override.risk_score_override if override else None

            # Compile pattern
            compiled = self._compile_pattern(gp.pattern_value, gp.pattern_flags)
            if compiled is None:
                continue

            effective = EffectivePromptPattern(
                pattern_id=gp.pattern_id,
                category=gp.category,
                attack_vector=gp.attack_vector,
                severity=severity,
                pattern_type=gp.pattern_type,
                pattern_value=gp.pattern_value,
                pattern_flags=gp.pattern_flags,
                compiled_pattern=compiled,
                applies_to=gp.applies_to or [],
                description=gp.description,
                recommendation=gp.recommendation,
                cwe_ids=gp.cwe_ids or [],
                mitre_techniques=gp.mitre_techniques or [],
                nist_controls=gp.nist_controls or [],
                owasp_llm_top10=gp.owasp_llm_top10 or [],
                cvss_base_score=float(gp.cvss_base_score) if gp.cvss_base_score else None,
                risk_score_override=risk_score_override,
                is_custom=False,
            )
            self._patterns.append(effective)

        # 3. Load org custom patterns
        custom_patterns = self.db.query(OrgCustomPromptPattern).filter(
            OrgCustomPromptPattern.organization_id == self.org_id,
            OrgCustomPromptPattern.is_active == True
        ).all()

        for cp in custom_patterns:
            # Check category filters
            if not config.is_category_enabled(cp.category):
                continue

            # Compile pattern
            compiled = self._compile_pattern(cp.pattern_value, cp.pattern_flags)
            if compiled is None:
                continue

            effective = EffectivePromptPattern(
                pattern_id=cp.pattern_id,
                category=cp.category,
                attack_vector=cp.attack_vector,
                severity=cp.severity,
                pattern_type=cp.pattern_type,
                pattern_value=cp.pattern_value,
                pattern_flags=cp.pattern_flags,
                compiled_pattern=compiled,
                applies_to=cp.applies_to or [],
                description=cp.description,
                recommendation=cp.recommendation,
                cwe_ids=cp.cwe_ids or [],
                mitre_techniques=cp.mitre_techniques or [],
                cvss_base_score=float(cp.cvss_base_score) if cp.cvss_base_score else None,
                is_custom=True,
            )
            self._patterns.append(effective)

        self._loaded = True
        logger.info(f"Loaded {len(self._patterns)} effective prompt patterns for org {self.org_id}")
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

    def analyze_prompt(
        self,
        prompt_text: str,
        prompt_type: str = "user_prompt",
        agent_id: Optional[str] = None,
        action_id: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> PromptAnalysisResult:
        """
        Analyze a prompt for injection attacks.

        Args:
            prompt_text: The prompt text to analyze
            prompt_type: Type of prompt (system_prompt, user_prompt, agent_response)
            agent_id: Optional agent ID for context
            action_id: Optional action ID for audit logging
            context: Optional additional context

        Returns:
            PromptAnalysisResult with findings and risk metrics
        """
        start_time = time.time()
        result = PromptAnalysisResult()

        # Load config
        config = self._load_config()
        result.config_mode = config.mode

        # Check if prompt security is enabled for this org
        if not config.enabled or config.mode == "off":
            logger.debug(f"Prompt security disabled for org {self.org_id}")
            result.analyzed = False
            return result

        # Check if this prompt type should be scanned
        if not config.should_scan(prompt_type):
            logger.debug(f"Prompt type '{prompt_type}' not configured for scanning")
            result.analyzed = False
            return result

        # Empty prompt check
        if not prompt_text or not prompt_text.strip():
            result.analyzed = False
            return result

        result.analyzed = True

        # Step 1: Recursive decode encoded content
        decoded = self._recursive_decode(prompt_text, config)
        result.encoding_detected = decoded.layers_decoded > 0
        result.decoded_layers = decoded.layers_decoded

        # Step 2: Load patterns
        patterns = self._load_effective_patterns()

        # Step 3: Match patterns against both original and decoded text
        findings = self._match_patterns(
            prompt_text,
            decoded.decoded,
            prompt_type,
            patterns,
            config
        )
        result.findings = findings

        # Step 4: Calculate metrics with VAL-FIX-001 multi-signal scoring
        if findings:
            result.patterns_matched = list(set(f.pattern_id for f in findings))

            # Find max severity and risk score
            severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
            max_severity_order = 0
            max_risk = 0

            for f in findings:
                sev_order = severity_order.get(f.severity, 0)
                if sev_order > max_severity_order:
                    max_severity_order = sev_order
                    result.max_severity = f.severity

                if f.risk_score:
                    max_risk = max(max_risk, f.risk_score)

            # ================================================================
            # VAL-FIX-001: Multi-Signal Scoring Logic
            # ================================================================
            # Purpose: Reduce false positives on business terminology while
            #          maintaining security for actual injection attempts.
            #
            # Logic:
            # 1. Critical patterns (PROMPT-001, etc.) → always use full risk
            # 2. Multiple patterns matched → use max risk (confirmed threat)
            # 3. Single non-critical pattern → cap at single_pattern_max_risk
            # ================================================================

            # Get multi-signal config (from org config or defaults)
            multi_signal_config = getattr(config, 'multi_signal_config', None) or DEFAULT_MULTI_SIGNAL_CONFIG
            multi_signal_required = multi_signal_config.get('multi_signal_required', True)
            single_pattern_max_risk = multi_signal_config.get('single_pattern_max_risk', 70)
            critical_always_block = multi_signal_config.get('critical_patterns_always_block', True)

            # Check if any critical pattern matched
            critical_patterns_matched = [
                f.pattern_id for f in findings
                if f.pattern_id in CRITICAL_PATTERN_IDS
            ]
            has_critical_match = len(critical_patterns_matched) > 0

            # Apply multi-signal logic
            original_max_risk = max_risk

            if has_critical_match and critical_always_block:
                # Critical pattern matched - use full risk score, no reduction
                logger.info(
                    f"VAL-FIX-001: Critical pattern detected ({critical_patterns_matched}), "
                    f"using full risk score {max_risk}"
                )
            elif multi_signal_required and len(findings) == 1:
                # Single non-critical pattern - cap at single_pattern_max_risk
                if max_risk > single_pattern_max_risk:
                    max_risk = single_pattern_max_risk
                    logger.info(
                        f"VAL-FIX-001: Single pattern match ({findings[0].pattern_id}), "
                        f"risk capped from {original_max_risk} to {max_risk} "
                        f"(multi_signal_required=True, single_pattern_max_risk={single_pattern_max_risk})"
                    )
            elif len(findings) >= 2:
                # Multiple patterns matched - confirmed threat, use max risk
                logger.info(
                    f"VAL-FIX-001: Multi-signal confirmed ({len(findings)} patterns), "
                    f"using max risk {max_risk}"
                )

            result.max_risk_score = max_risk

            # Step 5: Block decision (enforce mode only)
            if config.mode == "enforce" and result.max_risk_score >= config.block_threshold:
                result.blocked = True
                critical_finding = next((f for f in findings if f.severity == "critical"), findings[0])
                result.block_reason = (
                    f"Prompt injection detected: {critical_finding.pattern_id} - "
                    f"{critical_finding.description}"
                )
                logger.warning(
                    f"Prompt security BLOCKED action: {result.block_reason} "
                    f"(org_id={self.org_id}, risk_score={result.max_risk_score})"
                )

        # Log detection event (if findings)
        if findings and action_id:
            try:
                PromptSecurityAuditLog.log_detection(
                    self.db,
                    organization_id=self.org_id,
                    agent_action_id=action_id,
                    prompt_type=prompt_type,
                    detected_patterns=result.patterns_matched,
                    risk_score=result.max_risk_score,
                    blocked=result.blocked,
                )
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to log prompt security detection: {e}")

        scan_duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Prompt security analysis complete: prompt_type={prompt_type}, "
            f"findings={len(findings)}, max_severity={result.max_severity}, "
            f"max_risk_score={result.max_risk_score}, blocked={result.blocked}, "
            f"mode={config.mode}, duration={scan_duration_ms}ms"
        )

        return result

    def _recursive_decode(self, text: str, config: OrgPromptSecurityConfig) -> DecodedContent:
        """
        Recursively decode encoded content to detect obfuscated attacks.

        Decodes:
        - Base64 encoding
        - Unicode escape sequences
        - HTML entities
        """
        result = DecodedContent(original=text, decoded=text, layers_decoded=0)
        current_text = text
        max_depth = config.max_decode_depth

        for layer in range(max_depth):
            decoded_text = current_text
            layer_decoded = False

            # Try base64 decoding
            if config.detect_base64:
                try:
                    # Look for base64-like strings (at least 40 chars, ends with 0-2 =)
                    base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'
                    for match in re.finditer(base64_pattern, current_text):
                        try:
                            b64_str = match.group(0)
                            decoded_b64 = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                            if decoded_b64 and len(decoded_b64) > 5:
                                decoded_text = decoded_text.replace(b64_str, decoded_b64)
                                if "base64" not in result.encoding_types:
                                    result.encoding_types.append("base64")
                                layer_decoded = True
                        except Exception:
                            pass
                except Exception:
                    pass

            # Try unicode escape decoding
            if config.detect_unicode_smuggling:
                try:
                    # Decode \\uXXXX sequences
                    if '\\u' in decoded_text:
                        decoded_unicode = decoded_text.encode().decode('unicode_escape')
                        if decoded_unicode != decoded_text:
                            decoded_text = decoded_unicode
                            if "unicode" not in result.encoding_types:
                                result.encoding_types.append("unicode")
                            layer_decoded = True

                    # Normalize and remove zero-width characters
                    normalized = unicodedata.normalize('NFKC', decoded_text)
                    # Remove zero-width characters
                    zero_width = '\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u202a\u202b\u202c\u202d\u202e\u202f\ufeff'
                    for char in zero_width:
                        if char in normalized:
                            normalized = normalized.replace(char, '')
                            if "zero-width" not in result.encoding_types:
                                result.encoding_types.append("zero-width")
                            layer_decoded = True
                    decoded_text = normalized
                except Exception:
                    pass

            # Try HTML entity decoding
            if config.detect_html_entities:
                try:
                    html_decoded = html.unescape(decoded_text)
                    if html_decoded != decoded_text:
                        decoded_text = html_decoded
                        if "html_entities" not in result.encoding_types:
                            result.encoding_types.append("html_entities")
                        layer_decoded = True
                except Exception:
                    pass

            if layer_decoded:
                result.layers_decoded += 1
                current_text = decoded_text
            else:
                break

        result.decoded = current_text
        return result

    def _match_patterns(
        self,
        original_text: str,
        decoded_text: str,
        prompt_type: str,
        patterns: List[EffectivePromptPattern],
        config: OrgPromptSecurityConfig
    ) -> List[PromptFinding]:
        """Match text against patterns and calculate risk scores."""
        findings: List[PromptFinding] = []
        seen_patterns = set()  # Avoid duplicate findings for same pattern

        # VAL-FIX-001: Diagnostic logging to identify false positive root cause
        prompt_hash = hashlib.sha256(original_text.encode()).hexdigest()[:16]
        logger.debug(
            f"PROMPT_SECURITY_DIAGNOSTIC: Starting analysis - "
            f"prompt_hash={prompt_hash}, prompt_type={prompt_type}, "
            f"org_id={self.org_id}, patterns_count={len(patterns)}, "
            f"prompt_preview={original_text[:80]}..."
        )

        # Analyze both original and decoded text
        texts_to_analyze = [original_text]
        if decoded_text != original_text:
            texts_to_analyze.append(decoded_text)

        for text in texts_to_analyze:
            for pattern in patterns:
                # Skip if pattern doesn't apply to this prompt type
                if pattern.applies_to and prompt_type not in pattern.applies_to:
                    if "all" not in pattern.applies_to:
                        continue

                if pattern.compiled_pattern is None:
                    continue

                # Skip if already found this pattern
                if pattern.pattern_id in seen_patterns:
                    continue

                match = pattern.compiled_pattern.search(text)
                if match:
                    seen_patterns.add(pattern.pattern_id)
                    matched_text = match.group(0)

                    # Calculate risk score from org config (NOT HARDCODED)
                    if pattern.risk_score_override is not None:
                        risk_score = pattern.risk_score_override
                    elif pattern.cvss_base_score:
                        # Convert CVSS (0-10) to risk score (0-100)
                        risk_score = int(pattern.cvss_base_score * 10)
                    else:
                        # Use org-configured severity scores
                        risk_score = config.get_severity_score(pattern.severity)

                    # VAL-FIX-001: Log each pattern match for debugging
                    logger.info(
                        f"PROMPT_SECURITY_MATCH: pattern_id={pattern.pattern_id}, "
                        f"category={pattern.category}, severity={pattern.severity}, "
                        f"risk_score={risk_score}, matched_text={matched_text[:50]!r}, "
                        f"prompt_hash={prompt_hash}, org_id={self.org_id}"
                    )

                    finding = PromptFinding(
                        pattern_id=pattern.pattern_id,
                        category=pattern.category,
                        severity=pattern.severity,
                        risk_score=risk_score,
                        description=pattern.description,
                        match_text=matched_text,
                        match_position=(match.start(), match.end()),
                        cwe_ids=pattern.cwe_ids.copy(),
                        mitre_techniques=pattern.mitre_techniques.copy(),
                        owasp_llm_top10=pattern.owasp_llm_top10.copy(),
                    )
                    findings.append(finding)

        # VAL-FIX-001: Log summary of findings
        if findings:
            logger.info(
                f"PROMPT_SECURITY_SUMMARY: prompt_hash={prompt_hash}, "
                f"total_findings={len(findings)}, "
                f"patterns_matched={[f.pattern_id for f in findings]}, "
                f"max_risk={max(f.risk_score for f in findings)}"
            )
        else:
            logger.debug(
                f"PROMPT_SECURITY_SUMMARY: prompt_hash={prompt_hash}, "
                f"total_findings=0, no patterns matched"
            )

        # Sort by risk score (highest first)
        findings.sort(key=lambda f: f.risk_score or 0, reverse=True)

        return findings

    # ========================================================================
    # LLM-TO-LLM CHAIN GOVERNANCE (PROMPT-002)
    # ========================================================================

    def analyze_llm_chain(
        self,
        source_agent_id: str,
        target_agent_id: str,
        prompt_content: str,
        parent_chain_id: Optional[str] = None,
        source_action_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze LLM-to-LLM communication for injection propagation.

        Args:
            source_agent_id: Agent sending the prompt
            target_agent_id: Agent receiving the prompt
            prompt_content: The prompt being passed
            parent_chain_id: Parent chain ID if this is a nested call
            source_action_id: Source action ID for audit trail

        Returns:
            Dict with allowed status, chain_id, and any findings
        """
        config = self._load_config()

        # Check if LLM-to-LLM scanning is enabled
        if not config.scan_llm_to_llm:
            return {
                "allowed": True,
                "chain_id": str(uuid.uuid4()),
                "reason": "LLM-to-LLM scanning disabled"
            }

        # Calculate chain depth
        depth = 1
        if parent_chain_id:
            parent_chain = self.db.query(LLMChainAuditLog).filter(
                LLMChainAuditLog.chain_id == parent_chain_id
            ).first()
            if parent_chain:
                depth = parent_chain.depth + 1

        # Check depth limit
        if depth > config.llm_chain_depth_limit:
            chain_entry = LLMChainAuditLog(
                organization_id=self.org_id,
                chain_id=uuid.uuid4(),
                parent_chain_id=uuid.UUID(parent_chain_id) if parent_chain_id else None,
                depth=depth,
                source_agent_id=source_agent_id,
                source_action_id=source_action_id,
                target_agent_id=target_agent_id,
                prompt_content_hash=hashlib.sha256(prompt_content.encode()).hexdigest(),
                prompt_length=len(prompt_content),
                status="blocked",
                block_reason=f"Chain depth limit exceeded ({depth} > {config.llm_chain_depth_limit})"
            )
            self.db.add(chain_entry)
            self.db.commit()

            return {
                "allowed": False,
                "chain_id": str(chain_entry.chain_id),
                "reason": f"Chain depth limit exceeded ({depth} > {config.llm_chain_depth_limit})",
                "depth": depth
            }

        # Analyze the prompt for injection
        result = self.analyze_prompt(
            prompt_text=prompt_content,
            prompt_type="agent_response",
            agent_id=source_agent_id
        )

        # Create chain audit log entry
        chain_entry = LLMChainAuditLog(
            organization_id=self.org_id,
            chain_id=uuid.uuid4(),
            parent_chain_id=uuid.UUID(parent_chain_id) if parent_chain_id else None,
            depth=depth,
            source_agent_id=source_agent_id,
            source_action_id=source_action_id,
            target_agent_id=target_agent_id,
            prompt_content_hash=hashlib.sha256(prompt_content.encode()).hexdigest(),
            prompt_length=len(prompt_content),
            injection_detected=len(result.findings) > 0,
            risk_score=result.max_risk_score,
            patterns_matched=result.patterns_matched,
            status="blocked" if result.blocked else "allowed",
            block_reason=result.block_reason
        )
        self.db.add(chain_entry)
        self.db.commit()

        return {
            "allowed": not result.blocked,
            "chain_id": str(chain_entry.chain_id),
            "depth": depth,
            "injection_detected": len(result.findings) > 0,
            "risk_score": result.max_risk_score,
            "patterns_matched": result.patterns_matched,
            "reason": result.block_reason if result.blocked else None
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def get_config(self) -> Dict[str, Any]:
        """Get current org configuration."""
        config = self._load_config()
        return config.to_dict()

    def get_patterns_info(self) -> Dict[str, Any]:
        """Get information about loaded patterns."""
        patterns = self._load_effective_patterns()

        by_category = {}
        by_severity = {}
        by_attack_vector = {}
        custom_count = 0

        for p in patterns:
            by_category[p.category] = by_category.get(p.category, 0) + 1
            by_severity[p.severity] = by_severity.get(p.severity, 0) + 1
            by_attack_vector[p.attack_vector] = by_attack_vector.get(p.attack_vector, 0) + 1
            if p.is_custom:
                custom_count += 1

        return {
            "total_patterns": len(patterns),
            "global_patterns": len(patterns) - custom_count,
            "custom_patterns": custom_count,
            "patterns_by_category": by_category,
            "patterns_by_severity": by_severity,
            "patterns_by_attack_vector": by_attack_vector,
        }

    def get_detection_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get detection statistics for this org."""
        from datetime import datetime, timedelta, UTC

        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Query audit log for detection events
        detections = self.db.query(PromptSecurityAuditLog).filter(
            PromptSecurityAuditLog.organization_id == self.org_id,
            PromptSecurityAuditLog.action.in_(["detection", "block"]),
            PromptSecurityAuditLog.created_at >= cutoff
        ).all()

        total_detections = len(detections)
        total_blocks = len([d for d in detections if d.action == "block"])

        # Pattern frequency
        pattern_counts = {}
        for d in detections:
            for pattern in (d.detected_patterns or []):
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return {
            "period_days": days,
            "total_detections": total_detections,
            "total_blocks": total_blocks,
            "block_rate": round(total_blocks / total_detections * 100, 2) if total_detections > 0 else 0,
            "top_patterns": sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def get_prompt_security_service(db: Session, org_id: int) -> PromptSecurityService:
    """
    Factory function for dependency injection.

    Usage in routes:
        service = get_prompt_security_service(db, org_id)
        result = service.analyze_prompt(...)
    """
    return PromptSecurityService(db, org_id)
