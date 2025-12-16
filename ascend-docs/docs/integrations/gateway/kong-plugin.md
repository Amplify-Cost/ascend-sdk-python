---
sidebar_position: 3
title: Kong Gateway
description: ASCEND Plugin for Kong Gateway
---

# Kong Gateway Integration

> **Setup Time:** < 30 min | **Code Changes:** None | **Skill Level:** DevOps

Real-time AI agent governance for Kong Gateway with circuit breaker protection.

## Quick Decision

✅ **Use this if:** You run Kong Gateway (OSS or Enterprise)

❌ **Don't use if:** You're using AWS API Gateway (see [Lambda Authorizer](./aws-lambda-authorizer)) or Istio (see [Envoy/Istio](./envoy-istio))

## What You'll Get

- **Zero-code governance** — Plugin intercepts at gateway layer
- **FAIL SECURE design** — Blocks requests on any error
- **Circuit breaker** — Prevents cascade failures (5 failures → 30s reset)
- **Decision caching** — Sub-millisecond latency for repeated actions
- **Retry with backoff** — Configurable retry logic
- **Full audit trail** — Governance headers passed to upstream

## Prerequisites

Before starting, ensure you have:

- [ ] Kong Gateway installed (2.x or 3.x)
- [ ] LuaRocks package manager (for plugin installation)
- [ ] ASCEND Platform account with API key ([Get one here](https://pilot.owkai.app))
- [ ] Admin access to Kong configuration

## Quick Start (5 minutes)

### Step 1: Install the Plugin

```bash
luarocks install kong-plugin-ascend
```

Or with Docker:
```bash
docker run -e "KONG_PLUGINS=bundled,ascend" kong:latest
```

### Step 2: Enable the Plugin

```bash
curl -X POST http://localhost:8001/plugins \
  --data "name=ascend" \
  --data "config.api_url=https://pilot.owkai.app" \
  --data "config.api_key=YOUR_ASCEND_API_KEY"
```

### Step 3: Test It

```bash
# Request without agent ID (denied)
curl http://localhost:8000/api/users
# Expected: 401 Unauthorized - Missing X-Ascend-Agent-Id

# Request with agent ID
curl http://localhost:8000/api/users \
  -H "X-Ascend-Agent-Id: my-ai-agent"
# Expected: 200 OK (if approved)
```

## Full Setup Guide

### Installation Options

**Option A: LuaRocks (Recommended)**

```bash
luarocks install kong-plugin-ascend
```

**Option B: Manual Installation**

```bash
# Clone the plugin
git clone https://github.com/owkai/kong-plugin-ascend.git

# Copy to Kong plugins directory
cp -r kong-plugin-ascend/kong/plugins/ascend /usr/local/share/lua/5.1/kong/plugins/
```

**Option C: Docker**

```dockerfile
FROM kong:3.4

# Install the plugin
RUN luarocks install kong-plugin-ascend

# Enable the plugin
ENV KONG_PLUGINS=bundled,ascend
```

### Configuration

**Global Plugin (All Routes)**

```bash
curl -X POST http://localhost:8001/plugins \
  --data "name=ascend" \
  --data "config.api_url=https://pilot.owkai.app" \
  --data "config.api_key=YOUR_API_KEY" \
  --data "config.require_agent_id=true" \
  --data "config.fail_open=false" \
  --data "config.circuit_breaker_enabled=true"
```

**Per-Service Plugin**

```bash
curl -X POST http://localhost:8001/services/my-service/plugins \
  --data "name=ascend" \
  --data "config.api_url=https://pilot.owkai.app" \
  --data "config.api_key=YOUR_API_KEY"
```

**Per-Route Plugin**

```bash
curl -X POST http://localhost:8001/routes/my-route/plugins \
  --data "name=ascend" \
  --data "config.api_url=https://pilot.owkai.app" \
  --data "config.api_key=YOUR_API_KEY"
```

### Declarative Configuration (kong.yml)

```yaml
plugins:
  - name: ascend
    config:
      api_url: https://pilot.owkai.app
      api_key: ${ASCEND_API_KEY}
      require_agent_id: true
      fail_open: false
      block_on_pending: true
      cache_ttl_seconds: 60
      timeout_ms: 5000
      circuit_breaker_enabled: true
      circuit_breaker_threshold: 5
      circuit_breaker_reset_ms: 30000
      excluded_paths:
        - /health
        - /metrics
        - /ready
```

## Configuration Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | string | **required** | ASCEND Platform API URL |
| `api_key` | string | **required** | ASCEND Platform API key |
| `require_agent_id` | boolean | `true` | Require `X-Ascend-Agent-Id` header |
| `default_agent_id` | string | — | Default agent ID if header missing |
| `fail_open` | boolean | `false` | Allow on error (NOT RECOMMENDED) |
| `block_on_pending` | boolean | `true` | Block pending approvals |
| `cache_ttl_seconds` | number | `60` | Cache TTL for approved decisions |
| `timeout_ms` | number | `5000` | API request timeout in ms |
| `retry_count` | number | `2` | Number of retries on failure |
| `retry_delay_ms` | number | `100` | Delay between retries |
| `circuit_breaker_enabled` | boolean | `true` | Enable circuit breaker |
| `circuit_breaker_threshold` | number | `5` | Failures before opening |
| `circuit_breaker_reset_ms` | number | `30000` | Reset timeout (30 seconds) |
| `excluded_paths` | array | `[]` | Paths to skip governance |
| `environment` | string | `production` | Environment label |

<!-- VALIDATED:
  Source: kong-plugin-ascend/kong/plugins/ascend/constants.lua:73-74
  CIRCUIT_BREAKER_THRESHOLD = 5
  CIRCUIT_BREAKER_RESET_MS = 30000
  Status: ✅ VERIFIED
-->

## Circuit Breaker

The Kong plugin includes a circuit breaker to prevent cascade failures when ASCEND API is unavailable:

```
Closed → [5 failures] → Open → [30s] → Half-Open → [success] → Closed
                                    → [failure] → Open
```

| State | Behavior |
|-------|----------|
| **Closed** | Normal operation, requests evaluated |
| **Open** | All requests denied with 503 |
| **Half-Open** | Single test request allowed |

<!-- VALIDATED:
  Source: kong-plugin-ascend/kong/plugins/ascend/http_client.lua:30-136
  CircuitBreaker class with is_open(), record_success(), record_failure()
  Status: ✅ VERIFIED
-->

### Circuit Breaker Configuration

```bash
curl -X POST http://localhost:8001/plugins \
  --data "name=ascend" \
  --data "config.api_url=https://pilot.owkai.app" \
  --data "config.api_key=YOUR_API_KEY" \
  --data "config.circuit_breaker_enabled=true" \
  --data "config.circuit_breaker_threshold=5" \
  --data "config.circuit_breaker_reset_ms=30000"
```

## Response Behavior

| ASCEND Decision | HTTP Response | Headers Added |
|-----------------|---------------|---------------|
| `approved` | Continue to upstream | `X-Ascend-Status: approved`, action_id, risk_score |
| `pending_approval` | 403 Forbidden | `X-Ascend-Status: pending_approval`, action_id |
| `denied` | 403 Forbidden | `X-Ascend-Status: denied`, denial_reason |
| API Error | 503 Service Unavailable | `X-Ascend-Error: service_unavailable` |
| Circuit Open | 503 Service Unavailable | `X-Ascend-Error: circuit_breaker_open` |

### Denied Response Body

```json
{
  "error": "PermissionDenied",
  "message": "Action denied by governance policy",
  "action_id": "act_abc123",
  "denial_reason": "Risk score 85 exceeds threshold 70"
}
```

## Required Headers

| Header | Required | Description |
|--------|:--------:|-------------|
| `X-Ascend-Agent-Id` | **Yes*** | Unique identifier for the AI agent |
| `X-Ascend-Environment` | No | Override environment |
| `X-Ascend-Data-Sensitivity` | No | Data sensitivity level |

*Required unless `default_agent_id` is configured.

## Path Exclusions

Skip governance for health checks and metrics:

```yaml
config:
  excluded_paths:
    - /health
    - /ready
    - /metrics
    - ^/internal/.*  # Regex supported
```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/ascend/health
```

### Plugin Status

```bash
curl http://localhost:8001/plugins | jq '.data[] | select(.name=="ascend")'
```

### Circuit Breaker State

```bash
curl http://localhost:8001/ascend/circuit-breaker
```

Response:
```json
{
  "state": "closed",
  "failures": 0,
  "last_failure": null,
  "last_success": "2025-12-16T10:30:00Z"
}
```

## Troubleshooting

### All Requests Denied

1. **Check agent ID header**:
   ```bash
   curl -v -H "X-Ascend-Agent-Id: test-agent" http://localhost:8000/api/test
   ```

2. **Verify plugin is enabled**:
   ```bash
   curl http://localhost:8001/plugins | jq '.data[] | select(.name=="ascend")'
   ```

3. **Check API key**:
   ```bash
   curl https://pilot.owkai.app/health -H "X-API-Key: YOUR_KEY"
   ```

4. **Check Kong logs**:
   ```bash
   docker logs kong 2>&1 | grep ascend
   ```

### Circuit Breaker Keeps Opening

1. **Check ASCEND API health**:
   ```bash
   curl https://pilot.owkai.app/health
   ```

2. **Verify network connectivity**:
   ```bash
   docker exec kong curl https://pilot.owkai.app/health
   ```

3. **Increase threshold temporarily**:
   ```bash
   curl -X PATCH http://localhost:8001/plugins/PLUGIN_ID \
     --data "config.circuit_breaker_threshold=10"
   ```

4. **Review error logs** for root cause

### High Latency

1. **Enable caching**: Ensure `cache_ttl_seconds` > 0
2. **Check ASCEND API response times**
3. **Consider increasing timeout**: `timeout_ms=10000`
4. **Reduce retry count** if latency is acceptable: `retry_count=1`

## Kubernetes Deployment

### Helm Values

```yaml
# values.yaml
plugins:
  - name: ascend
    config:
      api_url: https://pilot.owkai.app
      api_key: ${ASCEND_API_KEY}

env:
  plugins: bundled,ascend

extraConfigMaps:
  - name: ascend-plugin
    mountPath: /usr/local/share/lua/5.1/kong/plugins/ascend
```

### Kong Ingress Controller

```yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: ascend-governance
  annotations:
    kubernetes.io/ingress.class: kong
plugin: ascend
config:
  api_url: https://pilot.owkai.app
  api_key: ${ASCEND_API_KEY}
  circuit_breaker_enabled: true
```

Apply to Ingress:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-api
  annotations:
    konghq.com/plugins: ascend-governance
spec:
  # ... ingress spec
```

## Feature Comparison

| Feature | Kong Plugin | Lambda | Envoy |
|---------|:-----------:|:------:|:-----:|
| Circuit Breaker | ✅ | ❌ | ✅ |
| Retry with Backoff | ✅ | ❌ | ✅ |
| Decision Caching | ✅ | ✅ | ✅ |
| gRPC Support | ❌ | ❌ | ✅ |
| Kubernetes Native | Via KIC | ❌ | ✅ |

## Next Steps

- [Gateway Overview](./) — Compare all gateway options
- [Lambda Authorizer](./aws-lambda-authorizer) — AWS API Gateway option
- [Envoy/Istio](./envoy-istio) — Kubernetes service mesh option
- [API Reference](/api-reference/actions) — Full API documentation

## Support

- **Documentation**: https://docs.ascend.owkai.app
- **Email**: support@owkai.app
- **Issues**: https://github.com/owkai/kong-plugin-ascend/issues
