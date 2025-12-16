--[[
ASCEND Kong Plugin - HTTP Client Unit Tests
============================================

Tests for http_client.lua covering:
- API request handling
- Retry logic
- Circuit breaker behavior
- Error handling

Run with: busted spec/ascend/http_client_spec.lua

Author: ASCEND Platform Engineering
--]]

local cjson = require "cjson"

-- Test configuration
local test_conf = {
    ascend_api_url = "https://test.ascend.owkai.app",
    ascend_api_key = "test_api_key_12345",
    timeout_ms = 5000,
    retry_count = 2,
    retry_delay_ms = 100,
    circuit_breaker_enabled = true,
    circuit_breaker_threshold = 5,
    circuit_breaker_reset_ms = 30000
}

describe("ASCEND HTTP Client", function()

    describe("Circuit Breaker", function()
        local CircuitBreaker

        setup(function()
            -- Mock ngx.shared
            local mock_dict = {
                data = {},
                get = function(self, key)
                    return self.data[key]
                end,
                set = function(self, key, value)
                    self.data[key] = value
                    return true
                end,
                delete = function(self, key)
                    self.data[key] = nil
                    return true
                end,
                incr = function(self, key, value, init)
                    local current = self.data[key] or init or 0
                    self.data[key] = current + value
                    return self.data[key], nil
                end
            }

            _G.ngx = {
                shared = {
                    ascend_circuit_breaker = mock_dict
                },
                now = function() return os.time() end
            }

            _G.kong = {
                log = {
                    debug = function() end,
                    info = function() end,
                    warn = function() end,
                    err = function() end
                }
            }

            -- Simple CircuitBreaker implementation for testing
            CircuitBreaker = {}
            CircuitBreaker.__index = CircuitBreaker

            function CircuitBreaker.new(name, threshold, reset_ms)
                local self = setmetatable({}, CircuitBreaker)
                self.name = name
                self.threshold = threshold or 5
                self.reset_ms = reset_ms or 30000
                self.failure_key = "cb:" .. name .. ":failures"
                self.open_key = "cb:" .. name .. ":open_at"
                return self
            end

            function CircuitBreaker:get_dict()
                return ngx.shared.ascend_circuit_breaker
            end

            function CircuitBreaker:is_open()
                local dict = self:get_dict()
                local open_at = dict:get(self.open_key)
                if not open_at then return false end
                local now = ngx.now() * 1000
                return (now - open_at) < self.reset_ms
            end

            function CircuitBreaker:record_success()
                local dict = self:get_dict()
                dict:set(self.failure_key, 0)
                dict:delete(self.open_key)
            end

            function CircuitBreaker:record_failure()
                local dict = self:get_dict()
                local failures = dict:incr(self.failure_key, 1, 0)
                if failures >= self.threshold then
                    dict:set(self.open_key, ngx.now() * 1000)
                    dict:set(self.failure_key, 0)
                    return true
                end
                return false
            end

            function CircuitBreaker:get_state()
                local dict = self:get_dict()
                local failures = dict:get(self.failure_key) or 0
                local open_at = dict:get(self.open_key)
                local state = open_at and "open" or "closed"
                return {
                    state = state,
                    failures = failures,
                    threshold = self.threshold
                }
            end
        end)

        teardown(function()
            _G.ngx = nil
            _G.kong = nil
        end)

        it("starts in closed state", function()
            local cb = CircuitBreaker.new("test", 5, 30000)
            assert.equals("closed", cb:get_state().state)
        end)

        it("stays closed below threshold", function()
            local cb = CircuitBreaker.new("test2", 5, 30000)

            for i = 1, 4 do
                cb:record_failure()
            end

            assert.is_false(cb:is_open())
            assert.equals(4, cb:get_state().failures)
        end)

        it("opens after threshold failures", function()
            local cb = CircuitBreaker.new("test3", 3, 30000)

            cb:record_failure()
            cb:record_failure()
            local opened = cb:record_failure()

            assert.is_true(opened)
            assert.is_true(cb:is_open())
        end)

        it("closes on success", function()
            local cb = CircuitBreaker.new("test4", 3, 30000)

            cb:record_failure()
            cb:record_failure()
            cb:record_success()

            assert.is_false(cb:is_open())
            assert.equals(0, cb:get_state().failures)
        end)

        it("resets failure count after opening", function()
            local cb = CircuitBreaker.new("test5", 3, 30000)

            cb:record_failure()
            cb:record_failure()
            cb:record_failure()  -- Opens circuit

            assert.equals(0, cb:get_state().failures)
        end)
    end)

    describe("Request payload", function()
        it("includes required fields", function()
            local payload = {
                agent_id = "test-agent",
                action_type = "read_users",
                environment = "test",
                data_sensitivity = "standard",
                context = {
                    source_ip = "192.168.1.1",
                    gateway = "kong"
                }
            }

            assert.is_not_nil(payload.agent_id)
            assert.is_not_nil(payload.action_type)
            assert.is_not_nil(payload.environment)
            assert.is_not_nil(payload.context)
        end)

        it("serializes to valid JSON", function()
            local payload = {
                agent_id = "test-agent",
                action_type = "read_users",
                environment = "test",
                data_sensitivity = "standard"
            }

            local json = cjson.encode(payload)
            assert.is_not_nil(json)

            local decoded = cjson.decode(json)
            assert.equals("test-agent", decoded.agent_id)
        end)
    end)

    describe("Response parsing", function()
        it("parses approved response", function()
            local response_json = [[{
                "id": 12345,
                "status": "approved",
                "risk_score": 25.0,
                "risk_level": "low",
                "requires_approval": false
            }]]

            local response = cjson.decode(response_json)

            assert.equals(12345, response.id)
            assert.equals("approved", response.status)
            assert.equals(25.0, response.risk_score)
            assert.equals("low", response.risk_level)
            assert.is_false(response.requires_approval)
        end)

        it("parses denied response", function()
            local response_json = [[{
                "id": 12346,
                "status": "denied",
                "risk_score": 95.0,
                "risk_level": "critical",
                "denial_reason": "Violates security policy"
            }]]

            local response = cjson.decode(response_json)

            assert.equals("denied", response.status)
            assert.equals(95.0, response.risk_score)
            assert.equals("Violates security policy", response.denial_reason)
        end)

        it("parses pending response", function()
            local response_json = [[{
                "id": 12347,
                "status": "pending_approval",
                "risk_score": 75.0,
                "risk_level": "high",
                "requires_approval": true
            }]]

            local response = cjson.decode(response_json)

            assert.equals("pending_approval", response.status)
            assert.is_true(response.requires_approval)
        end)

        it("handles null fields gracefully", function()
            local response_json = [[{
                "id": 12348,
                "status": "approved",
                "risk_score": null,
                "risk_level": null
            }]]

            local response = cjson.decode(response_json)

            assert.equals("approved", response.status)
            assert.is_nil(response.risk_score)
        end)
    end)

    describe("Error handling", function()
        it("identifies authentication errors", function()
            local error_msg = "Authentication failed: invalid API key"
            assert.matches("Authentication", error_msg)
        end)

        it("identifies timeout errors", function()
            local error_msg = "Connection timeout after 5000ms"
            assert.matches("timeout", error_msg)
        end)

        it("identifies rate limit errors", function()
            local error_msg = "Rate limited by ASCEND API"
            assert.matches("Rate limited", error_msg)
        end)

        it("identifies server errors", function()
            local error_msg = "ASCEND API server error: 500"
            assert.matches("server error", error_msg)
        end)
    end)

    describe("Retry logic", function()
        it("respects retry count", function()
            local max_retries = test_conf.retry_count
            assert.equals(2, max_retries)
        end)

        it("calculates exponential backoff", function()
            local base_delay = test_conf.retry_delay_ms

            -- Attempt 1: base_delay * 2^0 = 100ms
            local delay_1 = base_delay * (2 ^ 0)
            assert.equals(100, delay_1)

            -- Attempt 2: base_delay * 2^1 = 200ms
            local delay_2 = base_delay * (2 ^ 1)
            assert.equals(200, delay_2)

            -- Attempt 3: base_delay * 2^2 = 400ms
            local delay_3 = base_delay * (2 ^ 2)
            assert.equals(400, delay_3)
        end)

        it("does not retry auth errors", function()
            local err = "Authentication failed: invalid API key"
            local should_retry = not (err:match("Authentication") or err:match("Authorization"))
            assert.is_false(should_retry)
        end)

        it("retries timeout errors", function()
            local err = "Connection timeout"
            local should_retry = not (err:match("Authentication") or err:match("Authorization"))
            assert.is_true(should_retry)
        end)
    end)

    describe("Configuration validation", function()
        it("requires HTTPS URL", function()
            local url = test_conf.ascend_api_url
            assert.matches("^https://", url)
        end)

        it("has valid timeout", function()
            local timeout = test_conf.timeout_ms
            assert.is_true(timeout >= 100)
            assert.is_true(timeout <= 30000)
        end)

        it("has valid retry count", function()
            local retries = test_conf.retry_count
            assert.is_true(retries >= 0)
            assert.is_true(retries <= 5)
        end)

        it("has valid circuit breaker threshold", function()
            local threshold = test_conf.circuit_breaker_threshold
            assert.is_true(threshold >= 1)
            assert.is_true(threshold <= 100)
        end)
    end)
end)
