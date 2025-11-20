# SDK Architecture - OW-AI Python SDK

**Date**: 2025-11-20
**Status**: Phase 2 - Architecture Design
**Target**: Python 3.9+

---

## Package Structure

```
owkai-sdk-python/
├── owkai/
│   ├── __init__.py              # Main exports: OWKAIClient, init()
│   ├── client.py                # Core OWKAIClient class
│   ├── config.py                # Configuration management
│   ├── exceptions.py            # Custom exceptions
│   ├── models.py                # Response models (Pydantic)
│   ├── auth.py                  # API key authentication
│   ├── retry.py                 # Retry logic with exponential backoff
│   ├── cache.py                 # Response caching (in-memory + Redis)
│   ├── logging_config.py        # Structured logging
│   │
│   ├── integrations/            # Pre-built integrations
│   │   ├── __init__.py
│   │   ├── boto3_middleware.py  # Auto-patch boto3
│   │   ├── openai_middleware.py # Auto-patch OpenAI
│   │   ├── anthropic_middleware.py
│   │   └── langchain_tools.py   # LangChain tools
│   │
│   ├── middleware/              # Framework middleware
│   │   ├── __init__.py
│   │   ├── fastapi.py           # FastAPI middleware
│   │   └── flask.py             # Flask middleware
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── pii_detector.py      # PII detection
│       └── context_detection.py # Environment detection
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── quickstart.md
│   ├── integration_guide.md
│   └── api_reference.md
│
├── setup.py
├── README.md
├── requirements.txt
└── .env.example
```

---

## Core Client Design

**File**: `owkai/client.py`

```python
class OWKAIClient:
    """
    Enterprise-grade OW-AI governance client

    Features:
    - API key authentication
    - Automatic retries with exponential backoff
    - Response caching
    - Structured logging
    - Rate limit handling
    - Failover modes (fail-open/fail-closed)
    - Health checks
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://pilot.owkai.app/api",
        timeout: float = 5.0,
        max_retries: int = 3,
        cache_ttl: int = 300,
        fail_mode: str = "fail_closed",  # or "fail_open"
        enable_logging: bool = True
    ):
        # Validate API key format
        if not api_key:
            api_key = os.getenv("OWKAI_API_KEY")
        if not api_key:
            raise OWKAIError("API key required")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache = Cache(ttl=cache_ttl)
        self.fail_mode = fail_mode
        self.logger = setup_logging() if enable_logging else None

    def check_action(self, **kwargs) -> ActionResult:
        """Check if action is allowed by governance policies"""

        action_data = {
            "agent_id": kwargs.get("agent_id"),
            "action_type": kwargs.get("action_type"),
            "description": kwargs.get("description"),
            ...
        }

        # Check cache first
        cache_key = hash(frozenset(action_data.items()))
        if cached := self.cache.get(cache_key):
            return cached

        # Make API call with retries
        try:
            result = self._post_with_retry(
                "/agent-action",
                data=action_data
            )

            # Cache result
            self.cache.set(cache_key, result)

            return ActionResult(**result)

        except ServiceUnavailableError:
            # Failover mode
            if self.fail_mode == "fail_open":
                return ActionResult(status="allowed", reason="failover")
            else:
                raise ActionDeniedError("Service unavailable, fail-closed")

    def _post_with_retry(self, endpoint: str, data: dict) -> dict:
        """POST request with exponential backoff retry"""

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )

                # Check rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                    continue
                raise ServiceUnavailableError(f"API call failed: {e}")
```

---

## Boto3 Auto-Patch Architecture

**File**: `owkai/integrations/boto3_middleware.py`

```python
def auto_patch_boto3():
    """
    Automatically patch boto3 to govern ALL AWS API calls

    Usage:
        import owkai
        owkai.init(api_key="...")

        # Now all boto3 calls are governed
        import boto3
        s3 = boto3.client('s3')
        s3.delete_bucket('prod')  # ← Checked by OW-AI first
    """

    # Patch botocore event system
    import botocore.client

    original_make_request = botocore.client.BaseClient._make_request

    def governed_make_request(self, operation_model, request_dict, *args, **kwargs):
        # Extract AWS service and action
        service_name = self._service_model.service_name
        operation_name = operation_model.name

        # Check governance before AWS call
        client = get_owkai_client()
        result = client.check_action(
            agent_id="boto3-auto-patch",
            action_type="aws_api_call",
            description=f"{service_name}.{operation_name}",
            metadata={
                "service": service_name,
                "operation": operation_name,
                "params": request_dict.get("body", {})
            }
        )

        if result.status == "denied":
            raise ActionDeniedError(f"AWS call denied: {result.reason}")

        # If approved or pending, proceed
        return original_make_request(self, operation_model, request_dict, *args, **kwargs)

    botocore.client.BaseClient._make_request = governed_make_request
```

---

## Configuration Management

Supports 3 methods:

### 1. Environment Variables
```bash
export OWKAI_API_KEY="owkai_admin_xxx"
export OWKAI_BASE_URL="https://pilot.owkai.app/api"
export OWKAI_FAIL_MODE="fail_closed"
```

### 2. Config File (`~/.owkai/config.yaml`)
```yaml
api_key: owkai_admin_xxx
base_url: https://pilot.owkai.app/api
timeout: 5.0
fail_mode: fail_closed
cache_ttl: 300
```

### 3. Code
```python
import owkai

owkai.init(
    api_key="owkai_admin_xxx",
    base_url="https://pilot.owkai.app/api"
)
```

---

## Usage Examples

### Example 1: Basic Usage
```python
import owkai

# Initialize SDK
owkai.init(api_key="owkai_admin_xxx")

# Check action
result = owkai.check_action(
    agent_id="my-agent",
    action_type="database_write",
    description="Delete expired sessions"
)

if result.approved:
    # Execute action
    execute_deletion()
```

### Example 2: Boto3 Auto-Patch
```python
import owkai
owkai.init(api_key="owkai_admin_xxx")

# ALL boto3 calls now governed
import boto3
s3 = boto3.client('s3')
s3.delete_bucket('production')  # ← OW-AI checks this first
```

### Example 3: FastAPI Middleware
```python
from fastapi import FastAPI
from owkai.middleware.fastapi import OWKAIMiddleware

app = FastAPI()
app.add_middleware(OWKAIMiddleware, api_key="owkai_admin_xxx")

# All requests now logged and governed
```

---

## Error Handling

```python
from owkai.exceptions import (
    OWKAIError,               # Base exception
    AuthenticationError,      # Invalid API key
    ActionDeniedError,        # Action blocked
    RateLimitError,           # Too many requests
    ServiceUnavailableError   # API down
)

try:
    result = owkai.check_action(...)
except ActionDeniedError as e:
    print(f"Action denied: {e.reason}")
    print(f"Risk score: {e.risk_score}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ServiceUnavailableError:
    # Failover mode kicks in
    if owkai.fail_mode == "fail_open":
        print("Proceeding due to fail-open mode")
    else:
        raise
```

---

## Summary

**SDK Design Principles**:
- ✅ Simple initialization (1-2 lines)
- ✅ Automatic integrations (boto3 auto-patch)
- ✅ Enterprise error handling
- ✅ Production-grade retry logic
- ✅ Flexible configuration
- ✅ Comprehensive logging
- ✅ Fail-safe modes

**Estimated Size**: ~2,000 lines of production code

**Next**: Implementation Plan
