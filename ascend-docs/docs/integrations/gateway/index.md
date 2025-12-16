---
sidebar_position: 1
title: Gateway Integrations
description: Zero-code AI governance at the infrastructure layer
---

# Gateway Integrations

> **Zero-code AI governance for your existing API infrastructure**

Deploy AI agent governance without modifying a single line of application code. ASCEND gateway integrations intercept API requests at the infrastructure layer, evaluating each action against your security policies before reaching backend services.

## Choose Your Gateway

| Gateway | Best For | Setup Time | Deployment Method |
|---------|----------|------------|-------------------|
| [**AWS API Gateway**](./aws-lambda-authorizer) | AWS-native environments | < 1 hour | CloudFormation / SAM |
| [**Kong Gateway**](./kong-plugin) | Kong users, multi-cloud | < 30 min | LuaRocks / Helm |
| [**Envoy / Istio**](./envoy-istio) | Kubernetes, service mesh | < 30 min | Helm |

## Feature Comparison

| Feature | AWS Lambda | Kong | Envoy/Istio |
|---------|:----------:|:----:|:-----------:|
| **FAIL SECURE** | ✅ | ✅ | ✅ |
| **Circuit Breaker** | ❌ | ✅ | ✅ |
| **Decision Caching** | ✅ | ✅ | ✅ |
| **Kill-Switch** | ✅ | ✅ | ✅ |
| **Health Checks** | CloudWatch | HTTP | gRPC |
| **Metrics** | CloudWatch | Kong Metrics | Prometheus |
| **Retry with Backoff** | ❌ | ✅ | ✅ |

<!-- VALIDATED:
  Kong circuit breaker: kong-plugin-ascend/kong/plugins/ascend/constants.lua:73-74
  Envoy circuit breaker: ascend-envoy-authz/internal/config/config.go:93-95
  Lambda cache: lambda-authorizer/tests/test_handler.py:480-563
  Status: ✅ VERIFIED 2025-12-16
-->

## How It Works

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

### Request Flow

1. **AI Agent** sends API request with `X-Ascend-Agent-Id` header
2. **Gateway** intercepts request and forwards to ASCEND authorizer
3. **ASCEND Authorizer** evaluates action against policies via ASCEND API
4. **Decision** returned: `approved`, `denied`, or `pending_approval`
5. **Gateway** allows request to backend or returns error response

## FAIL SECURE Design

:::danger Critical Security Feature
All gateway integrations are configured to **FAIL SECURE** by default. If ASCEND is unreachable, requests are **DENIED**, not allowed.
:::

| Scenario | Behavior | HTTP Response |
|----------|----------|---------------|
| ASCEND API unreachable | Request DENIED | 503 |
| ASCEND API timeout | Request DENIED | 503 |
| Invalid API key | Request DENIED | 401 |
| Missing agent ID header | Request DENIED | 401 |
| Circuit breaker open | Request DENIED | 503 |
| Action denied by policy | Request DENIED | 403 |
| Pending approval required | Request DENIED | 403 |

## Required Headers

All gateway integrations expect these headers:

| Header | Required | Description |
|--------|:--------:|-------------|
| `X-Ascend-Agent-Id` | **Yes*** | Unique identifier for the AI agent |
| `X-Ascend-Environment` | No | Execution environment (production/staging/development) |
| `X-Ascend-Data-Sensitivity` | No | Data sensitivity level (none/pii/high_sensitivity) |

*Required unless `default_agent_id` is configured in the gateway.

## Response Headers

On successful authorization, these headers are added to the upstream request:

| Header | Description |
|--------|-------------|
| `X-Ascend-Status` | Decision: `approved`, `pending_approval`, `denied` |
| `X-Ascend-Action-Id` | Unique action ID for audit trail |
| `X-Ascend-Risk-Score` | Calculated risk score (0-100) |
| `X-Ascend-Risk-Level` | Classification: `low`, `medium`, `high`, `critical` |

## Circuit Breaker (Kong & Envoy Only)

Kong and Envoy/Istio integrations include circuit breaker protection to prevent cascade failures:

```
Closed → [5 failures] → Open → [30s] → Half-Open → [success] → Closed
                                    → [failure] → Open
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| Threshold | 5 failures | Failures before opening circuit |
| Reset Timeout | 30 seconds | Time before attempting recovery |

<!-- VALIDATED:
  Kong: constants.lua CIRCUIT_BREAKER_THRESHOLD=5, CIRCUIT_BREAKER_RESET_MS=30000
  Envoy: config.go CircuitBreakerThreshold=5, CircuitBreakerTimeout=30s
  Status: ✅ VERIFIED
-->

## Quick Decision Guide

### Choose AWS Lambda Authorizer if:

- ✅ You use AWS API Gateway (REST or HTTP API)
- ✅ You want native CloudWatch metrics and dashboards
- ✅ You prefer SAM/CloudFormation deployment
- ✅ You need Python-based customization

### Choose Kong Plugin if:

- ✅ You run Kong Gateway (OSS or Enterprise)
- ✅ You need circuit breaker protection
- ✅ You want LuaRocks package management
- ✅ You use Kong's declarative configuration

### Choose Envoy/Istio if:

- ✅ You run Kubernetes with Istio service mesh
- ✅ You need gRPC-native performance
- ✅ You want Helm-based deployment
- ✅ You need to govern pod-to-pod traffic

## Common Questions

**Q: Do I need the SDK if I use a Gateway?**

A: No! Gateway integration provides zero-code governance. The SDK is for deep application integration.

**Q: Can I use both SDK and Gateway?**

A: Yes! This provides defense in depth. Gateway blocks unauthorized requests before they reach your app, and SDK adds fine-grained control within your app.

**Q: What happens during ASCEND maintenance?**

A: All gateways FAIL SECURE by default. During maintenance, requests are denied. You can configure `fail_open: true` for non-critical environments (not recommended for production).

**Q: How do I test the integration?**

A: Each gateway guide includes test commands. Send a request with `X-Ascend-Agent-Id` header and check the response headers.

## Next Steps

- [AWS Lambda Authorizer Setup](./aws-lambda-authorizer) — CloudFormation deployment for AWS API Gateway
- [Kong Plugin Setup](./kong-plugin) — LuaRocks installation for Kong Gateway
- [Envoy/Istio Setup](./envoy-istio) — Helm deployment for Kubernetes

## Support

- **Documentation**: https://docs.ascend.owkai.app
- **Email**: support@owkai.app
- **Enterprise Support**: Contact your account representative
