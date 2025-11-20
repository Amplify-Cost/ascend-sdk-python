"""
Enterprise Risk Calculator - Hybrid Multi-Factor Risk Scoring
Engineer: Donald King (OW-kai Enterprise)
Date: 2025-11-14

Purpose:
Provides enterprise-grade risk assessment for AI agent actions by combining:
- Environment risk (35%)
- Data sensitivity risk (30%)
- CVSS technical vulnerability scoring (25%)
- Operational context (10%)

This addresses the testing report findings that CVSS-only scoring cannot
differentiate between safe and dangerous actions in operational context.

Architecture:
- Environment measures: "What's the business impact domain?" (0-35 points)
- Data Sensitivity measures: "What data is at risk?" (0-30 points)
- CVSS measures: "How severe is this action type technically?" (0-25 points)
- Operational Context measures: "When and how is this happening?" (0-10 points)

Expected Score Distribution:
- Dev read, no PII: 20-30/100 (auto-approve)
- Staging write, no PII: 40-55/100 (quick approval)
- Prod read, no PII: 45-60/100 (1-level approval)
- Prod write, no PII: 70-80/100 (1-2 level approval)
- Prod delete, no PII: 85-92/100 (2-level approval)
- Prod write with PII: 95-99/100 (2-3 level approval or deny)
"""
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnterpriseRiskCalculator:
    """
    🏢 ENTERPRISE HYBRID RISK SCORING ENGINE

    Combines multiple risk factors to produce contextually accurate risk scores
    that enable proper auto-approval, escalation, and denial decisions.
    """

    # ============================================================================
    # COMPONENT 1: ENVIRONMENT RISK (35% of final score, 0-35 points)
    # ============================================================================

    ENVIRONMENT_SCORES = {
        'production': 35,      # Maximum environmental risk
        'prod': 35,            # Alias
        'staging': 18,         # Medium environmental risk
        'stage': 18,           # Alias
        'development': 5,      # Low environmental risk
        'dev': 5,              # Alias
        'sandbox': 2,          # Minimal environmental risk
        'test': 3,             # Minimal environmental risk
        'unknown': 35          # Fail-safe: assume production
    }

    # ============================================================================
    # COMPONENT 2: DATA SENSITIVITY RISK (30% of final score, 0-30 points)
    # ============================================================================

    # PII Keywords for detection
    PII_KEYWORDS = {
        'high_sensitivity': [
            'ssn', 'social_security', 'credit_card', 'card_number', 'cvv',
            'password', 'credential', 'secret', 'api_key', 'private_key',
            'financial', 'payment', 'billing', 'bank_account'
        ],
        'medium_sensitivity': [
            'email', 'phone', 'address', 'name', 'dob', 'date_of_birth',
            'customer', 'user', 'patient', 'employee'
        ],
        'business_sensitive': [
            'proprietary', 'confidential', 'internal', 'strategic',
            'revenue', 'profit', 'contract'
        ]
    }

    def _calculate_data_sensitivity_score(
        self,
        contains_pii: bool,
        resource_name: str,
        description: str,
        action_metadata: Optional[Dict] = None
    ) -> int:
        """
        Calculate data sensitivity risk score (0-30 points)

        Scoring:
        - PII + Financial keywords: 30 points
        - PII only: 25 points
        - Customer/business data: 18 points
        - Internal/employee data: 12 points
        - Test/synthetic data: 0-5 points
        """
        score = 0
        combined_text = f"{resource_name} {description}".lower()

        # Check for high sensitivity keywords
        high_sensitivity_found = any(
            keyword in combined_text
            for keyword in self.PII_KEYWORDS['high_sensitivity']
        )

        # Check for medium sensitivity keywords
        medium_sensitivity_found = any(
            keyword in combined_text
            for keyword in self.PII_KEYWORDS['medium_sensitivity']
        )

        # Check for business sensitive keywords
        business_sensitive_found = any(
            keyword in combined_text
            for keyword in self.PII_KEYWORDS['business_sensitive']
        )

        # Scoring logic
        if contains_pii and high_sensitivity_found:
            score = 30  # PII + Financial/Credentials
            logger.info("🔐 Data Sensitivity: PII + High Sensitivity Keywords → 30/30 points")
        elif contains_pii:
            score = 25  # PII without financial keywords
            logger.info("🔐 Data Sensitivity: PII Flagged → 25/30 points")
        elif high_sensitivity_found:
            score = 22  # Financial/credentials without PII flag
            logger.info("🔐 Data Sensitivity: High Sensitivity Keywords → 22/30 points")
        elif medium_sensitivity_found:
            score = 18  # Customer/user data
            logger.info("🔐 Data Sensitivity: Customer Data → 18/30 points")
        elif business_sensitive_found:
            score = 12  # Business data
            logger.info("🔐 Data Sensitivity: Business Sensitive → 12/30 points")
        elif 'test' in combined_text or 'demo' in combined_text or 'synthetic' in combined_text:
            score = 0  # Test data
            logger.info("🔐 Data Sensitivity: Test/Synthetic Data → 0/30 points")
        else:
            score = 5  # Generic data
            logger.info("🔐 Data Sensitivity: Generic Data → 5/30 points")

        return score

    # ============================================================================
    # COMPONENT 3: ACTION TYPE RISK (Derived from CVSS, 0-25 points)
    # ============================================================================

    ACTION_TYPE_BASE_SCORES = {
        'delete': 25,          # Highest action risk (destructive, irreversible)
        'drop': 25,            # Alias for delete
        'destroy': 25,         # Alias for delete
        'write': 23,           # High action risk (modifies state)
        'create': 21,          # High action risk (creates resources)
        'update': 21,          # High action risk (modifies existing)
        'modify': 19,          # Medium-high action risk
        'execute': 16,         # Medium action risk (runs code)
        'run': 16,             # Alias for execute
        'read': 10,            # Low action risk (read-only)
        'list': 7,             # Low action risk (enumerate)
        'describe': 7,         # Low action risk (metadata only)
        'get': 10,             # Low action risk (read single item)
        'unknown': 19          # Fail-safe: assume moderate risk
    }

    # ============================================================================
    # COMPONENT 4: OPERATIONAL CONTEXT (10% of final score, 0-10 points)
    # ============================================================================

    def _calculate_operational_context_score(
        self,
        action_metadata: Optional[Dict] = None
    ) -> int:
        """
        Calculate operational context risk score (0-10 points)

        Factors:
        - Time of day (peak hours vs maintenance window)
        - Change window (approved vs unapproved)
        - User role/experience
        - Recent similar actions (anomaly detection - future enhancement)

        Current implementation: Basic scoring, can be enhanced
        """
        score = 8  # Baseline operational context score (conservative approach)

        # TODO: Future enhancements
        # - Peak hours detection (+2 points → max 10)
        # - Maintenance window detection (-5 points → min 3)
        # - User risk profile integration
        # - Anomaly detection (unusual action for this agent)

        logger.info(f"⏰ Operational Context: Baseline → {score}/10 points")
        return score

    # ============================================================================
    # MAIN CALCULATION METHOD
    # ============================================================================

    def calculate_hybrid_risk_score(
        self,
        cvss_score: Optional[float],
        environment: str,
        action_type: str,
        contains_pii: bool,
        resource_name: str,
        description: str,
        action_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate hybrid enterprise risk score

        Args:
            cvss_score: CVSS base score (0-10) from technical assessment
            environment: Target environment (production, staging, development)
            action_type: Type of action (read, write, delete, etc.)
            contains_pii: Boolean flag for PII data
            resource_name: Name of target resource
            description: Action description
            action_metadata: Optional additional context

        Returns:
            Dict with:
                - risk_score: Final score (0-100)
                - breakdown: Component scores
                - reasoning: Explanation of score
        """
        logger.info("=" * 80)
        logger.info("🏢 ENTERPRISE HYBRID RISK SCORING ENGINE")
        logger.info("=" * 80)

        # Component 1: Environment Risk (0-30 points)
        env_lower = environment.lower() if environment else 'unknown'
        environment_score = self.ENVIRONMENT_SCORES.get(env_lower, 30)
        logger.info(f"🌍 Environment: '{environment}' → {environment_score}/30 points")

        # Component 2: Data Sensitivity Risk (0-25 points)
        sensitivity_score = self._calculate_data_sensitivity_score(
            contains_pii, resource_name, description, action_metadata
        )

        # Component 3: Action Type Risk (0-25 points based on CVSS impact)
        # Use CVSS if available, otherwise use action type lookup
        if cvss_score is not None:
            # CVSS score 0-10, normalize to 0-25
            action_score = min(int(cvss_score * 2.5), 25)
            logger.info(f"⚙️  Action Type: CVSS {cvss_score:.1f} → {action_score}/25 points")
        else:
            # Fallback to action type lookup
            action_lower = action_type.lower() if action_type else 'unknown'
            action_score = self.ACTION_TYPE_BASE_SCORES.get(action_lower, 18)
            logger.info(f"⚙️  Action Type: '{action_type}' (no CVSS) → {action_score}/25 points")

        # Component 4: Operational Context (0-10 points)
        context_score = self._calculate_operational_context_score(action_metadata)

        # Calculate base score
        base_score = environment_score + sensitivity_score + action_score + context_score

        # Apply risk amplification for dangerous combinations
        # Production + High-risk actions deserve extra weight
        amplification_bonus = 0

        if environment_score >= 30:  # Production environment
            if sensitivity_score >= 20:  # PII data
                if action_score >= 20:  # Write/Delete action with PII
                    amplification_bonus = 10  # +10 points for production + PII + write/delete
                    logger.info(f"⚠️  Risk Amplification: Production + PII + Destructive Action → +{amplification_bonus} points")
                elif action_score >= 15:
                    amplification_bonus = 6  # +6 points for production + PII + moderate risk
                    logger.info(f"⚠️  Risk Amplification: Production + PII + Moderate Action → +{amplification_bonus} points")
            elif action_score >= 20:  # Production + destructive action (no PII)
                amplification_bonus = 8  # +8 points for production + write/delete
                logger.info(f"⚠️  Risk Amplification: Production + Destructive Action → +{amplification_bonus} points")
            elif action_score >= 15:  # Production + write action (no PII)
                amplification_bonus = 5  # +5 points for production + write
                logger.info(f"⚠️  Risk Amplification: Production + Write Action → +{amplification_bonus} points")

        # Calculate final score with amplification
        final_score = min(base_score + amplification_bonus, 100)

        # Determine risk level
        if final_score >= 85:
            risk_level = "critical"
        elif final_score >= 70:
            risk_level = "high"
        elif final_score >= 45:
            risk_level = "medium"
        elif final_score >= 25:
            risk_level = "low"
        else:
            risk_level = "minimal"

        # Build reasoning
        reasoning_parts = []
        if environment_score >= 25:
            reasoning_parts.append(f"Production environment (+{environment_score})")
        elif environment_score >= 10:
            reasoning_parts.append(f"Staging environment (+{environment_score})")
        else:
            reasoning_parts.append(f"Development environment (+{environment_score})")

        if sensitivity_score >= 20:
            reasoning_parts.append(f"PII/Sensitive data (+{sensitivity_score})")
        elif sensitivity_score >= 10:
            reasoning_parts.append(f"Customer data (+{sensitivity_score})")

        if action_score >= 30:
            reasoning_parts.append(f"Destructive action (+{action_score})")
        elif action_score >= 20:
            reasoning_parts.append(f"Modifying action (+{action_score})")
        else:
            reasoning_parts.append(f"Read-only action (+{action_score})")

        reasoning = "; ".join(reasoning_parts)

        logger.info("─" * 80)
        logger.info(f"📊 FINAL HYBRID RISK SCORE: {final_score}/100 ({risk_level.upper()})")
        logger.info(f"📋 Reasoning: {reasoning}")
        logger.info("=" * 80)

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "breakdown": {
                "environment_score": environment_score,
                "sensitivity_score": sensitivity_score,
                "action_score": action_score,
                "context_score": context_score
            },
            "reasoning": reasoning,
            "formula": f"({environment_score} env + {sensitivity_score} data + {action_score} action + {context_score} context) = {final_score}"
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

enterprise_risk_calculator = EnterpriseRiskCalculator()
