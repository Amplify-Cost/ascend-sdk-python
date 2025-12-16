"""
ASCEND Lambda Authorizer - IAM Policy Generator
================================================

GW-004: Generates IAM policy documents for API Gateway authorization.

Policy Types:
    - Allow: Permits the API call to proceed
    - Deny: Blocks the API call with reason

Context Variables:
    - Passes ASCEND decision details to downstream services
    - Includes action ID for audit correlation

Security:
    - FAIL SECURE: Any error results in Deny policy
    - Never generates Allow for pending/denied actions
    - Includes risk score in context for downstream decisions

Compliance: SOC 2 CC6.1, NIST AC-3
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from .ascend_client import AscendResponse
from .request_mapper import MappedRequest

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationPolicy:
    """
    IAM authorization policy for API Gateway.

    Attributes:
        principal_id: Identifier for the caller
        policy_document: IAM policy document
        context: Context variables passed to downstream
    """
    principal_id: str
    policy_document: Dict[str, Any]
    context: Dict[str, Any]

    def to_response(self) -> Dict[str, Any]:
        """Convert to API Gateway authorizer response format."""
        response = {
            "principalId": self.principal_id,
            "policyDocument": self.policy_document
        }

        if self.context:
            # Convert all values to strings (API Gateway requirement)
            response["context"] = {
                k: str(v) if v is not None else ""
                for k, v in self.context.items()
            }

        return response


class PolicyGenerator:
    """
    Generates IAM policies based on ASCEND authorization decisions.

    Implements FAIL SECURE pattern - any error or ambiguity
    results in a Deny policy.
    """

    # Context keys exposed to downstream services
    CONTEXT_KEYS = [
        "ascend_action_id",
        "ascend_status",
        "ascend_risk_score",
        "ascend_risk_level",
        "ascend_requires_approval",
        "ascend_correlation_id",
        "ascend_agent_id",
        "ascend_action_type"
    ]

    def __init__(self):
        """Initialize policy generator."""
        logger.info("GW-004: Policy generator initialized")

    def generate_policy(
        self,
        request: MappedRequest,
        response: AscendResponse,
        allow: bool
    ) -> AuthorizationPolicy:
        """
        Generate IAM policy from ASCEND response.

        Args:
            request: Mapped request details
            response: ASCEND API response
            allow: Whether to allow the request

        Returns:
            AuthorizationPolicy: Generated policy with context
        """
        principal_id = request.agent_id

        if allow:
            policy_document = self._create_allow_policy(request.method_arn)
            logger.info(
                f"GW-004: Generated ALLOW policy - "
                f"agent={principal_id}, action_id={response.id}"
            )
        else:
            policy_document = self._create_deny_policy(request.method_arn)
            logger.info(
                f"GW-004: Generated DENY policy - "
                f"agent={principal_id}, status={response.status}, "
                f"risk={response.risk_score}"
            )

        context = self._build_context(request, response)

        return AuthorizationPolicy(
            principal_id=principal_id,
            policy_document=policy_document,
            context=context
        )

    def generate_deny_policy(
        self,
        agent_id: str,
        method_arn: str,
        reason: str,
        error_code: Optional[str] = None
    ) -> AuthorizationPolicy:
        """
        Generate explicit Deny policy for error cases.

        Used for FAIL SECURE when ASCEND API is unreachable
        or returns an error.

        Args:
            agent_id: Agent identifier (or "unknown")
            method_arn: Resource ARN to deny
            reason: Human-readable denial reason
            error_code: Error code for debugging

        Returns:
            AuthorizationPolicy: Deny policy with error context
        """
        logger.warning(
            f"GW-004 FAIL SECURE: Generating DENY policy - "
            f"agent={agent_id}, reason={reason}"
        )

        return AuthorizationPolicy(
            principal_id=agent_id or "unknown",
            policy_document=self._create_deny_policy(method_arn),
            context={
                "ascend_status": "error",
                "ascend_error": reason,
                "ascend_error_code": error_code or "FAIL_SECURE",
                "ascend_agent_id": agent_id or "unknown"
            }
        )

    def _create_allow_policy(self, resource_arn: str) -> Dict[str, Any]:
        """
        Create Allow policy document.

        Args:
            resource_arn: Resource ARN to allow

        Returns:
            dict: IAM policy document
        """
        # Use wildcard for the resource to allow all methods
        # The specific authorization was already done by ASCEND
        base_arn = self._get_base_arn(resource_arn)

        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": [
                        resource_arn,  # Exact resource
                        f"{base_arn}/*"  # Allow related resources
                    ]
                }
            ]
        }

    def _create_deny_policy(self, resource_arn: str) -> Dict[str, Any]:
        """
        Create Deny policy document.

        Args:
            resource_arn: Resource ARN to deny

        Returns:
            dict: IAM policy document
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": resource_arn or "*"
                }
            ]
        }

    def _get_base_arn(self, method_arn: str) -> str:
        """
        Extract base ARN without method and resource path.

        Input: arn:aws:execute-api:region:account:api-id/stage/GET/resource
        Output: arn:aws:execute-api:region:account:api-id/stage
        """
        if not method_arn:
            return "*"

        try:
            # Split on '/' and take first parts (up to stage)
            parts = method_arn.split("/")
            if len(parts) >= 2:
                return "/".join(parts[:2])
        except Exception:
            pass

        return method_arn

    def _build_context(
        self,
        request: MappedRequest,
        response: AscendResponse
    ) -> Dict[str, Any]:
        """
        Build context dictionary for downstream services.

        All values are converted to strings as required by API Gateway.

        Args:
            request: Mapped request details
            response: ASCEND API response

        Returns:
            dict: Context variables
        """
        context = {
            # ASCEND response data
            "ascend_action_id": response.id,
            "ascend_status": response.status,
            "ascend_risk_score": response.risk_score,
            "ascend_risk_level": response.risk_level,
            "ascend_requires_approval": response.requires_approval,
            "ascend_alert_triggered": response.alert_triggered,
            "ascend_correlation_id": response.correlation_id or "",

            # Request context
            "ascend_agent_id": request.agent_id,
            "ascend_action_type": request.action_type,
            "ascend_environment": request.environment,
            "ascend_data_sensitivity": request.data_sensitivity,

            # Metadata
            "ascend_authorizer_version": "1.0.0"
        }

        # Add workflow ID if present
        if response.workflow_id:
            context["ascend_workflow_id"] = response.workflow_id

        return context


class PolicyCache:
    """
    Simple in-memory cache for authorization policies.

    Caches only APPROVED decisions to reduce API calls
    for repeated requests.

    Note: Lambda execution environment persists between
    invocations (warm starts), enabling caching.
    """

    def __init__(self, ttl_seconds: int = 60, max_size: int = 1000):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cache entries
            max_size: Maximum cache size
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, tuple] = {}  # key -> (policy, timestamp)

        logger.info(
            f"GW-004: Policy cache initialized - "
            f"ttl={ttl_seconds}s, max_size={max_size}"
        )

    def get(self, cache_key: str) -> Optional[AuthorizationPolicy]:
        """
        Get cached policy if valid.

        Args:
            cache_key: Cache key (from MappedRequest.cache_key)

        Returns:
            AuthorizationPolicy if cached and valid, None otherwise
        """
        import time

        entry = self._cache.get(cache_key)
        if not entry:
            return None

        policy, timestamp = entry

        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[cache_key]
            logger.debug(f"GW-004: Cache expired - {cache_key}")
            return None

        logger.debug(f"GW-004: Cache hit - {cache_key}")
        return policy

    def set(
        self,
        cache_key: str,
        policy: AuthorizationPolicy,
        response: AscendResponse
    ) -> None:
        """
        Cache policy if approved.

        Only caches APPROVED decisions. Pending/denied decisions
        should always be re-evaluated.

        Args:
            cache_key: Cache key
            policy: Authorization policy
            response: ASCEND response (to check status)
        """
        import time

        # Only cache approved decisions
        if not response.is_approved:
            logger.debug(
                f"GW-004: Not caching non-approved decision - "
                f"status={response.status}"
            )
            return

        # Enforce max size (simple LRU eviction)
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k][1]
            )
            del self._cache[oldest_key]
            logger.debug(f"GW-004: Cache eviction - {oldest_key}")

        self._cache[cache_key] = (policy, time.time())
        logger.debug(f"GW-004: Cached policy - {cache_key}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("GW-004: Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }


# Singleton instances
_generator_instance: Optional[PolicyGenerator] = None
_cache_instance: Optional[PolicyCache] = None


def get_policy_generator() -> PolicyGenerator:
    """Get or create policy generator instance."""
    global _generator_instance

    if _generator_instance is None:
        _generator_instance = PolicyGenerator()

    return _generator_instance


def get_policy_cache(ttl_seconds: int = 60) -> PolicyCache:
    """Get or create policy cache instance."""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = PolicyCache(ttl_seconds=ttl_seconds)

    return _cache_instance
