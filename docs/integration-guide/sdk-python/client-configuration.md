# Client Configuration

Configure the OWKAIClient for your environment and requirements.

> **Source of Truth**: Based on `OWKAIClient.__init__()` implementation (lines 113-150 in `python_sdk_example.py`)

## Basic Configuration

### Constructor Parameters

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient(
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    organization_slug: Optional[str] = None,
    timeout: int = 30,
    debug: bool = False
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | str | `https://pilot.owkai.app` | API endpoint URL (reads from `OWKAI_API_URL` env) |
| `api_key` | str | None | Organization API key (reads from `OWKAI_API_KEY` env) |
| `organization_slug` | str | None | Organization identifier (reads from `OWKAI_ORG_SLUG` env) |
| `timeout` | int | 30 | Request timeout in seconds |
| `debug` | bool | False | Enable debug logging |

## Initialization Methods

### Method 1: Environment Variables (Recommended)

Create a `.env` file:

```bash
OWKAI_API_URL=https://pilot.owkai.app
OWKAI_API_KEY=owkai_live_your_api_key_here
OWKAI_ORG_SLUG=your-organization-slug
```

Initialize client:

```python
from python_sdk_example import OWKAIClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Client reads from environment
client = OWKAIClient()
```

### Method 2: Direct Initialization

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient(
    api_url="https://pilot.owkai.app",
    api_key="owkai_live_your_api_key_here",
    organization_slug="your-org-slug"
)
```

### Method 3: Mixed Approach

```python
from python_sdk_example import OWKAIClient
import os

# Override only specific settings
client = OWKAIClient(
    api_key=os.getenv("CUSTOM_API_KEY"),
    timeout=60  # Override default timeout
)
```

## Environment-Specific Configuration

### Development Environment

```python
# development.py
from python_sdk_example import OWKAIClient

def get_dev_client():
    """Get client configured for development."""
    return OWKAIClient(
        api_url="https://dev.owkai.app",
        debug=True,  # Enable debug logging
        timeout=60   # Longer timeout for debugging
    )
```

### Production Environment

```python
# production.py
from python_sdk_example import OWKAIClient

def get_prod_client():
    """Get client configured for production."""
    return OWKAIClient(
        api_url="https://pilot.owkai.app",
        debug=False,  # Disable debug logging
        timeout=30    # Standard timeout
    )
```

### Multi-Environment Configuration

```python
import os
from python_sdk_example import OWKAIClient

def get_client():
    """Get client for current environment."""
    env = os.getenv("ENVIRONMENT", "development")

    configs = {
        "development": {
            "api_url": "https://dev.owkai.app",
            "debug": True,
            "timeout": 60
        },
        "staging": {
            "api_url": "https://staging.owkai.app",
            "debug": False,
            "timeout": 45
        },
        "production": {
            "api_url": "https://pilot.owkai.app",
            "debug": False,
            "timeout": 30
        }
    }

    config = configs.get(env, configs["development"])
    return OWKAIClient(**config)
```

## Request Configuration

### Timeout Configuration

```python
# Default timeout (30 seconds)
client = OWKAIClient()

# Custom timeout for slow networks
client = OWKAIClient(timeout=90)

# Short timeout for quick responses
client = OWKAIClient(timeout=10)
```

### Authentication Headers

The SDK automatically configures authentication headers (lines 142-148):

```python
# Automatically set by the SDK
self.headers = {
    "Content-Type": "application/json",
    "X-API-Key": self.api_key,                    # SEC-033 support
    "Authorization": f"Bearer {self.api_key}",    # Standard Bearer token
    "User-Agent": "OWKAIClient/2.0 Python"
}
```

Both `X-API-Key` and `Authorization: Bearer` headers are sent for maximum compatibility.

## Debug Mode

### Enable Debug Logging

```python
import logging
from python_sdk_example import OWKAIClient

# Configure logging format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug mode
client = OWKAIClient(debug=True)

# Now all requests will be logged
action = client.submit_action(...)
```

Debug mode output:
```
2025-12-04 10:30:00 - owkai-sdk - DEBUG - POST https://pilot.owkai.app/api/v1/actions/submit
2025-12-04 10:30:01 - owkai-sdk - INFO - Action submitted: act_123 - Status: approved
```

### Custom Logger

```python
import logging
from python_sdk_example import OWKAIClient

# Create custom logger
logger = logging.getLogger('owkai-sdk')
logger.setLevel(logging.INFO)

# Add file handler
handler = logging.FileHandler('owkai.log')
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)

# Initialize client with debug mode
client = OWKAIClient(debug=True)
```

## Connection Testing

### Test API Connectivity

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient()

# Test connection (uses /health and /api/deployment-info endpoints)
status = client.test_connection()

if status['status'] == 'connected':
    print(f"Connected successfully!")
    print(f"API Version: {status['api_version']}")
    print(f"Server Time: {status['server_time']}")
else:
    print(f"Connection failed: {status.get('error')}")
```

Implementation reference (lines 195-213):
```python
def test_connection(self) -> Dict:
    """Test API connectivity and authentication"""
    try:
        # Use health endpoint first
        health = self._request("GET", "/health")

        # Then verify authentication
        deployment = self._request("GET", "/api/deployment-info")

        return {
            "status": "connected",
            "api_version": deployment.get("version", "unknown"),
            "server_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

## Error Handling

### Connection Errors

```python
from python_sdk_example import OWKAIClient

try:
    client = OWKAIClient()
    status = client.test_connection()

    if status['status'] != 'connected':
        print(f"Connection failed: {status.get('error')}")

except ValueError as e:
    print(f"Configuration error: {e}")
    # Missing API key

except ConnectionError as e:
    print(f"Network error: {e}")
    # Cannot reach API

except TimeoutError as e:
    print(f"Request timed out: {e}")
    # Request took too long
```

### API Key Validation

The client validates API key on initialization (lines 139-140):

```python
if not self.api_key:
    raise ValueError("API key is required. Set OWKAI_API_KEY environment variable.")
```

## Thread Safety

The OWKAIClient is thread-safe and can be shared across threads:

```python
from python_sdk_example import OWKAIClient
from concurrent.futures import ThreadPoolExecutor

# Create single client instance
client = OWKAIClient()

def submit_action(action_data):
    """Submit action in thread."""
    action = AgentAction(**action_data)
    return client.submit_action(action)

# Use in thread pool
with ThreadPoolExecutor(max_workers=10) as executor:
    actions = [
        {"agent_id": "agent-1", "agent_name": "Agent 1",
         "action_type": "data_access", "resource": "database"},
        {"agent_id": "agent-2", "agent_name": "Agent 2",
         "action_type": "query", "resource": "analytics"}
    ]

    results = list(executor.map(submit_action, actions))
```

## Best Practices

### 1. Reuse Client Instances

```python
# ✅ Good - Reuse client
client = OWKAIClient()

for action in actions:
    response = client.submit_action(action)

# ❌ Bad - Creating new client each time
for action in actions:
    client = OWKAIClient()  # Inefficient!
    response = client.submit_action(action)
```

### 2. Use Environment Variables

```python
# ✅ Good - Environment variables
load_dotenv()
client = OWKAIClient()

# ❌ Bad - Hardcoded credentials
client = OWKAIClient(api_key="owkai_live_hardcoded_key")  # Security risk!
```

### 3. Handle Missing Configuration

```python
import os
from python_sdk_example import OWKAIClient

def get_client_safe():
    """Get client with error handling."""
    try:
        return OWKAIClient()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set OWKAI_API_KEY in your environment")
        raise
```

### 4. Configure Appropriate Timeouts

```python
# For real-time operations
realtime_client = OWKAIClient(timeout=5)

# For batch processing
batch_client = OWKAIClient(timeout=120)

# For long-running operations
longrun_client = OWKAIClient(timeout=300)
```

## Configuration Validation

```python
from python_sdk_example import OWKAIClient

def validate_configuration():
    """Validate client configuration."""
    try:
        # Initialize client
        client = OWKAIClient()

        # Test connection
        status = client.test_connection()

        if status['status'] == 'connected':
            print("✓ Configuration valid")
            print(f"  API URL: {client.api_url}")
            print(f"  API Version: {status['api_version']}")
            return True
        else:
            print("✗ Configuration invalid")
            print(f"  Error: {status.get('error')}")
            return False

    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return False
```

## API Endpoints Used

The OWKAIClient interacts with these endpoints:

| Endpoint | Method | Purpose | Line Reference |
|----------|--------|---------|----------------|
| `/health` | GET | Health check | 199 |
| `/api/deployment-info` | GET | API version | 202 |
| `/api/v1/actions/submit` | POST | Submit action | 229 |
| `/api/v1/actions/{id}/status` | GET | Get action status | 248 |
| `/api/v1/actions` | GET | List actions | 308 |
| `/api/v1/actions/{id}` | GET | Get action details | 324 |

## Next Steps

- [Agent Actions](/sdk/python/agent-actions) - Submit and manage actions
- [Error Handling](/sdk/python/error-handling) - Handle errors gracefully
- [API Reference](/sdk/python/api-reference) - Complete API documentation

## Source Code Reference

`OWKAIClient` implementation:
```
/ow-ai-backend/integration-examples/python_sdk_example.py (lines 105-326)
```

Key methods:
- `__init__()` - lines 113-150
- `_request()` - lines 152-193
- `test_connection()` - lines 195-213
- `submit_action()` - lines 215-234
