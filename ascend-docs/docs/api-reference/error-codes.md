---
sidebar_position: 8
title: Error Codes
description: API error codes and troubleshooting
---

# Error Codes

Complete reference for API error codes, error responses, and troubleshooting guidance.

## HTTP Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content to return |

### Client Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Request timeout |

---

## Error Response Format

All errors return a JSON response with the `detail` field:

### Simple Error

```json
{
  "detail": "Authentication required"
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
    },
    {
      "loc": ["body", "action_type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Error with Status Code

```json
{
  "detail": "Resource not found",
  "status_code": 404
}
```

---

## Authentication Errors

### 401 Unauthorized

**Causes:**
- Missing authentication header/cookie
- Expired access token
- Invalid token signature
- Malformed JWT token

**Error Messages:**

```json
{"detail": "Authentication required"}
{"detail": "Token has expired"}
{"detail": "Invalid token signature"}
{"detail": "Could not validate credentials"}
```

**Resolution:**
1. Ensure `X-API-Key` or `Authorization: Bearer` header is present
2. Check if token has expired (access tokens expire after 60 minutes)
3. Refresh expired tokens using `/api/auth/refresh`
4. Verify API key is valid and not revoked

---

### 403 Forbidden

**Causes:**
- Insufficient role permissions
- CSRF validation failed
- Cross-organization access attempt
- Admin-only endpoint accessed by non-admin

**Error Messages:**

```json
{"detail": "Admin access required"}
{"detail": "User has no organization"}
{"detail": "Organization context required"}
{"detail": "CSRF validation failed"}
{"detail": "Insufficient permissions for this operation"}
```

**Resolution:**
1. Verify user has required role (admin, manager, user)
2. Include CSRF token in mutating requests (POST, PUT, DELETE)
3. Ensure user belongs to an organization
4. Contact admin to elevate permissions if needed

---

## Rate Limiting Errors

### 429 Too Many Requests

**Error Response:**

```json
{
  "detail": "Rate limit exceeded"
}
```

**Headers:**

```
Retry-After: 3600
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
```

**Rate Limits:**

| Setting | Default | Maximum |
|---------|---------|---------|
| Requests per hour | 1,000 | 100,000 |
| Requests per day | 10,000 | 1,000,000 |

**Resolution:**
1. Wait for the time specified in `Retry-After` header
2. Implement exponential backoff in your integration
3. Request rate limit increase through admin console
4. Optimize API calls to reduce request frequency

---

## Validation Errors

### 422 Unprocessable Entity

**Common Validation Errors:**

```json
{
  "detail": "Missing required fields: agent_id, action_type"
}
```

```json
{
  "detail": [
    {
      "loc": ["body", "risk_score"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Field Requirements:**

| Field | Rules |
|-------|-------|
| `agent_id` | Required, 3-64 characters |
| `action_type` | Required, non-empty string |
| `risk_score` | 0-100 integer |
| `risk_level` | `low`, `medium`, `high`, `critical` |
| `email` | Valid email format |

---

## Resource Errors

### 404 Not Found

**Error Messages:**

```json
{"detail": "Agent not found"}
{"detail": "Action not found"}
{"detail": "Smart rule not found"}
{"detail": "MCP server not found"}
{"detail": "Policy not found"}
{"detail": "User not found"}
```

**Resolution:**
1. Verify resource ID is correct
2. Check if resource exists in your organization
3. Ensure resource hasn't been deleted
4. Use list endpoints to find valid resource IDs

---

### 409 Conflict

**Error Messages:**

```json
{"detail": "Agent with ID 'my-agent' already exists"}
{"detail": "MCP server filesystem-server already registered"}
{"detail": "API key with this name already exists"}
```

**Resolution:**
1. Use a different unique identifier
2. Update existing resource instead of creating new
3. Delete existing resource first if replacement is intended

---

## Workflow Errors

### Action Status Errors

```json
{"detail": "Action not in pending status"}
{"detail": "Action already approved"}
{"detail": "Action not approved. Current status: PENDING_APPROVAL"}
{"detail": "Invalid status transition"}
```

**Valid Status Transitions:**

| From | To | Action |
|------|-----|--------|
| `pending_approval` | `approved` | Approve |
| `pending_approval` | `denied` | Reject |
| `approved` | `completed` | Execute |
| `auto_approved` | `completed` | Execute |

---

### Approval Errors

```json
{"detail": "Insufficient approval level"}
{"detail": "Action requires L2 approval"}
{"detail": "Self-approval not permitted"}
```

**Approval Levels:**

| Level | Role Required |
|-------|---------------|
| 1 | User |
| 2 | Manager |
| 3 | Admin |
| 4 | Senior Admin |
| 5 | Security Officer |

---

## Agent Governance Errors

### Rate Limit Exceeded

```json
{
  "detail": "Rate limit exceeded",
  "limits": {
    "per_minute": {"limit": 10, "current": 12},
    "per_hour": {"limit": 100, "current": 105}
  }
}
```

### Budget Exceeded

```json
{
  "detail": "Daily budget exceeded",
  "budget": {
    "max_daily_usd": 1000,
    "current_spend_usd": 1045.50
  }
}
```

### Time Window Violation

```json
{
  "detail": "Action outside allowed time window",
  "allowed_window": {
    "start_time": "09:00",
    "end_time": "17:00",
    "timezone": "America/New_York",
    "current_time": "23:45"
  }
}
```

---

## Multi-Tenant Errors

### Organization Errors

```json
{"detail": "User has no organization"}
{"detail": "Organization not found"}
{"detail": "Organization context required"}
{"detail": "Cross-organization access denied"}
```

**Resolution:**
1. Ensure user is assigned to an organization
2. Verify organization exists and is active
3. API keys are scoped to single organization
4. Cannot access resources from other organizations

---

## Server Errors

### 500 Internal Server Error

```json
{"detail": "An unexpected error occurred"}
{"detail": "Database connection failed"}
{"detail": "Failed to process request"}
```

**Resolution:**
1. Retry request after brief delay
2. Check service status at status.ascend.ai
3. Contact support if error persists
4. Include correlation ID in support request

---

### 503 Service Unavailable

```json
{"detail": "Service temporarily unavailable"}
{"detail": "MCP governance system unavailable"}
{"detail": "Database maintenance in progress"}
```

**Resolution:**
1. Check status page for maintenance windows
2. Retry with exponential backoff
3. Wait for service to become available

---

## Error Handling Best Practices

### Retry Strategy

```python
import time
import requests

def api_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            # Rate limited - wait and retry
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue

        if response.status_code >= 500:
            # Server error - exponential backoff
            time.sleep(2 ** attempt)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### Error Logging

Include these fields when logging errors:

| Field | Description |
|-------|-------------|
| `correlation_id` | Request correlation ID from response |
| `timestamp` | When error occurred |
| `endpoint` | API endpoint called |
| `status_code` | HTTP status code |
| `error_detail` | Error message from response |

---

## Support

For persistent errors or unclear error messages:

1. Check [status.ascend.ai](https://status.ascend.ai) for service status
2. Review API documentation for correct usage
3. Contact support@ascend.ai with:
   - Correlation ID (if available)
   - Request details (endpoint, method, headers)
   - Response received
   - Timestamp of occurrence

---

*Source: Aggregated from all API route implementations*
