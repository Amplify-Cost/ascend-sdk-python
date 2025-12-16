--[[
ASCEND Kong Plugin - Request Handler
====================================

Main plugin logic implementing AI agent governance.

FAIL SECURE DESIGN:
- All errors result in request denial (403)
- Only explicitly approved actions proceed
- Circuit breaker prevents cascade failures

Plugin Lifecycle:
- init_worker: Initialize shared state
- access: Main authorization logic (blocks request if needed)
- log: Async metrics and logging

Author: ASCEND Platform Engineering
--]]

local constants = require "kong.plugins.ascend.constants"
local http_client  -- Lazy loaded to avoid circular dependency

local kong = kong
local ngx = ngx
local cjson = require "cjson.safe"
local fmt = string.format

-- Plugin handler object
local AscendHandler = {
    PRIORITY = constants.PRIORITY,
    VERSION = constants.VERSION
}

--------------------------------------------------------------------------------
-- Utility Functions
--------------------------------------------------------------------------------

--- Generate cache key from request attributes
-- @param agent_id Agent identifier
-- @param method HTTP method
-- @param path Request path
-- @return string Cache key
local function generate_cache_key(agent_id, method, path)
    -- Normalize path by replacing numeric IDs with placeholder
    local normalized_path = ngx.re.gsub(path, "/[0-9]+(/|$)", "/{id}$1", "jo")
    -- Also handle UUIDs
    normalized_path = ngx.re.gsub(normalized_path,
        "/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(/|$)",
        "/{id}$1", "ijo")

    return fmt("%s%s:%s:%s", constants.CACHE_PREFIX, agent_id, method, normalized_path)
end

--- Map HTTP method to action type
-- @param method HTTP method (GET, POST, etc.)
-- @return string Base action type
local function method_to_action(method)
    return constants.METHOD_ACTION_MAP[method] or "unknown"
end

--- Determine action type from path patterns
-- @param path Request path
-- @param method HTTP method
-- @param custom_mappings Custom action type mappings from config
-- @return string Action type
local function determine_action_type(path, method, custom_mappings)
    -- Check custom mappings first
    if custom_mappings then
        for pattern, action_type in pairs(custom_mappings) do
            if ngx.re.match(path, pattern, "ijo") then
                return action_type
            end
        end
    end

    -- Check built-in resource patterns
    for _, mapping in ipairs(constants.RESOURCE_PATTERNS) do
        if ngx.re.match(path, mapping.pattern, "ijo") then
            return mapping.action
        end
    end

    -- Default: method-based action with resource name
    local base_action = method_to_action(method)
    local resource = ngx.re.match(path, "^/([^/]+)", "jo")

    if resource and resource[1] then
        return fmt("%s_%s", base_action, resource[1])
    end

    return base_action
end

--- Check if path is excluded from governance
-- @param path Request path
-- @param excluded_paths List of excluded path patterns
-- @return boolean True if excluded
local function is_path_excluded(path, excluded_paths)
    if not excluded_paths or #excluded_paths == 0 then
        return false
    end

    for _, pattern in ipairs(excluded_paths) do
        if ngx.re.match(path, pattern, "ijo") then
            kong.log.debug("Path excluded from governance: ", path)
            return true
        end
    end

    return false
end

--- Extract agent ID from request
-- @param conf Plugin configuration
-- @return string|nil Agent ID or nil if not found
-- @return string|nil Error message if agent ID required but missing
local function extract_agent_id(conf)
    local agent_id = kong.request.get_header(constants.HEADERS.AGENT_ID)

    if agent_id then
        return agent_id, nil
    end

    -- Use default if configured
    if conf.default_agent_id then
        return conf.default_agent_id, nil
    end

    -- Check if required
    if conf.require_agent_id then
        return nil, "Missing required header: " .. constants.HEADERS.AGENT_ID
    end

    return nil, nil
end

--- Build request context for ASCEND API
-- @param conf Plugin configuration
-- @return table Request context
local function build_request_context(conf)
    local ctx = {
        source_ip = kong.client.get_ip(),
        request_id = kong.request.get_header(constants.HEADERS.REQUEST_ID) or ngx.var.request_id,
        timestamp = ngx.now() * 1000,  -- milliseconds
        gateway = "kong",
        gateway_version = kong.version
    }

    -- Add organization if configured
    if conf.organization_id then
        ctx.organization_id = conf.organization_id
    end

    return ctx
end

--- Build ASCEND API request payload
-- @param agent_id Agent identifier
-- @param action_type Action type
-- @param conf Plugin configuration
-- @return table API request payload
local function build_api_payload(agent_id, action_type, conf)
    local payload = {
        agent_id = agent_id,
        action_type = action_type,
        environment = conf.environment,
        data_sensitivity = conf.data_sensitivity,
        context = build_request_context(conf)
    }

    -- Optionally include request details
    if conf.include_request_body then
        local body, err = kong.request.get_body()
        if body and not err then
            -- Truncate if too large
            local body_str = cjson.encode(body)
            if body_str and #body_str <= conf.max_body_size then
                payload.request_body = body
            end
        end
    end

    return payload
end

--- Send deny response
-- @param status_code HTTP status code
-- @param error_code Error code constant
-- @param message Human-readable message
-- @param extra Additional response fields
local function deny_request(status_code, error_code, message, extra)
    local response = {
        error = error_code,
        message = message,
        timestamp = ngx.now() * 1000
    }

    -- Merge extra fields
    if extra then
        for k, v in pairs(extra) do
            response[k] = v
        end
    end

    kong.log.info(fmt("ASCEND DENY: %s - %s", error_code, message))

    return kong.response.exit(status_code, response, {
        ["Content-Type"] = "application/json",
        [constants.HEADERS.DECISION] = "denied"
    })
end

--- Allow request to proceed with governance headers
-- @param decision ASCEND decision response
local function allow_request(decision)
    -- Add governance headers for downstream services
    kong.service.request.set_header(constants.HEADERS.DECISION, "approved")
    kong.service.request.set_header(constants.HEADERS.ACTION_ID, tostring(decision.id or ""))

    if decision.risk_score then
        kong.service.request.set_header(constants.HEADERS.RISK_SCORE, tostring(decision.risk_score))
    end

    if decision.risk_level then
        kong.service.request.set_header(constants.HEADERS.RISK_LEVEL, decision.risk_level)
    end

    kong.log.info(fmt("ASCEND ALLOW: action_id=%s risk_score=%.1f",
        decision.id or "unknown", decision.risk_score or 0))
end

--------------------------------------------------------------------------------
-- Plugin Lifecycle Handlers
--------------------------------------------------------------------------------

--- Initialize worker process
function AscendHandler:init_worker()
    kong.log.info("ASCEND plugin initialized - FAIL SECURE mode")

    -- Lazy load HTTP client
    http_client = require "kong.plugins.ascend.http_client"
end

--- Main access phase handler
-- @param conf Plugin configuration
function AscendHandler:access(conf)
    local start_time = ngx.now()
    local method = kong.request.get_method()
    local path = kong.request.get_path()

    -- Store for log phase
    kong.ctx.plugin.start_time = start_time
    kong.ctx.plugin.method = method
    kong.ctx.plugin.path = path

    -- Check path exclusions
    if is_path_excluded(path, conf.excluded_paths) then
        kong.ctx.plugin.excluded = true
        return  -- Allow request
    end

    -- Extract agent ID
    local agent_id, err = extract_agent_id(conf)
    if err then
        return deny_request(
            conf.denied_status_code,
            constants.ERROR.MISSING_AGENT_ID,
            err
        )
    end

    if not agent_id then
        -- Not required, no default - allow but log warning
        kong.log.warn("No agent ID provided, skipping governance")
        kong.ctx.plugin.no_agent = true
        return
    end

    kong.ctx.plugin.agent_id = agent_id

    -- Determine action type
    local action_type = determine_action_type(path, method, conf.custom_action_types)
    kong.ctx.plugin.action_type = action_type

    -- Check cache for approved decision
    local cache_key = generate_cache_key(agent_id, method, path)

    if conf.cache_ttl > 0 then
        local cached = kong.cache:get(cache_key)
        if cached then
            kong.ctx.plugin.cache_hit = true
            kong.log.debug("Cache hit for: ", cache_key)
            allow_request(cached)
            return
        end
    end

    -- Submit to ASCEND API
    local payload = build_api_payload(agent_id, action_type, conf)
    local decision, api_err = http_client.submit_action(conf, payload)

    if api_err then
        kong.ctx.plugin.api_error = api_err

        -- FAIL SECURE: Deny on error unless fail_open configured
        if conf.fail_open then
            kong.log.warn("ASCEND API error, fail_open=true, allowing request: ", api_err)
            kong.ctx.plugin.fail_open_triggered = true
            return
        end

        return deny_request(
            conf.error_status_code,
            constants.ERROR.API_ERROR,
            "Governance service unavailable",
            { detail = api_err }
        )
    end

    kong.ctx.plugin.decision = decision

    -- Handle decision
    local status = decision.status

    if status == constants.STATUS.APPROVED then
        -- Cache approved decision
        if conf.cache_ttl > 0 then
            kong.cache:set(cache_key, decision, conf.cache_ttl)
        end

        allow_request(decision)
        return
    end

    if status == constants.STATUS.PENDING then
        -- Pending approval
        if conf.block_on_pending then
            return deny_request(
                conf.pending_status_code,
                constants.ERROR.PENDING,
                "Action requires approval",
                {
                    action_id = decision.id,
                    risk_score = decision.risk_score,
                    risk_level = decision.risk_level,
                    requires_approval = true
                }
            )
        else
            -- Allow but flag as pending
            kong.service.request.set_header(constants.HEADERS.DECISION, "pending")
            kong.service.request.set_header(constants.HEADERS.ACTION_ID, tostring(decision.id or ""))
            return
        end
    end

    if status == constants.STATUS.DENIED then
        return deny_request(
            conf.denied_status_code,
            constants.ERROR.DENIED,
            decision.denial_reason or "Action denied by governance policy",
            {
                action_id = decision.id,
                risk_score = decision.risk_score,
                risk_level = decision.risk_level,
                denial_reason = decision.denial_reason
            }
        )
    end

    -- Unknown status - FAIL SECURE
    kong.log.err("Unknown ASCEND status: ", status)
    return deny_request(
        conf.error_status_code,
        constants.ERROR.INTERNAL,
        "Invalid governance response"
    )
end

--- Log phase handler (async, after response sent)
-- @param conf Plugin configuration
function AscendHandler:log(conf)
    if not conf.log_decisions then
        return
    end

    local ctx = kong.ctx.plugin
    local latency_ms = (ngx.now() - (ctx.start_time or ngx.now())) * 1000

    -- Build log entry
    local log_entry = {
        plugin = constants.NAME,
        version = constants.VERSION,
        timestamp = ngx.now() * 1000,
        latency_ms = latency_ms,
        method = ctx.method,
        path = ctx.path,
        agent_id = ctx.agent_id,
        action_type = ctx.action_type,
        excluded = ctx.excluded or false,
        cache_hit = ctx.cache_hit or false,
        fail_open_triggered = ctx.fail_open_triggered or false
    }

    -- Add decision details
    if ctx.decision then
        log_entry.decision_status = ctx.decision.status
        log_entry.action_id = ctx.decision.id
        log_entry.risk_score = ctx.decision.risk_score
        log_entry.risk_level = ctx.decision.risk_level
    end

    -- Add error if present
    if ctx.api_error then
        log_entry.error = ctx.api_error
    end

    -- Log as JSON
    kong.log.info("ASCEND_DECISION: ", cjson.encode(log_entry))
end

return AscendHandler
