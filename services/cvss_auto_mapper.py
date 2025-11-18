"""
CVSS Auto-Mapper Service - ENTERPRISE v2.0
Automatically assigns CVSS metrics based on agent action characteristics

Industry Standards Alignment:
- NIST 800-53 Controls (AC, AU, SC, SI, etc.)
- MITRE ATT&CK Framework
- PCI-DSS 4.0 (payment/financial operations)
- SOX (financial transaction integrity)
- HIPAA (healthcare data operations)
- GDPR (personal data operations)

Enhancements v2.0:
- Comprehensive action mappings (30+ enterprise action types)
- Industry-aligned CVSS scoring (realistic risk levels)
- Separate database_read (LOW/MEDIUM) vs database_write (CRITICAL)
- AWS/Cloud infrastructure operations
- Healthcare/HIPAA-specific operations
- Network security operations
- Compliance and audit operations
- Container/K8s operations
- Secret/credential management

Engineer: OW-KAI Platform Engineering Team
Version: 2.0 (Enterprise Edition)
Date: 2025-11-18
"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from services.cvss_calculator import cvss_calculator

logger = logging.getLogger(__name__)


class CVSSAutoMapper:
    """
    Automatically maps agent actions to CVSS v3.1 metrics
    Based on action type, resource, and context

    ARCH-003 Enhancements:
    - Dynamic CVSS calculation based on context
    - Financial transaction detection
    - Production environment detection
    - PII data detection
    - Privilege escalation detection
    """

    # ============================================================================
    # ENTERPRISE ACTION MAPPINGS - Industry Standards Aligned
    # ============================================================================
    # Scoring Guidelines:
    # - CVSS 0.0-3.9 = LOW (routine operations, read-only, non-sensitive)
    # - CVSS 4.0-6.9 = MEDIUM (write operations, config changes, sensitive reads)
    # - CVSS 7.0-8.9 = HIGH (production changes, PII access, privilege changes)
    # - CVSS 9.0-10.0 = CRITICAL (data destruction, financial transactions, privilege escalation)
    # ============================================================================

    ACTION_MAPPINGS = {
        # ====================================================================
        # DATABASE OPERATIONS (Separated: Read vs Write)
        # ====================================================================

        # Database READ - CVSS 3.5-4.5 (LOW to MEDIUM)
        # Industry: NIST AC-3 (Access Enforcement), SOX read access
        "database_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",  # Reading non-PII data
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # Database WRITE - CVSS 9.0-9.3 (CRITICAL)
        # Industry: SOX data integrity, NIST SI-7 (Software Integrity)
        "database_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",  # Data integrity critical
            "availability_impact": "HIGH"
        },

        # Database DELETE - CVSS 9.0+ (CRITICAL)
        # Industry: SOX data retention, NIST SI-12 (Information Handling)
        "database_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"  # Data loss impact
        },

        # ====================================================================
        # FILE OPERATIONS
        # ====================================================================

        # File READ - CVSS 2.0-3.5 (LOW)
        # Industry: NIST AC-4 (Information Flow Enforcement)
        "file_read": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # File WRITE - CVSS 5.5-6.5 (MEDIUM)
        # Industry: NIST CM-3 (Configuration Change Control)
        "file_write": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",  # File integrity
            "availability_impact": "LOW"
        },

        # File DELETE - CVSS 6.5-7.5 (MEDIUM to HIGH)
        # Industry: NIST SI-12 (Information Handling and Retention)
        "file_delete": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"  # File loss
        },

        # ====================================================================
        # AWS/CLOUD INFRASTRUCTURE OPERATIONS
        # ====================================================================

        # AWS READ (describe, list, get) - CVSS 3.0-4.0 (LOW)
        # Industry: NIST CM-8 (System Component Inventory)
        "aws_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",  # Infrastructure metadata
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # AWS WRITE (create, update, modify) - CVSS 7.5-8.5 (HIGH)
        # Industry: NIST CM-3 (Configuration Change Control)
        "aws_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"  # Service impact
        },

        # AWS DELETE (terminate, delete) - CVSS 8.5-9.0 (HIGH to CRITICAL)
        # Industry: NIST CP-9 (System Backup), availability critical
        "aws_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"  # Resource deletion
        },

        # ====================================================================
        # FINANCIAL & PAYMENT OPERATIONS (PCI-DSS, SOX)
        # ====================================================================

        # Financial TRANSACTION - CVSS 9.0-9.8 (CRITICAL)
        # Industry: PCI-DSS Req 6.5.10, SOX financial integrity
        "financial_transaction": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",  # Payment data
            "integrity_impact": "HIGH",  # Transaction integrity
            "availability_impact": "HIGH"  # Revenue impact
        },

        # Financial REFUND - CVSS 8.5-9.0 (HIGH to CRITICAL)
        # Industry: PCI-DSS, SOX (revenue reversal)
        "financial_refund": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # ====================================================================
        # HEALTHCARE OPERATIONS (HIPAA)
        # ====================================================================

        # PHI/Medical Record READ - CVSS 6.5-7.5 (MEDIUM to HIGH)
        # Industry: HIPAA Security Rule § 164.308(a)(4)
        "healthcare_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",  # PHI is highly sensitive
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # PHI/Medical Record WRITE - CVSS 8.5-9.0 (HIGH to CRITICAL)
        # Industry: HIPAA Security Rule § 164.312(c)(1)
        "healthcare_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",  # Medical record integrity critical
            "availability_impact": "HIGH"
        },

        # ====================================================================
        # SECURITY & AUTHENTICATION OPERATIONS
        # ====================================================================

        # Privilege ESCALATION - CVSS 9.0-9.8 (CRITICAL)
        # Industry: NIST AC-2 (Account Management), MITRE ATT&CK T1078
        "privilege_escalation": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # User CREATION - CVSS 6.5-7.5 (MEDIUM to HIGH)
        # Industry: NIST AC-2 (Account Management)
        "user_create": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",  # Account integrity
            "availability_impact": "LOW"
        },

        # User DELETION - CVSS 5.5-6.5 (MEDIUM)
        # Industry: NIST AC-2 (Account Management)
        "user_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"  # User access loss
        },

        # Password RESET - CVSS 7.0-8.0 (HIGH)
        # Industry: NIST IA-5 (Authenticator Management)
        "password_reset": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",  # Account takeover risk
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },

        # Secret/Credential READ - CVSS 7.5-8.5 (HIGH)
        # Industry: NIST SC-12 (Cryptographic Key Management)
        "secret_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",  # Credential exposure
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # Secret/Credential WRITE - CVSS 8.0-9.0 (HIGH to CRITICAL)
        # Industry: NIST SC-12 (Cryptographic Key Management)
        "secret_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",  # Credential integrity
            "availability_impact": "HIGH"
        },

        # ====================================================================
        # NETWORK & INFRASTRUCTURE SECURITY
        # ====================================================================

        # Firewall MODIFICATION - CVSS 8.0-9.0 (HIGH to CRITICAL)
        # Industry: NIST SC-7 (Boundary Protection)
        "firewall_modification": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",  # Network exposure
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # Network SCAN - CVSS 3.0-4.0 (LOW)
        # Industry: NIST RA-5 (Vulnerability Scanning)
        "network_scan": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",  # Discovery activity
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # ====================================================================
        # CODE & DEPLOYMENT OPERATIONS
        # ====================================================================

        # Code DEPLOYMENT - CVSS 8.0-8.8 (HIGH)
        # Industry: NIST CM-3 (Configuration Change Control)
        "code_deployment": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",  # Code integrity
            "availability_impact": "HIGH"  # Service impact
        },

        # Container START/STOP - CVSS 6.5-7.5 (MEDIUM to HIGH)
        # Industry: NIST CM-2 (Baseline Configuration)
        "container_control": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "LOW",
            "availability_impact": "HIGH"  # Service availability
        },

        # ====================================================================
        # DATA OPERATIONS (PII, GDPR)
        # ====================================================================

        # Data EXFILTRATION - CVSS 7.5-8.5 (HIGH)
        # Industry: MITRE ATT&CK T1041, GDPR Article 33
        "data_exfiltration": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",  # Data breach
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # PII READ - CVSS 5.5-6.5 (MEDIUM)
        # Industry: GDPR Article 15, CCPA
        "pii_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",  # Personal data exposure
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # ====================================================================
        # COMPLIANCE & AUDIT OPERATIONS
        # ====================================================================

        # Audit Log READ - CVSS 3.0-4.0 (LOW)
        # Industry: NIST AU-6 (Audit Review)
        "audit_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # Audit Log MODIFICATION - CVSS 9.0-9.8 (CRITICAL)
        # Industry: NIST AU-9 (Protection of Audit Information), SOX
        "audit_modification": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",  # Audit trail integrity critical
            "availability_impact": "HIGH"
        },

        # ====================================================================
        # COMMUNICATION OPERATIONS
        # ====================================================================

        # Email SEND - CVSS 4.0-5.0 (MEDIUM)
        # Industry: NIST SC-8 (Transmission Confidentiality)
        "email_send": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "REQUIRED",  # Recipient interaction
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",  # Message content
            "availability_impact": "NONE"
        },

        # Notification SEND - CVSS 3.0-4.0 (LOW)
        # Industry: General communication
        "notification_send": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # ====================================================================
        # SYSTEM OPERATIONS
        # ====================================================================

        # System MODIFICATION - CVSS 8.5-9.3 (HIGH to CRITICAL)
        # Industry: NIST CM-3 (Configuration Change Control)
        "system_modification": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # System MONITORING - CVSS 2.0-3.0 (LOW)
        # Industry: NIST SI-4 (System Monitoring)
        "system_monitoring": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # ====================================================================
        # DEFAULT/GENERIC OPERATIONS
        # ====================================================================

        # API CALL (generic) - CVSS 4.0-5.0 (MEDIUM)
        # Industry: Baseline for unknown operations
        "api_call": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        }
    }

    def auto_assess_action(
        self,
        db: Session,
        action_id: int,
        action_type: str,
        context: Dict = None
    ) -> Dict:
        """
        Automatically create CVSS assessment for an agent action

        ARCH-003: Enhanced with context-aware adjustments before CVSS calculation
        """
        try:
            # Normalize action type (enhanced to check description)
            normalized_type = self._normalize_action_type(
                action_type,
                context.get("description", "") if context else ""
            )

            logger.info(
                f"ARCH-003: Normalized '{action_type}' → '{normalized_type}'"
            )

            # Get base metrics for this action type
            base_metrics = self.ACTION_MAPPINGS.get(
                normalized_type,
                self._get_default_metrics()
            )

            # Adjust metrics based on context (ARCH-003 enhanced)
            adjusted_metrics = self._adjust_for_context(base_metrics, context or {})

            # Calculate and store CVSS assessment
            result = cvss_calculator.assess_agent_action(
                db=db,
                action_id=action_id,
                metrics=adjusted_metrics,
                assessed_by="auto_mapper_arch003"
            )

            logger.info(
                f"ARCH-003: Auto-assessed action {action_id} ({normalized_type}): "
                f"CVSS {result['base_score']} ({result['severity']})"
            )

            return result

        except Exception as e:
            logger.error(
                f"ARCH-003: CVSS auto-assessment failed for action {action_id}: {e}",
                exc_info=True
            )
            # Graceful degradation: return medium risk
            return {
                "base_score": 5.0,
                "severity": "MEDIUM",
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N",
                "error": str(e)
            }

    def _normalize_action_type(self, action_type: str, description: str = "") -> str:
        """
        Normalize action type to enterprise-standard categories

        v2.0 Enhancement: Comprehensive action categorization with 30+ types
        Priority order ensures specific matches before generic ones
        """
        action_lower = action_type.lower()
        desc_lower = description.lower()
        combined = f"{action_lower} {desc_lower}"

        # ====================================================================
        # PRIORITY 1: Financial & Payment Operations (PCI-DSS, SOX)
        # ====================================================================
        if any(x in combined for x in ["refund", "chargeback", "reversal"]):
            return "financial_refund"

        financial_keywords = [
            "payment", "transaction", "billing", "invoice", "charge",
            "stripe", "paypal", "financial", "credit card", "debit", "purchase"
        ]
        if any(keyword in combined for keyword in financial_keywords):
            return "financial_transaction"

        # ====================================================================
        # PRIORITY 2: Healthcare/HIPAA Operations
        # ====================================================================
        healthcare_keywords = ["phi", "medical", "patient", "health", "hipaa", "ehr", "emr"]
        if any(keyword in combined for keyword in healthcare_keywords):
            if any(x in combined for x in ["write", "update", "modify", "create", "insert"]):
                return "healthcare_write"
            elif any(x in combined for x in ["read", "view", "get", "query", "select", "access"]):
                return "healthcare_read"

        # ====================================================================
        # PRIORITY 3: Security & Authentication Operations
        # ====================================================================

        # Audit log operations (check BEFORE general log operations)
        if any(x in combined for x in ["audit", "audit_log", "auditlog"]):
            if any(x in combined for x in ["modify", "delete", "tamper", "alter", "edit"]):
                return "audit_modification"
            return "audit_read"

        # Secret/credential management
        if any(x in combined for x in ["secret", "credential", "api_key", "token", "password"]):
            if any(x in combined for x in ["write", "create", "rotate", "update"]):
                return "secret_write"
            return "secret_read"

        # Password operations
        if "password" in combined and any(x in combined for x in ["reset", "change", "recover"]):
            return "password_reset"

        # Privilege escalation (check for privilege changes, NOT reads)
        privilege_keywords = [
            "admin", "administrator", "root", "sudo", "privilege", "privileges",
            "superuser", "elevated", "grant", "role", "permission"
        ]
        if any(keyword in combined for keyword in privilege_keywords):
            # Escalation: creating/modifying privileges
            if any(x in combined for x in ["create", "grant", "escalate", "elevate", "promote", "add"]):
                return "privilege_escalation"
            # User management
            if "user" in combined:
                if any(x in combined for x in ["delete", "remove", "deactivate"]):
                    return "user_delete"
                if any(x in combined for x in ["create", "add", "invite"]):
                    return "user_create"

        # ====================================================================
        # PRIORITY 4: Data Operations (PII, Exfiltration)
        # ====================================================================

        # Data exfiltration
        if any(x in combined for x in ["exfil", "exfiltrat", "extract", "download", "copy", "export"]):
            # But not routine backups
            if not any(x in combined for x in ["backup", "scheduled"]):
                return "data_exfiltration"

        # PII operations
        if any(x in combined for x in ["pii", "personal", "ssn", "social security"]):
            return "pii_read"

        # ====================================================================
        # PRIORITY 5: Database Operations (Separate Read/Write/Delete)
        # ====================================================================

        # Database DELETE (check BEFORE write)
        if any(x in combined for x in ["database", "db", "sql", "query"]):
            if any(x in combined for x in ["delete", "drop", "truncate", "remove"]):
                return "database_delete"

        # Database WRITE (check BEFORE read)
        if any(x in combined for x in ["database", "db", "sql"]):
            if any(x in combined for x in ["write", "update", "modify", "insert", "upsert", "create", "alter"]):
                return "database_write"

        # Database READ (must come AFTER write/delete)
        if any(x in combined for x in ["database", "db", "sql", "query"]):
            if any(x in combined for x in ["read", "select", "get", "query", "fetch", "view", "lookup"]):
                return "database_read"

        # ====================================================================
        # PRIORITY 6: AWS/Cloud Operations (Separate Read/Write/Delete)
        # ====================================================================

        aws_keywords = ["aws", "ec2", "s3", "rds", "lambda", "cloudformation", "eks", "ecs"]
        if any(keyword in combined for keyword in aws_keywords):
            if any(x in combined for x in ["terminate", "delete", "destroy"]):
                return "aws_delete"
            elif any(x in combined for x in ["create", "update", "modify", "start", "stop", "reboot", "scale"]):
                return "aws_write"
            elif any(x in combined for x in ["describe", "list", "get", "read", "view"]):
                return "aws_read"

        # ====================================================================
        # PRIORITY 7: File Operations (Separate Read/Write/Delete)
        # ====================================================================

        file_keywords = ["file", "document", "upload", "filesystem"]
        if any(keyword in combined for keyword in file_keywords):
            if any(x in combined for x in ["delete", "remove", "unlink"]):
                return "file_delete"
            elif any(x in combined for x in ["write", "create", "upload", "save", "modify"]):
                return "file_write"
            elif any(x in combined for x in ["read", "download", "view", "get", "fetch"]):
                return "file_read"

        # ====================================================================
        # PRIORITY 8: Network & Infrastructure
        # ====================================================================

        if any(x in combined for x in ["firewall", "security group", "network acl", "iptables"]):
            return "firewall_modification"

        if any(x in combined for x in ["scan", "port scan", "vulnerability scan", "nmap"]):
            return "network_scan"

        # ====================================================================
        # PRIORITY 9: Deployment & Code Operations
        # ====================================================================

        if any(x in combined for x in ["deploy", "deployment", "release", "rollout"]):
            return "code_deployment"

        container_keywords = ["docker", "container", "kubernetes", "k8s", "pod"]
        if any(keyword in combined for keyword in container_keywords):
            return "container_control"

        # ====================================================================
        # PRIORITY 10: Communication Operations
        # ====================================================================

        if any(x in combined for x in ["email", "send email", "mail"]):
            return "email_send"

        if any(x in combined for x in ["notification", "alert", "slack", "teams"]):
            return "notification_send"

        # ====================================================================
        # PRIORITY 11: System Operations
        # ====================================================================

        if any(x in combined for x in ["monitor", "monitoring", "metrics", "observability"]):
            return "system_monitoring"

        if any(x in combined for x in ["system", "config", "configuration", "install"]):
            return "system_modification"

        # ====================================================================
        # DEFAULT: Generic API Call
        # ====================================================================
        return "api_call"

    def _get_default_metrics(self) -> Dict[str, str]:
        """Default metrics for unknown action types"""
        return {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "LOW"
        }

    def _adjust_for_context(self, metrics: Dict[str, str], context: Dict) -> Dict[str, str]:
        """
        Adjust CVSS metrics based on action context

        ARCH-003 Major Enhancement:
        - Added production system detection
        - Added financial transaction detection
        - Added privilege escalation detection
        - Enhanced PII detection
        - Detailed adjustment logging
        """
        adjusted = metrics.copy()
        adjustments_made = []

        try:
            # Production environment = higher impact (ARCH-003 enhanced)
            production_system = context.get("production_system", False)
            if production_system or context.get("environment") == "production":
                # Production changes affect many users/systems
                if adjusted["scope"] != "CHANGED":
                    adjusted["scope"] = "CHANGED"
                    adjustments_made.append("scope→CHANGED (production)")

                # Production availability is critical
                if adjusted["availability_impact"] != "HIGH":
                    adjusted["availability_impact"] = "HIGH"
                    adjustments_made.append("A→HIGH (production)")

                # Production data is sensitive
                if adjusted["confidentiality_impact"] == "LOW":
                    adjusted["confidentiality_impact"] = "MEDIUM"
                    adjustments_made.append("C→MEDIUM (production)")

            # PII data = changed scope + high confidentiality (ARCH-003 enhanced)
            contains_pii = context.get("contains_pii", False)
            if contains_pii:
                adjusted["scope"] = "CHANGED"
                adjusted["confidentiality_impact"] = "HIGH"
                adjustments_made.append("C→HIGH+Scope→CHANGED (PII)")

            # Financial transaction context (ARCH-003 NEW)
            is_financial = context.get("financial_transaction", False)
            if is_financial:
                # Financial transactions require integrity and availability
                adjusted["integrity_impact"] = "HIGH"
                adjusted["availability_impact"] = "HIGH"
                adjusted["confidentiality_impact"] = "HIGH"  # Payment data
                adjusted["scope"] = "CHANGED"  # Affects customers
                adjustments_made.append("I/A/C→HIGH+Scope→CHANGED (financial)")

            # Privilege escalation context (ARCH-003 NEW)
            requires_admin = context.get("requires_admin", False)
            if requires_admin:
                adjusted["privileges_required"] = "HIGH"
                adjusted["scope"] = "CHANGED"  # Admin access affects system-wide
                adjustments_made.append("PR→HIGH+Scope→CHANGED (admin)")

            # Public facing resource (existing, preserved)
            if context.get("public_facing"):
                adjusted["attack_vector"] = "NETWORK"
                if adjusted["privileges_required"] != "HIGH":
                    adjusted["privileges_required"] = "NONE"
                adjustments_made.append("AV→NETWORK+PR→NONE (public)")

            # Log adjustments for audit trail
            if adjustments_made:
                logger.info(
                    f"ARCH-003: Context adjustments: {', '.join(adjustments_made)}"
                )
            else:
                logger.debug("ARCH-003: No context adjustments needed")

        except Exception as e:
            logger.error(
                f"ARCH-003: Error during context adjustment: {e}",
                exc_info=True
            )
            # Return unadjusted metrics on error (graceful degradation)

        return adjusted


# Singleton instance
cvss_auto_mapper = CVSSAutoMapper()
