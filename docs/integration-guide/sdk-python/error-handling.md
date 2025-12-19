---
title: Error Handling
sidebar_position: 1
---

# Error Handling

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-013 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Learn how to handle errors effectively when using the OW-AI Python SDK.

> **Source of Truth**: Based on `OWKAIClient._request()` error handling implementation (lines 152-193 in `python_sdk_example.py`)

## Exception Types

The SDK uses standard Python exceptions for error handling:

| Exception | Raised When | Example |
|-----------|-------------|---------|
| `ValueError` | Missing required configuration (API key) | Missing `OWKAI_API_KEY` |
| `requests.exceptions.HTTPError` | HTTP error response (4xx, 5xx) | 401 Unauthorized, 500 Server Error |
| `TimeoutError` | Request timeout | Network latency, slow server |
| `ConnectionError` | Network connection failure | Cannot reach API server |
| `Exception` | General API error | Wrapped API error responses |
| `PermissionError` | Action denied by policy | Raised by `execute_if_authorized()` |

## Basic Error Handling

### Try-Except Pattern

```python
from python_sdk_example import OWKAIClient, AgentAction

try:
    client = OWKAIClient()
    action = AgentAction(
        agent_id="my-agent",
        agent_name="My Agent",
        action_type="data_access",
        resource="database"
    )
    response = client.submit_action(action)
    print(f"Success: {response['action_id']}")

except ValueError as e:
    print(f"Configuration error: {e}")
    # Missing API key or invalid configuration

except TimeoutError as e:
    print(f"Request timed out: {e}")
    # Request took too long

except ConnectionError as e:
    print(f"Network error: {e}")
    # Cannot reach API server

except Exception as e:
    print(f"API error: {e}")
    # Other errors from API
```

## Configuration Errors

### Missing API Key

The SDK validates API key on initialization (lines 139-140):

```python
from python_sdk_example import OWKAIClient

try:
    client = OWKAIClient()  # No OWKAI_API_KEY in environment

except ValueError as e:
    print(f"Error: {e}")
    # Output: "API key is required. Set OWKAI_API_KEY environment variable."
```

**Solution**:
```bash
# Set environment variable
export OWKAI_API_KEY=owkai_live_your_key_here

# Or create .env file
echo "OWKAI_API_KEY=owkai_live_your_key_here" > .env
```

Implementation reference (lines 139-140):
```python
if not self.api_key:
    raise ValueError("API key is required. Set OWKAI_API_KEY environment variable.")
```

## HTTP Errors

### Authentication Errors (401)

```python
from python_sdk_example import OWKAIClient

try:
    client = OWKAIClient(api_key="invalid_key")
    response = client.test_connection()

except Exception as e:
    if "401" in str(e) or "Unauthorized" in str(e):
        print("Authentication failed - check your API key")
    else:
        print(f"Error: {e}")
```

### Authorization Errors (403)

```python
try:
    response = client.submit_action(action)

except Exception as e:
    if "403" in str(e) or "Forbidden" in str(e):
        print("Access denied - insufficient permissions")
    else:
        print(f"Error: {e}")
```

### Not Found Errors (404)

```python
try:
    action = client.get_action_details("nonexistent_id")

except Exception as e:
    if "404" in str(e) or "Not Found" in str(e):
        print("Action not found")
    else:
        print(f"Error: {e}")
```

### Server Errors (500)

```python
try:
    response = client.submit_action(action)

except Exception as e:
    if "500" in str(e) or "Internal Server Error" in str(e):
        print("Server error - try again later")
        # Log error and retry
    else:
        print(f"Error: {e}")
```

## Network Errors

### Connection Failure

Implementation reference (lines 191-193):
```python
except requests.exceptions.ConnectionError:
    logger.error("Connection error")
    raise ConnectionError("Failed to connect to OW-AI API")
```

Handling:
```python
import time
from python_sdk_example import OWKAIClient

def submit_with_retry(action, max_retries=3, backoff=2):
    """Submit action with exponential backoff retry."""
    last_error = None

    for attempt in range(max_retries):
        try:
            client = OWKAIClient()
            return client.submit_action(action)

        except ConnectionError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff ** attempt
                print(f"Connection failed, retrying in {wait}s...")
                time.sleep(wait)

    raise last_error
```

### Timeout Errors

Implementation reference (lines 188-189):
```python
except requests.exceptions.Timeout:
    logger.error("Request timeout")
    raise TimeoutError("API request timed out")
```

Handling:
```python
from python_sdk_example import OWKAIClient

try:
    client = OWKAIClient(timeout=30)  # 30 second timeout
    response = client.submit_action(action)

except TimeoutError as e:
    print(f"Request timed out: {e}")
    # Retry with longer timeout
    client = OWKAIClient(timeout=60)
    response = client.submit_action(action)
```

### Configurable Timeout

```python
# Default timeout
client = OWKAIClient()  # 30 seconds (default)

# Custom timeout for slow networks
client = OWKAIClient(timeout=90)

# Short timeout for fast-fail
client = OWKAIClient(timeout=5)
```

## API Response Errors

### Extracting Error Details

Implementation reference (lines 177-185):
```python
except requests.exceptions.HTTPError as e:
    error_detail = "Unknown error"
    try:
        error_detail = e.response.json().get('detail', str(e))
    except:
        error_detail = str(e)

    logger.error(f"API Error: {error_detail}")
    raise Exception(f"API Error: {error_detail}")
```

Usage:
```python
from python_sdk_example import OWKAIClient

try:
    client = OWKAIClient()
    response = client.submit_action(action)

except Exception as e:
    error_message = str(e)

    # Check for specific error patterns
    if "API Error:" in error_message:
        # Extract the actual error from the API
        api_error = error_message.replace("API Error: ", "")
        print(f"API returned error: {api_error}")
```

## Action-Level Errors

### Permission Denied

The `AuthorizedAgent.execute_if_authorized()` raises `PermissionError` (lines 450-452):

```python
from python_sdk_example import AuthorizedAgent

agent = AuthorizedAgent("my-agent", "My Agent")

def sensitive_operation():
    return {"result": "success"}

try:
    result = agent.execute_if_authorized(
        action_type="data_modification",
        resource="production_database",
        execute_fn=sensitive_operation
    )
    print(f"Result: {result}")

except PermissionError as e:
    print(f"Permission denied: {e}")
    # Log denial and notify user
```

Implementation reference (lines 450-452):
```python
elif status == 'denied':
    reason = decision.get('reason', 'No reason provided')
    raise PermissionError(f"Action denied: {reason}")
```

### Authorization Timeout

The `execute_if_authorized()` raises `TimeoutError` for decision timeouts (lines 454-455):

```python
try:
    result = agent.execute_if_authorized(
        action_type="transaction",
        resource="financial_account",
        execute_fn=process_transaction,
        timeout=60  # 60 second timeout
    )

except TimeoutError as e:
    print(f"Authorization timeout: {e}")
    # Approval took too long - notify and log
```

Implementation reference (lines 454-455):
```python
elif status == 'timeout':
    raise TimeoutError("Authorization decision timed out")
```

## Comprehensive Error Handler

```python
import logging
from python_sdk_example import OWKAIClient, AgentAction

logger = logging.getLogger(__name__)

def safe_submit_action(action: AgentAction) -> dict:
    """Submit action with comprehensive error handling."""

    try:
        client = OWKAIClient()
        response = client.submit_action(action)

        return {
            "success": True,
            "action_id": response.get('action_id'),
            "decision": response.get('decision', response.get('status')),
            "risk_score": response.get('risk_score')
        }

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {
            "success": False,
            "error": "configuration_error",
            "message": str(e),
            "retry": False
        }

    except TimeoutError as e:
        logger.warning(f"Request timeout: {e}")
        return {
            "success": False,
            "error": "timeout",
            "message": str(e),
            "retry": True
        }

    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return {
            "success": False,
            "error": "connection_error",
            "message": str(e),
            "retry": True
        }

    except Exception as e:
        error_message = str(e)

        # Parse API errors
        if "API Error:" in error_message:
            logger.error(f"API error: {error_message}")

            # Check for specific error codes
            if "401" in error_message or "Unauthorized" in error_message:
                return {
                    "success": False,
                    "error": "authentication_failed",
                    "message": "Invalid API key",
                    "retry": False
                }

            elif "403" in error_message or "Forbidden" in error_message:
                return {
                    "success": False,
                    "error": "authorization_failed",
                    "message": "Insufficient permissions",
                    "retry": False
                }

            elif "500" in error_message:
                return {
                    "success": False,
                    "error": "server_error",
                    "message": "Server error - try again",
                    "retry": True
                }

        logger.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": "unknown",
            "message": str(e),
            "retry": False
        }
```

Usage:
```python
action = AgentAction(
    agent_id="my-agent",
    agent_name="My Agent",
    action_type="data_access",
    resource="database"
)

result = safe_submit_action(action)

if result["success"]:
    print(f"Success! Action ID: {result['action_id']}")
elif result["retry"]:
    print(f"Temporary error: {result['message']} - Retrying...")
    time.sleep(5)
    result = safe_submit_action(action)
else:
    print(f"Permanent error: {result['error']} - {result['message']}")
```

## Retry Strategies

### Exponential Backoff

```python
import time
from python_sdk_example import OWKAIClient

def submit_with_exponential_backoff(action, max_retries=5):
    """Submit with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            client = OWKAIClient()
            return client.submit_action(action)

        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise

            wait = (2 ** attempt) + (random.randint(0, 1000) / 1000)
            print(f"Attempt {attempt + 1} failed, waiting {wait:.1f}s...")
            time.sleep(wait)

        except Exception as e:
            # Don't retry on auth errors, etc.
            raise
```

### Conditional Retry

```python
def should_retry(error):
    """Determine if error is retryable."""
    error_str = str(error)

    # Retry on network/timeout errors
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True

    # Retry on 5xx server errors
    if "500" in error_str or "503" in error_str:
        return True

    # Don't retry on auth errors
    if "401" in error_str or "403" in error_str:
        return False

    # Don't retry on validation errors
    if "400" in error_str:
        return False

    return False

def submit_with_conditional_retry(action, max_retries=3):
    """Submit with conditional retry logic."""
    last_error = None

    for attempt in range(max_retries):
        try:
            client = OWKAIClient()
            return client.submit_action(action)

        except Exception as e:
            last_error = e

            if not should_retry(e):
                raise

            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Retrying in {wait}s...")
                time.sleep(wait)

    raise last_error
```

## Logging Best Practices

### Enable Debug Logging

```python
import logging
from python_sdk_example import OWKAIClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('owkai.log'),
        logging.StreamHandler()
    ]
)

# Enable debug mode
client = OWKAIClient(debug=True)
```

### Structured Error Logging

```python
import logging
from python_sdk_example import OWKAIClient, AgentAction

logger = logging.getLogger(__name__)

def submit_with_logging(action: AgentAction):
    """Submit action with structured error logging."""

    try:
        client = OWKAIClient()
        response = client.submit_action(action)

        logger.info(
            "Action submitted successfully",
            extra={
                "action_id": response.get('action_id'),
                "agent_id": action.agent_id,
                "resource": action.resource,
                "decision": response.get('decision')
            }
        )

        return response

    except Exception as e:
        logger.error(
            "Action submission failed",
            extra={
                "agent_id": action.agent_id,
                "resource": action.resource,
                "action_type": action.action_type,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise
```

## Error Recovery Patterns

### Graceful Degradation

```python
def get_customer_data_safe(customer_id):
    """Get customer data with graceful degradation."""

    try:
        # Try with full authorization
        agent = AuthorizedAgent("my-agent", "My Agent")
        result = agent.execute_if_authorized(
            action_type="data_access",
            resource="customer_database",
            execute_fn=lambda: fetch_customer_data(customer_id),
            resource_id=customer_id,
            timeout=30
        )
        return result

    except PermissionError:
        # Fall back to cached data
        logger.warning("Permission denied, using cached data")
        return get_cached_customer_data(customer_id)

    except TimeoutError:
        # Fall back to summary view
        logger.warning("Timeout, returning summary")
        return get_customer_summary(customer_id)

    except Exception as e:
        # Return error state
        logger.error(f"Failed to get customer data: {e}")
        return {"error": "Data unavailable", "customer_id": customer_id}
```

### Circuit Breaker Pattern

```python
import time

class CircuitBreaker:
    """Simple circuit breaker for OW-AI API calls."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.is_open = False

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker."""

        # Check if circuit is open
        if self.is_open:
            if time.time() - self.last_failure < self.timeout:
                raise Exception("Circuit breaker open - service unavailable")
            else:
                # Try to close circuit
                self.is_open = False
                self.failure_count = 0

        try:
            result = func(*args, **kwargs)
            self.failure_count = 0  # Reset on success
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error("Circuit breaker opened")

            raise

# Usage
circuit_breaker = CircuitBreaker()

def submit_action_with_breaker(action):
    client = OWKAIClient()
    return circuit_breaker.call(client.submit_action, action)
```

## Best Practices

### 1. Always Handle Exceptions

```python
# ✅ Good - Proper error handling
try:
    response = client.submit_action(action)
    process_response(response)
except Exception as e:
    logger.error(f"Error: {e}")
    handle_error(e)

# ❌ Bad - No error handling
response = client.submit_action(action)  # Can crash application
```

### 2. Provide Context in Errors

```python
# ✅ Good - Contextual error information
try:
    response = client.submit_action(action)
except Exception as e:
    logger.error(
        f"Failed to submit action for agent {action.agent_id}: {e}",
        extra={
            "agent_id": action.agent_id,
            "resource": action.resource,
            "action_type": action.action_type
        }
    )
```

### 3. Use Appropriate Timeouts

```python
# ✅ Good - Appropriate timeouts per use case
realtime_client = OWKAIClient(timeout=5)       # Fast-fail
standard_client = OWKAIClient(timeout=30)      # Normal operations
batch_client = OWKAIClient(timeout=300)        # Long-running
```

### 4. Implement Retry Logic

```python
# ✅ Good - Retry transient errors
for attempt in range(3):
    try:
        return client.submit_action(action)
    except (ConnectionError, TimeoutError):
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)
```

## Next Steps

- [API Reference](/sdk/python/api-reference) - Complete API documentation
- [Client Configuration](/sdk/python/client-configuration) - Configure timeouts
- [Agent Actions](/sdk/python/agent-actions) - Submit and manage actions

## Source Code Reference

Error handling implementation:
```
/ow-ai-backend/integration-examples/python_sdk_example.py
```

Key methods:
- `OWKAIClient._request()` - lines 152-193 (HTTP error handling)
- `OWKAIClient.__init__()` - lines 139-140 (API key validation)
- `AuthorizedAgent.execute_if_authorized()` - lines 447-458 (Permission/Timeout errors)
