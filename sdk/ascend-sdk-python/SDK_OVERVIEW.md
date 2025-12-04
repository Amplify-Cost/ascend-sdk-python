# Ascend AI SDK - Technical Overview

## Package Information

- **Name**: `ascend-ai-sdk`
- **Version**: 1.0.0
- **Python**: 3.8+
- **License**: MIT
- **Location**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/sdk/ascend-sdk-python/`

## Architecture

### Core Components

```
ascend/
├── __init__.py          # Package exports and public API
├── client.py            # AscendClient - Main API client
├── agents.py            # AuthorizedAgent - High-level wrapper
├── models.py            # Data models (AgentAction, ActionResult, etc.)
├── exceptions.py        # Custom exception hierarchy
├── constants.py         # Enums, defaults, and configuration
└── utils/
    ├── retry.py         # Exponential backoff retry logic
    └── validation.py    # Input validation functions
```

### Public API

**Main Classes:**
- `AscendClient` - Low-level API client for direct control
- `AuthorizedAgent` - High-level agent wrapper (recommended)

**Models:**
- `AgentAction` - Action submission model
- `ActionResult` - Authorization response model
- `ListResult` - Paginated list response
- `ConnectionStatus` - Connection test result

**Exceptions:**
- `AscendError` - Base exception
- `AuthenticationError` - Invalid API key
- `AuthorizationDeniedError` - Action denied by policy
- `RateLimitError` - Rate limit exceeded
- `TimeoutError` - Operation timeout
- `ValidationError` - Invalid input
- `NetworkError` - Connection failure
- `ServerError` - Server-side error
- `NotFoundError` - Resource not found
- `ConflictError` - Resource conflict

**Enums:**
- `ActionType` - Standard action types
- `DecisionStatus` - Authorization statuses
- `RiskLevel` - Risk classifications

## API Endpoints Used

The SDK interacts with the following Ascend API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/actions/submit` | POST | Submit action for authorization |
| `/api/v1/actions/{id}` | GET | Get action details |
| `/api/v1/actions/{id}/status` | GET | Get action status |
| `/api/v1/actions` | GET | List actions (paginated) |
| `/api/v1/actions/{id}/approve` | POST | Approve pending action |
| `/api/v1/actions/{id}/reject` | POST | Reject pending action |
| `/health` | GET | Health check |
| `/api/deployment-info` | GET | API version info |

## Security Features

### Banking-Level Security Implementation

1. **Dual Authentication Headers**
   - `Authorization: Bearer <api_key>` (standard)
   - `X-API-Key: <api_key>` (backward compatible)

2. **API Key Security**
   - Never logged in plaintext (masked to `asce...x789`)
   - Validated on initialization
   - Minimum 20 character requirement
   - Format validation: `ascend_<env>_<random>`

3. **TLS/SSL**
   - Certificate validation always enabled
   - HTTPS required for all requests
   - No option to disable verification

4. **Request Tracing**
   - Unique correlation ID per request: `ascend-{16-char-hex}`
   - Included in all API calls via `X-Correlation-ID` header
   - Logged for debugging and audit

5. **Retry Logic**
   - Automatic retry with exponential backoff
   - Retries: 429 (rate limit), 500/502/503/504 (server errors)
   - No retry: 401/403 (auth), 400/422 (validation), 404 (not found)
   - Backoff: 1s, 2s, 4s (configurable)

6. **Input Validation**
   - All inputs validated before API submission
   - Type checking for all parameters
   - Length constraints enforced
   - Format validation (API keys, action IDs)

## Usage Patterns

### Pattern 1: Direct Client (Low-Level)

```python
from ascend import AscendClient, AgentAction

client = AscendClient()
action = AgentAction(
    agent_id="bot-001",
    agent_name="My Bot",
    action_type="data_access",
    resource="database"
)
result = client.submit_action(action)

if result.is_approved():
    # Execute action
    pass
```

**Use When:**
- Need fine-grained control
- Submitting actions without immediate execution
- Batch processing actions
- Custom decision waiting logic

### Pattern 2: Authorized Agent (High-Level)

```python
from ascend import AuthorizedAgent

agent = AuthorizedAgent(agent_id="bot-001", agent_name="My Bot")

result = agent.execute_if_authorized(
    action_type="data_access",
    resource="database",
    execute_fn=lambda: fetch_data()
)
```

**Use When:**
- Simple authorization + execution flow
- Want automatic decision waiting
- Prefer declarative style
- Don't need action ID before execution

### Pattern 3: Context Manager

```python
from ascend import AscendClient

with AscendClient() as client:
    result = client.submit_action(action)
    # Connection automatically closed
```

**Use When:**
- Short-lived operations
- Want automatic resource cleanup
- Script-based usage

## Error Handling Strategy

### Retryable vs Non-Retryable Errors

**Automatically Retried:**
- `NetworkError` - Connection failures
- `ServerError` - 500, 502, 503, 504
- `RateLimitError` - 429 (with backoff)

**Not Retried:**
- `AuthenticationError` - Invalid API key
- `ValidationError` - Invalid input
- `NotFoundError` - Resource not found
- `AuthorizationDeniedError` - Policy denial (business logic)

### Exception Hierarchy

```
Exception
└── AscendError (base)
    ├── AuthenticationError
    ├── AuthorizationDeniedError
    ├── RateLimitError
    ├── TimeoutError
    ├── ValidationError
    ├── NetworkError
    ├── ServerError
    ├── NotFoundError
    └── ConflictError
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ASCEND_API_KEY` | Yes | None | API key for authentication |
| `ASCEND_API_URL` | No | `https://pilot.owkai.app` | API endpoint URL |
| `ASCEND_DEBUG` | No | `false` | Enable debug logging |

### Client Configuration

```python
client = AscendClient(
    api_key="ascend_prod_...",        # API key
    base_url="https://pilot.owkai.app",  # API URL
    timeout=30,                        # Request timeout (seconds)
    debug=False                        # Debug logging
)
```

## Performance Characteristics

### Connection Pooling
- Uses `requests.Session` for connection reuse
- Persistent HTTP connections
- Reduced latency for multiple requests

### Caching
- No client-side caching (server-side handles this)
- Fresh data on every request
- Stateless client design

### Timeouts
- Default request timeout: 30 seconds (configurable)
- Default decision wait: 60 seconds (configurable)
- Poll interval: 2 seconds (configurable)

## Code Metrics

- **Total Lines**: ~3,200 (code + docs)
- **Python Files**: 14
- **Test Files**: 1 (basic suite)
- **Example Files**: 2
- **Documentation Files**: 5 (README, INSTALL, CHANGELOG, OVERVIEW, LICENSE)

## File Breakdown

| File | Lines | Purpose |
|------|-------|---------|
| `client.py` | ~500 | Main API client |
| `agents.py` | ~300 | Authorized agent wrapper |
| `models.py` | ~200 | Data models |
| `exceptions.py` | ~150 | Exception classes |
| `constants.py` | ~80 | Constants and enums |
| `utils/retry.py` | ~120 | Retry logic |
| `utils/validation.py` | ~150 | Input validation |
| `README.md` | ~500 | Documentation |
| `examples/basic_usage.py` | ~250 | Basic examples |
| `examples/financial_advisor.py` | ~300 | Advanced example |

## Testing

### Test Coverage

Currently includes basic unit tests:
- Client initialization
- API key validation
- Action validation
- Result parsing
- Error handling

**To Run:**
```bash
pytest
pytest --cov=ascend --cov-report=html
```

### Manual Testing

Use example scripts:
```bash
export ASCEND_API_KEY="your_key"
python examples/basic_usage.py
python examples/financial_advisor.py
```

## Publishing to PyPI

### Build Distribution

```bash
python -m build
```

Creates:
- `dist/ascend_ai_sdk-1.0.0-py3-none-any.whl`
- `dist/ascend-ai-sdk-1.0.0.tar.gz`

### Upload to PyPI

```bash
python -m twine upload dist/*
```

### Test PyPI (Recommended First)

```bash
python -m twine upload --repository testpypi dist/*
```

## Dependencies

### Runtime Dependencies
- `requests>=2.28.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment variable loading

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking
- `types-requests>=2.28.0` - Type stubs

## Compliance Alignment

The SDK is designed to support enterprise compliance requirements:

| Standard | SDK Features |
|----------|--------------|
| SOC 2 Type II | Audit trails, secure authentication |
| HIPAA | Data encryption (TLS), access logging |
| PCI-DSS | Secure key handling, no plaintext logging |
| GDPR | Data isolation, request tracing |
| SOX | Immutable audit logs, correlation IDs |

## Maintenance

### Versioning

Follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Current version: **1.0.0**

### Changelog

All changes documented in `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format.

## Support Channels

- **Documentation**: https://docs.ascendai.app/sdk/python
- **API Reference**: https://docs.ascendai.app/api
- **GitHub Issues**: https://github.com/ascend-ai/ascend-sdk-python/issues
- **Email**: sdk@ascendai.app
- **Support Portal**: https://ascendai.app/support

## Future Enhancements

Potential features for future versions:

1. **Async Support** - `asyncio` compatible client
2. **Webhook Handling** - Built-in webhook receiver
3. **Batch Operations** - Submit multiple actions
4. **Streaming** - WebSocket support for real-time decisions
5. **Metrics** - Client-side performance metrics
6. **Circuit Breaker** - Advanced failure handling
7. **Local Caching** - Optional response caching
8. **CLI Tool** - Command-line interface

---

**Generated**: 2025-12-04
**SDK Version**: 1.0.0
**Location**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/sdk/ascend-sdk-python/`
