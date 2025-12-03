# ASCEND Node.js/TypeScript SDK v2.0

Enterprise-grade AI governance SDK for Node.js and TypeScript applications.

## Features

- **Fail Mode Configuration** - Choose between fail-closed (secure) or fail-open (available) when ASCEND is unreachable
- **Circuit Breaker Pattern** - Automatic failure detection with graceful recovery
- **Agent Registration** - Register agents with capabilities and permissions
- **Action Evaluation** - Real-time authorization decisions with risk scoring
- **Completion Logging** - Track action success/failure for audit trails
- **Approval Workflows** - Human-in-the-loop approval for high-risk actions
- **MCP Integration** - Higher-order functions for MCP server tools
- **HMAC-SHA256 Signing** - Request integrity verification
- **Structured Logging** - JSON logs with automatic API key masking
- **Full TypeScript Support** - Complete type definitions included

## Installation

```bash
npm install @ascend/sdk
# or
yarn add @ascend/sdk
```

## Quick Start

```typescript
import { AscendClient, FailMode, Decision } from '@ascend/sdk';

// Initialize client
const client = new AscendClient({
  apiKey: 'owkai_your_api_key',
  agentId: 'agent-001',
  agentName: 'My AI Agent',
  failMode: FailMode.CLOSED,  // Block on ASCEND unreachable
});

// Register agent (call once on startup)
await client.register({
  agentType: 'automation',
  capabilities: ['data_access', 'file_operations'],
  allowedResources: ['production_db', '/var/log/*'],
});

// Evaluate action before execution
const decision = await client.evaluateAction({
  actionType: 'database.query',
  resource: 'production_db',
  parameters: { query: 'SELECT * FROM users WHERE active = true' },
});

if (decision.decision === Decision.ALLOWED) {
  // Execute your action
  const result = await executeDatabaseQuery();

  // Log completion
  await client.logActionCompleted(
    decision.actionId,
    { rowsReturned: result.length },
    150  // duration in ms
  );
} else if (decision.decision === Decision.DENIED) {
  console.log(`Action denied: ${decision.reason}`);
  console.log(`Policy violations: ${decision.policyViolations}`);
} else if (decision.decision === Decision.PENDING) {
  console.log(`Awaiting approval from: ${decision.requiredApprovers}`);
}
```

## Fail Mode Configuration

ASCEND supports two fail modes for handling service unavailability:

### Fail-Closed (Recommended for Production)

```typescript
const client = new AscendClient({
  apiKey: '...',
  agentId: '...',
  agentName: '...',
  failMode: FailMode.CLOSED,  // Default
});
```

When ASCEND is unreachable:
- All actions are **blocked**
- `ConnectionError` or `CircuitBreakerOpenError` thrown
- Ensures no unauthorized actions occur

### Fail-Open (Use with Caution)

```typescript
const client = new AscendClient({
  apiKey: '...',
  agentId: '...',
  agentName: '...',
  failMode: FailMode.OPEN,
});
```

When ASCEND is unreachable:
- Actions are **allowed** to proceed
- Returns synthetic `ALLOWED` decision with `fail_open_mode` condition
- Use only when availability is critical

## Circuit Breaker

The SDK includes an automatic circuit breaker to prevent cascading failures:

```typescript
const client = new AscendClient({
  apiKey: '...',
  agentId: '...',
  agentName: '...',
  circuitBreakerOptions: {
    failureThreshold: 5,     // Open after 5 failures
    recoveryTimeout: 30,     // Try recovery after 30s
    halfOpenMaxCalls: 3,     // Allow 3 test calls in half-open
  },
});

// Check circuit state
const state = client.getCircuitBreakerState();
console.log(`State: ${state.state}, Failures: ${state.failures}`);

// Reset circuit breaker
client.resetCircuitBreaker();
```

Circuit states:
- **CLOSED**: Normal operation, requests flow through
- **OPEN**: After threshold failures, requests fail immediately
- **HALF_OPEN**: After recovery timeout, limited test requests allowed

## MCP Server Integration

Integrate ASCEND governance with MCP (Model Context Protocol) servers:

```typescript
import { AscendClient } from '@ascend/sdk';
import { mcpGovernance, highRiskAction } from '@ascend/sdk/mcp';

const client = new AscendClient({ ... });

// Basic governance wrapper
const queryDatabase = mcpGovernance(client, {
  actionType: 'database.query',
  resource: 'production_db',
})(async (sql: string) => {
  return await db.execute(sql);
});

// High-risk action requiring human approval
const deleteRecords = highRiskAction(client, 'database.delete', 'production_db')(
  async (table: string, whereClause: string) => {
    return await db.execute(`DELETE FROM ${table} WHERE ${whereClause}`);
  }
);

// Use the governed functions
const result = await queryDatabase('SELECT * FROM users');
```

### MCP Governance Configuration

```typescript
import { mcpGovernance, MCPGovernanceConfig } from '@ascend/sdk/mcp';

const config: MCPGovernanceConfig = {
  waitForApproval: true,           // Wait for pending approvals
  approvalTimeoutMs: 300000,       // 5 minute timeout
  approvalPollIntervalMs: 5000,    // Check every 5 seconds
  raiseOnDenial: true,             // Throw error on denial
  logAllDecisions: true,           // Log all authorization decisions
  onApprovalRequired: (decision, toolName) => {
    notifyAdmin(`Approval needed for ${toolName}`);
  },
};

const writeConfig = mcpGovernance(client, {
  actionType: 'file.write',
  resource: '/etc/config',
  config,
})(writeToFile);
```

### Middleware Pattern

```typescript
import { MCPGovernanceMiddleware } from '@ascend/sdk/mcp';

const middleware = new MCPGovernanceMiddleware(client);

// Wrap multiple tools
const tools = {
  query: middleware.wrap('database.query', 'prod_db', queryFn),
  write: middleware.wrap('file.write', '/var/log', writeFn),
  delete: middleware.wrapHighRisk('database.delete', 'prod_db', deleteFn),
};

// Check governed tools
console.log(`Governed tools: ${middleware.governedTools}`);
```

## Approval Workflows

Handle human-in-the-loop approvals for high-risk actions:

```typescript
// Request with automatic approval waiting
const decision = await client.evaluateAction({
  actionType: 'financial.transfer',
  resource: 'payment_gateway',
  parameters: { amount: 50000, currency: 'USD' },
  waitForApproval: true,        // Block until approved/denied
  approvalTimeout: 300000,      // 5 minute timeout
  requireHumanApproval: true,   // Force human review
});

// Manual approval polling
const decision = await client.evaluateAction({
  actionType: 'financial.transfer',
  resource: 'payment_gateway',
  parameters: { amount: 50000 },
});

if (decision.decision === Decision.PENDING) {
  const approvalId = decision.approvalRequestId!;

  // Poll for approval
  while (true) {
    const status = await client.checkApproval(approvalId);
    if (status.status === 'approved') {
      // Execute action
      break;
    } else if (status.status === 'rejected') {
      // Handle rejection
      break;
    }
    await sleep(5000);
  }
}
```

## Webhook Configuration

Receive real-time notifications for authorization events:

```typescript
await client.configureWebhook({
  url: 'https://your-app.com/webhooks/ascend',
  events: [
    'action.evaluated',
    'action.approved',
    'action.denied',
    'action.completed',
    'action.failed',
  ],
  secret: 'your_webhook_secret',  // For signature verification
});
```

## Structured Logging

The SDK includes structured JSON logging with automatic API key masking:

```typescript
const client = new AscendClient({
  apiKey: '...',
  agentId: '...',
  agentName: '...',
  logLevel: 'DEBUG',  // DEBUG, INFO, WARNING, ERROR
  jsonLogs: true,     // Enable JSON format
});

// Logs automatically mask API keys:
// {"timestamp":"2024-01-15T10:30:00Z","level":"INFO","message":"Evaluating action","api_key":"owkai_****"}
```

## Error Handling

```typescript
import {
  AscendClient,
  AuthenticationError,
  AuthorizationError,
  CircuitBreakerOpenError,
  ConnectionError,
  TimeoutError,
  RateLimitError,
} from '@ascend/sdk';

try {
  const decision = await client.evaluateAction({ ... });
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.log(`Invalid API key: ${error.message}`);
  } else if (error instanceof AuthorizationError) {
    console.log(`Authorization denied: ${error.message}`);
    console.log(`Policy violations: ${error.policyViolations}`);
    console.log(`Risk score: ${error.riskScore}`);
  } else if (error instanceof CircuitBreakerOpenError) {
    console.log(`Service unavailable: ${error.message}`);
    console.log(`Recovery in: ${error.recoveryTimeSeconds}s`);
  } else if (error instanceof ConnectionError) {
    console.log(`Connection failed: ${error.message}`);
  } else if (error instanceof TimeoutError) {
    console.log(`Request timed out after ${error.timeoutMs}ms`);
  } else if (error instanceof RateLimitError) {
    console.log(`Rate limited, retry after ${error.retryAfter}s`);
  }
}
```

## API Reference

### AscendClient

```typescript
interface AscendClientOptions {
  apiKey: string;                    // Required: Organization API key
  agentId: string;                   // Required: Unique agent identifier
  agentName: string;                 // Required: Human-readable name
  apiUrl?: string;                   // Default: 'https://pilot.owkai.app'
  environment?: string;              // Default: 'production'
  failMode?: FailMode;               // Default: FailMode.CLOSED
  timeout?: number;                  // Request timeout in ms (default: 30000)
  maxRetries?: number;               // Default: 3
  debug?: boolean;                   // Enable debug logging
  logLevel?: LogLevel;               // 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  jsonLogs?: boolean;                // Use JSON format (default: true)
  enableMetrics?: boolean;           // Enable metrics collection
  signingSecret?: string;            // For HMAC signing
  circuitBreakerOptions?: {
    failureThreshold?: number;       // Default: 5
    recoveryTimeout?: number;        // Default: 30
    halfOpenMaxCalls?: number;       // Default: 3
  };
}
```

### Methods

| Method | Description |
|--------|-------------|
| `register(options)` | Register agent with ASCEND |
| `evaluateAction(options)` | Evaluate action for authorization |
| `logActionCompleted(actionId, result?, durationMs?)` | Log successful completion |
| `logActionFailed(actionId, error, durationMs?)` | Log action failure |
| `checkApproval(approvalRequestId)` | Check approval status |
| `configureWebhook(options)` | Configure webhook notifications |
| `testConnection()` | Test API connectivity |
| `getCircuitBreakerState()` | Get circuit breaker state |
| `resetCircuitBreaker()` | Reset circuit breaker |
| `getMetrics()` | Get metrics snapshot |

### Types

```typescript
// Decision values
enum Decision {
  ALLOWED = 'allowed',
  DENIED = 'denied',
  PENDING = 'pending',
}

// Evaluation result
interface EvaluateActionResult {
  decision: Decision;
  actionId: string;
  reason?: string;
  riskScore?: number;
  policyViolations: string[];
  conditions: string[];
  approvalRequestId?: string;
  requiredApprovers: string[];
  expiresAt?: string;
  metadata: Record<string, unknown>;
}

// Registration response
interface RegisterResponse {
  agentId: string;
  status: string;
  registeredAt: string;
  capabilities: string[];
  metadata?: Record<string, unknown>;
}
```

## Legacy Client (v1.0)

For backward compatibility, the legacy `OWKAIClient` is still available:

```typescript
import { OWKAIClient } from '@ascend/sdk';

const client = new OWKAIClient({
  apiKey: 'your-api-key',
});

const decision = await client.submitAction({
  agentId: 'agent-001',
  agentName: 'My Agent',
  actionType: ActionType.DATA_ACCESS,
  resource: 'customer_data',
});
```

## Compliance

This SDK supports the following compliance frameworks:

- **SOC 2 Type II** (CC6.1) - Access control and audit trails
- **HIPAA** (164.312(e)) - Transmission security
- **PCI-DSS** (8.2, 8.3) - API key management, MFA
- **NIST AI RMF** - Govern, Map, Measure, Manage
- **NIST 800-63B** - Authentication standards

## Support

- Documentation: https://docs.ascendowkai.com
- Issues: https://github.com/anthropics/ascend-sdk-nodejs/issues
- Email: support@ascendowkai.com
