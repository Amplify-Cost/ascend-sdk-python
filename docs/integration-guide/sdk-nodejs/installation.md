---
title: Node.js Integration
sidebar_position: 1
---

# Node.js Integration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-009 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Integrate Ascend AI Governance into your Node.js applications using the REST API.

> **No Published Package**
> There is no published npm package for Ascend. Use the REST API directly with `fetch` or `axios`, or copy the reference client below into your project.


## Requirements

- Node.js 18+ (for native fetch) or Node.js 14+ with `node-fetch`
- Environment variables for authentication

## Quick Start

### Option 1: Native Fetch (Node.js 18+)

```typescript
// ascend-client.ts
const ASCEND_API_URL = process.env.OWKAI_API_URL || 'https://pilot.owkai.app';
const ASCEND_API_KEY = process.env.OWKAI_API_KEY;

interface AgentAction {
  agent_id: string;
  agent_name: string;
  action_type: string;
  resource: string;
  resource_id?: string;
  action_details?: Record<string, unknown>;
  context?: Record<string, unknown>;
  risk_indicators?: Record<string, unknown>;
}

interface ActionResult {
  id: number;
  status: string;
  risk_score: number;
  risk_level: string;
  requires_approval: boolean;
  decision?: string;
}

async function submitAction(action: AgentAction): Promise<ActionResult> {
  const response = await fetch(`${ASCEND_API_URL}/api/v1/actions/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${ASCEND_API_KEY}`,
    },
    body: JSON.stringify(action),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Usage
const result = await submitAction({
  agent_id: 'my-agent-001',
  agent_name: 'My AI Agent',
  action_type: 'data_access',
  resource: 'customer_database',
});

console.log(`Status: ${result.status}, Risk: ${result.risk_score}`);
```

### Option 2: With Axios

```bash
npm install axios dotenv
```

```typescript
// ascend-client.ts
import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

dotenv.config();

class AscendClient {
  private client: AxiosInstance;

  constructor() {
    const apiKey = process.env.OWKAI_API_KEY;
    if (!apiKey) {
      throw new Error('OWKAI_API_KEY environment variable is required');
    }

    this.client = axios.create({
      baseURL: process.env.OWKAI_API_URL || 'https://pilot.owkai.app',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      timeout: 30000,
    });
  }

  async submitAction(action: AgentAction): Promise<ActionResult> {
    const { data } = await this.client.post('/api/v1/actions/submit', action);
    return data;
  }

  async getActionStatus(actionId: number): Promise<ActionResult> {
    const { data } = await this.client.get(`/api/v1/actions/${actionId}/status`);
    return data;
  }

  async listActions(limit = 50): Promise<{ actions: ActionResult[] }> {
    const { data } = await this.client.get('/api/v1/actions', { params: { limit } });
    return data;
  }

  async testConnection(): Promise<{ status: string }> {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export default AscendClient;
```

## Environment Configuration

```bash
# .env file
OWKAI_API_KEY=owkai_live_your_api_key_here
OWKAI_API_URL=https://pilot.owkai.app
```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/actions/submit` | POST | Submit agent action |
| `/api/v1/actions/{id}/status` | GET | Check action status |
| `/api/v1/actions` | GET | List recent actions |
| `/health` | GET | Test connectivity |

**Source:** `/ow-ai-backend/routes/authorization_routes.py`, `/ow-ai-backend/routes/agent_routes.py`

## TypeScript Types

```typescript
// types.ts
export interface AgentAction {
  agent_id: string;
  agent_name: string;
  action_type: 'data_access' | 'data_modification' | 'transaction' |
               'recommendation' | 'communication' | 'system_operation';
  resource: string;
  resource_id?: string;
  action_details?: Record<string, unknown>;
  context?: Record<string, unknown>;
  risk_indicators?: Record<string, unknown>;
}

export interface ActionResult {
  id: number;
  status: 'approved' | 'pending_approval' | 'denied' | 'timeout';
  risk_score: number;
  risk_level: 'minimal' | 'low' | 'medium' | 'high' | 'critical';
  requires_approval: boolean;
  alert_triggered: boolean;
  decision?: string;
  reason?: string;
}

export type DecisionStatus = 'pending' | 'approved' | 'denied' | 'requires_modification' | 'timeout';
```

## Next Steps

- [Client Configuration](/sdk/nodejs/client-configuration) - Advanced configuration
- [Agent Actions](/sdk/nodejs/agent-actions) - Submit and manage actions
- [Error Handling](/sdk/nodejs/error-handling) - Handle errors gracefully
