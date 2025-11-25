# OW-AI Enterprise SDK

Enterprise-grade Python SDK for AI Agent Authorization and Governance.

[![PyPI version](https://badge.fury.io/py/owkai-sdk.svg)](https://badge.fury.io/py/owkai-sdk)
[![Python versions](https://img.shields.io/pypi/pyversions/owkai-sdk.svg)](https://pypi.org/project/owkai-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The OW-AI SDK provides a secure, enterprise-ready interface for AI agents to submit actions for authorization through the OW-AI platform. It supports:

- **Agent Action Authorization**: Submit actions for risk assessment and approval workflows
- **boto3 Auto-Patching**: Transparent governance for all AWS API calls
- **Real-time Risk Assessment**: CVSS scoring, NIST/MITRE mapping
- **Approval Workflows**: Automatic routing to appropriate approvers
- **Comprehensive Audit Trails**: SOX, PCI-DSS, HIPAA, GDPR compliant logging

## Installation

```bash
# Core SDK
pip install owkai-sdk

# With boto3 integration
pip install owkai-sdk[boto3]

# With async support
pip install owkai-sdk[async]

# Development dependencies
pip install owkai-sdk[dev]

# Everything
pip install owkai-sdk[all]
```

## Quick Start

### Basic Usage

```python
from owkai import OWKAIClient

# Initialize client (reads OWKAI_API_KEY from environment)
client = OWKAIClient()

# Or with explicit API key
client = OWKAIClient(api_key="owkai_admin_your_api_key_here")

# Submit an action for authorization
result = client.execute_action(
    action_type="database_write",
    description="UPDATE users SET status='active' WHERE id=123",
    tool_name="postgresql",
    target_system="production-db"
)

print(f"Action ID: {result.action_id}")
print(f"Risk Score: {result.risk_score}")
print(f"Requires Approval: {result.requires_approval}")

# Wait for approval if required
if result.requires_approval:
    try:
        status = client.wait_for_approval(result.action_id, timeout=300)
        if status.approved:
            print("Action approved! Proceeding with execution...")
    except OWKAIApprovalTimeoutError:
        print("Approval not received in time")
    except OWKAIActionRejectedError as e:
        print(f"Action rejected: {e.rejection_reason}")
```

### boto3 Integration

Enable transparent governance for all AWS operations:

```python
from owkai.boto3_patch import enable_governance

# Enable OW-AI governance
enable_governance(
    api_key="owkai_admin_...",
    risk_threshold=70,        # Require approval for risk >= 70
    auto_approve_below=30,    # Auto-approve risk < 30
    bypass_read_only=True     # Skip governance for read operations
)

# Now all boto3 calls are governed
import boto3

s3 = boto3.client('s3')

# Low risk - auto-approved
s3.list_buckets()

# High risk - requires approval and blocks until approved
s3.delete_bucket(Bucket='production-data')
```

### Async Usage

```python
import asyncio
from owkai import AsyncOWKAIClient

async def main():
    async with AsyncOWKAIClient() as client:
        result = await client.execute_action(
            action_type="file_access",
            description="Read customer data file",
            tool_name="file-reader"
        )

        if result.requires_approval:
            status = await client.wait_for_approval(result.action_id)

asyncio.run(main())
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OWKAI_API_KEY` | API key for authentication | (required) |
| `OWKAI_BASE_URL` | API base URL | `https://pilot.owkai.app` |

### Client Options

```python
from owkai import OWKAIClient
from owkai.utils.retry import RetryConfig

client = OWKAIClient(
    api_key="owkai_admin_...",       # API key (or use env var)
    base_url="https://pilot.owkai.app",  # API URL
    timeout=30.0,                     # Request timeout (seconds)
    retry_config=RetryConfig(         # Retry configuration
        max_attempts=3,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0
    )
)
```

## Action Types

The SDK supports any action type string, but the platform provides specialized risk assessment for these categories:

| Action Type | Description | Typical Risk |
|------------|-------------|--------------|
| `database_write` | Database modifications | Medium-High |
| `database_delete` | Database deletions | High-Critical |
| `file_access` | File system access | Low-Medium |
| `file_write` | File modifications | Medium |
| `api_call` | External API calls | Medium |
| `network_access` | Network operations | Medium-High |
| `privilege_escalation` | Permission changes | Critical |
| `data_exfiltration_check` | Data export operations | High |

## Risk Assessment

Actions are automatically assessed using:

- **CVSS v3.1 Scoring**: 0-10 severity scale
- **NIST SP 800-53**: Control mapping
- **MITRE ATT&CK**: Technique classification

```python
result = client.execute_action(
    action_type="database_write",
    description="UPDATE sensitive_data SET ...",
    tool_name="postgresql",
    risk_context={
        "contains_pii": True,
        "production_system": True,
        "financial_impact": True
    }
)

# Access risk assessment
print(f"CVSS Score: {result.cvss_score}")
print(f"NIST Control: {result.nist_control}")
print(f"MITRE Technique: {result.mitre_technique}")
```

## Error Handling

```python
from owkai import OWKAIClient
from owkai.exceptions import (
    OWKAIAuthenticationError,
    OWKAIRateLimitError,
    OWKAIApprovalTimeoutError,
    OWKAIActionRejectedError,
    OWKAIValidationError,
    OWKAINetworkError
)

try:
    result = client.execute_action(...)
    status = client.wait_for_approval(result.action_id)

except OWKAIAuthenticationError:
    # Invalid or expired API key
    print("Check your API key")

except OWKAIRateLimitError as e:
    # Rate limit exceeded
    print(f"Retry after {e.retry_after} seconds")

except OWKAIApprovalTimeoutError as e:
    # Approval not received in time
    print(f"Action {e.action_id} timed out after {e.timeout}s")

except OWKAIActionRejectedError as e:
    # Action was explicitly rejected
    print(f"Rejected by {e.rejected_by}: {e.rejection_reason}")

except OWKAIValidationError as e:
    # Invalid request parameters
    print(f"Validation error: {e.field} - {e.constraint}")

except OWKAINetworkError as e:
    # Network communication error
    if e.is_retryable:
        # Implement retry logic
        pass
```

## Logging

The SDK uses structured logging for audit compliance:

```python
from owkai.utils.logging import configure_logging
import logging

# Enable debug logging
configure_logging(level=logging.DEBUG)

# Enable JSON logging for SIEM integration
configure_logging(level=logging.INFO, json_format=True)
```

## Security

- API keys are validated on initialization
- Keys are never logged or exposed in exceptions
- All requests use TLS 1.2+
- Automatic retry with exponential backoff
- Rate limiting with configurable thresholds

## Compliance

The SDK is designed for enterprise compliance requirements:

- **SOX**: Comprehensive audit trails
- **PCI-DSS**: Secure credential handling
- **HIPAA**: PHI access logging
- **GDPR**: Data processing records

## API Reference

### OWKAIClient

| Method | Description |
|--------|-------------|
| `execute_action()` | Submit action for authorization |
| `get_action_status()` | Get current action status |
| `wait_for_approval()` | Wait for action approval |
| `get_action_details()` | Get full action details |
| `health_check()` | Check API health |
| `get_usage_statistics()` | Get API key usage stats |

### boto3_patch

| Function | Description |
|----------|-------------|
| `enable_governance()` | Enable boto3 governance |
| `disable_governance()` | Disable boto3 governance |
| `is_governance_enabled()` | Check if governance is active |
| `get_governance_config()` | Get current configuration |

## Development

```bash
# Clone repository
git clone https://github.com/ow-ai/owkai-sdk.git
cd owkai-sdk

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black owkai tests
ruff check owkai tests
mypy owkai

# Build package
python -m build
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: https://docs.owkai.com/sdk
- Issues: https://github.com/ow-ai/owkai-sdk/issues
- Email: sdk@owkai.com
