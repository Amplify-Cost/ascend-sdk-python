# Backend API Integration Guide

## Overview

This guide documents how the frontend integrates with the OW-AI Backend API. All API endpoints use the `/api/*` prefix for standardization.

## Base Configuration

### Environment Setup

```javascript
// src/config/api.js
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'https://pilot.owkai.app',
  apiPrefix: '/api',
  timeout: 30000,
  withCredentials: true
};
```

### Authentication

The application uses dual authentication:
1. **JWT Bearer Tokens** - For API requests
2. **HTTP-Only Cookies** - For browser-based authentication

```javascript
// Example authenticated request
const response = await fetch(`${API_CONFIG.baseURL}/api/alerts`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  credentials: 'include'
});
```

## API Endpoints

### Authentication APIs

#### POST /auth/token
Login and receive JWT tokens

```javascript
// src/services/authService.js
export const login = async (email, password) => {
  const response = await fetch(`${API_CONFIG.baseURL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include'
  });

  const data = await response.json();
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    user: data.user
  };
};
```

#### GET /auth/me
Get current user information

```javascript
export const getCurrentUser = async (token) => {
  const response = await fetch(`${API_CONFIG.baseURL}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
    credentials: 'include'
  });
  return await response.json();
};
```

### Authorization APIs

#### GET /api/authorization/dashboard
Get authorization dashboard data

```javascript
// src/services/authorizationService.js
export const getDashboard = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/authorization/dashboard`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

**Response:**
```json
{
  "summary": {
    "total_pending": 5,
    "total_approved": 147,
    "total_executed": 134,
    "approval_rate": 86.5
  },
  "recent_activity": [...],
  "pending_actions": [...],
  "performance_metrics": {...}
}
```

#### GET /api/authorization/pending-actions
Get pending actions requiring approval

```javascript
export const getPendingActions = async (token, filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/authorization/pending-actions?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

**Query Parameters:**
- `risk_level`: Filter by risk level (low, medium, high, critical)
- `agent_id`: Filter by specific agent
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

#### POST /api/authorization/authorize/{action_id}
Approve or reject an action

```javascript
export const authorizeAction = async (token, actionId, decision, comment) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/authorization/authorize/${actionId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        decision,
        comment,
        conditions: {
          time_limit_hours: 2,
          monitoring_required: true
        }
      })
    }
  );
  return await response.json();
};
```

#### GET /api/authorization/workflow-config
Get workflow configuration

```javascript
export const getWorkflowConfig = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/authorization/workflow-config`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

### Alert Management APIs

#### GET /api/alerts
Get all alerts with filtering

```javascript
// src/services/alertService.js
export const getAlerts = async (token, filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/alerts?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

**Query Parameters:**
- `severity`: Filter by severity (low, medium, high, critical)
- `status`: Filter by status (new, acknowledged, resolved)
- `limit`: Number of results
- `start_date`: Start date for filtering
- `end_date`: End date for filtering

#### GET /api/alerts/ai-insights
Get AI-powered alert insights

```javascript
export const getAIInsights = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/alerts/ai-insights`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

**Response:**
```json
{
  "threat_summary": {
    "total_threats": 15,
    "critical_threats": 3,
    "automated_responses": 6,
    "false_positive_rate": 12.5,
    "avg_response_time": "4.2 minutes"
  },
  "predictive_analysis": {
    "risk_score": 75,
    "trend_direction": "increasing",
    "predicted_incidents": 2,
    "confidence_level": 87
  },
  "patterns_detected": [...],
  "recommendations": [...]
}
```

#### GET /api/alerts/threat-intelligence
Get threat intelligence data

```javascript
export const getThreatIntelligence = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/alerts/threat-intelligence`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

#### GET /api/alerts/performance-metrics
Get alert system performance metrics

```javascript
export const getPerformanceMetrics = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/alerts/performance-metrics`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

#### PATCH /api/alerts/{alert_id}
Update alert status

```javascript
export const updateAlertStatus = async (token, alertId, status, comment) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/alerts/${alertId}`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ status, comment })
    }
  );
  return await response.json();
};
```

### Smart Rules APIs

#### GET /api/smart-rules
List all smart rules

```javascript
// src/services/smartRulesService.js
export const getSmartRules = async (token) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/smart-rules`,
    {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    }
  );
  return await response.json();
};
```

#### POST /api/smart-rules/generate-from-nl
Generate rule from natural language

```javascript
export const generateRuleFromNL = async (token, description) => {
  const response = await fetch(
    `${API_CONFIG.baseURL}/api/smart-rules/generate-from-nl`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        description,
        severity: 'high',
        enabled: true
      })
    }
  );
  return await response.json();
};
```

## Error Handling

### Standard Error Format

All API errors follow this format:

```json
{
  "detail": "Error message description",
  "error_code": "AUTH_001",
  "timestamp": "2025-10-29T14:00:00Z",
  "request_id": "req_20251029_140000_123"
}
```

### Error Handling Implementation

```javascript
// src/utils/apiClient.js
export const handleApiError = (error, response) => {
  if (response.status === 401) {
    // Unauthorized - redirect to login
    window.location.href = '/login';
    return;
  }

  if (response.status === 403) {
    // Forbidden - show permission error
    throw new Error('Insufficient permissions');
  }

  if (response.status === 429) {
    // Rate limit exceeded
    throw new Error('Too many requests. Please try again later.');
  }

  // Generic error
  throw new Error(error.detail || 'An unexpected error occurred');
};
```

### Retry Logic

```javascript
export const fetchWithRetry = async (url, options, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;

      if (response.status >= 500 && i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      }

      throw await response.json();
    } catch (error) {
      if (i === retries - 1) throw error;
    }
  }
};
```

## React Hooks

### useApi Hook

```javascript
// src/hooks/useApi.js
import { useState, useEffect } from 'react';

export const useApi = (apiCall, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await apiCall();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, dependencies);

  return { data, loading, error };
};
```

### Usage Example

```javascript
// In a component
import { useApi } from '../hooks/useApi';
import { getDashboard } from '../services/authorizationService';

function Dashboard() {
  const token = useAuth().token;
  const { data, loading, error } = useApi(
    () => getDashboard(token),
    [token]
  );

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return <DashboardView data={data} />;
}
```

## Rate Limiting

The backend implements rate limiting:
- **Authenticated Users:** 100 requests per minute
- **Admin Users:** 200 requests per minute

### Client-Side Rate Limiting

```javascript
// src/utils/rateLimiter.js
class RateLimiter {
  constructor(maxRequests, timeWindow) {
    this.maxRequests = maxRequests;
    this.timeWindow = timeWindow;
    this.requests = [];
  }

  async throttle() {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.timeWindow);

    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.timeWindow - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.requests.push(now);
  }
}

export const apiRateLimiter = new RateLimiter(100, 60000); // 100 req/min
```

## WebSocket Integration (Future)

For real-time updates:

```javascript
// src/services/websocketService.js
export class WebSocketService {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.ws = null;
  }

  connect() {
    this.ws = new WebSocket(`${this.url}?token=${this.token}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }

  subscribe(channel, callback) {
    // Subscribe to specific channels (alerts, approvals, etc.)
  }
}
```

## Best Practices

1. **Always use the API_CONFIG** for base URLs
2. **Include credentials** for cookie-based auth
3. **Handle errors** consistently across the application
4. **Implement retry logic** for network failures
5. **Use TypeScript** for type safety (recommended)
6. **Cache responses** where appropriate
7. **Log API calls** in development for debugging
8. **Test API integrations** with mock data

## Migration from Old Endpoints

If you're migrating from old endpoints:

```javascript
// Old (deprecated)
fetch('/agent-control/dashboard')
fetch('/alerts')

// New (correct)
fetch('/api/authorization/dashboard')
fetch('/api/alerts')
```

## See Also

- [Backend API Reference](../../ow-ai-backend/enterprise-docs/api/API-REFERENCE.md)
- [Authentication Guide](../guides/AUTHENTICATION.md)
- [Error Handling Guide](../guides/ERROR-HANDLING.md)
