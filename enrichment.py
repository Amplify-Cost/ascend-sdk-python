# enrichment.py - Enterprise security enrichment with CVSS v3.1 integration
"""
ARCH-001: Enhanced with CVSS v3.1 quantitative risk scoring

This module provides security enrichment for agent actions including:
- Keyword-based MITRE ATT&CK tactic/technique mapping (existing)
- NIST control mapping (existing)
- CVSS v3.1 quantitative risk scoring (NEW)
- Context-aware metric assignment (NEW)
"""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


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

    # Convert to lowercase for case-insensitive matching
    action_lower = action_type.lower()
    desc_lower = (description or "").lower()

    # High-risk patterns
    high_risk_patterns = [
        "data_exfiltration", "exfiltrate", "leak", "steal", "copy_sensitive",
        "privilege_escalation", "escalate", "admin", "root", "sudo",
        "lateral_movement", "persistence", "backdoor", "malware"
    ]

    # Medium-risk patterns
    medium_risk_patterns = [
        "network_scan", "port_scan", "reconnaissance", "discovery",
        "credential_access", "password", "token", "key",
        "execution", "command", "script", "shell"
    ]

    # Determine base enrichment (existing keyword matching)
    result = None

    # Check for high-risk indicators
    if any(pattern in action_lower or pattern in desc_lower for pattern in high_risk_patterns):
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

    # Default to low risk
    else:
        result = {
            "risk_level": "low",
            "mitre_tactic": "Execution",
            "mitre_technique": "T1204 - User Execution",
            "nist_control": "AU-6",
            "nist_description": "Audit Review, Analysis, and Reporting",
            "recommendation": "Continue monitoring agent activities and maintain audit logs."
        }

    # ARCH-001: Add CVSS v3.1 quantitative scoring (if db session provided)
    if db is not None:
        try:
            from services.cvss_auto_mapper import cvss_auto_mapper

            # Build context from enrichment + provided context
            cvss_context = context or {}
            cvss_context.update({
                "risk_level": result["risk_level"],
                "contains_pii": any(x in desc_lower for x in ["pii", "personal", "credit card", "ssn", "patient"]),
                "production_system": any(x in desc_lower for x in ["production", "prod", "live"]),
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
                # If no action_id yet, just calculate metrics without storing
                from services.cvss_calculator import cvss_calculator
                normalized_type = cvss_auto_mapper._normalize_action_type(action_type)
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

    return result
