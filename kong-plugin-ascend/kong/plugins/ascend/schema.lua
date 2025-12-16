--[[
ASCEND Kong Plugin - Configuration Schema
==========================================

Declarative schema for Kong plugin configuration.
Validates all settings before plugin activation.

Author: ASCEND Platform Engineering
--]]

local typedefs = require "kong.db.schema.typedefs"
local constants = require "kong.plugins.ascend.constants"

-- Custom field validators
local function validate_sensitivity(value)
    if not constants.VALID_SENSITIVITIES[value] then
        return nil, "invalid data_sensitivity: must be one of public, internal, confidential, restricted, standard"
    end
    return true
end

local function validate_environment(value)
    if not constants.VALID_ENVIRONMENTS[value] then
        return nil, "invalid environment: must be one of development, staging, production, test"
    end
    return true
end

local function validate_api_url(value)
    if not value or value == "" then
        return nil, "ascend_api_url is required"
    end
    if not string.match(value, "^https://") then
        return nil, "ascend_api_url must use HTTPS"
    end
    return true
end

return {
    name = constants.NAME,
    fields = {
        -- Standard Kong fields
        { consumer = typedefs.no_consumer },
        { protocols = typedefs.protocols_http },

        -- Plugin configuration
        { config = {
            type = "record",
            fields = {
                -- Required: ASCEND API Configuration
                {
                    ascend_api_url = {
                        type = "string",
                        required = true,
                        description = "ASCEND Platform API URL (must use HTTPS)",
                        custom_validator = validate_api_url
                    }
                },
                {
                    ascend_api_key = {
                        type = "string",
                        required = true,
                        encrypted = true,  -- Kong encrypts this in datastore
                        referenceable = true,  -- Can use {vault://...} reference
                        description = "ASCEND Platform API key"
                    }
                },

                -- Required: Agent identification
                {
                    default_agent_id = {
                        type = "string",
                        required = false,
                        description = "Default agent ID if X-Ascend-Agent-Id header not present"
                    }
                },
                {
                    require_agent_id = {
                        type = "boolean",
                        default = true,
                        description = "Require X-Ascend-Agent-Id header (403 if missing)"
                    }
                },

                -- Behavior configuration
                {
                    fail_open = {
                        type = "boolean",
                        default = false,  -- FAIL SECURE by default
                        description = "Allow requests when ASCEND API is unavailable (NOT RECOMMENDED)"
                    }
                },
                {
                    block_on_pending = {
                        type = "boolean",
                        default = true,
                        description = "Block requests that require approval"
                    }
                },

                -- Context for ASCEND API
                {
                    environment = {
                        type = "string",
                        default = constants.DEFAULTS.ENVIRONMENT,
                        description = "Deployment environment",
                        custom_validator = validate_environment
                    }
                },
                {
                    data_sensitivity = {
                        type = "string",
                        default = constants.DEFAULTS.DATA_SENSITIVITY,
                        description = "Default data sensitivity level",
                        custom_validator = validate_sensitivity
                    }
                },
                {
                    organization_id = {
                        type = "string",
                        required = false,
                        description = "Organization ID for multi-tenant deployments"
                    }
                },

                -- Performance tuning
                {
                    timeout_ms = {
                        type = "integer",
                        default = constants.DEFAULTS.TIMEOUT_MS,
                        between = { 100, 30000 },
                        description = "ASCEND API timeout in milliseconds"
                    }
                },
                {
                    cache_ttl = {
                        type = "integer",
                        default = constants.DEFAULTS.CACHE_TTL,
                        between = { 0, 3600 },
                        description = "Cache TTL for approved decisions (0 to disable)"
                    }
                },
                {
                    retry_count = {
                        type = "integer",
                        default = constants.DEFAULTS.RETRY_COUNT,
                        between = { 0, 5 },
                        description = "Number of retry attempts on failure"
                    }
                },
                {
                    retry_delay_ms = {
                        type = "integer",
                        default = constants.DEFAULTS.RETRY_DELAY_MS,
                        between = { 10, 5000 },
                        description = "Delay between retries in milliseconds"
                    }
                },

                -- Circuit breaker configuration
                {
                    circuit_breaker_enabled = {
                        type = "boolean",
                        default = true,
                        description = "Enable circuit breaker for API resilience"
                    }
                },
                {
                    circuit_breaker_threshold = {
                        type = "integer",
                        default = constants.DEFAULTS.CIRCUIT_BREAKER_THRESHOLD,
                        between = { 1, 100 },
                        description = "Failures before circuit opens"
                    }
                },
                {
                    circuit_breaker_reset_ms = {
                        type = "integer",
                        default = constants.DEFAULTS.CIRCUIT_BREAKER_RESET_MS,
                        between = { 1000, 300000 },
                        description = "Time before circuit half-opens (ms)"
                    }
                },

                -- Logging and debugging
                {
                    log_decisions = {
                        type = "boolean",
                        default = true,
                        description = "Log all authorization decisions"
                    }
                },
                {
                    include_request_body = {
                        type = "boolean",
                        default = false,
                        description = "Include request body in ASCEND submission (privacy consideration)"
                    }
                },
                {
                    max_body_size = {
                        type = "integer",
                        default = 10240,  -- 10KB
                        between = { 0, 1048576 },  -- Max 1MB
                        description = "Maximum request body size to include"
                    }
                },

                -- Path exclusions (bypass governance)
                {
                    excluded_paths = {
                        type = "array",
                        elements = { type = "string" },
                        default = {},
                        description = "Paths to exclude from governance (e.g., /health, /metrics)"
                    }
                },

                -- Custom action type mapping
                {
                    custom_action_types = {
                        type = "map",
                        keys = { type = "string" },
                        values = { type = "string" },
                        default = {},
                        description = "Custom path pattern to action_type mapping"
                    }
                },

                -- Response customization
                {
                    denied_status_code = {
                        type = "integer",
                        default = 403,
                        one_of = { 403, 401, 451 },
                        description = "HTTP status code for denied requests"
                    }
                },
                {
                    pending_status_code = {
                        type = "integer",
                        default = 403,
                        one_of = { 403, 202, 429 },
                        description = "HTTP status code for pending approval"
                    }
                },
                {
                    error_status_code = {
                        type = "integer",
                        default = 503,
                        one_of = { 500, 502, 503 },
                        description = "HTTP status code for ASCEND API errors"
                    }
                }
            }
        }}
    },

    -- Entity checks (cross-field validation)
    entity_checks = {
        {
            -- If fail_open is true, log a warning
            custom_entity_check = {
                field_sources = { "config.fail_open" },
                fn = function(entity)
                    if entity.config.fail_open then
                        kong.log.warn("ASCEND plugin configured with fail_open=true - NOT RECOMMENDED for production")
                    end
                    return true
                end
            }
        },
        {
            -- Require default_agent_id if require_agent_id is false
            conditional = {
                if_field = "config.require_agent_id",
                if_match = { eq = false },
                then_field = "config.default_agent_id",
                then_match = { required = true }
            }
        }
    }
}
