"""
CVSS Auto-Mapper Service - ARCH-003
Automatically assigns CVSS metrics based on agent action characteristics

Enhancements:
- Fixed database write metrics (C/I/A: HIGH, Scope: CHANGED)
- Added financial transaction detection and mapping
- Enhanced context awareness (production, PII, financial, privilege)
- Improved action type normalization with description checking
- Enterprise error handling and logging
- Backward compatible with existing integrations

Engineer: OW-KAI Platform Engineering Team
Version: ARCH-003
Date: 2025-11-11
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

    # Action type to CVSS metric mappings (ARCH-003 enhanced)
    ACTION_MAPPINGS = {
        # Data exfiltration - high confidentiality impact
        "data_exfiltration": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",
            "confidentiality_impact": "HIGH",
            "integrity_impact": "NONE",
            "availability_impact": "NONE"
        },

        # Database write - FIXED (ARCH-003): Now HIGH for C/I/A, Scope CHANGED
        # Previously: CVSS 4.9 (MEDIUM), Now: CVSS 9.0+ (CRITICAL)
        "database_write": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",  # Was: UNCHANGED
            "confidentiality_impact": "HIGH",  # Was: NONE
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"  # Was: NONE
        },

        # System modification - all impacts
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

        # Financial transaction - NEW (ARCH-003)
        # Covers payment processing, billing, financial operations
        "financial_transaction": {
            "attack_vector": "NETWORK",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",
            "user_interaction": "NONE",
            "scope": "CHANGED",  # Financial impact affects customers
            "confidentiality_impact": "HIGH",  # PII/payment data
            "integrity_impact": "HIGH",  # Transaction integrity
            "availability_impact": "HIGH"  # Revenue impact
        },

        # Privilege escalation - NEW (ARCH-003)
        # Covers admin user creation, permission grants
        "privilege_escalation": {
            "attack_vector": "LOCAL",
            "attack_complexity": "LOW",
            "privileges_required": "LOW",  # Starting point
            "user_interaction": "NONE",
            "scope": "CHANGED",  # System-wide impact
            "confidentiality_impact": "HIGH",
            "integrity_impact": "HIGH",
            "availability_impact": "HIGH"
        },

        # File read - low confidentiality impact
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

        # API call - medium risk (baseline, adjusted by context)
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
        Normalize action type to standard categories

        ARCH-003 Enhancement: Also checks description for better categorization
        """
        action_lower = action_type.lower()
        desc_lower = description.lower()
        combined = f"{action_lower} {desc_lower}"

        # Financial transaction detection (ARCH-003 NEW)
        financial_keywords = [
            "payment", "transaction", "billing", "invoice", "charge", "refund",
            "stripe", "paypal", "financial", "credit card", "debit", "purchase"
        ]
        if any(keyword in combined for keyword in financial_keywords):
            return "financial_transaction"

        # Privilege escalation detection (ARCH-003 NEW)
        privilege_keywords = [
            "admin", "administrator", "root", "sudo", "privilege", "privileges",
            "superuser", "elevated", "grant", "permission", "access control"
        ]
        if any(keyword in combined for keyword in privilege_keywords):
            # But not if it's just reading/viewing
            if not any(x in combined for x in ["read", "view", "list", "get", "check"]):
                return "privilege_escalation"

        # Data exfiltration
        if any(x in combined for x in ["exfil", "export", "download", "copy", "extract"]):
            return "data_exfiltration"

        # Database operations
        elif any(x in combined for x in ["write", "update", "modify", "database", "schema", "sql"]):
            return "database_write"

        # System modification
        elif any(x in combined for x in ["system", "config", "deploy", "install", "firewall"]):
            return "system_modification"

        # File read
        elif any(x in combined for x in ["read", "view", "list", "get"]):
            return "file_read"

        # Default to API call
        else:
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
