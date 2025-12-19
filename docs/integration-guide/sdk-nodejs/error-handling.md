---
title: Error Handling
sidebar_position: 1
---

# Error Handling

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-008 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Handle errors gracefully when integrating with the Ascend API.

## Error Types

### HTTP Errors

```typescript
import axios, { AxiosError } from 'axios';

try {
  const result = await client.submitAction(action);
} catch (error) {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;

    switch (axiosError.response?.status) {
      case 400:
        console.error('Bad Request:', axiosError.response.data.detail);
        break;
      case 401:
        console.error('Authentication failed - check your API key');
        break;
      case 403:
        console.error('Access forbidden - check permissions');
        break;
      case 404:
        console.error('Resource not found');
        break;
      case 429:
        console.error('Rate limited - wait before retrying');
        break;
      case 500:
        console.error('Server error:', axiosError.response.data.detail);
        break;
      default:
        console.error('HTTP error:', axiosError.message);
    }
  } else {
    console.error('Unexpected error:', error);
  }
}
```

### Connection Errors

```typescript
try {
  await client.testConnection();
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNREFUSED') {
      console.error('Cannot connect to API server');
    } else if (error.code === 'ETIMEDOUT') {
      console.error('Connection timed out');
    } else if (error.code === 'ENOTFOUND') {
      console.error('DNS lookup failed - check API URL');
    }
  }
}
```

### Authorization Errors

```typescript
class AuthorizationError extends Error {
  constructor(public reason: string, public actionId?: number) {
    super(`Authorization denied: ${reason}`);
    this.name = 'AuthorizationError';
  }
}

class TimeoutError extends Error {
  constructor(public actionId: number, public timeoutMs: number) {
    super(`Authorization timed out after ${timeoutMs}ms`);
    this.name = 'TimeoutError';
  }
}

// Usage in AuthorizedAgent
async executeIfAuthorized<T>(/* ... */): Promise<T> {
  // ... submit and wait ...

  if (finalResult.decision === 'denied') {
    throw new AuthorizationError(
      finalResult.reason || 'No reason provided',
      result.id
    );
  }

  if (finalResult.decision === 'timeout') {
    throw new TimeoutError(result.id, timeoutMs);
  }

  // ... execute ...
}
```

## Retry Logic

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelayMs?: number;
    maxDelayMs?: number;
    retryOn?: number[];
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelayMs = 1000,
    maxDelayMs = 30000,
    retryOn = [429, 500, 502, 503, 504],
  } = options;

  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (!axios.isAxiosError(error)) {
        throw error;
      }

      const status = error.response?.status;

      // Don't retry client errors (except rate limiting)
      if (status && !retryOn.includes(status)) {
        throw error;
      }

      if (attempt === maxRetries) {
        break;
      }

      // Exponential backoff with jitter
      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelayMs
      );

      console.log(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

// Usage
const result = await withRetry(
  () => client.submitAction(action),
  { maxRetries: 3 }
);
```

## Comprehensive Error Handler

```typescript
interface ErrorResult {
  success: false;
  error: {
    type: 'auth' | 'network' | 'validation' | 'server' | 'unknown';
    message: string;
    code?: string;
    retryable: boolean;
  };
}

interface SuccessResult<T> {
  success: true;
  data: T;
}

type Result<T> = SuccessResult<T> | ErrorResult;

async function safeApiCall<T>(fn: () => Promise<T>): Promise<Result<T>> {
  try {
    const data = await fn();
    return { success: true, data };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;

      if (status === 401 || status === 403) {
        return {
          success: false,
          error: {
            type: 'auth',
            message: detail || 'Authentication failed',
            code: `HTTP_${status}`,
            retryable: false,
          },
        };
      }

      if (status === 400 || status === 422) {
        return {
          success: false,
          error: {
            type: 'validation',
            message: detail || 'Invalid request',
            code: `HTTP_${status}`,
            retryable: false,
          },
        };
      }

      if (status === 429 || (status && status >= 500)) {
        return {
          success: false,
          error: {
            type: 'server',
            message: detail || 'Server error',
            code: `HTTP_${status}`,
            retryable: true,
          },
        };
      }

      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        return {
          success: false,
          error: {
            type: 'network',
            message: 'Network connection failed',
            code: error.code,
            retryable: true,
          },
        };
      }
    }

    return {
      success: false,
      error: {
        type: 'unknown',
        message: String(error),
        retryable: false,
      },
    };
  }
}

// Usage
const result = await safeApiCall(() => client.submitAction(action));

if (result.success) {
  console.log('Action submitted:', result.data.id);
} else {
  console.error(`Error (${result.error.type}): ${result.error.message}`);
  if (result.error.retryable) {
    console.log('This error can be retried');
  }
}
```

## HTTP Status Codes

| Status | Meaning | Retryable |
|--------|---------|-----------|
| 400 | Bad Request - Invalid parameters | No |
| 401 | Unauthorized - Invalid API key | No |
| 403 | Forbidden - Insufficient permissions | No |
| 404 | Not Found - Resource doesn't exist | No |
| 422 | Validation Error - Invalid data | No |
| 429 | Too Many Requests - Rate limited | Yes (with backoff) |
| 500 | Internal Server Error | Yes |
| 502 | Bad Gateway | Yes |
| 503 | Service Unavailable | Yes |
| 504 | Gateway Timeout | Yes |

## Best Practices

1. **Always wrap API calls** in try-catch blocks
2. **Implement retry logic** for transient errors (429, 5xx)
3. **Use exponential backoff** to avoid overwhelming the server
4. **Log errors** with context for debugging
5. **Handle authorization denials** gracefully in your application
6. **Set appropriate timeouts** to prevent hanging requests

## Source Code Reference

Error handling patterns based on:
- `/ow-ai-backend/integration-examples/python_sdk_example.py:177-193`
- HTTP error codes from FastAPI routes in `/ow-ai-backend/routes/`

## Next Steps

- [Python SDK](/sdk/python/installation) - Python SDK documentation
- [REST API](/api/overview) - Direct REST API access
