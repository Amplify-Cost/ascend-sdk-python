"""
ASCEND Lambda Authorizer - Request Mapper
==========================================

GW-002: Maps API Gateway authorizer events to ASCEND action format.

Supported Event Types:
    - REQUEST authorizer (API Gateway REST API)
    - TOKEN authorizer (API Gateway REST API)
    - HTTP API v2 (API Gateway HTTP API)

Header Extraction:
    - X-Ascend-Agent-Id: Agent identifier (required)
    - X-Ascend-Environment: Execution environment (optional)
    - X-Ascend-Data-Sensitivity: Data sensitivity level (optional)
    - X-Ascend-Target-System: Target resource (optional)

Action Type Mapping:
    - HTTP method + resource path determines action_type
    - Supports custom action type via X-Ascend-Action-Type header

Compliance: SOC 2 CC6.1, NIST AC-3
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

from .config import validate_environment, validate_data_sensitivity

logger = logging.getLogger(__name__)


class RequestMappingError(Exception):
    """Raised when request mapping fails."""
    pass


@dataclass
class MappedRequest:
    """
    Mapped request ready for ASCEND API submission.

    Attributes:
        agent_id: Identifier of the calling agent/service
        action_type: Type of action being performed
        description: Human-readable action description
        tool_name: Always "api_gateway" for Lambda authorizer
        target_system: Target resource/system
        environment: Execution environment
        data_sensitivity: Data sensitivity level
        source_ip: Caller's IP address
        user_agent: Caller's user agent
        method_arn: Full method ARN for policy generation
        resource_path: API resource path
        http_method: HTTP method
        context: Additional context for risk assessment
    """
    agent_id: str
    action_type: str
    description: str
    tool_name: str
    target_system: Optional[str]
    environment: str
    data_sensitivity: str
    source_ip: Optional[str]
    user_agent: Optional[str]
    method_arn: str
    resource_path: str
    http_method: str
    context: Dict[str, Any]

    @property
    def cache_key(self) -> str:
        """Generate cache key for this request."""
        # Normalize resource path (remove IDs)
        normalized_path = self._normalize_path(self.resource_path)
        return f"{self.agent_id}:{self.action_type}:{normalized_path}"

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize resource path for caching.

        Replaces dynamic segments (IDs, UUIDs) with placeholders.
        Example: /users/123/orders/abc-def → /users/{id}/orders/{id}
        """
        # Replace numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=/|$)',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        return path


class RequestMapper:
    """
    Maps API Gateway events to ASCEND action format.

    Supports multiple API Gateway event formats and extracts
    relevant information for governance evaluation.
    """

    # HTTP method to action type base mapping
    METHOD_ACTION_MAP = {
        "GET": "read",
        "HEAD": "read",
        "OPTIONS": "read",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete"
    }

    # Resource patterns for action type refinement
    RESOURCE_ACTION_PATTERNS = {
        r"/admin": "admin_access",
        r"/users?/\d+": "user_data_access",
        r"/auth|/login|/logout": "authentication",
        r"/settings|/config": "configuration",
        r"/export|/download": "data_export",
        r"/upload|/import": "data_import",
        r"/execute|/run": "execution",
        r"/approve|/reject": "approval_action",
        r"/delete": "data_deletion",
        r"/pii|/sensitive": "sensitive_data_access"
    }

    def __init__(self, default_environment: str = "production"):
        """
        Initialize request mapper.

        Args:
            default_environment: Default environment if not in headers
        """
        self.default_environment = default_environment

    def map_event(self, event: dict) -> MappedRequest:
        """
        Map API Gateway event to ASCEND action format.

        Args:
            event: API Gateway authorizer event

        Returns:
            MappedRequest: Mapped request for ASCEND

        Raises:
            RequestMappingError: If mapping fails
        """
        try:
            # Detect event type and extract accordingly
            if self._is_http_api_v2(event):
                return self._map_http_api_v2(event)
            elif self._is_request_authorizer(event):
                return self._map_request_authorizer(event)
            elif self._is_token_authorizer(event):
                return self._map_token_authorizer(event)
            else:
                raise RequestMappingError("Unknown event format")

        except RequestMappingError:
            raise
        except Exception as e:
            logger.error(f"GW-002: Request mapping failed - {e}")
            raise RequestMappingError(f"Request mapping failed: {e}")

    def _is_http_api_v2(self, event: dict) -> bool:
        """Check if event is HTTP API v2 format."""
        return "version" in event and event.get("version") == "2.0"

    def _is_request_authorizer(self, event: dict) -> bool:
        """Check if event is REQUEST type authorizer."""
        return "type" in event and event.get("type") == "REQUEST"

    def _is_token_authorizer(self, event: dict) -> bool:
        """Check if event is TOKEN type authorizer."""
        return "type" in event and event.get("type") == "TOKEN"

    def _map_request_authorizer(self, event: dict) -> MappedRequest:
        """Map REQUEST type authorizer event."""
        headers = self._normalize_headers(event.get("headers", {}))

        # Extract required agent ID
        agent_id = self._extract_agent_id(headers, event)
        if not agent_id:
            raise RequestMappingError(
                "Missing required header: X-Ascend-Agent-Id"
            )

        # Extract request details
        method_arn = event.get("methodArn", "")
        http_method = event.get("httpMethod", event.get("requestContext", {}).get("httpMethod", "GET"))
        resource_path = event.get("path", event.get("resource", "/"))

        # Determine action type
        action_type = self._determine_action_type(
            http_method,
            resource_path,
            headers.get("x-ascend-action-type")
        )

        # Build description
        description = self._build_description(http_method, resource_path, agent_id)

        # Extract optional headers
        environment = validate_environment(
            headers.get("x-ascend-environment", self.default_environment)
        )
        data_sensitivity = validate_data_sensitivity(
            headers.get("x-ascend-data-sensitivity", "none")
        )
        target_system = headers.get("x-ascend-target-system", resource_path)

        # Request context
        request_context = event.get("requestContext", {})
        source_ip = request_context.get("identity", {}).get("sourceIp")
        user_agent = headers.get("user-agent")

        return MappedRequest(
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            tool_name="api_gateway",
            target_system=target_system,
            environment=environment,
            data_sensitivity=data_sensitivity,
            source_ip=source_ip,
            user_agent=user_agent,
            method_arn=method_arn,
            resource_path=resource_path,
            http_method=http_method,
            context=self._build_context(event, headers)
        )

    def _map_token_authorizer(self, event: dict) -> MappedRequest:
        """
        Map TOKEN type authorizer event.

        TOKEN authorizers have limited context, so we extract
        agent ID from the token itself or use a default.
        """
        method_arn = event.get("methodArn", "")
        auth_token = event.get("authorizationToken", "")

        # Parse method ARN for details
        arn_parts = self._parse_method_arn(method_arn)

        # Extract agent ID from token prefix (e.g., "Agent-xxx:token")
        agent_id = self._extract_agent_id_from_token(auth_token)
        if not agent_id:
            raise RequestMappingError(
                "Cannot determine agent ID from TOKEN authorizer. "
                "Use REQUEST authorizer or include agent ID in token prefix."
            )

        action_type = self._determine_action_type(
            arn_parts.get("http_method", "GET"),
            arn_parts.get("resource", "/"),
            None
        )

        description = self._build_description(
            arn_parts.get("http_method", "GET"),
            arn_parts.get("resource", "/"),
            agent_id
        )

        return MappedRequest(
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            tool_name="api_gateway",
            target_system=arn_parts.get("resource", "/"),
            environment=self.default_environment,
            data_sensitivity="none",
            source_ip=None,
            user_agent=None,
            method_arn=method_arn,
            resource_path=arn_parts.get("resource", "/"),
            http_method=arn_parts.get("http_method", "GET"),
            context={"authorizer_type": "TOKEN"}
        )

    def _map_http_api_v2(self, event: dict) -> MappedRequest:
        """Map HTTP API v2 (payload format 2.0) event."""
        headers = self._normalize_headers(event.get("headers", {}))

        # Extract required agent ID
        agent_id = self._extract_agent_id(headers, event)
        if not agent_id:
            raise RequestMappingError(
                "Missing required header: X-Ascend-Agent-Id"
            )

        # Extract from routeArn (HTTP API format)
        route_arn = event.get("routeArn", "")
        request_context = event.get("requestContext", {})
        http = request_context.get("http", {})

        http_method = http.get("method", "GET")
        resource_path = http.get("path", "/")

        action_type = self._determine_action_type(
            http_method,
            resource_path,
            headers.get("x-ascend-action-type")
        )

        description = self._build_description(http_method, resource_path, agent_id)

        environment = validate_environment(
            headers.get("x-ascend-environment", self.default_environment)
        )
        data_sensitivity = validate_data_sensitivity(
            headers.get("x-ascend-data-sensitivity", "none")
        )

        return MappedRequest(
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            tool_name="api_gateway",
            target_system=headers.get("x-ascend-target-system", resource_path),
            environment=environment,
            data_sensitivity=data_sensitivity,
            source_ip=http.get("sourceIp"),
            user_agent=headers.get("user-agent"),
            method_arn=route_arn,
            resource_path=resource_path,
            http_method=http_method,
            context=self._build_context(event, headers)
        )

    def _extract_agent_id(self, headers: dict, event: dict) -> Optional[str]:
        """
        Extract agent ID from headers or event context.

        Priority:
        1. X-Ascend-Agent-Id header
        2. requestContext.authorizer.principalId
        3. requestContext.identity.caller
        """
        # Try header first
        agent_id = headers.get("x-ascend-agent-id")
        if agent_id:
            return agent_id

        # Try request context
        request_context = event.get("requestContext", {})

        # Check authorizer context
        authorizer = request_context.get("authorizer", {})
        if authorizer.get("principalId"):
            return authorizer["principalId"]

        # Check identity
        identity = request_context.get("identity", {})
        if identity.get("caller"):
            return identity["caller"]

        return None

    def _extract_agent_id_from_token(self, token: str) -> Optional[str]:
        """Extract agent ID from token prefix (Agent-xxx:token)."""
        if not token:
            return None

        # Remove Bearer prefix if present
        if token.lower().startswith("bearer "):
            token = token[7:]

        # Check for Agent-xxx: prefix
        if ":" in token:
            prefix = token.split(":")[0]
            if prefix.startswith("Agent-"):
                return prefix

        return None

    def _determine_action_type(
        self,
        http_method: str,
        resource_path: str,
        custom_action_type: Optional[str]
    ) -> str:
        """
        Determine action type from HTTP method and resource path.

        Args:
            http_method: HTTP method (GET, POST, etc.)
            resource_path: API resource path
            custom_action_type: Custom action type from header (overrides)

        Returns:
            str: Action type for ASCEND
        """
        # Custom action type takes precedence
        if custom_action_type:
            return custom_action_type

        # Base action from HTTP method
        base_action = self.METHOD_ACTION_MAP.get(http_method.upper(), "unknown")

        # Refine based on resource path
        for pattern, action in self.RESOURCE_ACTION_PATTERNS.items():
            if re.search(pattern, resource_path, re.IGNORECASE):
                return action

        # Combine method and simplified path
        path_part = resource_path.strip("/").split("/")[0] if resource_path else "api"
        return f"{base_action}_{path_part}" if path_part else base_action

    def _build_description(
        self,
        http_method: str,
        resource_path: str,
        agent_id: str
    ) -> str:
        """Build human-readable action description."""
        return f"{http_method} {resource_path} by {agent_id} via API Gateway"

    def _build_context(self, event: dict, headers: dict) -> Dict[str, Any]:
        """Build context dictionary for ASCEND."""
        request_context = event.get("requestContext", {})

        return {
            "authorizer_type": event.get("type", "REQUEST"),
            "api_id": request_context.get("apiId"),
            "stage": request_context.get("stage"),
            "account_id": request_context.get("accountId"),
            "request_id": request_context.get("requestId"),
            "domain_name": request_context.get("domainName"),
            "query_params": event.get("queryStringParameters", {}),
            "path_params": event.get("pathParameters", {})
        }

    def _normalize_headers(self, headers: dict) -> dict:
        """Normalize header names to lowercase."""
        if not headers:
            return {}
        return {k.lower(): v for k, v in headers.items()}

    def _parse_method_arn(self, method_arn: str) -> dict:
        """
        Parse method ARN to extract components.

        Format: arn:aws:execute-api:region:account:api-id/stage/method/resource
        """
        result = {
            "region": "",
            "account_id": "",
            "api_id": "",
            "stage": "",
            "http_method": "GET",
            "resource": "/"
        }

        if not method_arn:
            return result

        try:
            parts = method_arn.split(":")
            if len(parts) >= 6:
                result["region"] = parts[3]
                result["account_id"] = parts[4]

                # Parse the rest (api-id/stage/method/resource)
                rest = parts[5].split("/")
                if len(rest) >= 1:
                    result["api_id"] = rest[0]
                if len(rest) >= 2:
                    result["stage"] = rest[1]
                if len(rest) >= 3:
                    result["http_method"] = rest[2]
                if len(rest) >= 4:
                    result["resource"] = "/" + "/".join(rest[3:])
        except Exception as e:
            logger.warning(f"GW-002: Failed to parse method ARN: {e}")

        return result


# Default mapper instance
_mapper_instance: Optional[RequestMapper] = None


def get_mapper(default_environment: str = "production") -> RequestMapper:
    """Get or create mapper instance."""
    global _mapper_instance

    if _mapper_instance is None:
        _mapper_instance = RequestMapper(default_environment)

    return _mapper_instance
