---
Document ID: ASCEND-GW-001
Version: 1.0.0
Author: OW-KAI Platform Engineering
Publisher: OW-kai Technologies Inc.
Classification: Customer Documentation
Last Updated: December 2025
Compliance: SOC 2 Type II, PCI-DSS, HIPAA
Verification: All claims verified against codebase commit 80c3727e
---

# Gateway Integration Overview

Zero-code AI agent governance at the infrastructure layer. Integrate ASCEND with your existing API gateways and service mesh without modifying application code.

## Why Gateway Integration?

Gateway-level integration provides:

- **Zero Application Changes**: Governance enforced at infrastructure layer
- **Uniform Policy Enforcement**: All traffic governed regardless of client
- **FAIL SECURE Design**: Requests blocked on any error (default behavior)
- **Complete Audit Trail**: Every decision logged with full context

## Available Gateway Integrations

| Gateway | Best For | Deployment | Key Features |
|---------|----------|------------|--------------|
| **[AWS Lambda Authorizer](./lambda-authorizer/)** | AWS API Gateway users | CloudFormation/SAM | CloudWatch integration, request caching |
| **[Kong Plugin](./kong-plugin/)** | Kong Gateway users | LuaRocks or manual | Circuit breaker, retry with backoff, decision caching |
| **[Envoy/Istio ext_authz](./envoy-istio/)** | Kubernetes/Service Mesh | Helm chart | gRPC native, circuit breaker, Istio AuthorizationPolicy |

## Decision Matrix

### Choose AWS Lambda Authorizer If:

- You use AWS API Gateway (REST or HTTP API)
- You want native CloudWatch metrics and dashboards
- You need SAM/CloudFormation deployment
- You prefer Python-based customization

### Choose Kong Plugin If:

- You run Kong Gateway (OSS or Enterprise)
- You need circuit breaker protection
- You want LuaRocks package management
- You use Kong's declarative configuration

### Choose Envoy/Istio ext_authz If:

- You run Kubernetes with Istio service mesh
- You need gRPC-native performance
- You want Helm-based deployment
- You need to govern pod-to-pod traffic

## Feature Comparison

| Feature | Lambda | Kong | Envoy |
|---------|--------|------|-------|
| **FAIL SECURE** | Yes | Yes | Yes |
| **Circuit Breaker** | No | Yes (5 failures/30s reset) | Yes (5 failures/30s reset) |
| **Retry with Backoff** | No | Yes (configurable) | Yes (configurable) |
| **Decision Caching** | Yes (approved only) | Yes (TTL-based) | Yes (approved only) |
| **gRPC Support** | No | No | Yes (native) |
| **Health Check** | CloudWatch | HTTP endpoint | gRPC Health |
| **Metrics** | CloudWatch | Kong metrics | Prometheus |

## Common Architecture

All gateway integrations follow the same flow:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  AI Agent   │────▶│   Gateway   │────▶│  ASCEND Authz   │────▶│  ASCEND API │
│  (Client)   │     │  (Proxy)    │     │  (Plugin/Ext)   │     │  (Platform) │
└─────────────┘     └──────┬──────┘     └────────┬────────┘     └──────┬──────┘
                           │                     │                      │
                           │                     │◀─────────────────────┤
                           │                     │   Decision Response  │
                           │◀────────────────────┤                      │
                           │   Allow/Deny        │                      │
                           ▼                     │                      │
                    ┌─────────────┐              │                      │
                    │  Backend    │              │                      │
                    │  Service    │              │                      │
                    └─────────────┘              │                      │
```

## Request Headers

All gateways expect these headers for agent identification:

| Header | Required | Description |
|--------|----------|-------------|
| `X-Ascend-Agent-Id` | Yes* | Unique identifier for the AI agent |
| `X-Ascend-Environment` | No | Execution environment (production/staging/development) |
| `X-Ascend-Data-Sensitivity` | No | Data sensitivity level (none/pii/high_sensitivity) |

*Required unless `require_agent_id=false` or `default_agent_id` is configured.

## Response Headers

On successful authorization, these headers are added to the request:

| Header | Description |
|--------|-------------|
| `X-Ascend-Status` | Decision status: `approved`, `pending_approval`, `denied` |
| `X-Ascend-Action-Id` | Unique action identifier for audit trail |
| `X-Ascend-Risk-Score` | Calculated risk score (0-100) |
| `X-Ascend-Risk-Level` | Risk classification: `low`, `medium`, `high`, `critical` |

## FAIL SECURE Behavior

**All gateways are configured to FAIL SECURE by default:**

| Scenario | Behavior |
|----------|----------|
| ASCEND API unreachable | Request DENIED (503) |
| ASCEND API timeout | Request DENIED (503) |
| Invalid API key | Request DENIED (401) |
| Missing agent ID header | Request DENIED (401) |
| Circuit breaker open | Request DENIED (503) |
| Action denied by policy | Request DENIED (403) |
| Pending approval required | Request DENIED (403) |

To change to FAIL OPEN (NOT RECOMMENDED for production):
- Lambda: Set `ASCEND_FAIL_OPEN=true`
- Kong: Set `fail_open: true`
- Envoy: Set `FAIL_OPEN=true`

## Quick Start Links

| Gateway | Quick Start | Full Documentation |
|---------|-------------|-------------------|
| Lambda | [5-minute setup](./lambda-authorizer/#quick-start) | [Full guide](./lambda-authorizer/) |
| Kong | [5-minute setup](./kong-plugin/#quick-start-30-minutes) | [Full guide](./kong-plugin/) |
| Envoy/Istio | [30-minute setup](./envoy-istio/#quick-start-30-minutes) | [Full guide](./envoy-istio/) |

## Support

- **Documentation**: https://docs.ascend.owkai.app
- **Email**: support@owkai.app
- **Enterprise Support**: Contact your account representative

---

*Gateway integrations maintained by OW-KAI Platform Engineering*
