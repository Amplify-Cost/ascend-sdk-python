"""
AI Recommendation Generator Service
ARCH-003 Phase 3: Context-aware security recommendations using LLM

This service generates actionable security recommendations based on:
- Action type and description
- Risk level and CVSS score
- MITRE ATT&CK tactics and techniques
- NIST controls
- Context flags (production, PII, financial, etc.)

Engineer: OW-KAI Platform Engineering Team
Date: 2025-11-11
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================================
# ARCH-003 Phase 3: AI RECOMMENDATION GENERATION
# ============================================================================

class AIRecommendationGenerator:
    """
    Generates context-aware security recommendations using LLM.
    Implements caching and graceful fallback for enterprise reliability.
    """

    def __init__(self):
        """Initialize AI recommendation generator with caching."""
        self._cache = {}  # In-memory cache (could be Redis in production)
        self._cache_ttl = timedelta(hours=24)  # Cache recommendations for 24 hours

        # Import OpenAI client
        try:
            from llm_utils import client as openai_client
            self.client = openai_client
            if self.client:
                logger.info("ARCH-003 Phase 3: AI recommendation generator initialized with OpenAI client")
            else:
                logger.warning("ARCH-003 Phase 3: OpenAI client not available, will use fallback recommendations")
        except Exception as e:
            logger.warning(f"ARCH-003 Phase 3: Failed to import OpenAI client: {e}, using fallback")
            self.client = None

    def generate_recommendation(
        self,
        action_type: str,
        description: str,
        risk_level: str,
        cvss_score: Optional[float] = None,
        mitre_tactic: Optional[str] = None,
        mitre_technique: Optional[str] = None,
        nist_control: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Generate context-aware security recommendation.

        Args:
            action_type: Type of agent action
            description: Human-readable description
            risk_level: Qualitative risk (low/medium/high)
            cvss_score: CVSS v3.1 base score (optional)
            mitre_tactic: MITRE ATT&CK tactic (optional)
            mitre_technique: MITRE ATT&CK technique (optional)
            nist_control: NIST SP 800-53 control (optional)
            context: Additional context flags (optional)

        Returns:
            AI-generated or fallback recommendation string
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(action_type, description, risk_level)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"ARCH-003 Phase 3: Using cached recommendation for {action_type}")
                return cached

            # Generate AI recommendation if client available
            if self.client:
                recommendation = self._generate_ai_recommendation(
                    action_type=action_type,
                    description=description,
                    risk_level=risk_level,
                    cvss_score=cvss_score,
                    mitre_tactic=mitre_tactic,
                    mitre_technique=mitre_technique,
                    nist_control=nist_control,
                    context=context or {}
                )

                # Cache the recommendation
                self._add_to_cache(cache_key, recommendation)

                logger.info(f"ARCH-003 Phase 3: Generated AI recommendation for {action_type} ({risk_level})")
                return recommendation
            else:
                # Fallback to static recommendations
                logger.debug(f"ARCH-003 Phase 3: Using fallback recommendation for {action_type}")
                return self._get_fallback_recommendation(action_type, risk_level, context or {})

        except Exception as e:
            logger.error(f"ARCH-003 Phase 3: AI recommendation generation failed: {e}, using fallback")
            return self._get_fallback_recommendation(action_type, risk_level, context or {})

    def _generate_ai_recommendation(
        self,
        action_type: str,
        description: str,
        risk_level: str,
        cvss_score: Optional[float],
        mitre_tactic: Optional[str],
        mitre_technique: Optional[str],
        nist_control: Optional[str],
        context: Dict
    ) -> str:
        """
        Generate AI recommendation using OpenAI API.

        Implements 2-second timeout for enterprise SLA compliance.
        """
        # Build context string
        context_flags = []
        if context.get("production_system"):
            context_flags.append("production environment")
        if context.get("contains_pii"):
            context_flags.append("contains PII")
        if context.get("financial_transaction"):
            context_flags.append("financial transaction")
        if context.get("requires_admin"):
            context_flags.append("requires admin privileges")

        context_str = ", ".join(context_flags) if context_flags else "standard context"

        # Build prompt
        prompt = f"""Generate a concise, actionable security recommendation for this agent action:

Action Type: {action_type}
Description: {description}
Risk Level: {risk_level.upper()}
CVSS Score: {cvss_score if cvss_score else 'N/A'}
MITRE Tactic: {mitre_tactic if mitre_tactic else 'N/A'}
MITRE Technique: {mitre_technique if mitre_technique else 'N/A'}
NIST Control: {nist_control if nist_control else 'N/A'}
Context: {context_str}

Provide 1-2 sentence recommendation that:
- Is specific to this action and context
- Mentions relevant compliance frameworks (PCI-DSS, GDPR, NIST, etc.)
- Provides actionable guidance for security teams
- Focuses on risk mitigation

Recommendation:"""

        try:
            # Call OpenAI with timeout
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity compliance expert specializing in risk assessment and enterprise security frameworks (PCI-DSS, GDPR, NIST SP 800-53, SOC 2). Provide concise, actionable security recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt.strip()
                    }
                ],
                max_tokens=150,
                temperature=0.7,
                timeout=2.0  # Enterprise SLA: 2-second timeout
            )

            recommendation = response.choices[0].message.content.strip()

            # Validate recommendation length
            if len(recommendation) > 500:
                recommendation = recommendation[:497] + "..."

            return recommendation

        except Exception as e:
            logger.warning(f"ARCH-003 Phase 3: OpenAI API call failed: {e}, using fallback")
            raise  # Re-raise to trigger fallback in parent

    def _get_fallback_recommendation(
        self,
        action_type: str,
        risk_level: str,
        context: Dict
    ) -> str:
        """
        Get static fallback recommendation when AI unavailable.

        Maintains backward compatibility with existing system.
        """
        action_lower = action_type.lower()

        # High-risk fallbacks with compliance mentions
        if risk_level == "high":
            if "payment" in action_lower or "financial" in action_lower or context.get("financial_transaction"):
                return "Financial transaction detected. Verify PCI-DSS compliance (Requirement 10.2), ensure transaction logging is enabled, and validate authorization chain per SOC 2 Type II requirements."
            elif "database" in action_lower and context.get("production_system"):
                return "Production database modification requires approval per change management policy. Ensure backup exists (NIST CP-9), validate authorization (NIST AC-3), and maintain audit trail per SOC 2 requirements."
            elif "pii" in action_lower or context.get("contains_pii"):
                return "PII access detected. Ensure GDPR Article 32 compliance, verify data minimization principles, and confirm valid legal basis for processing. Log access per NIST AU-2."
            else:
                return "High-risk action requires security review. Implement least privilege (NIST AC-6), enable comprehensive monitoring (NIST SI-4), and ensure proper authorization chain."

        # Medium-risk fallbacks
        elif risk_level == "medium":
            if "network" in action_lower or "scan" in action_lower:
                return "Network activity detected. Ensure authorized scanning per security policy (NIST RA-5), monitor for anomalies (NIST SI-4), and maintain scan logs for compliance audits."
            elif "credential" in action_lower or "password" in action_lower:
                return "Credential access requires strong authentication (NIST IA-2). Implement multi-factor authentication, rotate credentials regularly (NIST IA-5), and monitor for unauthorized access attempts."
            else:
                return "Medium-risk action requires monitoring. Validate legitimacy, maintain audit logs (NIST AU-2), and review for policy compliance during next security assessment."

        # Low-risk fallback
        else:
            return "Standard user activity detected. Continue monitoring for anomalies (NIST SI-4) and maintain audit logs (NIST AU-6) for compliance reporting."

    def _get_cache_key(self, action_type: str, description: str, risk_level: str) -> str:
        """Generate cache key for recommendation."""
        # Use first 100 chars of description to avoid cache bloat
        desc_short = description[:100] if description else ""
        return f"{action_type}:{risk_level}:{hash(desc_short)}"

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get recommendation from cache if not expired."""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if datetime.now() < cached_item["expires_at"]:
                return cached_item["recommendation"]
            else:
                # Remove expired item
                del self._cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, recommendation: str):
        """Add recommendation to cache with expiry."""
        self._cache[cache_key] = {
            "recommendation": recommendation,
            "expires_at": datetime.now() + self._cache_ttl,
            "created_at": datetime.now()
        }

        # Simple cache cleanup: remove old items if cache too large
        if len(self._cache) > 1000:
            # Remove oldest 20% of items
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1]["created_at"]
            )
            for key, _ in sorted_items[:200]:
                del self._cache[key]
            logger.info(f"ARCH-003 Phase 3: Cache cleanup performed, removed 200 old items")


# Singleton instance
ai_recommendation_generator = AIRecommendationGenerator()
