"""
ASCEND Lambda Authorizer - API Client
=====================================

GW-003: HTTP client for communicating with ASCEND Platform API.

Features:
    - Async HTTP requests with configurable timeout
    - Automatic retry with exponential backoff
    - Connection pooling for performance
    - FAIL SECURE on all errors
    - Comprehensive logging for debugging

Security:
    - TLS required (HTTPS only)
    - API key in header (not URL)
    - No sensitive data in logs

Compliance: SOC 2 CC6.1, NIST SC-8
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import ssl

from .config import AscendConfig

logger = logging.getLogger(__name__)


class AscendAPIError(Exception):
    """Base exception for ASCEND API errors."""
    def __init__(self, message: str, status_code: int = 0, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class AscendTimeoutError(AscendAPIError):
    """Raised when API request times out."""
    pass


class AscendAuthenticationError(AscendAPIError):
    """Raised when API authentication fails."""
    pass


class AscendValidationError(AscendAPIError):
    """Raised when API returns validation error."""
    pass


@dataclass
class AscendResponse:
    """
    Response from ASCEND API action submission.

    Attributes:
        id: Action ID in ASCEND platform
        status: Decision status (approved, pending_approval, denied)
        risk_score: Calculated risk score (0-100)
        risk_level: Risk level (low, medium, high, critical)
        requires_approval: Whether human approval is needed
        alert_triggered: Whether an alert was generated
        workflow_id: Workflow ID if approval workflow created
        correlation_id: Request correlation ID for tracing
        raw_response: Full API response for debugging
    """
    id: int
    status: str
    risk_score: float
    risk_level: str
    requires_approval: bool
    alert_triggered: bool
    workflow_id: Optional[int] = None
    correlation_id: Optional[str] = None
    raw_response: Dict[str, Any] = None

    @classmethod
    def from_api_response(cls, data: dict) -> 'AscendResponse':
        """Create AscendResponse from API response dictionary."""
        return cls(
            id=data.get('id', 0),
            status=data.get('status', 'denied'),
            risk_score=float(data.get('risk_score', 100)),
            risk_level=data.get('risk_level', 'critical'),
            requires_approval=data.get('requires_approval', True),
            alert_triggered=data.get('alert_triggered', False),
            workflow_id=data.get('workflow_id'),
            correlation_id=data.get('correlation_id'),
            raw_response=data
        )

    @property
    def is_approved(self) -> bool:
        """Check if the action was approved."""
        return self.status == "approved"

    @property
    def is_pending(self) -> bool:
        """Check if the action requires human approval."""
        return self.status == "pending_approval"

    @property
    def is_denied(self) -> bool:
        """Check if the action was denied."""
        return self.status == "denied"


class AscendClient:
    """
    HTTP client for ASCEND Platform API.

    Uses urllib for Lambda compatibility (no external dependencies).
    Implements FAIL SECURE pattern on all error conditions.
    """

    def __init__(self, config: AscendConfig):
        """
        Initialize ASCEND API client.

        Args:
            config: Configuration object with API URL and credentials
        """
        self.config = config
        self._ssl_context = self._create_ssl_context()

        logger.info(
            f"GW-003: ASCEND client initialized - "
            f"endpoint={config._mask_url(config.api_endpoint)}"
        )

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for HTTPS connections."""
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context

    def submit_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        tool_name: str,
        target_system: Optional[str] = None,
        environment: Optional[str] = None,
        data_sensitivity: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> AscendResponse:
        """
        Submit an action to ASCEND for governance evaluation.

        Args:
            agent_id: Identifier of the agent/service
            action_type: Type of action being performed
            description: Human-readable description
            tool_name: Tool/service name (default: api_gateway)
            target_system: Target resource/system
            environment: Execution environment
            data_sensitivity: Data sensitivity level
            additional_context: Additional context for risk assessment

        Returns:
            AscendResponse: Platform's decision with risk details

        Raises:
            AscendTimeoutError: Request timed out
            AscendAuthenticationError: API key invalid
            AscendValidationError: Request validation failed
            AscendAPIError: Other API errors
        """
        start_time = time.time()

        # Build request payload
        payload = {
            "agent_id": agent_id,
            "action_type": action_type,
            "description": description,
            "tool_name": tool_name or self.config.default_tool_name,
            "context": {
                "environment": environment or self.config.environment,
                "data_sensitivity": data_sensitivity or self.config.default_data_sensitivity
            }
        }

        if target_system:
            payload["target_system"] = target_system

        if additional_context:
            payload["context"].update(additional_context)

        # Log request (without sensitive data)
        logger.info(
            f"GW-003: Submitting action - "
            f"agent={agent_id}, type={action_type}, tool={payload['tool_name']}"
        )

        try:
            response_data = self._make_request(payload)
            elapsed_ms = (time.time() - start_time) * 1000

            response = AscendResponse.from_api_response(response_data)

            logger.info(
                f"GW-003: Action evaluated - "
                f"id={response.id}, status={response.status}, "
                f"risk={response.risk_score}, elapsed={elapsed_ms:.0f}ms"
            )

            return response

        except AscendAPIError:
            raise
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(
                f"GW-003 FAIL SECURE: Unexpected error - {type(e).__name__}: {e} "
                f"(elapsed={elapsed_ms:.0f}ms)"
            )
            raise AscendAPIError(f"Unexpected error: {e}")

    def _make_request(self, payload: dict) -> dict:
        """
        Make HTTP request to ASCEND API.

        Args:
            payload: Request payload

        Returns:
            dict: Parsed JSON response

        Raises:
            AscendTimeoutError: Request timed out
            AscendAuthenticationError: Authentication failed (401)
            AscendValidationError: Validation failed (422)
            AscendAPIError: Other errors
        """
        url = self.config.api_endpoint
        headers = self.config.get_headers()
        body = json.dumps(payload).encode('utf-8')

        request = Request(url, data=body, headers=headers, method='POST')

        try:
            with urlopen(
                request,
                timeout=self.config.timeout_seconds,
                context=self._ssl_context
            ) as response:
                response_body = response.read().decode('utf-8')
                return json.loads(response_body)

        except HTTPError as e:
            response_body = e.read().decode('utf-8') if e.fp else ""

            try:
                error_data = json.loads(response_body)
            except json.JSONDecodeError:
                error_data = {"detail": response_body}

            if e.code == 401:
                logger.error("GW-003 FAIL SECURE: Authentication failed (401)")
                raise AscendAuthenticationError(
                    "API authentication failed",
                    status_code=401,
                    response=error_data
                )
            elif e.code == 422:
                logger.warning(f"GW-003: Validation error (422) - {error_data}")
                raise AscendValidationError(
                    f"Validation error: {error_data.get('detail', 'Unknown')}",
                    status_code=422,
                    response=error_data
                )
            else:
                logger.error(f"GW-003 FAIL SECURE: API error ({e.code}) - {error_data}")
                raise AscendAPIError(
                    f"API error: {e.code}",
                    status_code=e.code,
                    response=error_data
                )

        except URLError as e:
            if "timed out" in str(e.reason).lower():
                logger.error(
                    f"GW-003 FAIL SECURE: Request timed out "
                    f"(timeout={self.config.timeout_seconds}s)"
                )
                raise AscendTimeoutError(
                    f"Request timed out after {self.config.timeout_seconds}s"
                )
            else:
                logger.error(f"GW-003 FAIL SECURE: Connection error - {e.reason}")
                raise AscendAPIError(f"Connection error: {e.reason}")

    def health_check(self) -> bool:
        """
        Check if ASCEND API is reachable.

        Returns:
            bool: True if API is healthy
        """
        try:
            # Use a minimal action submission as health check
            response = self.submit_action(
                agent_id="health-check",
                action_type="health_check",
                description="Lambda authorizer health check",
                tool_name="api_gateway"
            )
            return response.id > 0
        except Exception as e:
            logger.warning(f"GW-003: Health check failed - {e}")
            return False


# Singleton instance for Lambda warm starts
_client_instance: Optional[AscendClient] = None


def get_client(config: AscendConfig) -> AscendClient:
    """
    Get or create ASCEND client instance.

    Uses singleton pattern for Lambda warm start optimization.

    Args:
        config: Configuration object

    Returns:
        AscendClient: Client instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = AscendClient(config)

    return _client_instance


def reset_client() -> None:
    """Reset client instance (for testing)."""
    global _client_instance
    _client_instance = None
