# enrichment.py - Enterprise security enrichment with CVSS v3.1 integration
"""
ARCH-001: Enhanced with CVSS v3.1 quantitative risk scoring
ARCH-002: Enterprise-grade risk assessment with action-type classification

This module provides security enrichment for agent actions including:
- Action-type-based risk classification (NEW - ARCH-002)
- Expanded keyword-based pattern matching (ENHANCED - ARCH-002)
- Context-aware risk elevation (NEW - ARCH-002)
- MITRE ATT&CK tactic/technique mapping
- NIST control mapping
- CVSS v3.1 quantitative risk scoring (ARCH-001)
- Comprehensive audit logging (ARCH-002)

Enterprise Standards:
- Backward compatible with existing integrations
- Comprehensive error handling and graceful fallbacks
- Detailed audit logging for compliance
- Performance optimized pattern matching
"""

import logging
from typing import Dict, Optional, Set, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ============================================================================
# ARCH-002: ENTERPRISE RISK CLASSIFICATION CONSTANTS
# ============================================================================

# High-risk action types requiring immediate approval (risk score 85-95)
HIGH_RISK_ACTION_TYPES: Set[str] = {
    "database_write",      # Production database modifications
    "database_delete",     # Data deletion operations
    "data_export",         # Data exfiltration risk
    "data_exfiltration",   # Explicit exfiltration attempts
    "schema_change",       # Database schema modifications
    "user_create",         # User provisioning
    "user_provision",      # User provisioning (alternate naming)
    "permission_grant",    # Permission escalation
    "access_grant",        # Access control modifications
    "secret_access",       # Secrets/credentials access
    "credential_access",   # Credential operations
}

# Medium-risk action types requiring monitoring (risk score 55-70)
MEDIUM_RISK_ACTION_TYPES: Set[str] = {
    "system_modification",  # System configuration changes
    "api_call",            # External API calls (context dependent)
    "file_write",          # File system modifications
    "network_access",      # Network operations
    "config_change",       # Configuration modifications
    "service_restart",     # Service control operations
}

# Enterprise logging context
_risk_assessment_stats = {
    "total_assessments": 0,
    "high_risk_detections": 0,
    "action_type_matches": 0,
    "keyword_matches": 0,
    "context_elevations": 0
}


def evaluate_action_enrichment(
    action_type: str,
    description: str,
    db: Session = None,
    action_id: int = None,
    context: Dict = None
) -> dict:
    """
    Evaluate and enrich agent actions with security metadata.

    Args:
        action_type: Type of agent action (e.g., "database_write", "file_read")
        description: Human-readable description of the action
        db: Database session (optional, for CVSS integration)
        action_id: Agent action ID (optional, for CVSS storage)
        context: Additional context for CVSS scoring (optional)

    Returns:
        Dictionary with:
        - risk_level: Qualitative risk (low/medium/high) - BACKWARD COMPATIBLE
        - mitre_tactic: MITRE ATT&CK tactic - BACKWARD COMPATIBLE
        - mitre_technique: MITRE ATT&CK technique - BACKWARD COMPATIBLE
        - nist_control: NIST control ID - BACKWARD COMPATIBLE
        - nist_description: NIST control description - BACKWARD COMPATIBLE
        - recommendation: Security recommendation - BACKWARD COMPATIBLE
        - cvss_score: NIST CVSS v3.1 base score (0.0-10.0) - NEW
        - cvss_severity: CVSS severity (NONE|LOW|MEDIUM|HIGH|CRITICAL) - NEW
        - cvss_vector: CVSS vector string - NEW
    """

    # ========================================================================
    # ARCH-002: Enterprise-grade risk assessment with comprehensive logging
    # ========================================================================

    # Update stats for monitoring
    _risk_assessment_stats["total_assessments"] += 1

    # Convert to lowercase for case-insensitive matching
    action_lower = action_type.lower()
    desc_lower = (description or "").lower()

    # Determine assessment method used (for audit logging)
    assessment_method = "keyword_matching"  # Default
    risk_elevation_reason = None

    logger.debug(
        f"🔍 ARCH-002: Risk assessment started - "
        f"action_type='{action_type}', "
        f"description_length={len(description or '')}"
    )

    # ========================================================================
    # FIX #1: ACTION-TYPE-BASED RISK CLASSIFICATION (ENTERPRISE PRIORITY)
    # ========================================================================

    result = None

    # Check high-risk action types FIRST (before keyword matching)
    if action_lower in HIGH_RISK_ACTION_TYPES:
        assessment_method = "action_type_high_risk"
        _risk_assessment_stats["action_type_matches"] += 1
        _risk_assessment_stats["high_risk_detections"] += 1

        # Determine specific categorization based on action type
        if action_lower in ["database_write", "database_delete", "schema_change"]:
            result = {
                "risk_level": "high",
                "mitre_tactic": "Impact",
                "mitre_technique": "T1485 - Data Manipulation",
                "nist_control": "SI-7",
                "nist_description": "Software, Firmware, and Information Integrity",
                "recommendation": "Database operations require approval. Review change management procedures and ensure backup exists."
            }
        elif action_lower in ["data_export", "data_exfiltration"]:
            result = {
                "risk_level": "high",
                "mitre_tactic": "Exfiltration",
                "mitre_technique": "T1041 - Exfiltration Over C2 Channel",
                "nist_control": "SI-4",
                "nist_description": "Information System Monitoring",
                "recommendation": "Data export detected. Verify authorization and ensure compliance with data protection policies."
            }
        elif action_lower in ["user_create", "user_provision", "permission_grant", "access_grant"]:
            result = {
                "risk_level": "high",
                "mitre_tactic": "Privilege Escalation",
                "mitre_technique": "T1078 - Valid Accounts",
                "nist_control": "AC-2",
                "nist_description": "Account Management",
                "recommendation": "User/permission modification requires approval. Verify principle of least privilege."
            }
        elif action_lower in ["secret_access", "credential_access"]:
            result = {
                "risk_level": "high",
                "mitre_tactic": "Credential Access",
                "mitre_technique": "T1552 - Unsecured Credentials",
                "nist_control": "IA-5",
                "nist_description": "Authenticator Management",
                "recommendation": "Credential access detected. Ensure proper secrets management and rotation policies."
            }
        else:
            # Generic high-risk categorization
            result = {
                "risk_level": "high",
                "mitre_tactic": "Impact",
                "mitre_technique": "T1485 - Data Destruction",
                "nist_control": "SI-4",
                "nist_description": "Information System Monitoring",
                "recommendation": "High-risk action requires approval and security review."
            }

        logger.info(
            f"✅ ARCH-002: High-risk action type detected - "
            f"action_type='{action_type}', risk_level='high', "
            f"method='action_type_classification'"
        )

    # Check medium-risk action types
    elif action_lower in MEDIUM_RISK_ACTION_TYPES:
        assessment_method = "action_type_medium_risk"
        _risk_assessment_stats["action_type_matches"] += 1

        result = {
            "risk_level": "medium",
            "mitre_tactic": "Execution",
            "mitre_technique": "T1059 - Command and Scripting Interpreter",
            "nist_control": "SI-3",
            "nist_description": "Malicious Code Protection",
            "recommendation": "System modification requires monitoring. Validate legitimacy and maintain audit logs."
        }

        logger.info(
            f"⚠️  ARCH-002: Medium-risk action type detected - "
            f"action_type='{action_type}', risk_level='medium'"
        )

    # ========================================================================
    # FIX #2: EXPANDED KEYWORD PATTERN MATCHING (ENHANCED COVERAGE)
    # ========================================================================

    # If not classified by action type, use enhanced keyword matching
    if result is None:
        assessment_method = "keyword_matching_enhanced"
        _risk_assessment_stats["keyword_matches"] += 1

        # EXPANDED high-risk patterns (ARCH-002 enhancement)
        high_risk_patterns = [
            # Existing patterns (maintained for backward compatibility)
            "data_exfiltration", "exfiltrate", "leak", "steal", "copy_sensitive",
            "privilege_escalation", "escalate", "admin", "root", "sudo",
            "lateral_movement", "persistence", "backdoor", "malware",

            # NEW: Data sensitivity patterns (ARCH-002)
            "pii", "personal", "customer", "credit card", "ssn", "patient",
            "export", "exfil", "transfer", "sensitive", "confidential",

            # NEW: Production/Critical system patterns (ARCH-002)
            "production", "prod", "live", "schema", "drop", "truncate", "delete",

            # NEW: Financial/Payment patterns (ARCH-002)
            "payment", "transaction", "financial", "billing", "stripe", "paypal",
            "invoice", "charge", "refund",

            # NEW: Security infrastructure patterns (ARCH-002)
            "firewall", "security group", "acl", "access control", "auth", "vpn",
            "certificate", "encryption key", "private key",

            # NEW: Administrative actions (ARCH-002)
            "provision", "create user", "grant", "revoke", "modify permission",
            "elevate", "impersonate"
        ]

        # EXPANDED medium-risk patterns (ARCH-002 enhancement)
        medium_risk_patterns = [
            # Existing patterns
            "network_scan", "port_scan", "reconnaissance", "discovery",
            "credential_access", "password", "token", "key",
            "execution", "command", "script", "shell",

            # NEW: Configuration patterns (ARCH-002)
            "config", "configure", "setting", "parameter",

            # NEW: API/Integration patterns (ARCH-002)
            "webhook", "callback", "integration", "third party"
        ]

        # Check for high-risk indicators
        if any(pattern in action_lower or pattern in desc_lower for pattern in high_risk_patterns):
            _risk_assessment_stats["high_risk_detections"] += 1
            if "exfiltrat" in action_lower or "leak" in desc_lower:
                result = {
                    "risk_level": "high",
                    "mitre_tactic": "Exfiltration",
                    "mitre_technique": "T1041 - Exfiltration Over C2 Channel",
                    "nist_control": "SI-4",
                    "nist_description": "Information System Monitoring",
                    "recommendation": "Immediately investigate potential data exfiltration and block unauthorized data transfers."
                }
            elif "privilege" in action_lower or "escalat" in desc_lower:
                result = {
                    "risk_level": "high",
                    "mitre_tactic": "Privilege Escalation",
                    "mitre_technique": "T1068 - Exploitation for Privilege Escalation",
                    "nist_control": "AC-6",
                    "nist_description": "Least Privilege",
                    "recommendation": "Review user permissions and investigate unauthorized privilege escalation attempts."
                }
            else:
                result = {
                    "risk_level": "high",
                    "mitre_tactic": "Impact",
                    "mitre_technique": "T1485 - Data Destruction",
                    "nist_control": "SI-4",
                    "nist_description": "Information System Monitoring",
                    "recommendation": "Investigate high-risk activity and implement additional security controls."
                }

        # Check for medium-risk indicators
        elif any(pattern in action_lower or pattern in desc_lower for pattern in medium_risk_patterns):
            if "network" in action_lower or "scan" in desc_lower:
                result = {
                    "risk_level": "medium",
                    "mitre_tactic": "Discovery",
                    "mitre_technique": "T1046 - Network Service Scanning",
                    "nist_control": "SI-4",
                    "nist_description": "Information System Monitoring",
                    "recommendation": "Monitor network scanning activities and ensure they are authorized."
                }
            elif "credential" in action_lower or "password" in desc_lower:
                result = {
                    "risk_level": "medium",
                    "mitre_tactic": "Credential Access",
                    "mitre_technique": "T1110 - Brute Force",
                    "nist_control": "IA-5",
                    "nist_description": "Authenticator Management",
                    "recommendation": "Review credential access patterns and strengthen authentication mechanisms."
                }
            else:
                result = {
                    "risk_level": "medium",
                    "mitre_tactic": "Execution",
                    "mitre_technique": "T1059 - Command and Scripting Interpreter",
                    "nist_control": "SI-3",
                    "nist_description": "Malicious Code Protection",
                    "recommendation": "Monitor execution activities and validate legitimacy of commands."
                }

        # Default to low risk if no patterns matched
        else:
            result = {
                "risk_level": "low",
                "mitre_tactic": "Execution",
                "mitre_technique": "T1204 - User Execution",
                "nist_control": "AU-6",
                "nist_description": "Audit Review, Analysis, and Reporting",
                "recommendation": "Continue monitoring agent activities and maintain audit logs."
            }

    # ========================================================================
    # FIX #3: CONTEXT-AWARE RISK ELEVATION (PRODUCTION DETECTION)
    # ========================================================================

    # Elevate risk based on context (production systems, sensitive data)
    original_risk = result["risk_level"]

    # Production system detection
    production_indicators = ["production", "prod", "live", "prd"]
    is_production = any(indicator in desc_lower for indicator in production_indicators)

    # Sensitive data detection
    sensitive_data_indicators = ["pii", "personal", "customer", "credit card", "ssn", "patient", "confidential"]
    has_sensitive_data = any(indicator in desc_lower for indicator in sensitive_data_indicators)

    # Financial transaction detection
    financial_indicators = ["payment", "transaction", "billing", "invoice", "financial"]
    is_financial = any(indicator in desc_lower for indicator in financial_indicators)

    # Privilege escalation detection (ARCH-002 enhancement)
    privilege_indicators = ["admin", "administrator", "root", "sudo", "privilege", "privileges", "superuser", "elevated"]
    is_privilege_escalation = any(indicator in desc_lower for indicator in privilege_indicators)

    # Apply context-based elevation
    if is_production or has_sensitive_data or is_financial or is_privilege_escalation:
        elevation_reasons = []
        if is_production:
            elevation_reasons.append("production_system")
        if has_sensitive_data:
            elevation_reasons.append("sensitive_data")
        if is_financial:
            elevation_reasons.append("financial_transaction")
        if is_privilege_escalation:
            elevation_reasons.append("privilege_escalation")

        # Elevate risk level
        if result["risk_level"] == "low":
            result["risk_level"] = "medium"
            risk_elevation_reason = " + ".join(elevation_reasons)
            _risk_assessment_stats["context_elevations"] += 1

            logger.info(
                f"⬆️  ARCH-002: Risk elevated from low to medium - "
                f"action_type='{action_type}', reasons={elevation_reasons}"
            )

        elif result["risk_level"] == "medium":
            result["risk_level"] = "high"
            risk_elevation_reason = " + ".join(elevation_reasons)
            _risk_assessment_stats["context_elevations"] += 1
            _risk_assessment_stats["high_risk_detections"] += 1

            logger.info(
                f"⬆️  ARCH-002: Risk elevated from medium to high - "
                f"action_type='{action_type}', reasons={elevation_reasons}"
            )

            # Update recommendation to reflect elevation
            result["recommendation"] = (
                f"{result['recommendation']} "
                f"ELEVATED: {', '.join(elevation_reasons).replace('_', ' ').title()} detected."
            )

    # ARCH-001: Add CVSS v3.1 quantitative scoring (if db session provided)
    if db is not None:
        try:
            from services.cvss_auto_mapper import cvss_auto_mapper

            # Build context from enrichment + provided context (ARCH-003 enhanced)
            cvss_context = context or {}
            cvss_context.update({
                "description": description,  # ARCH-003: Pass description for better normalization
                "risk_level": result["risk_level"],
                "contains_pii": any(x in desc_lower for x in ["pii", "personal", "credit card", "ssn", "patient"]),
                "production_system": any(x in desc_lower for x in ["production", "prod", "live"]),
                "financial_transaction": any(x in desc_lower for x in ["payment", "transaction", "billing", "stripe", "paypal"]),  # ARCH-003: NEW
                "requires_admin": result["risk_level"] == "high"
            })

            # Calculate CVSS score (this will also store in cvss_assessments table if action_id provided)
            if action_id is not None:
                cvss_result = cvss_auto_mapper.auto_assess_action(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    context=cvss_context
                )
            else:
                # If no action_id yet, just calculate metrics without storing (ARCH-003 enhanced)
                from services.cvss_calculator import cvss_calculator
                normalized_type = cvss_auto_mapper._normalize_action_type(action_type, description)  # ARCH-003: Pass description
                base_metrics = cvss_auto_mapper.ACTION_MAPPINGS.get(
                    normalized_type,
                    cvss_auto_mapper._get_default_metrics()
                )
                adjusted_metrics = cvss_auto_mapper._adjust_for_context(base_metrics, cvss_context)
                cvss_result = cvss_calculator.calculate_base_score(adjusted_metrics)

            # Add CVSS fields to result
            result["cvss_score"] = cvss_result["base_score"]
            result["cvss_severity"] = cvss_result["severity"]
            result["cvss_vector"] = cvss_result["vector_string"]

            logger.info(
                f"CVSS enrichment: {action_type} -> "
                f"Score {cvss_result['base_score']} ({cvss_result['severity']})"
            )

        except Exception as e:
            # Graceful fallback: if CVSS fails, continue with keyword matching only
            logger.warning(f"CVSS enrichment failed for {action_type}: {e}, using keyword matching only")
            result["cvss_score"] = None
            result["cvss_severity"] = None
            result["cvss_vector"] = None

    else:
        # No database session provided - return keyword matching only (backward compatible)
        result["cvss_score"] = None
        result["cvss_severity"] = None
        result["cvss_vector"] = None

    # ========================================================================
    # ENTERPRISE LOGGING & AUDIT TRAIL (ARCH-002)
    # ========================================================================

    # Final assessment logging
    logger.info(
        f"📊 ARCH-002: Risk assessment complete - "
        f"action_type='{action_type}', "
        f"risk_level='{result['risk_level']}', "
        f"method='{assessment_method}', "
        f"mitre_tactic='{result.get('mitre_tactic')}', "
        f"nist_control='{result.get('nist_control')}'"
    )

    # Log statistics periodically (every 100 assessments)
    if _risk_assessment_stats["total_assessments"] % 100 == 0:
        logger.info(
            f"📈 ARCH-002: Risk Assessment Statistics - "
            f"Total: {_risk_assessment_stats['total_assessments']}, "
            f"High-Risk: {_risk_assessment_stats['high_risk_detections']}, "
            f"Action-Type Matches: {_risk_assessment_stats['action_type_matches']}, "
            f"Keyword Matches: {_risk_assessment_stats['keyword_matches']}, "
            f"Context Elevations: {_risk_assessment_stats['context_elevations']}"
        )

    # Add assessment metadata to result (for debugging and audit)
    result["_assessment_metadata"] = {
        "method": assessment_method,
        "elevation_reason": risk_elevation_reason,
        "original_risk": original_risk,
        "version": "ARCH-002"
    }

    return result


# ============================================================================
# ARCH-002: ENTERPRISE MONITORING FUNCTIONS
# ============================================================================

def get_risk_assessment_stats() -> Dict:
    """
    Get current risk assessment statistics for monitoring and dashboards.

    Returns:
        Dictionary with assessment statistics
    """
    return dict(_risk_assessment_stats)


def reset_risk_assessment_stats() -> None:
    """
    Reset risk assessment statistics (for testing or periodic resets).
    """
    global _risk_assessment_stats
    _risk_assessment_stats = {
        "total_assessments": 0,
        "high_risk_detections": 0,
        "action_type_matches": 0,
        "keyword_matches": 0,
        "context_elevations": 0
    }
    logger.info("🔄 ARCH-002: Risk assessment statistics reset")
