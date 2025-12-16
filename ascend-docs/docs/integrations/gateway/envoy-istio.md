---
sidebar_position: 4
title: Envoy / Istio
description: External Authorization Service for Envoy and Istio
---

# Envoy / Istio Integration

> **Setup Time:** < 30 min | **Code Changes:** None | **Skill Level:** DevOps/Platform

Real-time AI agent governance for Envoy proxy and Istio service mesh using the ext_authz API.

## Quick Decision

✅ **Use this if:** You run Kubernetes with Istio service mesh

❌ **Don't use if:** You're using AWS API Gateway (see [Lambda Authorizer](./aws-lambda-authorizer)) or Kong (see [Kong Plugin](./kong-plugin))

## What You'll Get

- **Zero-code governance** — Governance at the service mesh layer
- **FAIL SECURE design** — Blocks requests on any error
- **Circuit breaker** — Prevents cascade failures (5 failures → 30s reset)
- **gRPC native** — High-performance authorization checks
- **Helm deployment** — Standard Kubernetes deployment
- **Istio native** — Works with AuthorizationPolicy resources

## Prerequisites

Before starting, ensure you have:

- [ ] Kubernetes cluster (1.24+)
- [ ] Istio installed (1.17+)
- [ ] Helm v3+ installed
- [ ] `kubectl` configured for your cluster
- [ ] ASCEND Platform account with API key ([Get one here](https://pilot.owkai.app))

## Quick Start (< 30 minutes)

### Step 1: Create Namespace

```bash
kubectl create namespace ascend-system
kubectl label namespace ascend-system istio-injection=disabled
```

### Step 2: Deploy with Helm

```bash
# Create secret for API key
kubectl create secret generic ascend-api-key \
  --from-literal=api_key=YOUR_ASCEND_API_KEY \
  -n ascend-system

# Install with Helm
helm upgrade --install ascend-authz ./helm/ascend-authz \
  --namespace ascend-system \
  --set ascend.apiUrl=https://pilot.owkai.app \
  --set ascend.existingSecret=ascend-api-key
```

### Step 3: Configure Istio Extension Provider

```bash
kubectl edit configmap istio -n istio-system
```

Add under `data.mesh`:
```yaml
extensionProviders:
- name: "ascend-ext-authz"
  envoyExtAuthzGrpc:
    service: "ascend-authz.ascend-system.svc.cluster.local"
    port: 50051
    timeout: 5s
    failOpen: false
```

Restart Istio:
```bash
kubectl rollout restart deployment/istiod -n istio-system
```

### Step 4: Apply AuthorizationPolicy

```yaml
# governance-policy.yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: ascend-governance
  namespace: YOUR_NAMESPACE
spec:
  selector:
    matchLabels:
      ascend.io/governed: "true"
  action: CUSTOM
  provider:
    name: "ascend-ext-authz"
  rules:
  - to:
    - operation:
        paths: ["/*"]
        notPaths: ["/health", "/ready", "/metrics"]
```

```bash
kubectl apply -f governance-policy.yaml
```

### Step 5: Label Your Workloads

```bash
kubectl label deployment my-ai-agent ascend.io/governed=true -n YOUR_NAMESPACE
```

### Step 6: Test It

```bash
# Request without agent ID (denied)
kubectl exec -it deploy/my-ai-agent -- curl http://backend-service/api/users
# Expected: 401 Unauthorized - Missing X-Ascend-Agent-Id

# Request with agent ID
kubectl exec -it deploy/my-ai-agent -- curl \
  -H "X-Ascend-Agent-Id: my-agent" \
  http://backend-service/api/users
# Expected: 200 OK (if approved)
```

## Full Setup Guide

### Helm Installation

**Option A: With Existing Secret (Recommended)**

```bash
# Create the secret first
kubectl create secret generic ascend-api-key \
  --from-literal=api_key=YOUR_API_KEY \
  -n ascend-system

# Install chart
helm upgrade --install ascend-authz ./helm/ascend-authz \
  --namespace ascend-system \
  --set ascend.apiUrl=https://pilot.owkai.app \
  --set ascend.existingSecret=ascend-api-key
```

**Option B: Direct API Key (Development Only)**

```bash
helm upgrade --install ascend-authz ./helm/ascend-authz \
  --namespace ascend-system \
  --set ascend.apiUrl=https://pilot.owkai.app \
  --set ascend.apiKey=YOUR_API_KEY
```

:::warning Security
Never use `--set ascend.apiKey` in production. Use `existingSecret` instead.
:::

### Helm Values

```yaml
# values.yaml
ascend:
  apiUrl: https://pilot.owkai.app
  existingSecret: ascend-api-key
  environment: production
  timeout: 5s
  cacheTtl: 60s

circuitBreaker:
  enabled: true
  threshold: 5
  resetTimeout: 30s

agentId:
  header: x-ascend-agent-id
  required: true

security:
  failOpen: false
  blockOnPending: true

excludedPaths:
  - /health
  - /ready
  - /metrics

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

replicaCount: 2
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASCEND_API_URL` | **required** | ASCEND Platform API URL |
| `ASCEND_API_KEY` | **required** | ASCEND Platform API key |
| `AGENT_ID_HEADER` | `x-ascend-agent-id` | Header containing agent ID |
| `REQUIRE_AGENT_ID` | `true` | Require agent ID header |
| `FAIL_OPEN` | `false` | Allow on error (NOT RECOMMENDED) |
| `BLOCK_ON_PENDING` | `true` | Block pending approvals |
| `ENVIRONMENT` | `production` | Environment label |
| `TIMEOUT` | `5s` | API request timeout |
| `CACHE_TTL` | `60s` | Cache TTL for approved decisions |
| `CIRCUIT_BREAKER_ENABLED` | `true` | Enable circuit breaker |
| `CIRCUIT_BREAKER_THRESHOLD` | `5` | Failures before open |
| `CIRCUIT_BREAKER_TIMEOUT` | `30s` | Reset timeout |
| `LOG_LEVEL` | `info` | Log level (debug, info, warn, error) |
| `EXCLUDED_PATHS` | `/health,/ready,/metrics` | Paths to skip |

<!-- VALIDATED:
  Source: ascend-envoy-authz/internal/config/config.go:93-95
  CircuitBreakerEnabled: true, Threshold: 5, Timeout: 30s
  Status: ✅ VERIFIED
-->

## Circuit Breaker

The ext_authz service includes a circuit breaker to prevent cascade failures:

```
Closed → [5 failures] → Open → [30s] → Half-Open → [success] → Closed
                                    → [failure] → Open
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CIRCUIT_BREAKER_THRESHOLD` | 5 | Failures before opening |
| `CIRCUIT_BREAKER_TIMEOUT` | 30s | Time before half-open state |

When circuit is **open**, all requests return 503 Service Unavailable.

<!-- VALIDATED:
  Source: ascend-envoy-authz/internal/ascend/client.go:238
  newCircuitBreaker(threshold int, resetTimeout time.Duration)
  Status: ✅ VERIFIED
-->

## Response Behavior

| ASCEND Decision | gRPC Response | HTTP to Client |
|-----------------|---------------|----------------|
| `approved` | OK (continue) | Request continues to upstream |
| `pending_approval` | PERMISSION_DENIED | 403 Forbidden |
| `denied` | PERMISSION_DENIED | 403 Forbidden |
| API Error | UNAVAILABLE | 503 Service Unavailable |
| Circuit Open | UNAVAILABLE | 503 Service Unavailable |

### Response Headers

On successful authorization, these headers are added:

| Header | Description |
|--------|-------------|
| `x-ascend-status` | Decision: `approved`, `pending_approval`, `denied` |
| `x-ascend-action-id` | Unique action ID for audit |
| `x-ascend-risk-score` | Risk score (0-100) |
| `x-ascend-risk-level` | `low`, `medium`, `high`, `critical` |

### Check Response Headers

```bash
kubectl exec -it deploy/my-ai-agent -- curl -v \
  -H "X-Ascend-Agent-Id: my-agent" \
  http://backend-service/api/users 2>&1 | grep x-ascend
```

Expected output:
```
< x-ascend-status: approved
< x-ascend-action-id: 12345
< x-ascend-risk-score: 25.0
< x-ascend-risk-level: low
```

## Istio Integration

### Extension Provider Configuration

Add to Istio mesh config:

```yaml
# istio ConfigMap
data:
  mesh: |
    extensionProviders:
    - name: "ascend-ext-authz"
      envoyExtAuthzGrpc:
        service: "ascend-authz.ascend-system.svc.cluster.local"
        port: 50051
        timeout: 5s
        failOpen: false
```

### AuthorizationPolicy Examples

**Govern Specific Workloads (Recommended)**

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: ascend-governance
  namespace: production
spec:
  selector:
    matchLabels:
      ascend.io/governed: "true"
  action: CUSTOM
  provider:
    name: "ascend-ext-authz"
  rules:
  - to:
    - operation:
        paths: ["/*"]
        notPaths: ["/health", "/ready", "/metrics"]
```

**Govern Entire Namespace**

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: ascend-namespace-governance
  namespace: ai-agents
spec:
  action: CUSTOM
  provider:
    name: "ascend-ext-authz"
  rules:
  - to:
    - operation:
        paths: ["/*"]
        notPaths: ["/health", "/ready", "/metrics"]
```

**Govern Specific Paths Only**

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: ascend-sensitive-paths
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend-api
  action: CUSTOM
  provider:
    name: "ascend-ext-authz"
  rules:
  - to:
    - operation:
        paths:
          - "/api/users/*"
          - "/api/admin/*"
          - "/api/sensitive/*"
```

## Monitoring

### Health Check

```bash
# gRPC health check
grpcurl -plaintext ascend-authz.ascend-system:50051 \
  grpc.health.v1.Health/Check
```

### Prometheus Metrics

Metrics available on port 8080:

```bash
kubectl port-forward svc/ascend-authz 8080:8080 -n ascend-system
curl http://localhost:8080/metrics
```

Available metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `ascend_authz_requests_total` | Counter | Total authorization requests |
| `ascend_authz_decisions_total` | Counter | Decisions by status |
| `ascend_authz_latency_seconds` | Histogram | Request latency |
| `ascend_authz_circuit_breaker_state` | Gauge | Circuit breaker state |

### Structured Logs

JSON logs include:

```json
{
  "level": "info",
  "agent_id": "my-agent",
  "action_type": "api.users.list",
  "status": "approved",
  "risk_score": 25.0,
  "latency_ms": 12,
  "timestamp": "2025-12-16T10:30:00Z"
}
```

## Troubleshooting

### All Requests Denied

1. **Check agent ID header**:
   ```bash
   kubectl exec -it deploy/test-pod -- curl -v \
     -H "X-Ascend-Agent-Id: test-agent" \
     http://backend/api/test
   ```

2. **Verify ext_authz service is running**:
   ```bash
   kubectl get pods -n ascend-system
   kubectl logs -l app=ascend-authz -n ascend-system
   ```

3. **Check Istio extension provider**:
   ```bash
   kubectl get cm istio -n istio-system -o yaml | grep -A10 extensionProviders
   ```

4. **Verify AuthorizationPolicy**:
   ```bash
   kubectl get authorizationpolicy -A
   ```

5. **Check network connectivity**:
   ```bash
   kubectl exec -it deploy/ascend-authz -n ascend-system -- \
     curl https://pilot.owkai.app/health
   ```

### Circuit Breaker Keeps Opening

1. **Check ASCEND API health**:
   ```bash
   curl https://pilot.owkai.app/health
   ```

2. **Check service logs**:
   ```bash
   kubectl logs -l app=ascend-authz -n ascend-system --tail=100
   ```

3. **Increase threshold temporarily**:
   ```bash
   kubectl set env deployment/ascend-authz \
     CIRCUIT_BREAKER_THRESHOLD=10 \
     -n ascend-system
   ```

### High Latency

1. **Enable caching**: Ensure `CACHE_TTL` > 0
2. **Increase replicas**: `kubectl scale deployment/ascend-authz --replicas=3`
3. **Check resource limits**: Increase CPU/memory if throttled
4. **Review ASCEND API latency**: Check metrics dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 ASCEND ext_authz Service                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  cmd/server/main.go                                         │
│  └── gRPC Server (port 50051)                              │
│      ├── Authorization.Check (ext_authz)                   │
│      └── Health.Check (health probes)                      │
│                                                             │
│  internal/authz/handler.go                                  │
│  └── Check() → Extract agent ID → Map request → Call API   │
│                                                             │
│  internal/ascend/client.go                                  │
│  └── EvaluateAction() → Retry → Circuit breaker            │
│                                                             │
│  internal/mapper/mapper.go                                  │
│  └── MapCheckRequest() → HTTP method/path → action_type    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Feature Comparison

| Feature | Envoy/Istio | Lambda | Kong |
|---------|:-----------:|:------:|:----:|
| Circuit Breaker | ✅ | ❌ | ✅ |
| gRPC Native | ✅ | ❌ | ❌ |
| Kubernetes Native | ✅ | ❌ | Via KIC |
| Service Mesh | ✅ | ❌ | ❌ |
| Pod-to-Pod Governance | ✅ | ❌ | ❌ |

## Next Steps

- [Gateway Overview](./) — Compare all gateway options
- [Lambda Authorizer](./aws-lambda-authorizer) — AWS API Gateway option
- [Kong Plugin](./kong-plugin) — Kong Gateway option
- [API Reference](/api-reference/actions) — Full API documentation

## Support

- **Documentation**: https://docs.ascend.owkai.app
- **Email**: support@owkai.app
- **Issues**: https://github.com/owkai/ascend-envoy-authz/issues
