---
title: ASCEND Lambda Authorizer
sidebar_position: 1
---

# ASCEND Lambda Authorizer

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-003 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Zero-code AI governance for AWS API Gateway.

## Overview

The ASCEND Lambda Authorizer integrates your AWS API Gateway with the ASCEND Platform to provide real-time governance decisions for AI agent API calls. Every API request is evaluated against your organization's policies, risk thresholds, and compliance requirements before being allowed or denied.

## Features

- **Real-time Risk Assessment**: Every API call is evaluated by ASCEND's 11-stage risk pipeline
- **FAIL SECURE**: Errors always result in denial - no silent failures
- **Smart Caching**: Approved decisions are cached to minimize latency
- **CloudWatch Integration**: Full metrics, logging, and dashboards included
- **Multi-tenant Ready**: Supports organization-level isolation

## Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- ASCEND Platform account with API key
- AWS CLI and SAM CLI installed

### Step 1: Store Your API Key

```bash
aws secretsmanager create-secret \
    --name ascend/api-key \
    --secret-string '{"api_key":"your_ascend_api_key_here"}'
```

### Step 2: Deploy the Stack

```bash
cd cloudformation

sam deploy \
    --template-file template.yaml \
    --stack-name ascend-authorizer \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        AscendApiUrl=https://api.ascend.owkai.app \
        AscendApiKeySecret=arn:aws:secretsmanager:us-east-1:123456789012:secret:ascend/api-key \
        Environment=production
```

### Step 3: Configure API Gateway

Add the Lambda authorizer to your API Gateway:

```bash
# Get the authorizer ARN from the stack outputs
AUTHORIZER_ARN=$(aws cloudformation describe-stacks \
    --stack-name ascend-authorizer \
    --query 'Stacks[0].Outputs[?OutputKey==`AuthorizerFunctionArn`].OutputValue' \
    --output text)

# Create the authorizer in API Gateway
aws apigateway create-authorizer \
    --rest-api-id YOUR_API_ID \
    --name ascend-authorizer \
    --type REQUEST \
    --authorizer-uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${AUTHORIZER_ARN}/invocations" \
    --identity-source "method.request.header.X-Ascend-Agent-Id"
```

### Step 4: Add Required Headers to Your API Calls

```bash
curl -X GET https://your-api.execute-api.us-east-1.amazonaws.com/prod/users \
    -H "X-Ascend-Agent-Id: my-ai-agent" \
    -H "X-Ascend-Environment: production" \
    -H "X-Ascend-Data-Sensitivity: none"
```

## Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-Ascend-Agent-Id` | Yes | Unique identifier for the AI agent |
| `X-Ascend-Environment` | No | Execution environment (production/staging/development) |
| `X-Ascend-Data-Sensitivity` | No | Data sensitivity level (none/pii/high_sensitivity) |
| `X-Ascend-Target-System` | No | Target resource identifier |
| `X-Ascend-Action-Type` | No | Custom action type (overrides auto-detection) |

## How It Works

```
┌─────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│   API Client    │────▶│   API Gateway      │────▶│ Lambda Authorizer│
│  (AI Agent)     │     │                    │     │                  │
└─────────────────┘     └────────────────────┘     └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │  ASCEND Platform │
                                                   │  Risk Assessment │
                                                   └────────┬─────────┘
                                                            │
                              ┌──────────────────────────────┼──────────────────────────────┐
                              │                              │                              │
                              ▼                              ▼                              ▼
                     ┌────────────────┐            ┌────────────────┐            ┌────────────────┐
                     │   APPROVED     │            │PENDING_APPROVAL│            │     DENIED     │
                     │   Risk < 30    │            │  30 ≤ Risk < 80│            │   Risk ≥ 80    │
                     │                │            │                │            │                │
                     │ → Allow Policy │            │ → Deny Policy  │            │ → Deny Policy  │
                     │ → Cache 60s    │            │ → Action ID    │            │ → Reason       │
                     └────────────────┘            └────────────────┘            └────────────────┘
```

## Authorization Flow

1. **Request Mapping**: API Gateway event is mapped to ASCEND action format
2. **Cache Check**: If caching enabled, check for cached approved decision
3. **ASCEND API Call**: Submit action for governance evaluation
4. **Policy Generation**: Generate Allow/Deny IAM policy based on response
5. **Cache Update**: Cache approved decisions for configured TTL

## Response Statuses

| ASCEND Status | Result | Description |
|---------------|--------|-------------|
| `approved` | **Allow** | Action permitted, request continues |
| `pending_approval` | **Deny** | Needs human review, action ID in context |
| `denied` | **Deny** | Policy violation, reason in context |
| Error | **Deny** | FAIL SECURE - any error denies |

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ASCEND_API_URL` | Yes | - | ASCEND Platform API URL |
| `ASCEND_API_KEY` | Yes* | - | API key (or use secret ARN) |
| `ASCEND_API_KEY_SECRET_ARN` | Yes* | - | Secrets Manager ARN |
| `ASCEND_ENVIRONMENT` | No | production | Environment context |
| `ASCEND_CACHE_TTL` | No | 60 | Cache TTL in seconds |
| `ASCEND_TIMEOUT` | No | 4 | API timeout (max 4s) |
| `LOG_LEVEL` | No | INFO | Logging level |
| `ASCEND_METRICS_ENABLED` | No | true | Enable CloudWatch metrics |

*Either `ASCEND_API_KEY` or `ASCEND_API_KEY_SECRET_ARN` is required.

### CloudFormation Parameters

See `cloudformation/template.yaml` for all available parameters.

## Monitoring

### CloudWatch Dashboard

The deployment creates a CloudWatch dashboard with:
- Authorization decisions by status
- Latency percentiles (p50, p90, p99)
- Cache hit/miss rates
- Error counts by type
- Lambda invocation metrics

### CloudWatch Metrics

| Metric | Dimensions | Description |
|--------|------------|-------------|
| `Decisions` | Status, AgentId | Count of authorization decisions |
| `Latency` | - | Authorization latency (ms) |
| `CacheHits` | - | Successful cache lookups |
| `CacheMisses` | - | Cache misses requiring API call |
| `Errors` | ErrorType | Error counts by type |

### CloudWatch Alarms

Default alarms included:
- **HighErrorRate**: >10 errors in 5 minutes
- **HighLatency**: p99 >100ms for 15 minutes

## Troubleshooting

### Authorization Always Denied

1. Check `X-Ascend-Agent-Id` header is present
2. Verify API key is valid in Secrets Manager
3. Check CloudWatch logs for error details
4. Verify ASCEND Platform is reachable

### High Latency

1. Enable caching if disabled
2. Increase cache TTL
3. Check ASCEND API response times
4. Consider increasing Lambda memory

### Cache Not Working

1. Verify `ASCEND_CACHE_TTL` > 0
2. Only `approved` decisions are cached
3. Cache is per-Lambda-instance (cold starts reset)

## Security Considerations

- **FAIL SECURE**: All errors result in Deny
- **TLS Required**: All API communication uses HTTPS
- **Secret Management**: API key stored in Secrets Manager
- **No Sensitive Logging**: Tokens/keys never logged
- **Audit Trail**: All decisions logged to CloudWatch

## Support

- Documentation: https://docs.owkai.app
- Support: support@owkai.app
- Issues: https://github.com/owkai/ascend-lambda-authorizer/issues

## License

Apache-2.0

---

*ASCEND Platform Engineering - Making AI agents governable*
