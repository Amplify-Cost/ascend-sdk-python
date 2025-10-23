#!/bin/bash

# Enterprise API Setup Script
# This script creates all the necessary files for connecting your frontend to backend APIs

echo "🚀 Setting up Enterprise API Service Layer..."

# Ensure we're in the right directory (should contain src folder)
if [ ! -d "src" ]; then
    echo "❌ Error: src directory not found. Please run this from your project root."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p src/services
mkdir -p src/hooks
mkdir -p src/components

# Create EnterpriseApiService.js
echo "🔧 Creating API Service..."
cat > src/services/EnterpriseApiService.js << 'EOF'
/**
 * Enterprise API Service Layer
 * Maps frontend API calls to correct backend endpoints
 * Maintains 100% functionality while fixing endpoint routing
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

class EnterpriseApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Authorization endpoints
  async getAuthorizationData() {
    return this.request('/agent-control/pending-actions');
  }

  async approveAction(actionId, approvalData) {
    return this.request(`/agent-control/authorize-with-audit/${actionId}`, {
      method: 'POST',
      body: JSON.stringify(approvalData),
    });
  }

  async createTestActions(count = 5) {
    return this.request('/agent-control/create-test-actions', {
      method: 'POST',
      body: JSON.stringify({ count }),
    });
  }

  // Dashboard endpoints
  async getDashboardMetrics() {
    return this.request('/dashboard/metrics');
  }

  async getSystemHealth() {
    return this.request('/system/health');
  }

  // Chat/AI endpoints
  async sendChatMessage(message, context = {}) {
    return this.request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, context }),
    });
  }
}

export default new EnterpriseApiService();
EOF

# Create useEnterpriseApi.js hook
echo "🎣 Creating API hooks..."
cat > src/hooks/useEnterpriseApi.js << 'EOF'
/**
 * Enterprise API Hook - Replaces direct fetch calls with service layer
 * Maintains existing component interfaces while using correct endpoints
 */

import { useState, useEffect, useCallback } from 'react';
import EnterpriseApiService from '../services/EnterpriseApiService';

export function useAuthorizationData() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await EnterpriseApiService.getAuthorizationData();
      setData(result.data || result || []);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch authorization data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const approveAction = useCallback(async (actionId, approvalData) => {
    try {
      const result = await EnterpriseApiService.approveAction(actionId, approvalData);
      // Refresh data after approval
      await fetchData();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchData]);

  const createTestActions = useCallback(async (count = 5) => {
    try {
      const result = await EnterpriseApiService.createTestActions(count);
      // Refresh data after creating test actions
      await fetchData();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    approveAction,
    createTestActions,
  };
}

export function useDashboardData() {
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError(null);
        
        const [metricsData, healthData] = await Promise.all([
          EnterpriseApiService.getDashboardMetrics(),
          EnterpriseApiService.getSystemHealth(),
        ]);
        
        setMetrics(metricsData);
        setHealth(healthData);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  return { metrics, health, loading, error };
}

export function useChatApi() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (message, context = {}) => {
    try {
      setLoading(true);
      const response = await EnterpriseApiService.sendChatMessage(message, context);
      
      setMessages(prev => [...prev, 
        { role: 'user', content: message },
        { role: 'assistant', content: response.message || response.content }
      ]);
      
      return response;
    } catch (err) {
      console.error('Failed to send message:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { messages, sendMessage, loading };
}
EOF

# Create EnterpriseApiProvider component
echo "⚛️  Creating API Provider component..."
cat > src/components/EnterpriseApiProvider.jsx << 'EOF'
/**
 * Enterprise API Provider - Context provider for API service
 */

import React, { createContext, useContext } from 'react';
import EnterpriseApiService from '../services/EnterpriseApiService';

const EnterpriseApiContext = createContext(null);

export function EnterpriseApiProvider({ children }) {
  return (
    <EnterpriseApiContext.Provider value={EnterpriseApiService}>
      {children}
    </EnterpriseApiContext.Provider>
  );
}

export function useEnterpriseApi() {
  const context = useContext(EnterpriseApiContext);
  if (!context) {
    throw new Error('useEnterpriseApi must be used within an EnterpriseApiProvider');
  }
  return context;
}
EOF

# Create a sample component update file
echo "📝 Creating example component update..."
cat > src/components/AuthorizationExample.jsx << 'EOF'
/**
 * Example: How to update your existing authorization components
 * Replace your old fetch calls with this pattern
 */

import React from 'react';
import { useAuthorizationData } from '../hooks/useEnterpriseApi';

export function AuthorizationExample() {
  const { 
    data, 
    loading, 
    error, 
    approveAction, 
    createTestActions 
  } = useAuthorizationData();

  const handleApproval = async (actionId) => {
    try {
      await approveAction(actionId, { approved: true, timestamp: new Date().toISOString() });
      console.log('✅ Action approved successfully!');
    } catch (error) {
      console.error('❌ Approval failed:', error);
    }
  };

  const handleCreateTest = async () => {
    try {
      await createTestActions(5);
      console.log('✅ Test actions created!');
    } catch (error) {
      console.error('❌ Failed to create test actions:', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Authorization Dashboard</h2>
      <button onClick={handleCreateTest}>
        Create Test Actions
      </button>
      
      {data.map((action) => (
        <div key={action.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
          <h3>{action.type}</h3>
          <p>{action.description}</p>
          <button onClick={() => handleApproval(action.id)}>
            Approve Action
          </button>
        </div>
      ))}
    </div>
  );
}
EOF

# Create integration guide
echo "📋 Creating integration guide..."
cat > INTEGRATION_GUIDE.md << 'EOF'
# Enterprise API Integration Guide

## Files Created:
- ✅ `src/services/EnterpriseApiService.js` - Main API service
- ✅ `src/hooks/useEnterpriseApi.js` - React hooks for API calls
- ✅ `src/components/EnterpriseApiProvider.jsx` - Context provider
- ✅ `src/components/AuthorizationExample.jsx` - Example component

## Next Steps:

### 1. Update your main App component:
```jsx
import { EnterpriseApiProvider } from './components/EnterpriseApiProvider';

function App() {
  return (
    <EnterpriseApiProvider>
      {/* Your existing app content */}
    </EnterpriseApiProvider>
  );
}
```

### 2. Update your authorization components:
Replace old fetch calls with:
```jsx
import { useAuthorizationData } from '../hooks/useEnterpriseApi';

// Use the hook in your component:
const { data, loading, error, approveAction, createTestActions } = useAuthorizationData();
```

### 3. Test the integration:
- Your API calls now use the correct backend endpoints
- Approval buttons will work with `/agent-control/authorize-with-audit/{id}`
- Test data generation works with `/agent-control/create-test-actions`

## API Endpoints Mapped:
- Authorization data: `/agent-control/pending-actions`
- Approve actions: `/agent-control/authorize-with-audit/{id}`
- Create test data: `/agent-control/create-test-actions`
- Dashboard metrics: `/dashboard/metrics`
- System health: `/system/health`

Your frontend is now connected to your working backend APIs! 🎉
EOF

echo ""
echo "✅ Enterprise API Service Layer setup complete!"
echo ""
echo "📁 Files created:"
echo "   • src/services/EnterpriseApiService.js"
echo "   • src/hooks/useEnterpriseApi.js" 
echo "   • src/components/EnterpriseApiProvider.jsx"
echo "   • src/components/AuthorizationExample.jsx"
echo "   • INTEGRATION_GUIDE.md"
echo ""
echo "🔧 Next steps:"
echo "   1. Update your App.jsx to wrap with EnterpriseApiProvider"
echo "   2. Replace old fetch calls with useAuthorizationData hook"
echo "   3. Test your authorization components"
echo ""
echo "📖 Check INTEGRATION_GUIDE.md for detailed instructions"
echo ""
echo "🎉 Your frontend is now ready to connect to your working backend!"