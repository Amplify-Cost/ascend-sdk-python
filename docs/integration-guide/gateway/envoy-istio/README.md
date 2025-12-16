# ASCEND Envoy External Authorization Service

Real-time AI agent governance for Envoy proxy and Istio service mesh. Zero-code integration with the ASCEND Platform.

## Overview

The ASCEND ext_authz service implements Envoy's external authorization API, enabling AI agent governance at the service mesh layer. Every request is evaluated against enterprise policies before reaching backend services.

```
AI Agent (Pod) → Envoy Sidecar → ASCEND ext_authz → Backend Service
                                       ↓
                               ASCEND Platform API
                               (Policy Evaluation)
```

**Key Features:**
- **FAIL SECURE**: Blocks requests on any error (configurable)
- **Circuit Breaker**: Prevents cascade failures (5 failures → 30s reset)
- **Decision Caching**: Sub-millisecond latency for repeated actions
- **gRPC Health Check**: Native Kubernetes health probes
- **Istio Native**: Works with AuthorizationPolicy resources

## Quick Start (< 30 minutes)

### Prerequisites

- Kubernetes cluster with Istio installed (1.17+)
- `kubectl` configured for your cluster
- `helm` v3+ installed
- ASCEND Platform API key ([Get one here](https://ascend.owkai.app))

### Step 1: Create Namespace

```bash
kubectl create namespace ascend-system
kubectl label namespace ascend-system istio-injection=disabled
```

### Step 2: Deploy with Helm

```bash
# Add your API key
helm upgrade --install ascend-authz ./helm/ascend-authz \
  --namespace ascend-system \
  --set ascend.apiUrl=https://pilot.owkai.app \
  --set ascend.apiKey=YOUR_API_KEY
```

Or with an existing secret:
```bash
# Create secret first
kubectl create secret generic ascend-api-key \
  --from-literal=api_key=YOUR_API_KEY \
  -n ascend-system

# Install with existing secret
helm upgrade --install ascend-authz ./helm/ascend-authz \
  --namespace ascend-system \
  --set ascend.apiUrl=https://pilot.owkai.app \
  --set ascend.existingSecret=ascend-api-key
```

### Step 3: Configure Istio Extension Provider

Add the ASCEND extension provider to your Istio mesh config:

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

Restart Istio to pick up changes:
```bash
kubectl rollout restart deployment/istiod -n istio-system
```

### Step 4: Apply AuthorizationPolicy

Create an AuthorizationPolicy to enable governance:

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

Add the governance label to workloads you want to protect:

```bash
kubectl label deployment my-ai-agent ascend.io/governed=true -n YOUR_NAMESPACE
```

### Step 6: Test the Integration

```bash
# Make a request without agent ID (should be denied)
kubectl exec -it deploy/my-ai-agent -- curl http://backend-service/api/users
# Expected: 401 Unauthorized - Missing X-Ascend-Agent-Id

# Make a request with agent ID
kubectl exec -it deploy/my-ai-agent -- curl \
  -H "X-Ascend-Agent-Id: my-agent" \
  http://backend-service/api/users
# Expected: 200 OK (if approved by ASCEND)
```

Check response headers:
```bash
kubectl exec -it deploy/my-ai-agent -- curl -v \
  -H "X-Ascend-Agent-Id: my-agent" \
  http://backend-service/api/users 2>&1 | grep x-ascend
```

Expected headers on success:
```
x-ascend-status: approved
x-ascend-action-id: 12345
x-ascend-risk-score: 25.0
x-ascend-risk-level: low
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

### Helm Values

See `helm/ascend-authz/values.yaml` for full configuration options.

## Response Behavior

| ASCEND Decision | HTTP Response | Headers |
|-----------------|---------------|---------|
| `approved` | Continue to upstream | `x-ascend-status: approved`, action_id, risk_score |
| `pending_approval` | 403 Forbidden | `x-ascend-status: pending_approval`, action_id |
| `denied` | 403 Forbidden | `x-ascend-status: denied`, denial_reason |
| API Error | 503 Service Unavailable | `x-ascend-error: service_unavailable` |

### Denied Response Body

```json
{
  "error": "PermissionDenied",
  "message": "Action denied by governance policy"
}
```

## Circuit Breaker

The circuit breaker protects against ASCEND API failures:

```
Closed → [5 failures] → Open → [30s] → Half-Open → [success] → Closed
                                    → [failure] → Open
```

When open, all requests are denied with 503 status.

## Path Exclusions

Configure paths to bypass governance:

```yaml
excludedPaths:
  - "/health"
  - "/ready"
  - "/metrics"
  - "^/internal/"  # Regex supported
```

## Monitoring

### Health Check

```bash
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

### Metrics

Prometheus metrics available on port 8080:
```bash
curl http://localhost:8080/metrics
```

### Logs

Structured JSON logs include:
- `agent_id`: Agent identifier
- `action_type`: Mapped action type
- `status`: Decision status
- `risk_score`: Calculated risk score
- `latency_ms`: Request latency

## Development

### Build

```bash
make build
```

### Test

```bash
make test
```

### Docker

```bash
make docker
```

### Local Run

```bash
ASCEND_API_URL=https://pilot.owkai.app \
ASCEND_API_KEY=your_key \
make run
```

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

## Troubleshooting

### All Requests Denied

1. Check API key is valid
2. Verify circuit breaker isn't open: `kubectl logs deploy/ascend-authz`
3. Ensure `X-Ascend-Agent-Id` header is present
4. Check network connectivity to ASCEND API

### High Latency

1. Enable caching: `CACHE_TTL=60s`
2. Check ASCEND API response times
3. Consider increasing replica count

### Circuit Breaker Keeps Opening

1. Check ASCEND API health
2. Verify network connectivity
3. Review error logs for root cause
4. Increase threshold temporarily: `CIRCUIT_BREAKER_THRESHOLD=10`

## Support

- Documentation: https://docs.ascend.owkai.app
- Issues: https://github.com/owkai/ascend-envoy-authz/issues
- Email: support@owkai.app

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12 | Initial release |

---

**Author:** ASCEND Platform Engineering
**License:** Proprietary
