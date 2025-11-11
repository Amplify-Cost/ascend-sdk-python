# enrichment.py - Enterprise security enrichment with CVSS v3.1 integration
"""
ARCH-001: Enhanced with CVSS v3.1 quantitative risk scoring
ARCH-002: Enterprise-grade risk assessment with action-type classification
ARCH-003: Database-driven MITRE/NIST mappings (Phase 2)

This module provides security enrichment for agent actions including:
- Action-type-based risk classification (NEW - ARCH-002)
- Expanded keyword-based pattern matching (ENHANCED - ARCH-002)
- Context-aware risk elevation (NEW - ARCH-002)
- MITRE ATT&CK tactic/technique mapping (DATABASE-DRIVEN - ARCH-003 Phase 2)
- NIST control mapping (DATABASE-DRIVEN - ARCH-003 Phase 2)
- CVSS v3.1 quantitative risk scoring (ARCH-001)
- Comprehensive audit logging (ARCH-002)

Enterprise Standards:
- Backward compatible with existing integrations
- Comprehensive error handling and graceful fallbacks
- Detailed audit logging for compliance
- Performance optimized pattern matching
"""

import logging
from typing import Dict, Optional, Set, Tuple, List
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


# ============================================================================
# ARCH-003 Phase 2: DATABASE-DRIVEN MITRE/NIST MAPPINGS
# ============================================================================

def _get_mitre_nist_from_database(
    db: Session,
    action_id: int,
    action_type: str,
    normalized_action_type: str
) -> Tuple[str, str, str, str]:
    """
    Query database for MITRE/NIST mappings based on action type.

    ARCH-003 Phase 2: Replaces hardcoded mappings with database-driven queries.
    Uses existing mitre_mapper and nist_mapper services.

    Args:
        db: Database session
        action_id: Agent action ID (required for mapping storage)
        action_type: Original action type
        normalized_action_type: Normalized action type from risk assessment

    Returns:
        Tuple of (mitre_tactic, mitre_technique, nist_control, nist_description)
        Falls back to default values if database query fails.
    """
    try:
        from services.mitre_mapper import mitre_mapper
        from services.nist_mapper import nist_mapper

        # Default fallback values (backward compatible)
        mitre_tactic = "Execution"
        mitre_technique = "T1059 - Command and Scripting Interpreter"
        nist_control = "SI-3"
        nist_description = "Malicious Code Protection"

        # Query MITRE mappings from database
        try:
            mitre_results = mitre_mapper.map_action_to_techniques(
                db=db,
                action_id=action_id,
                action_type=normalized_action_type,
                context={}
            )

            if mitre_results and len(mitre_results) > 0:
                # Use highest confidence mapping (first result)
                top_mitre = mitre_results[0]
                mitre_tactic = top_mitre.get("tactic", mitre_tactic)
                technique_id = top_mitre.get("technique_id", "T1059")
                technique_name = top_mitre.get("name", "Command and Scripting Interpreter")
                mitre_technique = f"{technique_id} - {technique_name}"

                logger.info(
                    f"ARCH-003 Phase 2: MITRE mapping from database - "
                    f"action_id={action_id}, tactic='{mitre_tactic}', technique='{mitre_technique}'"
                )
            else:
                logger.debug(f"ARCH-003 Phase 2: No MITRE mappings found for {normalized_action_type}, using defaults")

        except Exception as e:
            logger.warning(f"ARCH-003 Phase 2: MITRE query failed: {e}, using defaults")

        # Query NIST mappings from database
        try:
            nist_results = nist_mapper.map_action_to_controls(
                db=db,
                action_id=action_id,
                action_type=normalized_action_type,
                auto_assess=True
            )

            if nist_results and len(nist_results) > 0:
                # Use PRIMARY relevance mapping (first result)
                top_nist = nist_results[0]
                nist_control = top_nist.get("control_id", nist_control)
                nist_description = top_nist.get("title", nist_description)

                logger.info(
                    f"ARCH-003 Phase 2: NIST mapping from database - "
                    f"action_id={action_id}, control='{nist_control}', title='{nist_description}'"
                )
            else:
                logger.debug(f"ARCH-003 Phase 2: No NIST mappings found for {normalized_action_type}, using defaults")

        except Exception as e:
            logger.warning(f"ARCH-003 Phase 2: NIST query failed: {e}, using defaults")

        return (mitre_tactic, mitre_technique, nist_control, nist_description)

    except Exception as e:
        # Critical error - return safe defaults
        logger.error(f"ARCH-003 Phase 2: Critical error in MITRE/NIST query: {e}, using safe defaults")
        return (
            "Execution",
            "T1059 - Command and Scripting Interpreter",
            "SI-3",
            "Malicious Code Protection"
        )


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

        # ARCH-003 Phase 2: Get MITRE/NIST from database if available
        if db is not None and action_id is not None:
            mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                db=db,
                action_id=action_id,
                action_type=action_type,
                normalized_action_type=action_lower
            )
        else:
            # Fallback to defaults if no database session
            mitre_tactic = "Impact"
            mitre_technique = "T1485 - Data Manipulation"
            nist_control = "SI-4"
            nist_description = "Information System Monitoring"

        # Determine specific recommendation based on action type
        if action_lower in ["database_write", "database_delete", "schema_change"]:
            recommendation = "Database operations require approval. Review change management procedures and ensure backup exists."
        elif action_lower in ["data_export", "data_exfiltration"]:
            recommendation = "Data export detected. Verify authorization and ensure compliance with data protection policies."
        elif action_lower in ["user_create", "user_provision", "permission_grant", "access_grant"]:
            recommendation = "User/permission modification requires approval. Verify principle of least privilege."
        elif action_lower in ["secret_access", "credential_access"]:
            recommendation = "Credential access detected. Ensure proper secrets management and rotation policies."
        else:
            recommendation = "High-risk action requires approval and security review."

        result = {
            "risk_level": "high",
            "mitre_tactic": mitre_tactic,
            "mitre_technique": mitre_technique,
            "nist_control": nist_control,
            "nist_description": nist_description,
            "recommendation": recommendation
        }

        logger.info(
            f"✅ ARCH-002/ARCH-003: High-risk action type detected - "
            f"action_type='{action_type}', risk_level='high', "
            f"method='action_type_classification', db_mappings={'yes' if (db and action_id) else 'no'}"
        )

    # Check medium-risk action types
    elif action_lower in MEDIUM_RISK_ACTION_TYPES:
        assessment_method = "action_type_medium_risk"
        _risk_assessment_stats["action_type_matches"] += 1

        # ARCH-003 Phase 2: Get MITRE/NIST from database if available
        if db is not None and action_id is not None:
            mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                db=db,
                action_id=action_id,
                action_type=action_type,
                normalized_action_type=action_lower
            )
        else:
            # Fallback to defaults
            mitre_tactic = "Execution"
            mitre_technique = "T1059 - Command and Scripting Interpreter"
            nist_control = "SI-3"
            nist_description = "Malicious Code Protection"

        result = {
            "risk_level": "medium",
            "mitre_tactic": mitre_tactic,
            "mitre_technique": mitre_technique,
            "nist_control": nist_control,
            "nist_description": nist_description,
            "recommendation": "System modification requires monitoring. Validate legitimacy and maintain audit logs."
        }

        logger.info(
            f"⚠️  ARCH-002/ARCH-003: Medium-risk action type detected - "
            f"action_type='{action_type}', risk_level='medium', db_mappings={'yes' if (db and action_id) else 'no'}"
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

            # Determine normalized action type based on keywords
            if "exfiltrat" in action_lower or "leak" in desc_lower:
                normalized_type = "data_exfiltration"
                recommendation = "Immediately investigate potential data exfiltration and block unauthorized data transfers."
            elif "privilege" in action_lower or "escalat" in desc_lower:
                normalized_type = "privilege_escalation"
                recommendation = "Review user permissions and investigate unauthorized privilege escalation attempts."
            elif any(x in action_lower or x in desc_lower for x in ["payment", "transaction", "financial"]):
                normalized_type = "financial_transaction"
                recommendation = "Financial transaction detected. Verify authorization and ensure PCI-DSS compliance."
            elif any(x in action_lower or x in desc_lower for x in ["database", "schema", "drop", "truncate"]):
                normalized_type = "database_write"
                recommendation = "Database operation detected. Review change management and ensure backup exists."
            else:
                normalized_type = "impact"
                recommendation = "Investigate high-risk activity and implement additional security controls."

            # ARCH-003 Phase 2: Get MITRE/NIST from database if available
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type=normalized_type
                )
            else:
                # Fallback defaults
                mitre_tactic = "Impact"
                mitre_technique = "T1485 - Data Destruction"
                nist_control = "SI-4"
                nist_description = "Information System Monitoring"

            result = {
                "risk_level": "high",
                "mitre_tactic": mitre_tactic,
                "mitre_technique": mitre_technique,
                "nist_control": nist_control,
                "nist_description": nist_description,
                "recommendation": recommendation
            }

        # Check for medium-risk indicators
        elif any(pattern in action_lower or pattern in desc_lower for pattern in medium_risk_patterns):
            # Determine normalized action type based on keywords
            if "network" in action_lower or "scan" in desc_lower:
                normalized_type = "network_monitoring"
                recommendation = "Monitor network scanning activities and ensure they are authorized."
            elif "credential" in action_lower or "password" in desc_lower:
                normalized_type = "credential_access"
                recommendation = "Review credential access patterns and strengthen authentication mechanisms."
            else:
                normalized_type = "execution"
                recommendation = "Monitor execution activities and validate legitimacy of commands."

            # ARCH-003 Phase 2: Get MITRE/NIST from database if available
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type=normalized_type
                )
            else:
                # Fallback defaults
                mitre_tactic = "Execution"
                mitre_technique = "T1059 - Command and Scripting Interpreter"
                nist_control = "SI-3"
                nist_description = "Malicious Code Protection"

            result = {
                "risk_level": "medium",
                "mitre_tactic": mitre_tactic,
                "mitre_technique": mitre_technique,
                "nist_control": nist_control,
                "nist_description": nist_description,
                "recommendation": recommendation
            }

        # Default to low risk if no patterns matched
        else:
            # ARCH-003 Phase 2: Get MITRE/NIST from database if available
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type="execution"
                )
            else:
                # Fallback defaults
                mitre_tactic = "Execution"
                mitre_technique = "T1204 - User Execution"
                nist_control = "AU-6"
                nist_description = "Audit Review, Analysis, and Reporting"

            result = {
                "risk_level": "low",
                "mitre_tactic": mitre_tactic,
                "mitre_technique": mitre_technique,
                "nist_control": nist_control,
                "nist_description": nist_description,
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
