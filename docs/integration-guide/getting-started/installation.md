# Installation

OW-AI Authorization Center integrates via REST API. There is **no package to install** from pip or npm.

## Integration Methods

| Method | Use Case | Complexity |
|--------|----------|------------|
| **Reference Implementation** | Copy verified client code | Low |
| **Direct REST API** | Custom integration | Medium |
| **Integration Examples** | Learn from working examples | Low |

## System Requirements

- **Python**: 3.8+ with `requests` library
- **Node.js**: 18+ with `axios` or `fetch`
- **Network**: HTTPS outbound to `pilot.owkai.app` (port 443)
- **Authentication**: API key from OW-AI dashboard

## Method 1: Reference Implementation (Recommended)

### Python

Copy the official reference client from the backend repository:

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py` (622 lines)

```bash
# 1. Install dependencies
pip install requests python-dotenv

# 2. Download reference implementation
curl -O https://raw.githubusercontent.com/OW-AI/ow-ai-backend/main/integration-examples/python_sdk_example.py

# 3. Set environment variables
export OWKAI_API_KEY="owkai_admin_xxxxxxxxxxxx"
export OWKAI_API_URL="https://pilot.owkai.app"

# 4. Run example
python python_sdk_example.py
```

### Node.js

**Source:** `/ow-ai-backend/integration-examples/nodejs_sdk_example.js` (510 lines)

```bash
# 1. Install dependencies
npm install axios dotenv

# 2. Download reference implementation
curl -O https://raw.githubusercontent.com/OW-AI/ow-ai-backend/main/integration-examples/nodejs_sdk_example.js

# 3. Create .env file
echo "OWKAI_API_KEY=owkai_admin_xxxxxxxxxxxx" > .env
echo "OWKAI_API_URL=https://pilot.owkai.app" >> .env

# 4. Run example
node nodejs_sdk_example.js
```

## Method 2: Direct REST API

### Minimal Python Client

```python
import os
import requests
from typing import Dict, Optional

class OWKAIClient:
    """
    Minimal OW-AI Authorization Center client.

    Based on: /ow-ai-backend/integration-examples/python_sdk_example.py:105-326
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_url = api_url or os.getenv('OWKAI_API_URL', 'https://pilot.owkai.app')
        self.api_key = api_key or os.getenv('OWKAI_API_KEY')
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("API key required. Set OWKAI_API_KEY environment variable.")

        # Authentication headers
        # Source: /ow-ai-backend/routes/authorization_routes.py:2219
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "OWKAIClient/2.0 Python"
        }

    def submit_action(self, **action_data) -> Dict:
        """
        Submit agent action for authorization.

        Required fields: agent_id, action_type, description, tool_name
        Endpoint: POST /api/v1/actions/submit
        Source: /ow-ai-backend/routes/authorization_routes.py:2202-2395
        """
        url = f"{self.api_url}/api/v1/actions/submit"

        response = requests.post(
            url,
            headers=self.headers,
            json=action_data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_action_status(self, action_id: int) -> Dict:
        """
        Get current status of an action.

        Endpoint: GET /api/v1/actions/{action_id}/status
        Source: /ow-ai-backend/routes/agent_routes.py:691-721
        """
        url = f"{self.api_url}/api/v1/actions/{action_id}/status"

        response = requests.get(
            url,
            headers=self.headers,
            timeout=10  # Status checks are fast
        )
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> Dict:
        """Test API connectivity and authentication"""
        try:
            # Health check
            response = requests.get(f"{self.api_url}/health", timeout=5)
            response.raise_for_status()

            # Verify authentication
            response = requests.get(
                f"{self.api_url}/api/deployment-info",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()

            return {
                "status": "connected",
                "api_version": response.json().get("version", "unknown")
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
```

### Minimal Node.js Client

```javascript
/**
 * Minimal OW-AI Authorization Center client.
 *
 * Based on: /ow-ai-backend/integration-examples/nodejs_sdk_example.js:89-264
 */
const axios = require('axios');

class OWKAIClient {
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || process.env.OWKAI_API_URL || 'https://pilot.owkai.app';
    this.apiKey = options.apiKey || process.env.OWKAI_API_KEY;
    this.timeout = options.timeout || 30000;

    if (!this.apiKey) {
      throw new Error('API key required. Set OWKAI_API_KEY environment variable.');
    }

    // Authentication headers
    // Source: /ow-ai-backend/routes/authorization_routes.py:2219
    this.headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
      'User-Agent': 'OWKAIClient/2.0 Node'
    };
  }

  /**
   * Submit agent action for authorization.
   *
   * Endpoint: POST /api/v1/actions/submit
   * Source: /ow-ai-backend/routes/authorization_routes.py:2202-2395
   */
  async submitAction(actionData) {
    const response = await axios.post(
      `${this.apiUrl}/api/v1/actions/submit`,
      actionData,
      { headers: this.headers, timeout: this.timeout }
    );
    return response.data;
  }

  /**
   * Get current status of an action.
   *
   * Endpoint: GET /api/v1/actions/{action_id}/status
   * Source: /ow-ai-backend/routes/agent_routes.py:691-721
   */
  async getActionStatus(actionId) {
    const response = await axios.get(
      `${this.apiUrl}/api/v1/actions/${actionId}/status`,
      { headers: this.headers, timeout: 10000 }
    );
    return response.data;
  }

  /**
   * Test API connectivity and authentication
   */
  async testConnection() {
    try {
      // Health check
      await axios.get(`${this.apiUrl}/health`, { timeout: 5000 });

      // Verify authentication
      const response = await axios.get(
        `${this.apiUrl}/api/deployment-info`,
        { headers: this.headers, timeout: 5000 }
      );

      return {
        status: 'connected',
        apiVersion: response.data.version || 'unknown'
      };
    } catch (error) {
      return {
        status: 'error',
        error: error.message
      };
    }
  }
}

module.exports = { OWKAIClient };
```

## Environment Configuration

### .env File (Recommended)

```bash
# Required
OWKAI_API_KEY=owkai_admin_xxxxxxxxxxxx

# Optional (defaults shown)
OWKAI_API_URL=https://pilot.owkai.app
OWKAI_TIMEOUT=30
```

### Python: Load Environment Variables

```python
from dotenv import load_dotenv
import os

load_dotenv()

client = OWKAIClient(
    api_key=os.getenv('OWKAI_API_KEY'),
    api_url=os.getenv('OWKAI_API_URL')
)
```

### Node.js: Load Environment Variables

```javascript
require('dotenv').config();

const client = new OWKAIClient({
  apiKey: process.env.OWKAI_API_KEY,
  apiUrl: process.env.OWKAI_API_URL
});
```

## Verify Installation

### Python

```python
from owkai_client import OWKAIClient

client = OWKAIClient()
status = client.test_connection()

if status['status'] == 'connected':
    print(f"✅ Connected to OW-AI (version: {status['api_version']})")
else:
    print(f"❌ Connection failed: {status['error']}")
```

### Node.js

```javascript
const { OWKAIClient } = require('./owkai_client');

(async () => {
  const client = new OWKAIClient();
  const status = await client.testConnection();

  if (status.status === 'connected') {
    console.log(`✅ Connected to OW-AI (version: ${status.apiVersion})`);
  } else {
    console.log(`❌ Connection failed: ${status.error}`);
  }
})();
```

## Integration Examples

The backend repository contains complete working examples:

| Example | File | Description |
|---------|------|-------------|
| Python SDK | `python_sdk_example.py` | Full-featured reference implementation (622 lines) |
| Node.js SDK | `nodejs_sdk_example.js` | Full-featured reference implementation (510 lines) |
| MCP Server | `03_mcp_server.py` | Async MCP server integration (404 lines) |
| FastAPI Middleware | `04_fastapi_middleware.py` | FastAPI authorization middleware (587 lines) |
| Cron Job | `05_automation_cron.py` | Scheduled task integration (448 lines) |

**Location:** `/ow-ai-backend/integration-examples/`

## Troubleshooting

### Connection Issues

```python
# Test with verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

client = OWKAIClient(debug=True)
status = client.test_connection()
```

### SSL Certificate Errors

```bash
# Python: Update certifi
pip install --upgrade certifi requests

# Node.js: Use system CA
export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
```

### Firewall Rules

Ensure outbound HTTPS (port 443) access to:
- `pilot.owkai.app` (API endpoint)

## Next Steps

- [Authentication](/getting-started/authentication) - API key management
- [First Agent Action](/getting-started/first-agent-action) - Submit your first action
- [Integration Examples](https://github.com/OW-AI/ow-ai-backend/tree/main/integration-examples) - Working code examples
