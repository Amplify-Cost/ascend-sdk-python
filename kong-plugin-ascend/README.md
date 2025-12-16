# ASCEND Kong Gateway Plugin

Real-time AI agent governance for Kong Gateway. Zero-code integration with the ASCEND Platform.

## Overview

The ASCEND plugin intercepts API requests at the gateway layer, evaluating each AI agent action against enterprise governance policies before allowing access to backend services.

```
AI Agent → Kong Gateway → ASCEND Plugin → Backend Service
                              ↓
                    ASCEND Platform API
                    (Policy Evaluation)
```

**Key Features:**
- **FAIL SECURE**: Blocks requests on any error (configurable)
- **Circuit Breaker**: Prevents cascade failures
- **Decision Caching**: Sub-millisecond latency for repeated actions
- **Full Audit Trail**: Governance headers passed to upstream services

## Quick Start (< 30 minutes)

### Prerequisites

- Kong Gateway 3.0+ (OSS or Enterprise)
- ASCEND Platform API key ([Get one here](https://ascend.owkai.app))
- `lua-resty-http` module (included in Kong)

### Step 1: Install the Plugin

**Option A: LuaRocks**
```bash
luarocks install kong-plugin-ascend
```

**Option B: Manual Installation**
```bash
# Copy plugin files to Kong's plugin directory
cp -r kong/plugins/ascend /usr/local/share/lua/5.1/kong/plugins/
```

### Step 2: Enable the Plugin in Kong

Add to `kong.conf`:
```
plugins = bundled,ascend
```

Or set environment variable:
```bash
export KONG_PLUGINS="bundled,ascend"
```

### Step 3: Configure the Plugin

**Via Kong Admin API:**
```bash
curl -X POST http://localhost:8001/plugins \
  --data "name=ascend" \
  --data "config.ascend_api_url=https://api.ascend.owkai.app" \
  --data "config.ascend_api_key=YOUR_API_KEY"
```

**Via Declarative Configuration (kong.yml):**
```yaml
plugins:
  - name: ascend
    config:
      ascend_api_url: https://api.ascend.owkai.app
      ascend_api_key: YOUR_API_KEY
      environment: production
      data_sensitivity: standard
      cache_ttl: 60
      fail_open: false
```

### Step 4: Test the Integration

```bash
# Make a request with agent ID header
curl -H "X-Ascend-Agent-Id: my-agent" http://localhost:8000/api/users

# Check response headers
curl -v -H "X-Ascend-Agent-Id: my-agent" http://localhost:8000/api/users 2>&1 | grep X-Ascend
```

**Expected Headers (on success):**
```
X-Ascend-Decision: approved
X-Ascend-Action-Id: 12345
X-Ascend-Risk-Score: 25.0
X-Ascend-Risk-Level: low
```

## Configuration Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ascend_api_url` | string | **required** | ASCEND Platform API URL (must be HTTPS) |
| `ascend_api_key` | string | **required** | ASCEND Platform API key |
| `require_agent_id` | boolean | `true` | Require X-Ascend-Agent-Id header |
| `default_agent_id` | string | `nil` | Default agent ID if header missing |
| `fail_open` | boolean | `false` | Allow requests when API unavailable (NOT RECOMMENDED) |
| `block_on_pending` | boolean | `true` | Block requests requiring approval |
| `environment` | string | `production` | Deployment environment |
| `data_sensitivity` | string | `standard` | Data sensitivity level |
| `timeout_ms` | integer | `5000` | API timeout in milliseconds |
| `cache_ttl` | integer | `60` | Cache TTL for approved decisions (seconds) |
| `retry_count` | integer | `2` | Number of retry attempts |
| `circuit_breaker_enabled` | boolean | `true` | Enable circuit breaker |
| `circuit_breaker_threshold` | integer | `5` | Failures before circuit opens |
| `circuit_breaker_reset_ms` | integer | `30000` | Circuit reset time (ms) |
| `excluded_paths` | array | `[]` | Paths to exclude from governance |
| `denied_status_code` | integer | `403` | HTTP status for denied requests |
| `error_status_code` | integer | `503` | HTTP status for API errors |

## Response Behavior

| ASCEND Decision | Kong Response | Headers Added |
|-----------------|---------------|---------------|
| `approved` | Continue to upstream | `X-Ascend-Decision: approved`, `X-Ascend-Action-Id`, `X-Ascend-Risk-Score` |
| `pending_approval` | HTTP 403 (default) | Error body with `action_id`, `risk_score` |
| `denied` | HTTP 403 | Error body with `denial_reason` |
| API Error | HTTP 503 (FAIL SECURE) | Error body with `message` |

### Denied Response Body

```json
{
  "error": "ACCESS_DENIED",
  "message": "Action denied by governance policy",
  "action_id": 12345,
  "risk_score": 95.0,
  "risk_level": "critical",
  "denial_reason": "Unauthorized admin access attempt"
}
```

## Path Exclusions

Exclude health checks and metrics from governance:

```yaml
config:
  excluded_paths:
    - "^/health$"
    - "^/metrics$"
    - "^/ready$"
    - "^/live$"
```

## Custom Action Type Mapping

Override default action type detection:

```yaml
config:
  custom_action_types:
    "^/api/v1/sensitive-data": "sensitive_data_access"
    "^/internal/": "internal_operation"
```

## Circuit Breaker Behavior

The circuit breaker protects against ASCEND API failures:

1. **Closed** (normal): Requests go to ASCEND API
2. **Open** (after 5 failures): Requests blocked with 503
3. **Half-Open** (after 30s): Single request tests API health

```
Failures: [1] [2] [3] [4] [5] → CIRCUIT OPEN → 30s → HALF-OPEN → Success → CLOSED
```

Configure thresholds:
```yaml
config:
  circuit_breaker_threshold: 3    # Open after 3 failures
  circuit_breaker_reset_ms: 60000 # Test after 60 seconds
```

## Logging

Enable decision logging:

```yaml
config:
  log_decisions: true
```

Log entries are written to Kong's log with prefix `ASCEND_DECISION`:

```json
{
  "plugin": "ascend",
  "timestamp": 1702345678000,
  "latency_ms": 45,
  "agent_id": "my-agent",
  "action_type": "read_users",
  "decision_status": "approved",
  "risk_score": 25.0,
  "cache_hit": false
}
```

## Multi-Tenant Configuration

For multi-tenant deployments, set organization ID:

```yaml
config:
  organization_id: "org_12345"
```

This ensures actions are evaluated against the correct tenant's policies.

## Kong Shared Memory Configuration

The circuit breaker requires shared memory. Add to `kong.conf`:

```
nginx_http_lua_shared_dict = ascend_circuit_breaker 1m
```

Or via environment:
```bash
export KONG_NGINX_HTTP_LUA_SHARED_DICT="ascend_circuit_breaker 1m"
```

## Testing

Run unit tests:
```bash
busted spec/ascend/handler_spec.lua -v
busted spec/ascend/http_client_spec.lua -v
```

Run all tests:
```bash
busted spec/ -v
```

## Troubleshooting

### Plugin Not Loading

Check Kong logs:
```bash
kong error.log | grep ascend
```

Verify plugin is enabled:
```bash
curl http://localhost:8001/plugins/enabled | jq '.enabled_plugins | contains(["ascend"])'
```

### All Requests Denied

1. Verify API key is correct
2. Check circuit breaker state isn't open
3. Review Kong error logs for API connectivity issues
4. Ensure `X-Ascend-Agent-Id` header is present

### High Latency

1. Enable caching: `cache_ttl: 60`
2. Check ASCEND API response times
3. Consider increasing timeout if network latency is high

### Circuit Breaker Keeps Opening

1. Check ASCEND API health at `/health`
2. Verify network connectivity to ASCEND API
3. Review failure logs for root cause
4. Temporarily increase threshold while investigating

## Support

- Documentation: https://docs.ascend.owkai.app
- Issues: https://github.com/owkai/kong-plugin-ascend/issues
- Email: support@owkai.app

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12 | Initial release |

---

**Author:** ASCEND Platform Engineering
**License:** Proprietary
