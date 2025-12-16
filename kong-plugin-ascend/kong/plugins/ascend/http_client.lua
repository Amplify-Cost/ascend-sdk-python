--[[
ASCEND Kong Plugin - HTTP Client
================================

HTTP client for ASCEND Platform API with:
- Connection pooling (via resty.http)
- Retry with exponential backoff
- Circuit breaker pattern
- Timeout handling

FAIL SECURE: All errors return nil + error message

Author: ASCEND Platform Engineering
--]]

local http = require "resty.http"
local cjson = require "cjson.safe"
local constants = require "kong.plugins.ascend.constants"

local kong = kong
local ngx = ngx
local fmt = string.format

local _M = {}

--------------------------------------------------------------------------------
-- Circuit Breaker Implementation
--------------------------------------------------------------------------------

local CircuitBreaker = {}
CircuitBreaker.__index = CircuitBreaker

--- Create new circuit breaker instance
-- @param name Circuit breaker name
-- @param threshold Failure threshold before opening
-- @param reset_ms Time in ms before half-open
-- @return CircuitBreaker instance
function CircuitBreaker.new(name, threshold, reset_ms)
    local self = setmetatable({}, CircuitBreaker)
    self.name = name
    self.threshold = threshold or 5
    self.reset_ms = reset_ms or 30000
    self.dict_name = constants.SHARED_DICT.CIRCUIT_BREAKER

    -- Keys in shared dict
    self.failure_key = fmt("cb:%s:failures", name)
    self.open_key = fmt("cb:%s:open_at", name)

    return self
end

--- Get shared dict (lazy)
-- @return ngx.shared dict or nil
function CircuitBreaker:get_dict()
    local dict = ngx.shared[self.dict_name]
    if not dict then
        kong.log.warn("Circuit breaker shared dict not available: ", self.dict_name)
    end
    return dict
end

--- Check if circuit is open
-- @return boolean True if circuit is open (should not make requests)
function CircuitBreaker:is_open()
    local dict = self:get_dict()
    if not dict then
        return false  -- No dict, circuit is closed
    end

    local open_at = dict:get(self.open_key)
    if not open_at then
        return false
    end

    -- Check if reset time has passed (half-open)
    local now = ngx.now() * 1000
    if now - open_at >= self.reset_ms then
        -- Half-open: allow one request to test
        kong.log.info("Circuit breaker half-open, testing: ", self.name)
        return false
    end

    return true
end

--- Record a successful request
function CircuitBreaker:record_success()
    local dict = self:get_dict()
    if not dict then
        return
    end

    -- Reset failure count and close circuit
    dict:set(self.failure_key, 0)
    dict:delete(self.open_key)

    kong.log.debug("Circuit breaker success recorded: ", self.name)
end

--- Record a failed request
-- @return boolean True if circuit just opened
function CircuitBreaker:record_failure()
    local dict = self:get_dict()
    if not dict then
        return false
    end

    -- Increment failure count
    local failures, err = dict:incr(self.failure_key, 1, 0)
    if err then
        kong.log.err("Circuit breaker incr error: ", err)
        return false
    end

    kong.log.debug(fmt("Circuit breaker failure %d/%d: %s",
        failures, self.threshold, self.name))

    -- Check if threshold reached
    if failures >= self.threshold then
        -- Open the circuit
        local now = ngx.now() * 1000
        dict:set(self.open_key, now)
        dict:set(self.failure_key, 0)  -- Reset for next cycle

        kong.log.warn(fmt("Circuit breaker OPEN: %s (failures=%d, reset_ms=%d)",
            self.name, failures, self.reset_ms))

        return true
    end

    return false
end

--- Get circuit state for diagnostics
-- @return table State information
function CircuitBreaker:get_state()
    local dict = self:get_dict()
    if not dict then
        return { state = "unknown", dict_missing = true }
    end

    local failures = dict:get(self.failure_key) or 0
    local open_at = dict:get(self.open_key)
    local now = ngx.now() * 1000

    local state
    if open_at then
        if now - open_at >= self.reset_ms then
            state = "half-open"
        else
            state = "open"
        end
    else
        state = "closed"
    end

    return {
        state = state,
        failures = failures,
        threshold = self.threshold,
        open_at = open_at,
        reset_ms = self.reset_ms
    }
end

-- Module-level circuit breaker instance
local circuit_breaker

--------------------------------------------------------------------------------
-- HTTP Client Functions
--------------------------------------------------------------------------------

--- Initialize HTTP client module
-- @param conf Plugin configuration
local function init_circuit_breaker(conf)
    if not circuit_breaker and conf.circuit_breaker_enabled then
        circuit_breaker = CircuitBreaker.new(
            "ascend_api",
            conf.circuit_breaker_threshold,
            conf.circuit_breaker_reset_ms
        )
    end
end

--- Make HTTP request to ASCEND API
-- @param conf Plugin configuration
-- @param payload Request payload
-- @return table|nil Response body or nil on error
-- @return string|nil Error message
local function make_request(conf, payload)
    local httpc = http.new()

    -- Set timeout
    httpc:set_timeout(conf.timeout_ms)

    -- Build URL
    local url = conf.ascend_api_url .. "/api/v1/actions/submit"

    -- Encode payload
    local body = cjson.encode(payload)
    if not body then
        return nil, "Failed to encode request payload"
    end

    -- Make request
    local res, err = httpc:request_uri(url, {
        method = "POST",
        body = body,
        headers = {
            [constants.HEADERS.CONTENT_TYPE] = "application/json",
            [constants.HEADERS.API_KEY] = conf.ascend_api_key
        },
        ssl_verify = true,
        keepalive_timeout = 60000,  -- 60s connection pooling
        keepalive_pool = 10
    })

    if not res then
        return nil, fmt("HTTP request failed: %s", err or "unknown error")
    end

    -- Check status code
    if res.status == 401 then
        return nil, "Authentication failed: invalid API key"
    end

    if res.status == 403 then
        return nil, "Authorization failed: API key lacks permission"
    end

    if res.status == 429 then
        return nil, "Rate limited by ASCEND API"
    end

    if res.status >= 500 then
        return nil, fmt("ASCEND API server error: %d", res.status)
    end

    if res.status ~= 200 and res.status ~= 201 then
        return nil, fmt("Unexpected status code: %d", res.status)
    end

    -- Parse response
    local response = cjson.decode(res.body)
    if not response then
        return nil, "Failed to parse API response"
    end

    return response, nil
end

--- Submit action to ASCEND API with retry and circuit breaker
-- @param conf Plugin configuration
-- @param payload Request payload
-- @return table|nil ASCEND decision or nil on error
-- @return string|nil Error message
function _M.submit_action(conf, payload)
    -- Initialize circuit breaker if needed
    init_circuit_breaker(conf)

    -- Check circuit breaker
    if circuit_breaker and circuit_breaker:is_open() then
        kong.log.warn("Circuit breaker open, skipping ASCEND API call")
        return nil, "Circuit breaker open - ASCEND API temporarily unavailable"
    end

    local last_err
    local retry_count = conf.retry_count or 0

    for attempt = 0, retry_count do
        if attempt > 0 then
            -- Exponential backoff
            local delay_ms = conf.retry_delay_ms * (2 ^ (attempt - 1))
            ngx.sleep(delay_ms / 1000)

            kong.log.info(fmt("Retry attempt %d/%d after %dms",
                attempt, retry_count, delay_ms))
        end

        local response, err = make_request(conf, payload)

        if response then
            -- Success - record and return
            if circuit_breaker then
                circuit_breaker:record_success()
            end

            return response, nil
        end

        -- Record failure
        last_err = err
        kong.log.warn(fmt("ASCEND API request failed (attempt %d): %s",
            attempt + 1, err))

        -- Check if error is retryable
        if err:match("Authentication") or err:match("Authorization") then
            -- Don't retry auth errors
            break
        end
    end

    -- All retries failed
    if circuit_breaker then
        circuit_breaker:record_failure()
    end

    return nil, last_err
end

--- Get circuit breaker state (for diagnostics)
-- @return table Circuit breaker state
function _M.get_circuit_state()
    if not circuit_breaker then
        return { state = "not_initialized" }
    end
    return circuit_breaker:get_state()
end

--- Health check - test ASCEND API connectivity
-- @param conf Plugin configuration
-- @return boolean True if healthy
-- @return string|nil Error message if unhealthy
function _M.health_check(conf)
    local httpc = http.new()
    httpc:set_timeout(5000)  -- 5s for health check

    local url = conf.ascend_api_url .. "/health"

    local res, err = httpc:request_uri(url, {
        method = "GET",
        headers = {
            [constants.HEADERS.API_KEY] = conf.ascend_api_key
        },
        ssl_verify = true
    })

    if not res then
        return false, fmt("Health check failed: %s", err or "unknown error")
    end

    if res.status ~= 200 then
        return false, fmt("Health check returned status: %d", res.status)
    end

    return true, nil
end

return _M
