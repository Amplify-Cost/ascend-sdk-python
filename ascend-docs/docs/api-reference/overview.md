---
sidebar_position: 1
title: API Overview
description: Introduction to the Ascend API
---

# API Overview

The Ascend API provides programmatic access to the enterprise AI governance platform for agent management, action approval, policy enforcement, and analytics.

## Base URL

```
https://pilot.owkai.app/api
```

All API endpoints are versioned where applicable. The primary action submission API uses `/api/v1/`.

## Authentication Methods

The API supports three authentication methods:

| Method | Header | Use Case |
|--------|--------|----------|
| **Session Cookie** | `Cookie: access_token=...` | Admin UI, browser-based access |
| **Bearer Token** | `Authorization: Bearer <jwt>` | Cognito JWT, programmatic access |
| **API Key** | `X-API-Key: <key>` or `Authorization: Bearer <key>` | SDK integration, automation |

### Quick Start with API Key

```bash
# Generate an API key from the Admin Console
# Then use it in your requests:

curl "https://pilot.owkai.app/api/v1/actions" \
  -H "X-API-Key: owkai_admin_your_api_key_here"
```

### Quick Start with JWT

```bash
# After Cognito authentication:
curl "https://pilot.owkai.app/api/v1/actions" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..."
```

## API Categories

| Category | Base Path | Description |
|----------|-----------|-------------|
| [Actions](/docs/api-reference/actions) | `/api/v1/actions` | Submit and manage agent actions |
| [Agents](/docs/api-reference/agents) | `/api/registry/agents` | Agent registration and management |
| [Smart Rules](/docs/api-reference/smart-rules) | `/api/smart-rules` | Automated governance rules |
| [Analytics](/docs/api-reference/analytics) | `/api/analytics` | Metrics and reporting |
| [MCP Governance](/docs/api-reference/mcp-governance) | `/api/mcp-governance` | MCP server governance |

## Request Format

All POST/PUT/PATCH requests should use JSON:

```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/submit" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-service-agent",
    "action_type": "email_send",
    "description": "Send welcome email"
  }'
```

## Response Format

All responses are JSON with consistent structure:

### Success Response

```json
{
  "success": true,
  "data": {
    "id": "action_123",
    "status": "approved"
  }
}
```

### Error Response

```json
{
  "detail": "Authentication required",
  "status_code": 401
}
```

### Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "agent_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

API keys have configurable rate limits:

| Setting | Default | Maximum |
|---------|---------|---------|
| Requests per hour | 1,000 | 100,000 |
| Requests per day | 10,000 | 1,000,000 |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1704067200
```

When rate limited, you'll receive:

```json
{
  "detail": "Rate limit exceeded"
}
```

**Headers:**
```
Retry-After: 3600
```

## Pagination

List endpoints support pagination:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `limit` | 50 | Items per page (max 100) |
| `offset` | 0 | Starting position |
| `page` | 1 | Page number (alternative) |

**Example:**

```bash
curl "https://pilot.owkai.app/api/v1/actions?limit=20&offset=40"
```

**Response:**

```json
{
  "total": 150,
  "limit": 20,
  "offset": 40,
  "items": [...]
}
```

## Multi-Tenant Isolation

All API requests are automatically filtered by organization:

- Your API key is linked to your organization
- You can only access data belonging to your organization
- Cross-tenant access is blocked at the database layer (SEC-007)

**Compliance:** SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)

## Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes (POST/PUT) | `application/json` |
| `X-API-Key` | Conditional | API key authentication |
| `Authorization` | Conditional | Bearer token authentication |
| `X-Request-ID` | No | Request correlation ID |
| `X-CSRF-Token` | Cookie auth only | CSRF protection token |

## SDK Integration

Official SDKs are available for common languages:

| Language | Package | Documentation |
|----------|---------|---------------|
| Python | `ascend-sdk` | [Python SDK](/docs/sdk/python) |
| Node.js | `@ascend/sdk` | [Node.js SDK](/docs/sdk/nodejs) |
| REST | N/A | [REST API](/docs/sdk/rest) |

## Webhooks

Configure webhooks to receive real-time notifications:

```json
{
  "event_type": "action.approved",
  "webhook_url": "https://your-server.com/webhook",
  "secret": "your_webhook_secret"
}
```

Events are signed with HMAC-SHA256 for verification.

## Health Check

Verify API availability:

```bash
curl "https://pilot.owkai.app/health"
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

## Support

- **Documentation**: [docs.ascend.ai](https://docs.ascend.ai)
- **Status**: [status.ascend.ai](https://status.ascend.ai)
- **Support**: support@ascend.ai

---

*Source: [main.py](https://github.com/owkai/ow-ai-backend/blob/main/main.py), [dependencies.py](https://github.com/owkai/ow-ai-backend/blob/main/dependencies.py)*
