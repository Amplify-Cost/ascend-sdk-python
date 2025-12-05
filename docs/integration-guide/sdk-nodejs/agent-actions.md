# Agent Actions

Submit AI agent actions for authorization and risk assessment.

## Action Types

```typescript
type ActionType =
  | 'data_access'       // Reading data
  | 'data_modification' // Writing/updating data
  | 'transaction'       // Financial operations
  | 'recommendation'    // AI suggestions
  | 'communication'     // Sending messages
  | 'system_operation'; // System commands
```

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:55-62`

## Submit an Action

```typescript
import AscendClient from './ascend-client';

const client = new AscendClient();

const result = await client.submitAction({
  agent_id: 'financial-advisor-001',
  agent_name: 'Financial Advisor AI',
  action_type: 'transaction',
  resource: 'customer_account',
  resource_id: 'ACC-12345',
  action_details: {
    operation: 'transfer',
    amount: 5000,
    currency: 'USD',
    destination: 'savings_account',
  },
  context: {
    user_request: 'Transfer $5000 to my savings',
    session_id: 'sess_abc123',
    ip_address: '192.168.1.100',
  },
  risk_indicators: {
    pii_involved: false,
    financial_data: true,
    data_sensitivity: 'high',
  },
});

console.log(`Action ID: ${result.id}`);
console.log(`Status: ${result.status}`);
console.log(`Risk Score: ${result.risk_score}`);
console.log(`Risk Level: ${result.risk_level}`);
```

## Response Structure

```typescript
interface ActionResult {
  id: number;                    // Unique action ID
  status: string;                // 'approved' | 'pending_approval' | 'denied'
  risk_score: number;            // 0-100
  risk_level: string;            // 'minimal' | 'low' | 'medium' | 'high' | 'critical'
  requires_approval: boolean;    // True if human review needed
  alert_triggered: boolean;      // True if alert was created
  decision?: string;             // Final decision
  reason?: string;               // Denial reason if applicable
}
```

## Risk-Based Routing

Actions are automatically routed based on risk score:

| Risk Score | Risk Level | Default Behavior |
|------------|------------|------------------|
| 0-24 | Minimal | Auto-approve |
| 25-44 | Low | Auto-approve |
| 45-69 | Medium | Auto-approve with logging |
| 70-84 | High | Requires approval |
| 85-100 | Critical | Requires approval + alert |

**Source:** `/ow-ai-backend/services/enterprise_risk_calculator_v2.py`

## Wait for Decision

For actions requiring approval:

```typescript
const result = await client.submitAction({
  agent_id: 'high-value-agent',
  agent_name: 'Transaction Agent',
  action_type: 'transaction',
  resource: 'bank_account',
  action_details: { amount: 100000 },
});

if (result.status === 'pending_approval') {
  console.log('Action requires human approval...');

  // Wait up to 2 minutes for decision
  const finalResult = await client.waitForDecision(result.id, 120000);

  switch (finalResult.decision) {
    case 'approved':
      console.log('Action approved - proceeding');
      // Execute the action
      break;
    case 'denied':
      console.log(`Action denied: ${finalResult.reason}`);
      break;
    case 'timeout':
      console.log('No decision received in time');
      break;
  }
}
```

## Authorized Agent Wrapper

Create an agent wrapper for automatic authorization:

```typescript
class AuthorizedAgent {
  private client: AscendClient;
  private agentId: string;
  private agentName: string;

  constructor(agentId: string, agentName: string) {
    this.client = new AscendClient();
    this.agentId = agentId;
    this.agentName = agentName;
  }

  async executeIfAuthorized<T>(
    actionType: string,
    resource: string,
    executeFn: () => Promise<T>,
    options: {
      resourceId?: string;
      details?: Record<string, unknown>;
      context?: Record<string, unknown>;
      riskIndicators?: Record<string, unknown>;
      timeoutMs?: number;
    } = {}
  ): Promise<T> {
    const result = await this.client.submitAction({
      agent_id: this.agentId,
      agent_name: this.agentName,
      action_type: actionType,
      resource: resource,
      resource_id: options.resourceId,
      action_details: options.details,
      context: options.context,
      risk_indicators: options.riskIndicators,
    });

    // Wait for decision if pending
    let finalResult = result;
    if (result.status === 'pending_approval') {
      finalResult = await this.client.waitForDecision(
        result.id,
        options.timeoutMs || 60000
      );
    }

    // Check authorization
    if (finalResult.decision === 'approved' || finalResult.status === 'approved') {
      return executeFn();
    }

    if (finalResult.decision === 'denied') {
      throw new Error(`Action denied: ${finalResult.reason || 'No reason provided'}`);
    }

    throw new Error(`Authorization timeout or unexpected status: ${finalResult.status}`);
  }
}

// Usage
const agent = new AuthorizedAgent('data-agent-001', 'Data Access Agent');

const data = await agent.executeIfAuthorized(
  'data_access',
  'customer_database',
  async () => {
    // This only runs if authorized
    return await database.query('SELECT * FROM customers LIMIT 10');
  },
  {
    details: { query_type: 'read', table: 'customers' },
    riskIndicators: { pii_involved: true },
  }
);
```

## List Recent Actions

```typescript
const { actions } = await client.listActions({ limit: 20 });

for (const action of actions) {
  console.log(`${action.id}: ${action.status} (risk: ${action.risk_score})`);
}
```

## Get Action Details

```typescript
const details = await client.getActionDetails(12345);
console.log(JSON.stringify(details, null, 2));
```

## API Endpoints

| Operation | Endpoint | Source |
|-----------|----------|--------|
| Submit | POST `/api/v1/actions/submit` | `authorization_routes.py` |
| Status | GET `/api/v1/actions/{id}/status` | `agent_routes.py` |
| List | GET `/api/v1/actions` | `agent_routes.py` |
| Details | GET `/api/v1/actions/{id}` | `agent_routes.py` |

## Next Steps

- [Error Handling](/sdk/nodejs/error-handling) - Handle errors gracefully
- [Python SDK](/sdk/python/installation) - Python SDK documentation
