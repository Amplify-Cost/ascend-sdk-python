---
sidebar_position: 2
title: AWS API Gateway
description: Lambda Authorizer for AWS API Gateway
---

# AWS API Gateway Integration

> **Setup Time:** < 1 hour | **Code Changes:** None | **Skill Level:** DevOps

Zero-code AI governance for AWS API Gateway using a Lambda Authorizer.

## Quick Decision

✅ **Use this if:** You're running AWS API Gateway (REST or HTTP API)

❌ **Don't use if:** You're using Kong (see [Kong Plugin](./kong-plugin)) or Istio (see [Envoy/Istio](./envoy-istio))

## What You'll Get

- **Zero-code governance** — No application changes required
- **Real-time risk assessment** — Every API call evaluated by ASCEND's risk pipeline
- **FAIL SECURE design** — Errors always result in denial
- **Smart caching** — Approved decisions cached to minimize latency
- **CloudWatch integration** — Full metrics, logging, and dashboards
- **Complete audit trail** — Every decision logged with context

## Prerequisites

Before starting, ensure you have:

- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI configured (`aws configure`)
- [ ] AWS SAM CLI installed ([Install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- [ ] ASCEND Platform account with API key ([Get one here](https://pilot.owkai.app))

## Quick Start (5 minutes)

### Step 1: Store Your API Key

```bash
aws secretsmanager create-secret \
    --name ascend/api-key \
    --secret-string '{"api_key":"YOUR_ASCEND_API_KEY"}'
```

<!-- VALIDATED:
  Command: Standard AWS Secrets Manager CLI
  Status: ✅ VERIFIED
-->

### Step 2: Deploy the Stack

```bash
cd cloudformation

sam deploy \
    --template-file template.yaml \
    --stack-name ascend-authorizer \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        AscendApiUrl=https://pilot.owkai.app \
        AscendApiKeySecret=arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT:secret:ascend/api-key \
        Environment=production
```

### Step 3: Test the Integration

```bash
# Request without agent ID (should be denied)
curl -X GET https://YOUR_API.execute-api.us-east-1.amazonaws.com/prod/users
# Expected: 401 Unauthorized

# Request with agent ID
curl -X GET https://YOUR_API.execute-api.us-east-1.amazonaws.com/prod/users \
    -H "X-Ascend-Agent-Id: my-ai-agent"
# Expected: 200 OK (if approved by ASCEND)
```

## Full Setup Guide

### 1. Create the Secret

Store your ASCEND API key securely in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
    --name ascend/api-key \
    --description "ASCEND Platform API key for Lambda Authorizer" \
    --secret-string '{"api_key":"owkai_live_YOUR_KEY_HERE"}'
```

:::warning Security
Never hardcode API keys in code or CloudFormation templates. Always use Secrets Manager.
:::

### 2. Deploy with CloudFormation

**Option A: SAM CLI (Recommended)**

```bash
sam deploy \
    --template-file template.yaml \
    --stack-name ascend-authorizer \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        AscendApiUrl=https://pilot.owkai.app \
        AscendApiKeySecret=arn:aws:secretsmanager:REGION:ACCOUNT:secret:ascend/api-key \
        Environment=production \
        CacheTtlSeconds=60 \
        TimeoutSeconds=4
```

**Option B: AWS Console**

1. Go to CloudFormation → Create Stack
2. Upload `template.yaml`
3. Fill in parameters
4. Check "I acknowledge that AWS CloudFormation might create IAM resources"
5. Create Stack

### 3. Configure API Gateway

After the stack is created, attach the authorizer to your API:

```bash
# Get the authorizer ARN from stack outputs
AUTHORIZER_ARN=$(aws cloudformation describe-stacks \
    --stack-name ascend-authorizer \
    --query 'Stacks[0].Outputs[?OutputKey==`AuthorizerFunctionArn`].OutputValue' \
    --output text)

# Create the authorizer in API Gateway
aws apigateway create-authorizer \
    --rest-api-id YOUR_API_ID \
    --name ascend-authorizer \
    --type REQUEST \
    --authorizer-uri "arn:aws:apigateway:REGION:lambda:path/2015-03-31/functions/${AUTHORIZER_ARN}/invocations" \
    --identity-source "method.request.header.X-Ascend-Agent-Id"
```

### 4. Apply to Methods

In the AWS Console:

1. Go to API Gateway → Your API → Resources
2. Select a method (e.g., GET /users)
3. Click "Method Request"
4. Set "Authorization" to your `ascend-authorizer`
5. Deploy the API to apply changes

## Configuration Reference

### CloudFormation Parameters

| Parameter | Required | Default | Description |
|-----------|:--------:|---------|-------------|
| `AscendApiUrl` | **Yes** | — | ASCEND Platform API URL |
| `AscendApiKeySecret` | **Yes** | — | Secrets Manager ARN for API key |
| `Environment` | No | production | Environment label |
| `CacheTtlSeconds` | No | 60 | Cache TTL for approved decisions |
| `TimeoutSeconds` | No | 4 | API request timeout (max 4s) |
| `LogLevel` | No | INFO | Logging level |
| `MetricsEnabled` | No | true | Enable CloudWatch metrics |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASCEND_API_URL` | **required** | ASCEND Platform API URL |
| `ASCEND_API_KEY` | **required*** | API key (or use secret ARN) |
| `ASCEND_API_KEY_SECRET_ARN` | **required*** | Secrets Manager ARN |
| `ASCEND_ENVIRONMENT` | production | Environment context |
| `ASCEND_CACHE_TTL` | 60 | Cache TTL in seconds |
| `ASCEND_TIMEOUT` | 4 | API timeout (max 4s) |
| `LOG_LEVEL` | INFO | Logging level |
| `ASCEND_METRICS_ENABLED` | true | Enable CloudWatch metrics |

*Either `ASCEND_API_KEY` or `ASCEND_API_KEY_SECRET_ARN` is required.

## Required Headers

| Header | Required | Description |
|--------|:--------:|-------------|
| `X-Ascend-Agent-Id` | **Yes** | Unique identifier for the AI agent |
| `X-Ascend-Environment` | No | Override environment (production/staging/development) |
| `X-Ascend-Data-Sensitivity` | No | Data sensitivity level (none/pii/high_sensitivity) |
| `X-Ascend-Target-System` | No | Target resource identifier |
| `X-Ascend-Action-Type` | No | Custom action type (overrides auto-detection) |

## Response Behavior

| ASCEND Decision | Result | Description |
|-----------------|--------|-------------|
| `approved` | **Allow** | Request continues to backend |
| `pending_approval` | **Deny** | Needs human review, action ID returned |
| `denied` | **Deny** | Policy violation, reason returned |
| Error | **Deny** | FAIL SECURE — any error denies |

<!-- VALIDATED:
  Source: lambda-authorizer/src/policy_generator.py
  Cache behavior: lambda-authorizer/tests/test_handler.py:480-563
  Status: ✅ VERIFIED
-->

## Caching Behavior

The Lambda Authorizer caches **approved decisions only** to minimize latency:

| Decision | Cached | Reason |
|----------|:------:|--------|
| `approved` | ✅ Yes | Safe to cache positive decisions |
| `denied` | ❌ No | May change if policy updated |
| `pending_approval` | ❌ No | Status may change when approved |
| Error | ❌ No | Should retry |

Default cache TTL: **60 seconds** (configurable via `CacheTtlSeconds`)

<!-- VALIDATED:
  Source: lambda-authorizer/tests/test_handler.py:508-533
  "Test that cache does NOT store denied decisions"
  Status: ✅ VERIFIED
-->

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
| `Latency` | — | Authorization latency (ms) |
| `CacheHits` | — | Successful cache lookups |
| `CacheMisses` | — | Cache misses requiring API call |
| `Errors` | ErrorType | Error counts by type |

### CloudWatch Alarms

Default alarms included:

- **HighErrorRate**: >10 errors in 5 minutes
- **HighLatency**: p99 >100ms for 15 minutes

## Troubleshooting

### Authorization Always Denied

1. **Check agent ID header**: Ensure `X-Ascend-Agent-Id` is present
   ```bash
   curl -v -H "X-Ascend-Agent-Id: test-agent" https://YOUR_API/endpoint
   ```

2. **Verify API key**: Check key is valid in Secrets Manager
   ```bash
   aws secretsmanager get-secret-value --secret-id ascend/api-key
   ```

3. **Check CloudWatch logs**: Look for error messages
   ```bash
   aws logs tail /aws/lambda/ascend-authorizer --follow
   ```

4. **Verify ASCEND connectivity**: Test API directly
   ```bash
   curl -X GET https://pilot.owkai.app/health \
       -H "X-API-Key: YOUR_KEY"
   ```

### High Latency

1. **Enable caching**: Ensure `CacheTtlSeconds` > 0
2. **Increase cache TTL**: Set `CacheTtlSeconds=300` for 5 minutes
3. **Check Lambda memory**: Increase to 256MB or 512MB
4. **Check ASCEND API latency**: Review CloudWatch metrics

### Lambda Timeout

1. Maximum Lambda authorizer timeout is **29 seconds**
2. ASCEND timeout should be **4 seconds** or less
3. If ASCEND is slow, circuit breaker isn't available (use Kong or Envoy instead)

## Security Best Practices

1. **Use Secrets Manager** — Never hardcode API keys
2. **Restrict IAM permissions** — Lambda only needs `secretsmanager:GetSecretValue`
3. **Enable VPC** — Optional, for private API access
4. **Monitor failures** — Set up CloudWatch alarms
5. **Rotate API keys** — Use ASCEND key rotation feature

## Limitations

| Feature | Status | Alternative |
|---------|--------|-------------|
| Circuit Breaker | ❌ Not available | Use Kong or Envoy |
| Retry with Backoff | ❌ Not available | Use Kong or Envoy |
| gRPC Support | ❌ Not available | Use Envoy |

## Next Steps

- [Gateway Overview](./) — Compare all gateway options
- [Kong Plugin](./kong-plugin) — Alternative with circuit breaker
- [Envoy/Istio](./envoy-istio) — Kubernetes-native option
- [API Reference](/api-reference/actions) — Full API documentation

## Support

- **Documentation**: https://docs.ascend.owkai.app
- **Email**: support@owkai.app
- **Issues**: https://github.com/owkai/ascend-lambda-authorizer/issues
