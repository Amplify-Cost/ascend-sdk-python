"""
CVSS Auto-Mapper Service - SEC-103b
Automatically assigns CVSS metrics based on agent action characteristics

SEC-103b Enhancements:
- Comprehensive enterprise action type mappings (50+ action types)
- Fixed normalization order (read before write)
- Industry coverage: Financial, Healthcare, Government, Enterprise
- Fail secure: Unknown actions default to HIGH risk
- MCP server tool support

Previous versions: ARCH-003
Engineer: OW-KAI Platform Engineering Team
Version: SEC-103b
Date: 2025-12-06
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

    SEC-103b: Comprehensive enterprise action mapping
    - 50+ action types across all enterprise domains
    - Proper risk differentiation (LOW/MEDIUM/HIGH/CRITICAL)
    - Fail secure design
    """

    # SEC-103b: Comprehensive ACTION_MAPPINGS for enterprise environments
    ACTION_MAPPINGS = {
        # ===== READ OPERATIONS (LOW RISK) =====
        "database_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "file_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "api_read": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "analytics_query": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "api_call": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },

        # ===== WRITE OPERATIONS (MEDIUM RISK) =====
        "database_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "file_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "api_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "record_update": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },

        # ===== DELETE OPERATIONS (HIGH RISK) =====
        "database_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "file_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "record_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # ===== DATA MOVEMENT (HIGH RISK) =====
        "data_export": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "data_exfiltration": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "NONE",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "bulk_transfer": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },

        # ===== FINANCIAL SERVICES (HIGH/CRITICAL RISK) =====
        "execute_trade": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "funds_transfer": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "payment_process": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "financial_transaction": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "account_modification": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "credit_decision": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "fraud_override": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },

        # ===== HEALTHCARE / HIPAA (HIGH/CRITICAL RISK) =====
        "phi_access": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "phi_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "prescription_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "medical_record_update": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "diagnosis_submit": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "insurance_claim": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },

        # ===== PII / GDPR (HIGH RISK) =====
        "pii_access": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "pii_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "pii_delete": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "consent_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },

        # ===== SYSTEM / INFRASTRUCTURE (CRITICAL RISK) =====
        "system_modification": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "config_change": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "credential_access": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },
        "privilege_escalation": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "firewall_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "service_restart": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "LOW",
            "availability_impact": "HIGH"
        },

        # ===== COMMUNICATION (MEDIUM RISK) =====
        "email_send": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },
        "notification_send": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "NONE",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },
        "message_send": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },

        # ===== HR / EMPLOYEE DATA (HIGH RISK) =====
        "employee_record_access": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "employee_record_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "payroll_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "termination_process": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },

        # ===== LEGAL / CONTRACTS (HIGH RISK) =====
        "contract_sign": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "contract_modify": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "NONE"
        },
        "legal_hold": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        },

        # ===== MCP SERVER TOOLS (COMMON) =====
        "execute_query": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "execute_command": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "shell_execute": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "code_execute": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "HIGH",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },
        "web_request": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "LOW",
            "availability_impact": "NONE"
        },
        "browser_navigate": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "LOW",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },
        "screenshot_capture": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "UNCHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # ===== DEFAULT FALLBACK (HIGH RISK - FAIL SECURE) =====
        "unknown_action": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "NONE",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
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

        SEC-103b: Enhanced with comprehensive action mapping
        """
        try:
            # Normalize action type (SEC-103b: fixed order)
            normalized_type = self._normalize_action_type(
                action_type,
                context.get("description", "") if context else ""
            )

            logger.info(
                f"SEC-103b: Normalized '{action_type}' -> '{normalized_type}'"
            )

            # Get base metrics for this action type
            base_metrics = self.ACTION_MAPPINGS.get(
                normalized_type,
                self._get_default_metrics()
            )

            # Adjust metrics based on context
            adjusted_metrics = self._adjust_for_context(base_metrics, context or {})

            # Calculate and store CVSS assessment
            result = cvss_calculator.assess_agent_action(
                db=db,
                action_id=action_id,
                metrics=adjusted_metrics,
                assessed_by="auto_mapper_sec103b"
            )

            logger.info(
                f"SEC-103b: Auto-assessed action {action_id} ({normalized_type}): "
                f"CVSS {result['base_score']} ({result['severity']})"
            )

            return result

        except Exception as e:
            logger.error(
                f"SEC-103b: CVSS auto-assessment failed for action {action_id}: {e}",
                exc_info=True
            )
            # Fail secure: return HIGH risk on error
            return {
                "base_score": 7.5,
                "severity": "HIGH",
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
                "error": str(e)
            }

    def _normalize_action_type(self, action_type: str, description: str = "") -> str:
        """
        SEC-103b: Comprehensive action type normalization for enterprise environments.

        Normalizes action types to standardized CVSS mappings.
        Order matters - check specific patterns before generic ones.
        Unknown actions default to HIGH risk (fail secure).
        """
        if not action_type:
            return "unknown_action"

        action_lower = action_type.lower()
        desc_lower = description.lower()
        combined = f"{action_lower} {desc_lower}"

        # ===== EXACT MATCHES FIRST =====
        if action_lower in self.ACTION_MAPPINGS:
            return action_lower

        # ===== READ OPERATIONS (LOW RISK) - CHECK FIRST =====
        if any(x in combined for x in [
            "database_read", "db_read", "select", "query", "fetch",
            "get_record", "find", "search", "lookup", "retrieve"
        ]):
            return "database_read"

        if any(x in combined for x in [
            "file_read", "read_file", "download_file", "view_file"
        ]):
            return "file_read"

        if any(x in combined for x in [
            "api_read", "api_get", "rest_get", "graphql_query"
        ]):
            return "api_read"

        if any(x in combined for x in [
            "analytics", "metrics", "stats", "report_view", "dashboard"
        ]):
            return "analytics_query"

        # Generic read - only if no write/delete indicators
        if any(x in combined for x in ["read", "view", "list", "get"]) and \
           not any(x in combined for x in ["write", "update", "delete", "modify", "create", "insert"]):
            return "file_read"

        # ===== FINANCIAL SERVICES (HIGH/CRITICAL RISK) =====
        if any(x in combined for x in [
            "trade", "execute_trade", "order", "buy", "sell", "position"
        ]):
            return "execute_trade"

        if any(x in combined for x in [
            "transfer", "wire", "ach", "funds_transfer", "remittance"
        ]):
            return "funds_transfer"

        if any(x in combined for x in [
            "payment", "pay", "charge", "debit", "credit_card"
        ]):
            return "payment_process"

        if any(x in combined for x in [
            "credit_decision", "loan_approval", "underwriting"
        ]):
            return "credit_decision"

        if any(x in combined for x in [
            "fraud_override", "fraud_bypass", "risk_override"
        ]):
            return "fraud_override"

        if any(x in combined for x in [
            "account_modify", "account_update", "account_change"
        ]):
            return "account_modification"

        # ===== HEALTHCARE / HIPAA (HIGH RISK) =====
        if any(x in combined for x in [
            "phi_access", "patient_record", "medical_record", "health_record", "hipaa"
        ]) and not any(x in combined for x in ["modify", "update", "write"]):
            return "phi_access"

        if any(x in combined for x in [
            "phi_modify", "patient_update", "medical_update"
        ]):
            return "phi_modify"

        if any(x in combined for x in [
            "prescription", "rx_", "medication", "drug_order"
        ]):
            return "prescription_write"

        if any(x in combined for x in [
            "diagnosis", "clinical_decision", "treatment_plan"
        ]):
            return "diagnosis_submit"

        if any(x in combined for x in [
            "insurance_claim", "claim_submit", "billing"
        ]):
            return "insurance_claim"

        # ===== PII / GDPR =====
        if any(x in combined for x in [
            "pii_access", "personal_data", "gdpr"
        ]) and not any(x in combined for x in ["modify", "update", "write", "delete"]):
            return "pii_access"

        if any(x in combined for x in [
            "pii_modify", "pii_update", "personal_data_update"
        ]):
            return "pii_modify"

        if any(x in combined for x in [
            "pii_delete", "gdpr_delete", "right_to_forget", "data_erasure"
        ]):
            return "pii_delete"

        if any(x in combined for x in [
            "consent", "opt_out", "opt_in", "preference"
        ]):
            return "consent_modify"

        # ===== DATA EXPORT / EXFILTRATION (HIGH RISK) =====
        if any(x in combined for x in [
            "export", "bulk_export", "data_export", "extract", "dump"
        ]):
            return "data_export"

        if any(x in combined for x in [
            "exfiltration", "data_theft", "unauthorized_transfer"
        ]):
            return "data_exfiltration"

        if any(x in combined for x in [
            "bulk_transfer", "mass_transfer", "batch_transfer"
        ]):
            return "bulk_transfer"

        # ===== DELETE OPERATIONS (HIGH RISK) =====
        if any(x in combined for x in [
            "database_delete", "db_delete", "drop", "truncate", "purge"
        ]):
            return "database_delete"

        if any(x in combined for x in [
            "file_delete", "remove_file", "unlink"
        ]):
            return "file_delete"

        if any(x in combined for x in [
            "record_delete", "delete_record", "remove_record"
        ]):
            return "record_delete"

        # Generic delete
        if any(x in combined for x in ["delete", "remove", "destroy"]):
            return "database_delete"

        # ===== WRITE/UPDATE OPERATIONS (MEDIUM RISK) =====
        if any(x in combined for x in [
            "database_write", "db_write", "insert", "update", "upsert"
        ]):
            return "database_write"

        if any(x in combined for x in [
            "file_write", "write_file", "upload", "save_file"
        ]):
            return "file_write"

        if any(x in combined for x in [
            "api_write", "api_post", "api_put", "rest_post"
        ]):
            return "api_write"

        if any(x in combined for x in [
            "record_update", "update_record", "modify_record"
        ]):
            return "record_update"

        # Generic write - AFTER read check
        if any(x in combined for x in ["write", "create", "insert", "modify"]):
            return "database_write"

        # ===== SYSTEM / INFRASTRUCTURE (CRITICAL RISK) =====
        if any(x in combined for x in [
            "system", "config", "configuration", "setting"
        ]) and any(x in combined for x in ["change", "modify", "update"]):
            return "config_change"

        if any(x in combined for x in [
            "credential", "password", "secret", "key_rotation", "api_key"
        ]):
            return "credential_access"

        if any(x in combined for x in [
            "privilege", "permission", "role_change", "admin_grant", "sudo"
        ]):
            return "privilege_escalation"

        if any(x in combined for x in [
            "firewall", "security_group", "network_rule", "acl"
        ]):
            return "firewall_modify"

        if any(x in combined for x in [
            "restart", "reboot", "shutdown", "stop_service"
        ]):
            return "service_restart"

        if any(x in combined for x in [
            "deploy", "install", "upgrade", "patch"
        ]):
            return "system_modification"

        # ===== HR / EMPLOYEE =====
        if any(x in combined for x in [
            "employee", "hr_record", "personnel"
        ]) and any(x in combined for x in ["modify", "update", "write"]):
            return "employee_record_modify"

        if any(x in combined for x in [
            "employee", "hr_record", "personnel"
        ]):
            return "employee_record_access"

        if any(x in combined for x in [
            "payroll", "salary", "compensation", "bonus"
        ]):
            return "payroll_modify"

        if any(x in combined for x in [
            "termination", "offboard", "fire", "let_go"
        ]):
            return "termination_process"

        # ===== LEGAL / CONTRACTS =====
        if any(x in combined for x in [
            "contract_sign", "signature", "e_sign", "docusign"
        ]):
            return "contract_sign"

        if any(x in combined for x in [
            "contract", "agreement", "nda", "legal_doc"
        ]):
            return "contract_modify"

        if any(x in combined for x in [
            "legal_hold", "litigation", "discovery", "preserve"
        ]):
            return "legal_hold"

        # ===== COMMUNICATION =====
        if any(x in combined for x in [
            "email", "mail_send", "smtp"
        ]):
            return "email_send"

        if any(x in combined for x in [
            "notification", "alert", "push"
        ]):
            return "notification_send"

        if any(x in combined for x in [
            "message", "chat", "slack", "teams"
        ]):
            return "message_send"

        # ===== MCP SERVER TOOLS =====
        if any(x in combined for x in [
            "execute_query", "run_query", "sql"
        ]):
            return "execute_query"

        if any(x in combined for x in [
            "execute_command", "run_command", "exec"
        ]):
            return "execute_command"

        if any(x in combined for x in [
            "shell", "bash", "terminal", "cmd"
        ]):
            return "shell_execute"

        if any(x in combined for x in [
            "code_execute", "eval", "run_code", "python_exec"
        ]):
            return "code_execute"

        if any(x in combined for x in [
            "http", "request", "fetch", "curl", "web_request"
        ]):
            return "web_request"

        if any(x in combined for x in [
            "browser", "navigate", "puppeteer", "selenium"
        ]):
            return "browser_navigate"

        if any(x in combined for x in [
            "screenshot", "capture", "screen_grab"
        ]):
            return "screenshot_capture"

        # ===== FAIL SECURE - UNKNOWN ACTIONS GET HIGH RISK =====
        logger.warning(f"SEC-103b: Unknown action type '{action_type}' - defaulting to HIGH risk")
        return "unknown_action"

    def _get_default_metrics(self) -> Dict[str, str]:
        """SEC-103b: Fail secure - unknown actions get HIGH risk metrics"""
        return {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "NONE",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "LOW"
        }

    def _adjust_for_context(self, metrics: Dict[str, str], context: Dict) -> Dict[str, str]:
        """
        Adjust CVSS metrics based on action context

        SEC-103b: Uses SDK parameters (environment, data_sensitivity)
        """
        adjusted = metrics.copy()
        adjustments_made = []

        try:
            # Production environment = higher impact
            production_system = context.get("production_system", False)
            environment = context.get("environment", "development")
            if production_system or environment == "production":
                if adjusted["scope"] != "CHANGED":
                    adjusted["scope"] = "CHANGED"
                    adjustments_made.append("scope->CHANGED (production)")

                if adjusted["availability_impact"] != "HIGH":
                    adjusted["availability_impact"] = "HIGH"
                    adjustments_made.append("A->HIGH (production)")

                if adjusted["confidentiality_impact"] == "LOW":
                    adjusted["confidentiality_impact"] = "MEDIUM"
                    adjustments_made.append("C->MEDIUM (production)")

            # PII/sensitive data = high confidentiality
            contains_pii = context.get("contains_pii", False)
            data_sensitivity = context.get("data_sensitivity", "none")
            if contains_pii or data_sensitivity in ["high_sensitivity", "pii", "sensitive"]:
                adjusted["scope"] = "CHANGED"
                adjusted["confidentiality_impact"] = "HIGH"
                adjustments_made.append("C->HIGH+Scope->CHANGED (sensitive data)")

            # Financial transaction context
            is_financial = context.get("financial_transaction", False)
            if is_financial:
                adjusted["integrity_impact"] = "HIGH"
                adjusted["availability_impact"] = "HIGH"
                adjusted["confidentiality_impact"] = "HIGH"
                adjusted["scope"] = "CHANGED"
                adjustments_made.append("I/A/C->HIGH+Scope->CHANGED (financial)")

            # Log adjustments for audit trail
            if adjustments_made:
                logger.info(
                    f"SEC-103b: Context adjustments: {', '.join(adjustments_made)}"
                )
            else:
                logger.debug("SEC-103b: No context adjustments needed")

        except Exception as e:
            logger.error(
                f"SEC-103b: Error during context adjustment: {e}",
                exc_info=True
            )

        return adjusted


# Singleton instance
cvss_auto_mapper = CVSSAutoMapper()
