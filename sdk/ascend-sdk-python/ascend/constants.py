"""
Ascend AI SDK Constants
========================

Action types, risk levels, and other constants used across the SDK.
"""

from enum import Enum


class ActionType(str, Enum):
    """
    Standard action types for agent authorization.

    These map to policy conditions in the Ascend platform.
    """
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION = "transaction"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    SYSTEM_OPERATION = "system_operation"
    QUERY = "query"
    FILE_ACCESS = "file_access"
    API_CALL = "api_call"
    DATABASE_OPERATION = "database_operation"


class DecisionStatus(str, Enum):
    """Authorization decision statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_MODIFICATION = "requires_modification"
    TIMEOUT = "timeout"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Default configuration values
DEFAULT_API_URL = "https://pilot.owkai.app"
DEFAULT_TIMEOUT = 30
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_DECISION_TIMEOUT = 60

# Retry configuration (exponential backoff)
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF_FACTOR = 2.0
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# SDK version
SDK_VERSION = "1.0.0"
USER_AGENT = f"AscendSDK-Python/{SDK_VERSION}"

# API endpoints - Unified v1 API (single source of truth)
API_ENDPOINTS = {
    # Primary endpoints (v1 - full governance pipeline)
    "submit_action": "/api/v1/actions/submit",
    "get_action": "/api/v1/actions/{action_id}",
    "action_status": "/api/v1/actions/{action_id}/status",
    "list_actions": "/api/v1/actions",
    "approve_action": "/api/v1/actions/{action_id}/approve",
    "reject_action": "/api/v1/actions/{action_id}/reject",
    # System endpoints
    "health": "/health",
    "deployment_info": "/api/deployment-info",
}

# Environment variable names
ENV_VAR_API_KEY = "ASCEND_API_KEY"
ENV_VAR_API_URL = "ASCEND_API_URL"
ENV_VAR_DEBUG = "ASCEND_DEBUG"
