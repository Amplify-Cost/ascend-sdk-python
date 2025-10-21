

import { API_BASE_URL } from './config/api';
import logger from '../utils/logger.js';
/**
 * Enterprise API Service Layer - CORRECTED VERSION
 * Maps frontend API calls to actual working backend endpoints
 * Eliminates demo data fallback by using correct API paths
 */


class EnterpriseApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.authToken = null;
  }

  // Authentication management
  setAuthToken(token) {
    this.authToken = token;
  }

  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      ...options,
    };

    try {
      logger.debug(`🔄 API Request: ${options.method || 'GET'} ${url}`);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        logger.error(`❌ API Error ${response.status}:`, errorText);
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      logger.debug(`✅ API Response:`, data);
      return data;
    } catch (error) {
      logger.error('💥 API Request failed:', error);
      throw error;
    }
  }

  // CORRECTED: Authorization endpoints using actual working backend paths
  async getAuthorizationData() {
    try {
      // First try the main dashboard endpoint that we know works
      const dashboardData = await this.request('/api/authorization/dashboard');
      
      // Also get pending actions 
      const pendingActions = await this.request('/agent-control/pending-actions');
      
      // Combine the data in the format the frontend expects
      return {
        success: true,
        dashboard: dashboardData,
        pendingActions: pendingActions.actions || [],
        // Provide fallback structure if needed
        metrics: dashboardData.kpis || {},
        systemStatus: dashboardData.system_status || {}
      };
    } catch (error) {
      logger.error('Failed to load authorization data:', error);
      // Don't fall back to demo data - throw error so frontend knows to handle it
      throw error;
    }
  }

  // CORRECTED: Use actual working approval endpoint
  async approveAction(actionId, approvalData = {}) {
    return this.request(`/agent-control/authorize-with-audit/${actionId}`, {
      method: 'POST',
      body: JSON.stringify({
        approved: true,
        reason: approvalData.reason || 'Approved by administrator',
        ...approvalData
      }),
    });
  }

  // CORRECTED: Use actual working deny endpoint
  async denyAction(actionId, reason = 'Denied by administrator') {
    return this.request(`/agent-control/authorize-with-audit/${actionId}`, {
      method: 'POST',
      body: JSON.stringify({
        approved: false,
        reason: reason
      }),
    });
  }

  // CORRECTED: Dashboard endpoints using actual working paths
  async getDashboardMetrics() {
    return this.request('/api/authorization/dashboard');
  }

  // CORRECTED: Use working health endpoint
  async getSystemHealth() {
    return this.request('/health');
  }

  // Agent Actions endpoints
  async getAgentActions() {
    return this.request('/agent-actions');
  }

  async createAgentAction(actionData) {
    return this.request('/agent-actions', {
      method: 'POST',
      body: JSON.stringify(actionData),
    });
  }

  // MCP Governance endpoints
  async getMCPActions() {
    return this.request('/api/mcp-governance/actions');
  }

  async evaluateMCPAction(actionData) {
    return this.request('/api/mcp-governance/evaluate-action', {
      method: 'POST',
      body: JSON.stringify(actionData),
    });
  }

  // Analytics endpoints
  async getAnalytics() {
    return this.request('/api/analytics/dashboard');
  }

  async getRealtimeMetrics() {
    return this.request('/analytics/realtime/metrics');
  }

  // Authentication endpoints
  async login(credentials) {
    const response = await this.request('/auth/token', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    if (response.access_token) {
      this.setAuthToken(response.access_token);
    }
    
    return response;
  }

  async logout() {
    this.authToken = null;
    // If backend has logout endpoint, call it
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch (error) {
      logger.warn('Logout endpoint not available:', error);
    }
  }

  // Smart Rules endpoints (if implemented)
  async getSmartRules() {
    return this.request('/api/smart-rules');
  }

  async createSmartRule(ruleData) {
    return this.request('/api/smart-rules', {
      method: 'POST',
      body: JSON.stringify(ruleData),
    });
  }

  // Test data creation (for development/testing)
  async createTestActions(count = 5) {
    try {
      return this.request('/agent-control/create-test-actions', {
        method: 'POST',
        body: JSON.stringify({ count }),
      });
    } catch (error) {
      logger.warn('Test action creation not available:', error);
      throw error;
    }
  }

  // Utility method to test all endpoints
  async testConnectivity() {
    const tests = [
      { name: 'Health Check', endpoint: '/health' },
      { name: 'Dashboard', endpoint: '/api/authorization/dashboard' },
      { name: 'Pending Actions', endpoint: '/agent-control/pending-actions' },
      { name: 'Agent Actions', endpoint: '/agent-actions' },
      { name: 'MCP Actions', endpoint: '/api/mcp-governance/actions' }
    ];

    const results = {};
    
    for (const test of tests) {
      try {
        await this.request(test.endpoint);
        results[test.name] = 'SUCCESS';
      } catch (error) {
        results[test.name] = `FAILED: ${error.message}`;
      }
    }
    
    return results;
  }
}

export default new EnterpriseApiService();
