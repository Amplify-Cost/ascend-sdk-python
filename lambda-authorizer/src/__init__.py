"""
ASCEND Lambda Authorizer
========================

Zero-code AI governance for AWS API Gateway.

This Lambda authorizer integrates with the ASCEND Platform to provide
real-time governance decisions for AI agent API calls.

Features:
    - Real-time risk assessment via ASCEND Platform
    - FAIL SECURE design - errors result in denial
    - Caching for approved decisions
    - CloudWatch metrics and structured logging
    - Support for REST API and HTTP API

Usage:
    Deploy as Lambda authorizer in API Gateway and configure
    environment variables for ASCEND API access.

Environment Variables:
    ASCEND_API_URL: ASCEND platform API URL (required)
    ASCEND_API_KEY: API key for authentication (required)
    ASCEND_ENVIRONMENT: Environment context (default: production)
    ASCEND_CACHE_TTL: Cache TTL in seconds (default: 60)
    ASCEND_TIMEOUT: API timeout in seconds (default: 4)

Compliance: SOC 2, NIST 800-53, PCI-DSS
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "ASCEND Platform Engineering"

from .handler import lambda_handler
from .config import load_config, AscendConfig, ConfigurationError
from .ascend_client import (
    AscendClient,
    AscendResponse,
    AscendAPIError,
    AscendTimeoutError,
    AscendAuthenticationError,
    AscendValidationError
)
from .request_mapper import RequestMapper, MappedRequest, RequestMappingError
from .policy_generator import PolicyGenerator, AuthorizationPolicy, PolicyCache
from .cloudwatch import (
    AuthorizationMetrics,
    StructuredLogger,
    MetricsPublisher,
    track_authorization
)

__all__ = [
    # Main handler
    "lambda_handler",

    # Configuration
    "load_config",
    "AscendConfig",
    "ConfigurationError",

    # API Client
    "AscendClient",
    "AscendResponse",
    "AscendAPIError",
    "AscendTimeoutError",
    "AscendAuthenticationError",
    "AscendValidationError",

    # Request Mapping
    "RequestMapper",
    "MappedRequest",
    "RequestMappingError",

    # Policy Generation
    "PolicyGenerator",
    "AuthorizationPolicy",
    "PolicyCache",

    # Observability
    "AuthorizationMetrics",
    "StructuredLogger",
    "MetricsPublisher",
    "track_authorization"
]
