# Ascend AI Governance Platform - Node.js SDK

[![npm version](https://badge.fury.io/js/%40ascend-ai%2Fsdk.svg)](https://www.npmjs.com/package/@ascend-ai/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Node.js SDK for the **Ascend AI Governance Platform** - Enterprise-grade AI agent authorization and risk management.

## Features

- **Banking-Level Security**: Dual authentication headers, TLS 1.2+, API key masking
- **Automatic Retry**: Exponential backoff with jitter for transient failures
- **Type-Safe**: Full TypeScript support with comprehensive type definitions
- **Correlation Tracking**: Automatic request tracking for distributed systems
- **Error Handling**: Rich error classes with security-safe logging
- **Async/Await**: Modern promise-based API
- **Zero Dependencies**: Only axios for HTTP (minimal footprint)

## Installation

```bash
npm install @ascend-ai/sdk
```

```bash
yarn add @ascend-ai/sdk
```

## Quick Start

### 1. Set up authentication

```bash
export ASCEND_API_KEY="owkai_admin_..."
export ASCEND_API_URL="https://pilot.owkai.app"  # Optional
```

### 2. Submit an action for authorization

```typescript
import { AscendClient } from '@ascend-ai/sdk';

const client = new AscendClient();

const result = await client.submitAction({
  agent_id: 'gpt-4-customer-support',
  agent_name: 'Customer Support Bot',
  action_type: 'data_access',
  resource: 'customer_database',
  resource_id: 'user_12345',
  action_details: {
    query: 'SELECT * FROM customers WHERE id = ?'
  }
});

console.log('Status:', result.status);         // 'approved' | 'pending_approval' | 'denied'
console.log('Risk Score:', result.risk_score); // 0-100
console.log('Risk Level:', result.risk_level); // 'minimal' | 'low' | 'medium' | 'high' | 'critical'
```

### 3. Wait for approval decision

```typescript
if (result.requires_approval) {
  console.log('Waiting for human approval...');

  const final = await client.waitForDecision(result.id, 60000); // 1 minute timeout

  if (final.status === 'approved') {
    console.log('Approved! Reason:', final.reason);
  } else {
    console.log('Denied! Reason:', final.reason);
  }
}
```

## Usage Patterns

### Pattern 1: Direct Client Usage

```typescript
import { AscendClient } from '@ascend-ai/sdk';

const client = new AscendClient({
  apiKey: 'owkai_admin_...',  // Or use ASCEND_API_KEY env var
  timeout: 30000,              // 30 seconds
  maxRetries: 3,
  debug: true                  // Enable logging
});

// Submit action
const result = await client.submitAction({
  agent_id: 'gpt-4',
  agent_name: 'Financial Advisor Bot',
  action_type: 'transaction',
  resource: 'trading_system',
  action_details: {
    action: 'buy',
    symbol: 'AAPL',
    quantity: 100,
    amount: 17500
  },
  risk_indicators: {
    unusual_amount: true,
    off_hours: false
  }
});

// Check status
console.log(result.status);  // 'approved', 'pending_approval', or 'denied'

// Get updated status
const updated = await client.getActionStatus(result.id);
```

### Pattern 2: Authorized Agent Wrapper

The `AuthorizedAgent` wrapper simplifies the common pattern of "request → wait → execute":

```typescript
import { AuthorizedAgent } from '@ascend-ai/sdk';

const agent = new AuthorizedAgent(
  'gpt-4-customer-support',
  'Customer Support Bot'
);

// Execute with automatic authorization
const customer = await agent.executeIfAuthorized({
  authorization: {
    action_type: 'data_access',
    resource: 'customer_database',
    resource_id: 'user_12345'
  },
  action: async () => {
    // This only executes if approved
    return await database.getCustomer('user_12345');
  },
  onDenied: (result) => {
    console.log('Access denied:', result.reason);
    return null; // Return fallback value
  },
  onPending: (result) => {
    console.log('Waiting for approval...');
  }
});

console.log('Customer data:', customer);
```

### Pattern 3: Convenience Methods

```typescript
const agent = new AuthorizedAgent('gpt-4', 'My Agent');

// Data access
await agent.requestDataAccess('customer_database', 'user_12345');

// Data modification
await agent.requestDataModification('customer_database', 'user_12345', {
  email: 'newemail@example.com'
});

// Transaction
await agent.requestTransaction('payment_system', {
  amount: 10000,
  recipient: 'vendor_abc'
}, 'transaction_xyz', {
  high_value: true
});

// Communication
await agent.requestCommunication('email_system', {
  to: 'customer@example.com',
  subject: 'Account Update'
});

// System operation
await agent.requestSystemOperation('kubernetes_cluster', {
  action: 'scale',
  replicas: 10
});
```

## Action Types

| Action Type | Description | Examples |
|-------------|-------------|----------|
| `data_access` | Reading sensitive data | Database queries, file access |
| `data_modification` | Creating, updating, deleting data | CRUD operations |
| `transaction` | Financial or state-changing operations | Payments, trades, account changes |
| `recommendation` | AI-generated suggestions to users | Product recommendations, advice |
| `communication` | Sending emails, messages, notifications | Email, SMS, Slack |
| `system_operation` | Infrastructure or system-level operations | Deployments, scaling, configuration |

## Risk Levels

| Risk Level | Risk Score | Auto-Approved | Description |
|------------|------------|---------------|-------------|
| `minimal` | 0-20 | Yes | Routine operations, low impact |
| `low` | 21-40 | Yes | Standard operations, minimal risk |
| `medium` | 41-60 | Configurable | Moderate impact, may need review |
| `high` | 61-80 | No | High impact, requires approval |
| `critical` | 81-100 | No | Severe impact, requires approval |

## Error Handling

```typescript
import {
  AscendError,
  AuthenticationError,
  AuthorizationDeniedError,
  RateLimitError,
  TimeoutError,
  ValidationError
} from '@ascend-ai/sdk';

try {
  const result = await client.submitAction(action);
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
    // Check API key
  } else if (error instanceof AuthorizationDeniedError) {
    console.error('Action denied:', error.reason);
    console.error('Action ID:', error.actionId);
    // Log denial for audit
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited, retry after:', error.retryAfter);
    // Wait before retrying
  } else if (error instanceof TimeoutError) {
    console.error('Request timeout:', error.timeoutMs);
    // Increase timeout or check network
  } else if (error instanceof ValidationError) {
    console.error('Invalid input:', error.field, error.value);
    // Fix input data
  } else if (error instanceof AscendError) {
    console.error('Ascend error:', error.message);
    console.error('Correlation ID:', error.correlationId);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Advanced Usage

### Listing Actions

```typescript
const result = await client.listActions({
  status: 'approved',
  risk_level: 'high',
  agent_id: 'gpt-4',
  start_date: '2025-01-01T00:00:00Z',
  end_date: '2025-12-31T23:59:59Z',
  page: 1,
  limit: 50
});

console.log(`Found ${result.total} actions across ${result.total_pages} pages`);

result.actions.forEach(action => {
  console.log(`Action ${action.id}: ${action.status} (risk: ${action.risk_level})`);
});
```

### Testing Connection

```typescript
const status = await client.testConnection();

if (status.connected) {
  console.log(`✓ Connected to Ascend API in ${status.latency_ms}ms`);
  console.log(`Organization ID: ${status.organization_id}`);
} else {
  console.error(`✗ Connection failed: ${status.error}`);
}
```

### Custom Configuration

```typescript
const client = new AscendClient({
  apiKey: process.env.ASCEND_API_KEY,
  baseUrl: 'https://pilot.owkai.app',
  timeout: 60000,     // 60 seconds
  maxRetries: 5,      // 5 retry attempts
  debug: true         // Enable debug logging
});
```

## Security Best Practices

1. **Never hardcode API keys** - Use environment variables
2. **Use HTTPS only** - The SDK enforces TLS 1.2+
3. **Mask sensitive data** - SDK automatically masks API keys in logs
4. **Track requests** - Use correlation IDs for distributed tracing
5. **Handle errors** - Implement proper error handling and retry logic

## API Reference

### AscendClient

```typescript
class AscendClient {
  constructor(config?: ClientConfig)

  submitAction(action: AgentAction): Promise<ActionResult>
  getAction(actionId: number): Promise<ActionResult>
  getActionStatus(actionId: number): Promise<ActionResult>
  waitForDecision(actionId: number, timeoutMs?: number): Promise<ActionResult>
  listActions(params?: ListParams): Promise<ListResult>
  testConnection(): Promise<ConnectionStatus>
}
```

### AuthorizedAgent

```typescript
class AuthorizedAgent {
  constructor(agentId: string, agentName: string, client?: AscendClient)

  requestAuthorization(options: AuthorizationOptions): Promise<ActionResult>
  executeIfAuthorized<T>(options: ExecuteOptions<T>): Promise<T>

  // Convenience methods
  requestDataAccess(resource: string, resourceId?: string): Promise<ActionResult>
  requestDataModification(resource: string, resourceId?: string, details?: object): Promise<ActionResult>
  requestTransaction(resource: string, details: object, resourceId?: string): Promise<ActionResult>
  requestCommunication(resource: string, details: object): Promise<ActionResult>
  requestSystemOperation(resource: string, details: object): Promise<ActionResult>
}
```

## TypeScript Support

The SDK is written in TypeScript and includes full type definitions:

```typescript
import type {
  AgentAction,
  ActionResult,
  ActionType,
  ActionStatus,
  RiskLevel,
  ClientConfig,
  ListParams,
  ListResult,
  ConnectionStatus,
  AuthorizationOptions,
  ExecuteOptions
} from '@ascend-ai/sdk';
```

## Examples

### Example 1: Customer Support Bot

```typescript
import { AuthorizedAgent } from '@ascend-ai/sdk';

const supportBot = new AuthorizedAgent('gpt-4-support', 'Customer Support Bot');

async function handleCustomerQuery(customerId: string) {
  const customerData = await supportBot.executeIfAuthorized({
    authorization: {
      action_type: 'data_access',
      resource: 'customer_database',
      resource_id: customerId,
      context: {
        ip_address: '192.168.1.1',
        user_agent: 'SupportApp/1.0'
      }
    },
    action: async () => {
      return await database.getCustomer(customerId);
    },
    onDenied: () => {
      throw new Error('Access to customer data denied');
    }
  });

  return customerData;
}
```

### Example 2: Financial Transaction Agent

```typescript
import { AuthorizedAgent } from '@ascend-ai/sdk';

const financialAgent = new AuthorizedAgent('gpt-4-finance', 'Financial Advisor Bot');

async function processTransaction(transaction: Transaction) {
  const result = await financialAgent.requestTransaction(
    'payment_system',
    {
      type: 'transfer',
      amount: transaction.amount,
      from: transaction.fromAccount,
      to: transaction.toAccount
    },
    transaction.id,
    {
      high_value: transaction.amount > 10000,
      international: transaction.international,
      unusual_time: isOffHours()
    }
  );

  if (result.requires_approval) {
    await notifyCompliance(result);
    const final = await financialAgent.getClient().waitForDecision(result.id);
    return final;
  }

  return result;
}
```

### Example 3: Batch Processing

```typescript
import { AscendClient } from '@ascend-ai/sdk';

const client = new AscendClient();

async function processBatchActions(actions: AgentAction[]) {
  const results = await Promise.all(
    actions.map(action => client.submitAction(action))
  );

  const needsApproval = results.filter(r => r.requires_approval);
  console.log(`${needsApproval.length} actions need approval`);

  // Wait for all approvals
  const approvals = await Promise.all(
    needsApproval.map(r => client.waitForDecision(r.id, 300000)) // 5 min
  );

  return approvals;
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASCEND_API_KEY` | API key for authentication | (required) |
| `ASCEND_API_URL` | Base URL for Ascend API | `https://pilot.owkai.app` |

## Support

- Documentation: https://docs.ascendai.app
- Issues: https://github.com/ascend-ai/sdk-node/issues
- Email: support@ascendai.app

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

---

**Ascend AI Governance Platform** - Enterprise-grade AI agent authorization and risk management
