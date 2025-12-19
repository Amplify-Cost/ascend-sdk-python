---
title: Python SDK Installation
sidebar_position: 1
---

# Python SDK Installation

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-014 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

The OW-AI Python SDK provides a simple interface for integrating AI governance into your Python applications.

> **Source of Truth**: This documentation is based on the actual implementation in `/ow-ai-backend/integration-examples/python_sdk_example.py` (lines 1-622)

## Requirements

- Python 3.8 or higher
- pip package manager

## Installation

### Prerequisites

Install the required dependencies:

```bash
pip install requests python-dotenv
```

### SDK Integration

The OW-AI SDK is currently distributed as source code. You have two options:

**Option 1: Copy the SDK Classes (Recommended)**

Copy the following classes from `/integration-examples/python_sdk_example.py` into your project:

- `OWKAIClient` (lines 105-310)
- `AuthorizedAgent` (lines 328-458)
- `AgentAction` (lines 74-102)
- `ActionType` (lines 55-62)
- `DecisionStatus` (lines 65-72)

**Option 2: Import from Integration Examples**

```python
import sys
sys.path.append('/path/to/ow-ai-backend/integration-examples')
from python_sdk_example import OWKAIClient, AuthorizedAgent, AgentAction
```

## Environment Variables

Create a `.env` file in your project root:

```bash
# API Configuration
OWKAI_API_URL=https://pilot.owkai.app
OWKAI_API_KEY=owkai_live_your_api_key_here
OWKAI_ORG_SLUG=your-organization-slug
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OWKAI_API_URL` | No | `https://pilot.owkai.app` | API endpoint URL |
| `OWKAI_API_KEY` | **Yes** | - | Your organization's API key |
| `OWKAI_ORG_SLUG` | No | - | Organization identifier |

## Verify Installation

Create a test script `test_connection.py`:

```python
from python_sdk_example import OWKAIClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client
client = OWKAIClient()

# Test connection
status = client.test_connection()
print(f"Connection Status: {status['status']}")

if status['status'] == 'connected':
    print(f"API Version: {status['api_version']}")
    print(f"Server Time: {status['server_time']}")
else:
    print(f"Error: {status.get('error')}")
```

Run the test:

```bash
python test_connection.py
```

Expected output:
```
Connection Status: connected
API Version: 2.0
Server Time: 2025-12-04T10:30:00
```

## Quick Start

```python
from python_sdk_example import OWKAIClient, AgentAction, ActionType

# Initialize client
client = OWKAIClient()

# Submit an agent action
action = AgentAction(
    agent_id="customer-service-agent",
    agent_name="Customer Service AI",
    action_type=ActionType.DATA_ACCESS.value,
    resource="customer_database",
    resource_id="CUST-12345",
    action_details={
        "operation": "read",
        "fields": ["name", "email", "balance"]
    },
    context={
        "user_request": "Show customer profile",
        "session_id": "sess_abc123"
    },
    risk_indicators={
        "pii_involved": True,
        "financial_data": True,
        "data_sensitivity": "medium"
    }
)

# Submit for authorization
response = client.submit_action(action)

print(f"Action ID: {response['action_id']}")
print(f"Status: {response['status']}")
print(f"Decision: {response.get('decision', 'pending')}")
```

## Logging Configuration

The SDK uses Python's built-in logging module:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug mode
client = OWKAIClient(debug=True)
```

## Docker Installation

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir requests python-dotenv

# Copy SDK files
COPY integration-examples/python_sdk_example.py /app/
COPY your_application.py /app/

WORKDIR /app

CMD ["python", "your_application.py"]
```

## Security Standards

The OW-AI SDK implements enterprise security standards:

- **SOC 2 Type II Compliant** - Multi-tenant data isolation
- **PCI-DSS 8.3** - API key authentication with Bearer tokens
- **HIPAA 164.312** - Audit trails for all actions
- **NIST 800-63B** - Secure authentication mechanisms

## API Authentication

The SDK supports two authentication headers (per SEC-033 implementation, lines 142-148):

```python
# Both headers are sent automatically
headers = {
    "X-API-Key": self.api_key,           # SEC-033 support
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json",
    "User-Agent": "OWKAIClient/2.0 Python"
}
```

## Troubleshooting

### Missing API Key

```
ValueError: API key is required. Set OWKAI_API_KEY environment variable.
```

**Solution**: Create a `.env` file or set the environment variable:
```bash
export OWKAI_API_KEY=owkai_live_your_key
```

### Connection Errors

```python
# Test with custom timeout
client = OWKAIClient(timeout=60)  # 60 seconds
status = client.test_connection()
```

### SSL Certificate Errors

```bash
# Update certificates
pip install --upgrade certifi
```

### Import Errors

```python
# Verify Python version
import sys
print(f"Python version: {sys.version}")

# Verify dependencies
import requests
import dotenv
print("Dependencies installed successfully")
```

## Next Steps

- [Client Configuration](/sdk/python/client-configuration) - Configure the SDK client
- [Agent Actions](/sdk/python/agent-actions) - Submit and manage actions
- [Error Handling](/sdk/python/error-handling) - Handle errors gracefully
- [API Reference](/sdk/python/api-reference) - Complete API documentation

## Source Code Reference

The complete SDK implementation is available in:
```
/ow-ai-backend/integration-examples/python_sdk_example.py
```

Key classes and their line numbers:
- `ActionType` enum: lines 55-62
- `DecisionStatus` enum: lines 65-72
- `AgentAction` dataclass: lines 74-102
- `OWKAIClient` class: lines 105-326
- `AuthorizedAgent` class: lines 328-458
- Example usage: lines 465-621
