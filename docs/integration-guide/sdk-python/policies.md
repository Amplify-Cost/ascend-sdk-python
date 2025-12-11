---
Document ID: ASCEND-SDK-PY-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Policy Management

Learn how governance policies work in the OW-AI platform and how they affect your AI agent actions.

> **Note**: The Python SDK currently focuses on submitting agent actions for governance. Policy management is performed through the OW-AI web interface. This document explains how policies affect SDK usage.

## Overview

Policies in OW-AI define governance rules for AI agent actions. When you submit an action via the SDK, it is evaluated against your organization's active policies to determine if it should be:

- **Approved** - Action can proceed immediately
- **Requires Approval** - Action needs human review
- **Denied** - Action is blocked by policy
- **Escalated** - Action requires higher-level approval

## How Policies Affect SDK Calls

### Policy Evaluation Flow

```
SDK submit_action()
    ↓
OW-AI API receives action
    ↓
Policy Engine evaluates action
    ↓
Risk Score calculated
    ↓
Policies matched and applied
    ↓
Decision returned to SDK
```

### Example: Low-Risk Action

```python
from python_sdk_example import AuthorizedAgent

agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI"
)

# Low-risk query (typically auto-approved)
decision = agent.request_authorization(
    action_type="query",
    resource="market_data",
    details={
        "operation": "read",
        "data_type": "public_prices"
    },
    risk_indicators={
        "pii_involved": False,
        "financial_data": False
    }
)

# Response: { "decision": "approved", "risk_score": 15 }
print(f"Decision: {decision.get('decision')}")  # "approved"
```

### Example: High-Risk Action

```python
# High-risk transaction (requires approval)
decision = agent.request_authorization(
    action_type="transaction",
    resource="customer_account",
    resource_id="ACC-98765",
    details={
        "operation": "transfer",
        "amount": 50000,
        "currency": "USD",
        "destination": "external_account"
    },
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True,
        "data_sensitivity": "critical"
    },
    timeout=300  # Wait up to 5 minutes for approval
)

# Response: { "decision": "pending", "risk_score": 85 }
if decision.get('decision') == 'pending':
    print("Action requires manual review by compliance officer")
```

## Policy-Aware SDK Usage

### 1. Provide Rich Context

Help policies make accurate decisions by providing detailed information:

```python
action = AgentAction(
    agent_id="customer-service-agent",
    agent_name="Customer Service AI",
    action_type="data_access",
    resource="customer_database",
    resource_id="CUST-12345",

    # Detailed action information
    action_details={
        "operation": "read",
        "fields": ["name", "email", "order_history"],
        "purpose": "customer_support",
        "ticket_id": "SUPPORT-789"
    },

    # Business context
    context={
        "user_request": "Show order history for refund",
        "session_id": "sess_abc123",
        "support_agent_email": "john@company.com",
        "customer_consent": True
    },

    # Risk assessment
    risk_indicators={
        "pii_involved": True,
        "financial_data": True,
        "data_sensitivity": "medium",
        "regulatory_scope": "GDPR",
        "customer_verified": True
    }
)
```

### 2. Handle All Possible Outcomes

```python
from python_sdk_example import OWKAIClient, AgentAction

client = OWKAIClient()
action = AgentAction(...)

response = client.submit_action(action)
decision = response.get('decision', response.get('status'))

if decision == 'approved':
    # Policy allows immediate execution
    execute_action()

elif decision == 'pending':
    # Policy requires human approval
    action_id = response['action_id']
    print(f"Waiting for approval: {action_id}")

    # Wait for decision
    final = client.wait_for_decision(action_id, timeout=300)

    if final.get('decision') == 'approved':
        execute_action()
    else:
        log_denial(final)

elif decision == 'denied':
    # Policy blocks this action
    reason = response.get('reason', 'No reason provided')
    print(f"Action blocked by policy: {reason}")
    log_blocked_action(response)

elif decision == 'timeout':
    # Approval request timed out
    print("Approval timeout - action not executed")
    notify_timeout(response['action_id'])
```

### 3. Use Risk Indicators

Risk indicators help policies assess actions accurately:

```python
# Data classification risk indicators
risk_indicators = {
    # Data sensitivity
    "pii_involved": True,
    "financial_data": True,
    "health_data": False,
    "data_sensitivity": "high",  # low, medium, high, critical

    # Regulatory compliance
    "regulatory_scope": "GDPR,HIPAA",
    "compliance_required": True,

    # Transaction risk
    "amount_threshold": "exceeded",
    "external_transfer": True,
    "unusual_pattern": False,

    # Access control
    "customer_verified": True,
    "mfa_completed": True,
    "access_reason": "customer_request"
}
```

## Common Policy Patterns

### Pattern 1: Risk Threshold Policy

Policies often use risk scores to determine approval requirements:

```
IF risk_score < 30
    THEN auto_approve

IF risk_score >= 30 AND risk_score < 70
    THEN require_approval(compliance_team)

IF risk_score >= 70
    THEN require_approval(security_team) + escalate(management)
```

SDK usage:
```python
# Low risk (score: 15) → Auto-approved
decision = agent.request_authorization(
    action_type="query",
    resource="public_data",
    risk_indicators={"pii_involved": False}
)
# Result: {"decision": "approved", "risk_score": 15}

# Medium risk (score: 45) → Requires approval
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_data",
    risk_indicators={"pii_involved": True}
)
# Result: {"decision": "pending", "risk_score": 45}

# High risk (score: 85) → Requires senior approval
decision = agent.request_authorization(
    action_type="transaction",
    resource="financial_account",
    details={"amount": 100000},
    risk_indicators={"amount_threshold": "exceeded"}
)
# Result: {"decision": "pending", "risk_score": 85}
```

### Pattern 2: Resource-Based Policy

Policies can restrict access to specific resources:

```
IF resource == "production_database"
    AND action_type == "data_modification"
    THEN require_approval(dba_team)
```

SDK usage:
```python
# Production resource → Requires approval
decision = agent.request_authorization(
    action_type="data_modification",
    resource="production_database",
    details={"operation": "update", "table": "customers"}
)
```

### Pattern 3: Time-Based Policy

Policies may vary by time of day:

```
IF time BETWEEN 00:00 AND 06:00
    AND resource == "financial_system"
    THEN require_approval(security_team)
```

SDK usage:
```python
# Off-hours access → May require additional approval
decision = agent.request_authorization(
    action_type="data_access",
    resource="financial_system",
    context={
        "access_time": "02:30:00",
        "timezone": "UTC"
    }
)
```

## Testing Against Policies

### Test Actions Without Execution

While the SDK doesn't have a dedicated policy evaluation endpoint, you can test by submitting actions with clear test indicators:

```python
# Include test context
test_action = AgentAction(
    agent_id="test-agent",
    agent_name="Test Agent",
    action_type="data_access",
    resource="test_resource",
    context={
        "environment": "test",
        "purpose": "policy_validation"
    }
)

response = client.submit_action(test_action)
print(f"Would be {response.get('decision')} with risk score {response.get('risk_score')}")
```

### Gradual Risk Escalation Testing

Test how policies respond to increasing risk:

```python
test_cases = [
    {"amount": 1000, "expected": "approved"},
    {"amount": 10000, "expected": "approved"},
    {"amount": 50000, "expected": "pending"},
    {"amount": 100000, "expected": "pending"}
]

for test in test_cases:
    decision = agent.request_authorization(
        action_type="transaction",
        resource="test_account",
        details={"amount": test["amount"]},
        wait_for_decision=False
    )

    actual = decision.get('decision')
    print(f"Amount: ${test['amount']:,} → {actual} (expected: {test['expected']})")
```

## Policy Configuration (Web UI)

Policy management is performed through the OW-AI web interface at `https://pilot.owkai.app`. Administrators can:

### Create Policies

Navigate to **Settings → Governance → Policies** to create new policies:

1. **Policy Name**: Descriptive name (e.g., "High-Value Transaction Approval")
2. **Conditions**: When the policy applies
   - Risk score thresholds
   - Action types
   - Resource patterns
   - Time windows
3. **Action**: What happens when matched
   - Auto-approve
   - Require approval
   - Block
   - Escalate
4. **Priority**: Order of evaluation (higher priority = evaluated first)

### Policy Conditions

Conditions determine when a policy applies:

| Condition Type | Example | SDK Field |
|----------------|---------|-----------|
| Action Type | `action_type == "transaction"` | `action.action_type` |
| Resource | `resource CONTAINS "production"` | `action.resource` |
| Risk Score | `risk_score >= 70` | Calculated by platform |
| Risk Indicator | `risk_indicators.pii_involved == true` | `action.risk_indicators` |
| Amount | `details.amount > 50000` | `action.action_details` |
| Time | `time BETWEEN 00:00 AND 06:00` | Server time |

### Policy Actions

| Policy Action | SDK Response | Behavior |
|---------------|--------------|----------|
| Auto-Approve | `{"decision": "approved"}` | Action proceeds immediately |
| Require Approval | `{"decision": "pending"}` | Human review required |
| Block | `{"decision": "denied"}` | Action prevented |
| Escalate | `{"decision": "pending"}` | Escalated to higher authority |

## Best Practices

### 1. Design for Policy Evaluation

```python
# ✅ Good - Rich information for policies
action = AgentAction(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    action_type="transaction",
    resource="customer_account",
    resource_id="ACC-12345",
    action_details={
        "operation": "transfer",
        "amount": 50000,
        "currency": "USD",
        "source": "checking",
        "destination": "savings",
        "reason": "customer_request"
    },
    context={
        "user_id": "USER-789",
        "session_id": "sess_abc123",
        "ip_address": "192.168.1.100",
        "mfa_verified": True,
        "timestamp": "2025-12-04T10:30:00Z"
    },
    risk_indicators={
        "amount_threshold": "normal",
        "external_transfer": False,
        "unusual_pattern": False,
        "customer_verified": True
    }
)

# ❌ Bad - Minimal information
action = AgentAction(
    agent_id="agent",
    agent_name="Agent",
    action_type="transaction",
    resource="account"
)
```

### 2. Handle Pending States Gracefully

```python
# ✅ Good - Proper pending handling
response = client.submit_action(action)

if response.get('decision') == 'pending':
    action_id = response['action_id']

    # Notify user
    print(f"Your request requires approval (ID: {action_id})")

    # Option 1: Wait synchronously
    final = client.wait_for_decision(action_id, timeout=300)

    # Option 2: Store and check later
    store_pending_action(action_id)

    # Option 3: Subscribe to webhook (if configured)
    await_webhook_notification(action_id)
```

### 3. Log Policy Decisions

```python
import logging

logger = logging.getLogger(__name__)

response = client.submit_action(action)

logger.info(
    "Policy decision",
    extra={
        "action_id": response.get('action_id'),
        "decision": response.get('decision'),
        "risk_score": response.get('risk_score'),
        "policies_evaluated": response.get('policies_evaluated', []),
        "agent_id": action.agent_id,
        "resource": action.resource
    }
)
```

### 4. Implement Fallback Strategies

```python
def execute_with_fallback(agent, primary_action, fallback_action):
    """Try primary action, fall back if denied."""

    # Try primary action
    decision = agent.request_authorization(**primary_action)

    if decision.get('decision') == 'approved':
        return execute_primary()

    elif decision.get('decision') == 'denied':
        logger.warning("Primary action denied, trying fallback")

        # Try fallback action
        fallback_decision = agent.request_authorization(**fallback_action)

        if fallback_decision.get('decision') == 'approved':
            return execute_fallback()

    raise PermissionError("All options denied by policy")
```

## Policy Troubleshooting

### Why was my action denied?

Check the response for policy details:

```python
response = client.submit_action(action)

if response.get('decision') == 'denied':
    print(f"Reason: {response.get('reason')}")
    print(f"Blocking policy: {response.get('blocking_policy')}")
    print(f"Risk score: {response.get('risk_score')}")
```

### Why is approval taking so long?

```python
# Set appropriate timeout
decision = agent.request_authorization(
    action_type="transaction",
    resource="financial_account",
    timeout=300  # 5 minutes for high-priority
)

if decision.get('decision') == 'timeout':
    # Approval workflow may be backed up
    print("Approval timeout - check with compliance team")
    print(f"Action ID: {decision.get('action_id')}")
```

### How can I reduce approval requirements?

1. Lower risk scores by providing better context
2. Use more specific action_types
3. Include verification flags in risk_indicators
4. Work with admins to adjust policy thresholds

## Next Steps

- [Error Handling](/sdk/python/error-handling) - Handle policy errors
- [API Reference](/sdk/python/api-reference) - Complete SDK documentation
- **OW-AI Web Interface** - Manage policies at `https://pilot.owkai.app`

## Additional Resources

- **Policy Documentation**: See the OW-AI web interface for your organization's specific policies
- **Risk Scoring**: Contact your OW-AI administrator for risk score calculation details
- **Compliance**: Work with your compliance team to understand approval workflows
