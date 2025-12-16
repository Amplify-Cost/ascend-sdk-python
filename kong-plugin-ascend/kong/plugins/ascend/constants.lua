--[[
ASCEND Kong Plugin - Constants
==============================

Shared constants for the ASCEND governance plugin.

Author: ASCEND Platform Engineering
--]]

local constants = {
    -- Plugin metadata
    NAME = "ascend",
    VERSION = "1.0.0",
    PRIORITY = 900,  -- After auth plugins, before proxy

    -- HTTP methods to action type mapping
    METHOD_ACTION_MAP = {
        GET = "read",
        POST = "create",
        PUT = "update",
        PATCH = "update",
        DELETE = "delete",
        HEAD = "read",
        OPTIONS = "read"
    },

    -- Resource patterns for special action types
    -- Pattern → action_type suffix
    RESOURCE_PATTERNS = {
        { pattern = "^/admin", action = "admin_access" },
        { pattern = "^/export", action = "data_export" },
        { pattern = "^/import", action = "data_import" },
        { pattern = "^/batch", action = "batch_operation" },
        { pattern = "^/bulk", action = "bulk_operation" },
        { pattern = "/users?/", action = "user_data_access" },
        { pattern = "/customers?/", action = "customer_data_access" },
        { pattern = "/payment", action = "payment_operation" },
        { pattern = "/billing", action = "billing_operation" },
        { pattern = "/config", action = "config_change" },
        { pattern = "/settings", action = "settings_change" },
        { pattern = "/audit", action = "audit_access" },
        { pattern = "/logs?", action = "log_access" },
        { pattern = "/reports?", action = "report_access" },
        { pattern = "/analytics", action = "analytics_access" },
        { pattern = "/dashboard", action = "dashboard_access" },
        { pattern = "/api.?keys?", action = "api_key_management" },
        { pattern = "/tokens?", action = "token_management" },
        { pattern = "/secrets?", action = "secret_access" },
        { pattern = "/credentials?", action = "credential_access" }
    },

    -- ASCEND API response statuses
    STATUS = {
        APPROVED = "approved",
        PENDING = "pending_approval",
        DENIED = "denied"
    },

    -- Risk levels
    RISK_LEVEL = {
        LOW = "low",
        MEDIUM = "medium",
        HIGH = "high",
        CRITICAL = "critical"
    },

    -- Default configuration values
    DEFAULTS = {
        TIMEOUT_MS = 5000,
        CACHE_TTL = 60,
        RETRY_COUNT = 2,
        RETRY_DELAY_MS = 100,
        CIRCUIT_BREAKER_THRESHOLD = 5,
        CIRCUIT_BREAKER_RESET_MS = 30000,
        DATA_SENSITIVITY = "standard",
        ENVIRONMENT = "production"
    },

    -- HTTP headers
    HEADERS = {
        AGENT_ID = "X-Ascend-Agent-Id",
        API_KEY = "X-API-Key",
        REQUEST_ID = "X-Request-Id",
        ACTION_ID = "X-Ascend-Action-Id",
        RISK_SCORE = "X-Ascend-Risk-Score",
        RISK_LEVEL = "X-Ascend-Risk-Level",
        DECISION = "X-Ascend-Decision",
        CONTENT_TYPE = "Content-Type"
    },

    -- Error codes
    ERROR = {
        MISSING_AGENT_ID = "MISSING_AGENT_ID",
        API_ERROR = "ASCEND_API_ERROR",
        TIMEOUT = "ASCEND_TIMEOUT",
        CIRCUIT_OPEN = "CIRCUIT_BREAKER_OPEN",
        DENIED = "ACCESS_DENIED",
        PENDING = "PENDING_APPROVAL",
        INTERNAL = "INTERNAL_ERROR"
    },

    -- Cache key prefix
    CACHE_PREFIX = "ascend:decision:",

    -- Shared dict names
    SHARED_DICT = {
        CIRCUIT_BREAKER = "ascend_circuit_breaker",
        CACHE = "ascend_cache"
    },

    -- Valid data sensitivity levels
    VALID_SENSITIVITIES = {
        public = true,
        internal = true,
        confidential = true,
        restricted = true,
        standard = true
    },

    -- Valid environments
    VALID_ENVIRONMENTS = {
        development = true,
        staging = true,
        production = true,
        test = true
    }
}

return constants
