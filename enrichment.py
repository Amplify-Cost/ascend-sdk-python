# enrichment.py - Enterprise security enrichment with CVSS v3.1 integration
"""
ARCH-001: Enhanced with CVSS v3.1 quantitative risk scoring
ARCH-002: Enterprise-grade risk assessment with action-type classification
ARCH-003: Database-driven MITRE/NIST mappings (Phase 2) - DEPRECATED
ARCH-004: Enterprise-grade NIST/MITRE compliance mapping system (CURRENT)

This module provides security enrichment for agent actions including:
- Action-type-based risk classification (ARCH-002)
- Expanded keyword-based pattern matching (ARCH-002)
- Context-aware risk elevation (ARCH-002)
- Enterprise NIST SP 800-53 control mapping (NEW - ARCH-004)
- Enterprise MITRE ATT&CK tactic/technique mapping (NEW - ARCH-004)
- Context-aware compliance override logic (NEW - ARCH-004)
- CVSS v3.1 quantitative risk scoring (ARCH-001)
- Comprehensive audit logging (ARCH-002)

ARCH-004 Enhancements:
- Action-specific NIST/MITRE mappings (not generic)
- Context-aware overrides based on description keywords
- Official NIST SP 800-53 controls and MITRE ATT&CK IDs
- Priority mapping: Context > Action Type > Default
- Comprehensive compliance logging for audit trails

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
# ARCH-004: ENTERPRISE-GRADE NIST/MITRE COMPLIANCE MAPPING
# ============================================================================

# Enterprise NIST SP 800-53 and MITRE ATT&CK Compliance Mappings
# This provides action-specific, context-aware compliance controls
ENTERPRISE_COMPLIANCE_MAPPINGS = {
    "database_write": {
        "nist_control": "AC-3",
        "nist_family": "Access Control",
        "nist_description": "Access Enforcement",
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1003",
        "mitre_technique_name": "OS Credential Dumping"
    },
    "database_read": {
        "nist_control": "AU-2",
        "nist_family": "Audit and Accountability",
        "nist_description": "Audit Events",
        "mitre_tactic": "TA0009",
        "mitre_tactic_name": "Collection",
        "mitre_technique": "T1005",
        "mitre_technique_name": "Data from Local System"
    },
    "database_delete": {
        "nist_control": "AC-3",
        "nist_family": "Access Control",
        "nist_description": "Access Enforcement",
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1485",
        "mitre_technique_name": "Data Destruction"
    },
    "api_call": {
        "nist_control": "SI-3",
        "nist_family": "System and Information Integrity",
        "nist_description": "Malicious Code Protection",
        "mitre_tactic": "TA0002",
        "mitre_tactic_name": "Execution",
        "mitre_technique": "T1059",
        "mitre_technique_name": "Command and Scripting Interpreter"
    },
    "financial_transaction": {
        "nist_control": "AU-9",
        "nist_family": "Audit and Accountability",
        "nist_description": "Protection of Audit Information",
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1565",
        "mitre_technique_name": "Data Manipulation"
    },
    "credentials_access": {
        "nist_control": "IA-5",
        "nist_family": "Identification and Authentication",
        "nist_description": "Authenticator Management",
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1552",
        "mitre_technique_name": "Unsecured Credentials"
    },
    "system_modification": {
        "nist_control": "CM-3",
        "nist_family": "Configuration Management",
        "nist_description": "Configuration Change Control",
        "mitre_tactic": "TA0005",
        "mitre_tactic_name": "Defense Evasion",
        "mitre_technique": "T1562",
        "mitre_technique_name": "Impair Defenses"
    },
    "file_access": {
        "nist_control": "AC-4",
        "nist_family": "Access Control",
        "nist_description": "Information Flow Enforcement",
        "mitre_tactic": "TA0009",
        "mitre_tactic_name": "Collection",
        "mitre_technique": "T1005",
        "mitre_technique_name": "Data from Local System"
    },
    "file_write": {
        "nist_control": "AC-3",
        "nist_family": "Access Control",
        "nist_description": "Access Enforcement",
        "mitre_tactic": "TA0002",
        "mitre_tactic_name": "Execution",
        "mitre_technique": "T1059",
        "mitre_technique_name": "Command and Scripting Interpreter"
    },
    "privilege_escalation": {
        "nist_control": "AC-6",
        "nist_family": "Access Control",
        "nist_description": "Least Privilege",
        "mitre_tactic": "TA0004",
        "mitre_tactic_name": "Privilege Escalation",
        "mitre_technique": "T1078",
        "mitre_technique_name": "Valid Accounts"
    },
    "data_export": {
        "nist_control": "AC-4",
        "nist_family": "Access Control",
        "nist_description": "Information Flow Enforcement",
        "mitre_tactic": "TA0010",
        "mitre_tactic_name": "Exfiltration",
        "mitre_technique": "T1041",
        "mitre_technique_name": "Exfiltration Over C2 Channel"
    },
    "data_exfiltration": {
        "nist_control": "AC-4",
        "nist_family": "Access Control",
        "nist_description": "Information Flow Enforcement",
        "mitre_tactic": "TA0010",
        "mitre_tactic_name": "Exfiltration",
        "mitre_technique": "T1041",
        "mitre_technique_name": "Exfiltration Over C2 Channel"
    },
    "schema_change": {
        "nist_control": "CM-3",
        "nist_family": "Configuration Management",
        "nist_description": "Configuration Change Control",
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1485",
        "mitre_technique_name": "Data Destruction"
    },
    "user_create": {
        "nist_control": "AC-2",
        "nist_family": "Access Control",
        "nist_description": "Account Management",
        "mitre_tactic": "TA0003",
        "mitre_tactic_name": "Persistence",
        "mitre_technique": "T1136",
        "mitre_technique_name": "Create Account"
    },
    "user_provision": {
        "nist_control": "AC-2",
        "nist_family": "Access Control",
        "nist_description": "Account Management",
        "mitre_tactic": "TA0003",
        "mitre_tactic_name": "Persistence",
        "mitre_technique": "T1136",
        "mitre_technique_name": "Create Account"
    },
    "permission_grant": {
        "nist_control": "AC-6",
        "nist_family": "Access Control",
        "nist_description": "Least Privilege",
        "mitre_tactic": "TA0004",
        "mitre_tactic_name": "Privilege Escalation",
        "mitre_technique": "T1098",
        "mitre_technique_name": "Account Manipulation"
    },
    "access_grant": {
        "nist_control": "AC-3",
        "nist_family": "Access Control",
        "nist_description": "Access Enforcement",
        "mitre_tactic": "TA0004",
        "mitre_tactic_name": "Privilege Escalation",
        "mitre_technique": "T1098",
        "mitre_technique_name": "Account Manipulation"
    },
    "secret_access": {
        "nist_control": "IA-5",
        "nist_family": "Identification and Authentication",
        "nist_description": "Authenticator Management",
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1552",
        "mitre_technique_name": "Unsecured Credentials"
    },
    "credential_access": {
        "nist_control": "IA-5",
        "nist_family": "Identification and Authentication",
        "nist_description": "Authenticator Management",
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1552",
        "mitre_technique_name": "Unsecured Credentials"
    },
    "network_access": {
        "nist_control": "SC-7",
        "nist_family": "System and Communications Protection",
        "nist_description": "Boundary Protection",
        "mitre_tactic": "TA0011",
        "mitre_tactic_name": "Command and Control",
        "mitre_technique": "T1071",
        "mitre_technique_name": "Application Layer Protocol"
    },
    "config_change": {
        "nist_control": "CM-3",
        "nist_family": "Configuration Management",
        "nist_description": "Configuration Change Control",
        "mitre_tactic": "TA0005",
        "mitre_tactic_name": "Defense Evasion",
        "mitre_technique": "T1562",
        "mitre_technique_name": "Impair Defenses"
    },
    "service_restart": {
        "nist_control": "SI-12",
        "nist_family": "System and Information Integrity",
        "nist_description": "Information Handling and Retention",
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1489",
        "mitre_technique_name": "Service Stop"
    }
}


def get_enterprise_compliance_mapping(action_type: str, description: str = "") -> dict:
    """
    Enterprise-grade NIST/MITRE mapping with context awareness.

    ARCH-004: Provides action-specific and context-aware compliance mappings
    using official NIST SP 800-53 controls and MITRE ATT&CK framework.

    Args:
        action_type: Type of agent action (e.g., "database_write", "api_call")
        description: Action description for context-based overrides

    Returns:
        Dictionary with NIST and MITRE compliance mappings
    """
    description_lower = description.lower() if description else ""

    # Context-based overrides for more specific mappings (priority order)
    # Financial transactions get AU-9 (Audit Protection) + TA0040 (Impact)
    if any(keyword in description_lower for keyword in ["payment", "financial", "transaction", "billing", "stripe", "paypal", "invoice", "charge", "refund"]):
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("financial_transaction")
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'financial_transaction' detected - action_type={action_type}, NIST={mapping['nist_control']}, MITRE={mapping['mitre_tactic']}")
        return mapping

    # Credential/secret access gets IA-5 (Authenticator Management) + TA0006 (Credential Access)
    if any(keyword in description_lower for keyword in ["credential", "password", "secret", "token", "api key", "private key", "auth"]):
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("credentials_access")
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'credentials_access' detected - action_type={action_type}, NIST={mapping['nist_control']}, MITRE={mapping['mitre_tactic']}")
        return mapping

    # Privilege escalation gets AC-6 (Least Privilege) + TA0004 (Privilege Escalation)
    if any(keyword in description_lower for keyword in ["privilege", "admin", "administrator", "sudo", "root", "superuser", "elevated", "escalate"]):
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("privilege_escalation")
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'privilege_escalation' detected - action_type={action_type}, NIST={mapping['nist_control']}, MITRE={mapping['mitre_tactic']}")
        return mapping

    # Data exfiltration gets AC-4 (Information Flow) + TA0010 (Exfiltration)
    if any(keyword in description_lower for keyword in ["exfiltrate", "exfil", "leak", "steal", "copy sensitive", "export"]):
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("data_exfiltration")
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'data_exfiltration' detected - action_type={action_type}, NIST={mapping['nist_control']}, MITRE={mapping['mitre_tactic']}")
        return mapping

    # Schema changes get CM-3 (Configuration Change) + TA0040 (Impact)
    if any(keyword in description_lower for keyword in ["schema", "alter table", "drop table", "create table", "truncate"]):
        mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("schema_change")
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Context override 'schema_change' detected - action_type={action_type}, NIST={mapping['nist_control']}, MITRE={mapping['mitre_tactic']}")
        return mapping

    # Use action type mapping (normalized to lowercase)
    action_lower = action_type.lower()
    mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get(action_lower)

    if mapping:
        logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Action type mapping - action_type={action_type}, NIST={mapping['nist_control']} ({mapping['nist_family']}), MITRE={mapping['mitre_tactic']} ({mapping['mitre_tactic_name']})")
        return mapping

    # Default fallback for unknown action types
    default_mapping = ENTERPRISE_COMPLIANCE_MAPPINGS.get("api_call")
    logger.info(f"ARCH-004 ENTERPRISE COMPLIANCE: Using default mapping for unknown action_type={action_type}, NIST={default_mapping['nist_control']}, MITRE={default_mapping['mitre_tactic']}")
    return default_mapping


# ============================================================================
# ARCH-003 Phase 2: DATABASE-DRIVEN MITRE/NIST MAPPINGS (LEGACY)
# ============================================================================

def _get_mitre_nist_from_database(
    db: Session,
    action_id: int,
    action_type: str,
    normalized_action_type: str,
    description: str = ""
) -> Tuple[str, str, str, str]:
    """
    Get MITRE/NIST mappings with enterprise-grade accuracy.

    ARCH-004: Uses enterprise compliance mappings as primary source,
    with database queries as secondary enrichment (backward compatible).

    Priority:
    1. Enterprise compliance mappings (ARCH-004) - Accurate, context-aware
    2. Database queries (ARCH-003 Phase 2) - Legacy, fallback only

    Args:
        db: Database session
        action_id: Agent action ID (required for mapping storage)
        action_type: Original action type
        normalized_action_type: Normalized action type from risk assessment
        description: Action description for context-aware mapping

    Returns:
        Tuple of (mitre_tactic, mitre_technique, nist_control, nist_description)
    """
    try:
        # ====================================================================
        # ARCH-004: PRIMARY SOURCE - Enterprise Compliance Mappings
        # ====================================================================

        # Get enterprise-grade mapping (context-aware, action-specific)
        enterprise_mapping = get_enterprise_compliance_mapping(
            action_type=normalized_action_type or action_type,
            description=description
        )

        # ARCH-004 ENTERPRISE: Return IDs for database storage, names for display
        # Frontend and database expect IDs (TA0006, T1003) not names
        mitre_tactic = enterprise_mapping["mitre_tactic"]  # "TA0006" not "Credential Access"
        mitre_technique = enterprise_mapping["mitre_technique"]  # "T1003" not "T1003 - OS Credential Dumping"
        nist_control = enterprise_mapping["nist_control"]
        nist_description = enterprise_mapping["nist_description"]

        logger.info(
            f"ARCH-004: Enterprise compliance mapping applied - "
            f"action_id={action_id}, action_type='{normalized_action_type}', "
            f"NIST={nist_control} ({enterprise_mapping['nist_family']}), "
            f"MITRE={enterprise_mapping['mitre_tactic']} ({mitre_tactic})"
        )

        # ====================================================================
        # ARCH-003 Phase 2: SECONDARY SOURCE - Database enrichment (optional)
        # ====================================================================

        # Optionally query database for additional context (non-critical)
        # This maintains backward compatibility but doesn't override enterprise mappings
        try:
            from services.mitre_mapper import mitre_mapper
            from services.nist_mapper import nist_mapper

            # Query database for supplementary information (log only, don't override)
            try:
                mitre_results = mitre_mapper.map_action_to_techniques(
                    db=db,
                    action_id=action_id,
                    action_type=normalized_action_type,
                    context={}
                )
                if mitre_results and len(mitre_results) > 0:
                    logger.debug(
                        f"ARCH-003 Phase 2: Database MITRE suggestion available "
                        f"(not used, enterprise mapping takes priority)"
                    )
            except Exception as e:
                logger.debug(f"ARCH-003 Phase 2: Database MITRE query skipped: {e}")

            try:
                nist_results = nist_mapper.map_action_to_controls(
                    db=db,
                    action_id=action_id,
                    action_type=normalized_action_type,
                    auto_assess=True
                )
                if nist_results and len(nist_results) > 0:
                    logger.debug(
                        f"ARCH-003 Phase 2: Database NIST suggestion available "
                        f"(not used, enterprise mapping takes priority)"
                    )
            except Exception as e:
                logger.debug(f"ARCH-003 Phase 2: Database NIST query skipped: {e}")

        except Exception as e:
            logger.debug(f"ARCH-003 Phase 2: Database enrichment skipped: {e}")

        return (mitre_tactic, mitre_technique, nist_control, nist_description)

    except Exception as e:
        # ARCH-004 ENTERPRISE: Critical error - return safe defaults (IDs not names)
        logger.error(f"ARCH-004: Critical error in compliance mapping: {e}, using safe defaults")
        default = ENTERPRISE_COMPLIANCE_MAPPINGS.get("api_call")
        return (
            default["mitre_tactic"],  # Return ID: "TA0002"
            default["mitre_technique"],  # Return ID: "T1059"
            default["nist_control"],
            default["nist_description"]
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

        # ARCH-004: Get MITRE/NIST from enterprise mappings (with database enrichment)
        if db is not None and action_id is not None:
            mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                db=db,
                action_id=action_id,
                action_type=action_type,
                normalized_action_type=action_lower,
                description=description
            )
        else:
            # ARCH-004: Fallback to enterprise mappings (no database session)
            enterprise_mapping = get_enterprise_compliance_mapping(
                action_type=action_lower,
                description=description
            )
            # ARCH-004 ENTERPRISE: Return IDs for database/frontend compatibility
            mitre_tactic = enterprise_mapping["mitre_tactic"]
            mitre_technique = enterprise_mapping["mitre_technique"]
            nist_control = enterprise_mapping["nist_control"]
            nist_description = enterprise_mapping["nist_description"]

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

        # ARCH-004: Get MITRE/NIST from enterprise mappings (with database enrichment)
        if db is not None and action_id is not None:
            mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                db=db,
                action_id=action_id,
                action_type=action_type,
                normalized_action_type=action_lower,
                description=description
            )
        else:
            # ARCH-004: Fallback to enterprise mappings (no database session)
            enterprise_mapping = get_enterprise_compliance_mapping(
                action_type=action_lower,
                description=description
            )
            # ARCH-004 ENTERPRISE: Return IDs for database/frontend compatibility
            mitre_tactic = enterprise_mapping["mitre_tactic"]
            mitre_technique = enterprise_mapping["mitre_technique"]
            nist_control = enterprise_mapping["nist_control"]
            nist_description = enterprise_mapping["nist_description"]

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

            # ARCH-004: Get MITRE/NIST from enterprise mappings (with database enrichment)
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type=normalized_type,
                    description=description
                )
            else:
                # ARCH-004: Fallback to enterprise mappings (no database session)
                enterprise_mapping = get_enterprise_compliance_mapping(
                    action_type=normalized_type,
                    description=description
                )
                mitre_tactic = enterprise_mapping["mitre_tactic_name"]
                mitre_technique = f"{enterprise_mapping['mitre_technique']} - {enterprise_mapping['mitre_technique_name']}"
                nist_control = enterprise_mapping["nist_control"]
                nist_description = enterprise_mapping["nist_description"]

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

            # ARCH-004: Get MITRE/NIST from enterprise mappings (with database enrichment)
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type=normalized_type,
                    description=description
                )
            else:
                # ARCH-004: Fallback to enterprise mappings (no database session)
                enterprise_mapping = get_enterprise_compliance_mapping(
                    action_type=normalized_type,
                    description=description
                )
                mitre_tactic = enterprise_mapping["mitre_tactic_name"]
                mitre_technique = f"{enterprise_mapping['mitre_technique']} - {enterprise_mapping['mitre_technique_name']}"
                nist_control = enterprise_mapping["nist_control"]
                nist_description = enterprise_mapping["nist_description"]

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
            # ARCH-004: Get MITRE/NIST from enterprise mappings (with database enrichment)
            if db is not None and action_id is not None:
                mitre_tactic, mitre_technique, nist_control, nist_description = _get_mitre_nist_from_database(
                    db=db,
                    action_id=action_id,
                    action_type=action_type,
                    normalized_action_type="execution",
                    description=description
                )
            else:
                # ARCH-004: Fallback to enterprise mappings (no database session)
                enterprise_mapping = get_enterprise_compliance_mapping(
                    action_type=action_type,
                    description=description
                )
                mitre_tactic = enterprise_mapping["mitre_tactic_name"]
                mitre_technique = f"{enterprise_mapping['mitre_technique']} - {enterprise_mapping['mitre_technique_name']}"
                nist_control = enterprise_mapping["nist_control"]
                nist_description = enterprise_mapping["nist_description"]

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
    # SEC-103: Check explicit environment parameter first, then fall back to keyword detection
    production_indicators = ["production", "prod", "live", "prd"]
    is_production = (
        (context or {}).get("environment") == "production" or  # SEC-103: Explicit SDK parameter
        any(indicator in desc_lower for indicator in production_indicators)
    )

    # Sensitive data detection
    # SEC-103: Check explicit data_sensitivity parameter first, then fall back to keyword detection
    sensitive_data_indicators = ["pii", "personal", "customer", "credit card", "ssn", "patient", "confidential"]
    sdk_data_sensitivity = (context or {}).get("data_sensitivity", "none")
    has_sensitive_data = (
        sdk_data_sensitivity in ["high_sensitivity", "pii", "sensitive"] or  # SEC-103: Explicit SDK parameter
        any(indicator in desc_lower for indicator in sensitive_data_indicators)
    )

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
        "version": "ARCH-003"  # Updated to ARCH-003 for Phase 3
    }

    # ========================================================================
    # ARCH-003 Phase 3: AI-GENERATED RECOMMENDATIONS
    # ========================================================================

    # Generate AI-powered recommendation (with fallback to static)
    try:
        from services.ai_recommendation_generator import ai_recommendation_generator

        # Save original static recommendation as fallback
        static_recommendation = result.get("recommendation", "")

        # Generate AI recommendation
        ai_recommendation = ai_recommendation_generator.generate_recommendation(
            action_type=action_type,
            description=description,
            risk_level=result["risk_level"],
            cvss_score=result.get("cvss_score"),
            mitre_tactic=result.get("mitre_tactic"),
            mitre_technique=result.get("mitre_technique"),
            nist_control=result.get("nist_control"),
            context=cvss_context if db is not None else context
        )

        # Use AI recommendation if generated successfully
        if ai_recommendation and len(ai_recommendation) > 10:
            result["recommendation"] = ai_recommendation
            result["_assessment_metadata"]["ai_generated"] = True
            logger.info(f"ARCH-003 Phase 3: AI recommendation generated for {action_type}")
        else:
            # Keep static recommendation
            result["_assessment_metadata"]["ai_generated"] = False
            logger.debug(f"ARCH-003 Phase 3: Using static recommendation for {action_type}")

    except Exception as e:
        # Graceful fallback: keep static recommendation on any error
        logger.warning(f"ARCH-003 Phase 3: AI recommendation generation failed: {e}, using static")
        result["_assessment_metadata"]["ai_generated"] = False

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
