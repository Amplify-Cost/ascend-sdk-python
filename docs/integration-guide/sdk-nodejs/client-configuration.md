---
title: Client Configuration
sidebar_position: 1
---

# Client Configuration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-007 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Configure the Ascend REST API client for your Node.js application.

## Environment Variables

```bash
# Required
OWKAI_API_KEY=owkai_live_your_api_key_here

# Optional
OWKAI_API_URL=https://pilot.owkai.app  # Default
OWKAI_TIMEOUT=30000                     # 30 seconds default
OWKAI_ORG_SLUG=your-organization        # For multi-tenant
```

## Full Client Implementation

```typescript
// ascend-client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

export interface ClientConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  debug?: boolean;
}

export interface AgentAction {
  agent_id: string;
  agent_name: string;
  action_type: string;
  resource: string;
  resource_id?: string;
  action_details?: Record<string, unknown>;
  context?: Record<string, unknown>;
  risk_indicators?: Record<string, unknown>;
}

export interface ActionResult {
  id: number;
  status: string;
  risk_score: number;
  risk_level: string;
  requires_approval: boolean;
  alert_triggered: boolean;
  decision?: string;
}

export class AscendClient {
  private client: AxiosInstance;
  private debug: boolean;

  constructor(config: ClientConfig = {}) {
    const apiKey = config.apiKey || process.env.OWKAI_API_KEY;

    if (!apiKey) {
      throw new Error('API key is required. Set OWKAI_API_KEY environment variable or pass apiKey in config.');
    }

    this.debug = config.debug || false;

    this.client = axios.create({
      baseURL: config.baseUrl || process.env.OWKAI_API_URL || 'https://pilot.owkai.app',
      timeout: config.timeout || parseInt(process.env.OWKAI_TIMEOUT || '30000'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'X-API-Key': apiKey,  // SEC-033: Support both headers
        'User-Agent': 'AscendClient/1.0 Node.js',
      },
    });

    // Request interceptor for debugging
    if (this.debug) {
      this.client.interceptors.request.use((config) => {
        console.log(`[Ascend] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      });
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (this.debug) {
          console.error(`[Ascend] Error: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );
  }

  async testConnection(): Promise<{ status: string; version?: string }> {
    try {
      await this.client.get('/health');
      const { data } = await this.client.get('/api/deployment-info');
      return { status: 'connected', version: data.version };
    } catch (error) {
      return { status: 'error' };
    }
  }

  async submitAction(action: AgentAction): Promise<ActionResult> {
    const { data } = await this.client.post('/api/v1/actions/submit', action);
    return data;
  }

  async getActionStatus(actionId: number): Promise<ActionResult> {
    const { data } = await this.client.get(`/api/v1/actions/${actionId}/status`);
    return data;
  }

  async waitForDecision(actionId: number, timeoutMs = 60000, pollIntervalMs = 2000): Promise<ActionResult> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getActionStatus(actionId);

      if (status.decision !== 'pending') {
        return status;
      }

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }

    return {
      id: actionId,
      status: 'timeout',
      risk_score: 0,
      risk_level: 'unknown',
      requires_approval: false,
      alert_triggered: false,
      decision: 'timeout',
    };
  }

  async listActions(params: { limit?: number; offset?: number; status?: string } = {}): Promise<{ actions: ActionResult[] }> {
    const { data } = await this.client.get('/api/v1/actions', { params });
    return data;
  }

  async getActionDetails(actionId: number): Promise<ActionResult> {
    const { data } = await this.client.get(`/api/v1/actions/${actionId}`);
    return data;
  }
}

export default AscendClient;
```

## Usage Examples

### Basic Usage

```typescript
import AscendClient from './ascend-client';

const client = new AscendClient();

// Test connection
const conn = await client.testConnection();
console.log(`Connected: ${conn.status}`);

// Submit action
const result = await client.submitAction({
  agent_id: 'my-agent',
  agent_name: 'My AI Agent',
  action_type: 'data_access',
  resource: 'customer_database',
});
```

### With Custom Configuration

```typescript
const client = new AscendClient({
  apiKey: 'owkai_live_xxx',
  baseUrl: 'https://your-deployment.owkai.app',
  timeout: 60000,
  debug: true,
});
```

### Wait for Approval

```typescript
const result = await client.submitAction({
  agent_id: 'high-risk-agent',
  agent_name: 'Financial Agent',
  action_type: 'transaction',
  resource: 'bank_account',
  action_details: { amount: 50000 },
});

if (result.status === 'pending_approval') {
  console.log('Waiting for human approval...');
  const finalResult = await client.waitForDecision(result.id, 120000);
  console.log(`Final decision: ${finalResult.decision}`);
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `testConnection()` | GET `/health`, `/api/deployment-info` | Test API connectivity |
| `submitAction()` | POST `/api/v1/actions/submit` | Submit action for authorization |
| `getActionStatus()` | GET `/api/v1/actions/{id}/status` | Get current status |
| `waitForDecision()` | Polls `getActionStatus()` | Wait for final decision |
| `listActions()` | GET `/api/v1/actions` | List recent actions |
| `getActionDetails()` | GET `/api/v1/actions/{id}` | Get full action details |

**Source:** `/ow-ai-backend/routes/authorization_routes.py`, `/ow-ai-backend/routes/agent_routes.py`

## Next Steps

- [Agent Actions](/sdk/nodejs/agent-actions) - Submit and manage actions
- [Error Handling](/sdk/nodejs/error-handling) - Handle errors gracefully
