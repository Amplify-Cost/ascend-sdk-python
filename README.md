# Ascend AI SDK for Python

Official Python SDK for [Ascend AI Governance Platform](https://ascendai.app) - Enterprise-grade authorization and governance for AI agents.

[![Python Version](https://img.shields.io/pypi/pyversions/ascend-ai-sdk)](https://pypi.org/project/ascend-ai-sdk/)
[![License](https://img.shields.io/pypi/l/ascend-ai-sdk)](https://github.com/ascend-ai/ascend-sdk-python/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-ascendai.app-blue)](https://docs.ascendai.app/sdk/python)

## Features

- **Banking-Level Security**: SOC 2, HIPAA, PCI-DSS compliant authorization
- **Automatic Retry**: Exponential backoff for transient failures
- **Dual Authentication**: Support for both `Authorization: Bearer` and `X-API-Key` headers
- **Type Safety**: Full type hints for Python 3.8+
- **Comprehensive Error Handling**: Specific exceptions for every failure mode
- **Request Tracing**: Correlation IDs for debugging
- **Production Ready**: Used by Fortune 500 companies

## Installation

```bash
pip install ascend-ai-sdk
```

**Requirements:**
- Python 3.8 or higher
- `requests` (automatically installed)
- `python-dotenv` (automatically installed)

## Quick Start

### 1. Get Your API Key

```bash
# Set your API key as environment variable
export ASCEND_API_KEY="ascend_prod_your_key_here"
```

Or create a `.env` file:
```env
ASCEND_API_KEY=ascend_prod_your_key_here
ASCEND_API_URL=https://pilot.owkai.app  # Optional, defaults to production
```

### 2. Submit an Action for Authorization

```python
from ascend import AscendClient, AgentAction

# Initialize client
client = AscendClient()

# Create action
action = AgentAction(
    agent_id="customer-bot-001",
    agent_name="Customer Service Bot",
    action_type="data_access",
    resource="customer_profile",
    resource_id="CUST-12345"
)

# Submit for authorization
result = client.submit_action(action)

if result.is_approved():
    print("✅ Action approved!")
    # Execute your action here
elif result.is_denied():
    print(f"❌ Action denied: {result.reason}")
else:
    print("⏳ Action pending manual review")
```

### 3. Execute Only If Authorized (Recommended)

```python
from ascend import AuthorizedAgent

# Create authorized agent
agent = AuthorizedAgent(
    agent_id="financial-bot-001",
    agent_name="Financial Advisor AI"
)

# Execute function only if authorized
try:
    portfolio = agent.execute_if_authorized(
        action_type="data_access",
        resource="customer_portfolio",
        resource_id="ACC-12345",
        execute_fn=lambda: fetch_portfolio("ACC-12345"),
        risk_indicators={"pii_involved": True}
    )
    print(f"Portfolio data: {portfolio}")

except AuthorizationDeniedError as e:
    print(f"Access denied: {e.message}")
```

## Usage Examples

### Financial Transaction with Risk Indicators

```python
from ascend import AuthorizedAgent

agent = AuthorizedAgent(
    agent_id="payment-bot-001",
    agent_name="Payment Processing Bot"
)

def process_large_payment(amount, recipient):
    # Your payment processing logic
    return {"status": "success", "transaction_id": "TXN-123"}

try:
    result = agent.execute_if_authorized(
        action_type="transaction",
        resource="payment_gateway",
        resource_id=recipient,
        execute_fn=lambda: process_large_payment(50000, recipient),
        details={
            "amount": 50000,
            "currency": "USD",
            "destination": "external_account"
        },
        risk_indicators={
            "amount_threshold": "exceeded",
            "external_transfer": True,
            "data_sensitivity": "critical"
        }
    )
    print(f"Payment processed: {result}")

except AuthorizationDeniedError as e:
    print(f"Transaction blocked by policy: {e.message}")
```

### Customer Data Access with Context

```python
from ascend import AscendClient, AgentAction

client = AscendClient()

action = AgentAction(
    agent_id="support-bot-001",
    agent_name="Customer Support AI",
    action_type="data_access",
    resource="customer_pii",
    resource_id="CUST-98765",
    action_details={
        "fields_requested": ["name", "email", "phone", "ssn"],
        "reason": "Customer identity verification"
    },
    context={
        "session_id": "sess_abc123",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
    },
    risk_indicators={
        "pii_involved": True,
        "sensitive_fields": ["ssn"],
        "data_classification": "restricted"
    }
)

result = client.submit_action(action)

if result.is_pending():
    # Wait up to 60 seconds for manual approval
    result = client.wait_for_decision(result.action_id, timeout_ms=60000)

if result.is_approved():
    # Fetch customer data
    customer_data = fetch_customer_pii("CUST-98765")
else:
    print(f"Access denied by {result.policy_matched}: {result.reason}")
```

### Listing Recent Actions

```python
from ascend import AscendClient

client = AscendClient()

# Get all pending actions
pending = client.list_actions(limit=10, status="pending")
print(f"Found {pending.total} pending actions")

for action in pending.actions:
    print(f"  - {action.action_id}: {action.metadata.get('action_type')} (Risk: {action.risk_level})")

# Pagination
if pending.has_more:
    next_page = client.list_actions(limit=10, offset=10, status="pending")
```

### Testing Connection

```python
from ascend import AscendClient

client = AscendClient()

status = client.test_connection()

if status.is_connected():
    print(f"✅ Connected to Ascend API v{status.api_version}")
    print(f"   Latency: {status.latency_ms:.0f}ms")
else:
    print(f"❌ Connection failed: {status.error}")
```

### Context Manager (Automatic Cleanup)

```python
from ascend import AscendClient, AgentAction

with AscendClient() as client:
    action = AgentAction(
        agent_id="bot-001",
        agent_name="My Bot",
        action_type="query",
        resource="database"
    )
    result = client.submit_action(action)
    print(f"Status: {result.status}")
# Connection automatically closed
```

## Error Handling

The SDK provides specific exceptions for different failure modes:

```python
from ascend import (
    AscendClient,
    AuthenticationError,
    AuthorizationDeniedError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    NetworkError,
    ServerError,
    NotFoundError
)

client = AscendClient()

try:
    result = client.submit_action(action)

except AuthenticationError as e:
    # Invalid API key
    print(f"Authentication failed: {e.message}")
    print("Check your ASCEND_API_KEY environment variable")

except ValidationError as e:
    # Invalid input data
    print(f"Validation error: {e.message}")
    print("Check your action fields")

except RateLimitError as e:
    # Rate limit exceeded
    print(f"Rate limit hit: {e.message}")
    print("Wait before retrying")

except TimeoutError as e:
    # Request or decision timeout
    print(f"Timeout: {e.message}")

except NetworkError as e:
    # Connection failed
    print(f"Network error: {e.message}")
    print("Check your internet connection")

except ServerError as e:
    # Ascend API error (automatically retried)
    print(f"Server error: {e.message}")
    print("Contact Ascend support if persistent")

except NotFoundError as e:
    # Resource not found
    print(f"Not found: {e.message}")
```

## Action Types

Standard action types supported by Ascend:

```python
from ascend.constants import ActionType

# Data operations
ActionType.DATA_ACCESS          # Reading data
ActionType.DATA_MODIFICATION    # Updating/deleting data
ActionType.QUERY                # Database queries

# Business operations
ActionType.TRANSACTION          # Financial transactions
ActionType.RECOMMENDATION       # AI recommendations
ActionType.COMMUNICATION        # External communications

# System operations
ActionType.SYSTEM_OPERATION     # System changes
ActionType.FILE_ACCESS          # File operations
ActionType.API_CALL             # External API calls
ActionType.DATABASE_OPERATION   # Database changes
```

## Configuration

### Environment Variables

```bash
# Required
ASCEND_API_KEY=ascend_prod_your_key_here

# Optional
ASCEND_API_URL=https://pilot.owkai.app  # Default: production API
ASCEND_DEBUG=true                        # Enable debug logging
```

### Programmatic Configuration

```python
from ascend import AscendClient

client = AscendClient(
    api_key="ascend_prod_...",      # API key (or use env var)
    base_url="https://pilot.owkai.app",  # API URL (or use env var)
    timeout=30,                      # Request timeout in seconds
    debug=True                       # Enable debug logging
)
```

## Advanced Features

### Automatic Retry with Exponential Backoff

The SDK automatically retries failed requests with exponential backoff:

- **Retryable errors**: Network errors, 429 (rate limit), 500/502/503/504 (server errors)
- **Non-retryable errors**: 401/403 (auth), 400/422 (validation), 404 (not found)
- **Backoff schedule**: 1s, 2s, 4s (configurable)

```python
# Retries are automatic - no configuration needed
result = client.submit_action(action)
```

### Correlation IDs for Request Tracing

Every request includes a correlation ID for debugging:

```python
# Correlation IDs are automatically generated
# Check logs for: [ascend-abc123def456] format
result = client.submit_action(action)
```

### API Key Security

API keys are never logged in plaintext:

```python
client = AscendClient(api_key="ascend_prod_abc123xyz789")
# Logs show: "API Key: asce...x789" (masked)
```

## Best Practices

### 1. Use AuthorizedAgent for Simplicity

```python
# ✅ Recommended
agent = AuthorizedAgent(agent_id="bot-001", agent_name="My Bot")
result = agent.execute_if_authorized(
    action_type="data_access",
    resource="database",
    execute_fn=lambda: fetch_data()
)

# ⚠️ More verbose
client = AscendClient()
action = AgentAction(agent_id="bot-001", ...)
result = client.submit_action(action)
if result.is_approved():
    data = fetch_data()
```

### 2. Provide Rich Context

```python
# ✅ Good - includes context and risk indicators
action = AgentAction(
    agent_id="bot-001",
    agent_name="My Bot",
    action_type="transaction",
    resource="payment_gateway",
    action_details={"amount": 1000, "currency": "USD"},
    context={"session_id": "sess_123", "ip": "1.2.3.4"},
    risk_indicators={"high_value": False, "external": True}
)

# ⚠️ Minimal - harder to audit
action = AgentAction(
    agent_id="bot-001",
    agent_name="My Bot",
    action_type="transaction",
    resource="payment"
)
```

### 3. Handle Denials Gracefully

```python
# ✅ Good - graceful degradation
try:
    data = agent.execute_if_authorized(
        action_type="data_access",
        resource="sensitive_data",
        execute_fn=lambda: fetch_sensitive_data()
    )
except AuthorizationDeniedError:
    # Fall back to public data
    data = fetch_public_data()

# ❌ Bad - crashes on denial
data = agent.execute_if_authorized(...)  # No error handling
```

### 4. Use Context Managers

```python
# ✅ Good - automatic cleanup
with AscendClient() as client:
    result = client.submit_action(action)

# ⚠️ Manual cleanup required
client = AscendClient()
try:
    result = client.submit_action(action)
finally:
    client.close()
```

## Development

### Installing from Source

```bash
git clone https://github.com/ascend-ai/ascend-sdk-python.git
cd ascend-sdk-python
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=ascend  # With coverage
```

### Type Checking

```bash
mypy ascend
```

### Code Formatting

```bash
black ascend tests
```

## Support

- **Documentation**: https://docs.ascendai.app/sdk/python
- **API Reference**: https://docs.ascendai.app/api
- **Support Portal**: https://ascendai.app/support
- **GitHub Issues**: https://github.com/ascend-ai/ascend-sdk-python/issues
- **Email**: sdk@ascendai.app

## Compliance

The Ascend SDK is designed for enterprise security and compliance:

- **SOC 2 Type II**: Multi-tenant isolation, audit trails
- **HIPAA**: Data encryption, access controls
- **PCI-DSS**: Secure API endpoints, token management
- **GDPR**: Data isolation, right to deletion
- **SOX**: Immutable audit logs, segregation of duties

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Built with ❤️ by the Ascend AI team**
