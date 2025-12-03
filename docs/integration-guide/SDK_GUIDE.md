# Ascend SDK Integration Guide

**Document ID:** ASCEND-INT-004
**Version:** 2.0.0
**Classification:** Developer Guide
**Publisher:** OW-kai Corporation

---

## Overview

The Ascend SDK provides the easiest way to integrate AI agent governance into your applications. This guide covers installation, configuration, and common usage patterns.

---

## Installation

### Python

```bash
pip install ascend-sdk
```

### JavaScript/TypeScript

```bash
npm install @ascend/sdk
# or
yarn add @ascend/sdk
```

### Go

```bash
go get github.com/ascendowkai/sdk-go
```

---

## Quick Start

### Python

```python
from ascend_sdk import AscendClient

# Initialize the client
client = AscendClient(
    api_key="ascend_your_api_key_here",
    base_url="https://your-domain.ascendowkai.com"  # Optional
)

# Submit an action for governance evaluation
result = client.evaluate_action(
    agent_id="finance-agent-001",
    action_type="database.read",
    tool_name="postgres_query",
    description="Querying user analytics data"
)

# Check the result
if result.approved:
    print(f"Action approved with risk score: {result.risk_score}")
    # Proceed with the action
else:
    print(f"Action requires approval: {result.status}")
    # Wait for approval or handle denial
```

### JavaScript/TypeScript

```typescript
import { AscendClient } from '@ascend/sdk';

// Initialize the client
const client = new AscendClient({
  apiKey: 'ascend_your_api_key_here',
  baseUrl: 'https://your-domain.ascendowkai.com'  // Optional
});

// Submit an action for governance evaluation
const result = await client.evaluateAction({
  agentId: 'finance-agent-001',
  actionType: 'database.read',
  toolName: 'postgres_query',
  description: 'Querying user analytics data'
});

// Check the result
if (result.approved) {
  console.log(`Action approved with risk score: ${result.riskScore}`);
  // Proceed with the action
} else {
  console.log(`Action requires approval: ${result.status}`);
  // Wait for approval or handle denial
}
```

---

## Configuration Options

### Client Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | string | Required | Your Ascend API key |
| `base_url` | string | Production URL | Custom API endpoint |
| `timeout` | int | 30000 | Request timeout in milliseconds |
| `retry_count` | int | 3 | Number of retries on failure |
| `fail_mode` | string | "closed" | Behavior on failure: "open" or "closed" |

### Python Configuration

```python
from ascend_sdk import AscendClient, FailMode

client = AscendClient(
    api_key="ascend_your_api_key_here",
    base_url="https://your-domain.ascendowkai.com",
    timeout=30000,
    retry_count=3,
    fail_mode=FailMode.CLOSED  # Block actions if Ascend is unreachable
)
```

### JavaScript Configuration

```typescript
import { AscendClient, FailMode } from '@ascend/sdk';

const client = new AscendClient({
  apiKey: 'ascend_your_api_key_here',
  baseUrl: 'https://your-domain.ascendowkai.com',
  timeout: 30000,
  retryCount: 3,
  failMode: FailMode.CLOSED
});
```

---

## Fail Modes

The SDK supports two fail modes for when Ascend is unreachable:

### Closed Mode (Default - Recommended)
When Ascend is unreachable, **block all actions**. This is the safest option for compliance-critical environments.

```python
client = AscendClient(
    api_key="ascend_key",
    fail_mode=FailMode.CLOSED
)

try:
    result = client.evaluate_action(...)
except AscendUnreachableError:
    # Action is blocked - do not proceed
    log.error("Ascend unreachable, action blocked")
```

### Open Mode
When Ascend is unreachable, **allow actions to proceed**. Use only in development or when availability is more important than governance.

```python
client = AscendClient(
    api_key="ascend_key",
    fail_mode=FailMode.OPEN
)

try:
    result = client.evaluate_action(...)
    if result.approved:
        # Proceed normally
        pass
except AscendUnreachableError:
    # Action allowed due to open mode - proceed with caution
    log.warning("Ascend unreachable, proceeding in open mode")
```

---

## Polling for Approval

For actions that require manual approval, use the polling mechanism:

### Python

```python
# Submit action
result = client.evaluate_action(
    agent_id="finance-agent-001",
    action_type="financial.transfer",
    tool_name="bank_transfer",
    description="Transfer $50,000 to vendor account"
)

if result.requires_approval:
    print(f"Action {result.action_id} pending approval")

    # Poll for decision (blocks until approved/denied or timeout)
    decision = client.wait_for_decision(
        action_id=result.action_id,
        timeout=300,  # 5 minutes
        poll_interval=5  # Check every 5 seconds
    )

    if decision.approved:
        print("Action approved, proceeding...")
    else:
        print(f"Action denied: {decision.rejection_reason}")
```

### JavaScript

```typescript
const result = await client.evaluateAction({...});

if (result.requiresApproval) {
  console.log(`Action ${result.actionId} pending approval`);

  const decision = await client.waitForDecision(
    result.actionId,
    { timeout: 300, pollInterval: 5 }
  );

  if (decision.approved) {
    console.log('Action approved, proceeding...');
  } else {
    console.log(`Action denied: ${decision.rejectionReason}`);
  }
}
```

---

## LangChain Integration

### Python with LangChain

```python
from langchain.agents import AgentExecutor
from ascend_sdk import AscendClient
from ascend_sdk.integrations.langchain import AscendGovernanceCallback

# Initialize Ascend client
ascend = AscendClient(api_key="ascend_your_api_key")

# Create governance callback
governance = AscendGovernanceCallback(
    client=ascend,
    agent_id="langchain-finance-agent"
)

# Add to your agent
agent = AgentExecutor(
    agent=your_agent,
    tools=your_tools,
    callbacks=[governance]
)

# All tool calls will be governed through Ascend
result = agent.run("Analyze Q4 financial data")
```

---

## Error Handling

### Python

```python
from ascend_sdk import (
    AscendClient,
    AscendAuthenticationError,
    AscendRateLimitError,
    AscendUnreachableError,
    AscendValidationError
)

client = AscendClient(api_key="ascend_key")

try:
    result = client.evaluate_action(...)
except AscendAuthenticationError:
    print("Invalid API key")
except AscendRateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after} seconds")
except AscendValidationError as e:
    print(f"Invalid request: {e.errors}")
except AscendUnreachableError:
    print("Ascend service unreachable")
```

### JavaScript

```typescript
import {
  AscendClient,
  AscendAuthenticationError,
  AscendRateLimitError,
  AscendUnreachableError,
  AscendValidationError
} from '@ascend/sdk';

try {
  const result = await client.evaluateAction({...});
} catch (error) {
  if (error instanceof AscendAuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof AscendRateLimitError) {
    console.error(`Rate limited, retry after ${error.retryAfter}s`);
  } else if (error instanceof AscendValidationError) {
    console.error('Invalid request:', error.errors);
  } else if (error instanceof AscendUnreachableError) {
    console.error('Ascend service unreachable');
  }
}
```

---

## Response Object Reference

### EvaluateActionResult

| Property | Type | Description |
|----------|------|-------------|
| `action_id` | int | Unique action identifier |
| `status` | string | Current status: approved, pending, denied |
| `approved` | bool | Whether action is approved |
| `risk_score` | int | Risk score (0-100) |
| `risk_level` | string | Risk level: low, medium, high, critical |
| `requires_approval` | bool | Whether manual approval needed |
| `alert_generated` | bool | Whether an alert was created |
| `alert_id` | int? | Alert ID if generated |
| `compliance` | object | NIST/MITRE/CVSS data |
| `risk_assessment` | object | Policy and hybrid risk breakdown |
| `automation` | object | Playbook and workflow results |

---

## Best Practices

### 1. Use Environment Variables

```python
import os
from ascend_sdk import AscendClient

client = AscendClient(
    api_key=os.environ["ASCEND_API_KEY"],
    base_url=os.environ.get("ASCEND_BASE_URL")
)
```

### 2. Implement Proper Error Handling

Always handle potential errors gracefully, especially in production:

```python
def governed_action(client, action_params):
    try:
        result = client.evaluate_action(**action_params)
        if not result.approved and result.requires_approval:
            # Queue for async approval
            return {"queued": True, "action_id": result.action_id}
        return {"approved": result.approved, "risk_score": result.risk_score}
    except AscendUnreachableError:
        # Log and handle based on fail mode
        logger.error("Ascend unreachable")
        raise
```

### 3. Use Descriptive Action Descriptions

Provide detailed descriptions to improve risk assessment accuracy:

```python
# Good - detailed description
result = client.evaluate_action(
    agent_id="finance-agent",
    action_type="financial.transfer",
    tool_name="bank_api",
    description="Transfer $50,000 from operating account to vendor ABC Corp for Q4 invoice payment"
)

# Bad - vague description
result = client.evaluate_action(
    agent_id="agent",
    action_type="financial.transfer",
    tool_name="api",
    description="transfer money"
)
```

### 4. Monitor and Log

```python
result = client.evaluate_action(...)

logger.info(
    "Ascend evaluation",
    extra={
        "action_id": result.action_id,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "approved": result.approved,
        "policy_risk": result.risk_assessment.get("policy_risk"),
        "hybrid_risk": result.risk_assessment.get("hybrid_risk")
    }
)
```

---

## Support

- **SDK Issues**: https://github.com/ascendowkai/sdk-python/issues
- **Documentation**: https://docs.ascendowkai.com
- **Support**: support@ascendowkai.com

---

*Document Version: 2.0.0 | Last Updated: December 2025*
