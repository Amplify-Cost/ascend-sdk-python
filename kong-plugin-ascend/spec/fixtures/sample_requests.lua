--[[
ASCEND Kong Plugin - Test Fixtures
==================================

Sample request/response data for testing.

Author: ASCEND Platform Engineering
--]]

local _M = {}

-- Sample approved response
_M.approved_response = {
    id = 12345,
    status = "approved",
    risk_score = 25.0,
    risk_level = "low",
    requires_approval = false,
    alert_triggered = false,
    processing_time_ms = 45
}

-- Sample denied response
_M.denied_response = {
    id = 12346,
    status = "denied",
    risk_score = 95.0,
    risk_level = "critical",
    requires_approval = false,
    denial_reason = "Action violates security policy: unauthorized admin access",
    matched_rules = {
        "block_admin_access_from_unknown_agents",
        "require_approval_for_critical_operations"
    }
}

-- Sample pending response
_M.pending_response = {
    id = 12347,
    status = "pending_approval",
    risk_score = 75.0,
    risk_level = "high",
    requires_approval = true,
    alert_triggered = true,
    approvers = {
        "security-team@example.com"
    }
}

-- Sample API request events
_M.get_users_request = {
    method = "GET",
    path = "/api/v1/users",
    headers = {
        ["X-Ascend-Agent-Id"] = "test-agent-001",
        ["Content-Type"] = "application/json",
        ["X-Request-Id"] = "req-12345"
    },
    query_params = {
        page = "1",
        limit = "100"
    }
}

_M.create_user_request = {
    method = "POST",
    path = "/api/v1/users",
    headers = {
        ["X-Ascend-Agent-Id"] = "test-agent-001",
        ["Content-Type"] = "application/json"
    },
    body = {
        email = "test@example.com",
        name = "Test User"
    }
}

_M.delete_user_request = {
    method = "DELETE",
    path = "/api/v1/users/12345",
    headers = {
        ["X-Ascend-Agent-Id"] = "test-agent-001"
    }
}

_M.admin_request = {
    method = "POST",
    path = "/admin/settings",
    headers = {
        ["X-Ascend-Agent-Id"] = "test-agent-001"
    }
}

_M.payment_request = {
    method = "POST",
    path = "/api/v1/payments/process",
    headers = {
        ["X-Ascend-Agent-Id"] = "payment-agent"
    },
    body = {
        amount = 1000.00,
        currency = "USD"
    }
}

-- Sample configurations
_M.default_config = {
    ascend_api_url = "https://test.ascend.owkai.app",
    ascend_api_key = "test_api_key_12345",
    require_agent_id = true,
    fail_open = false,
    block_on_pending = true,
    environment = "test",
    data_sensitivity = "standard",
    timeout_ms = 5000,
    cache_ttl = 60,
    retry_count = 2,
    retry_delay_ms = 100,
    circuit_breaker_enabled = true,
    circuit_breaker_threshold = 5,
    circuit_breaker_reset_ms = 30000,
    log_decisions = true,
    excluded_paths = { "^/health$", "^/metrics$", "^/ready$" },
    custom_action_types = {},
    denied_status_code = 403,
    pending_status_code = 403,
    error_status_code = 503
}

_M.fail_open_config = {
    ascend_api_url = "https://test.ascend.owkai.app",
    ascend_api_key = "test_api_key_12345",
    require_agent_id = true,
    fail_open = true,  -- NOT RECOMMENDED
    block_on_pending = true,
    environment = "test",
    data_sensitivity = "standard",
    timeout_ms = 5000,
    cache_ttl = 60,
    retry_count = 0,  -- No retries in fail_open
    circuit_breaker_enabled = false
}

_M.strict_config = {
    ascend_api_url = "https://test.ascend.owkai.app",
    ascend_api_key = "test_api_key_12345",
    require_agent_id = true,
    fail_open = false,
    block_on_pending = true,
    environment = "production",
    data_sensitivity = "restricted",
    timeout_ms = 3000,
    cache_ttl = 30,
    retry_count = 3,
    retry_delay_ms = 50,
    circuit_breaker_enabled = true,
    circuit_breaker_threshold = 3,
    circuit_breaker_reset_ms = 60000,
    denied_status_code = 403,
    pending_status_code = 403,
    error_status_code = 503
}

-- Expected action type mappings
_M.action_type_mappings = {
    { path = "/api/v1/users", method = "GET", expected = "read_users" },
    { path = "/api/v1/users", method = "POST", expected = "user_data_access" },
    { path = "/api/v1/users/123", method = "DELETE", expected = "user_data_access" },
    { path = "/admin/settings", method = "POST", expected = "admin_access" },
    { path = "/api/v1/payments/process", method = "POST", expected = "payment_operation" },
    { path = "/api/v1/export/report", method = "GET", expected = "data_export" },
    { path = "/api/v1/config", method = "PUT", expected = "config_change" },
    { path = "/api/v1/audit/logs", method = "GET", expected = "audit_access" }
}

-- Error scenarios
_M.error_scenarios = {
    timeout = {
        error = "Connection timeout after 5000ms",
        expected_status = 503,
        expected_code = "ASCEND_API_ERROR"
    },
    auth_failure = {
        error = "Authentication failed: invalid API key",
        expected_status = 503,
        expected_code = "ASCEND_API_ERROR"
    },
    rate_limited = {
        error = "Rate limited by ASCEND API",
        expected_status = 503,
        expected_code = "ASCEND_API_ERROR"
    },
    server_error = {
        error = "ASCEND API server error: 500",
        expected_status = 503,
        expected_code = "ASCEND_API_ERROR"
    },
    circuit_open = {
        error = "Circuit breaker open - ASCEND API temporarily unavailable",
        expected_status = 503,
        expected_code = "CIRCUIT_BREAKER_OPEN"
    }
}

return _M
