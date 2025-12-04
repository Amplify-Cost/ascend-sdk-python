

import { API_BASE_URL } from './config/api';
import logger from '../utils/logger.js';
import { fetchWithAuth } from '../utils/fetchWithAuth.js';
/**
 * Enterprise API Service Layer - CORRECTED VERSION
 * Maps frontend API calls to actual working backend endpoints
 * Eliminates demo data fallback by using correct API paths
 * Uses fetchWithAuth for enterprise cookie-based authentication
 */


class EnterpriseApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    // 🏢 ENTERPRISE: Cookie-based authentication - no token storage needed
    // All authentication handled by fetchWithAuth via HttpOnly cookies
  }

  async request(endpoint, options = {}) {
    // 🏢 ENTERPRISE: Use fetchWithAuth for cookie-based authentication + CSRF
    // This ensures credentials: "include" and automatic CSRF token handling
    try {
      logger.debug(`🔄 Enterprise API Request: ${options.method || 'GET'} ${endpoint}`);
      const data = await fetchWithAuth(endpoint, options);
      logger.debug(`✅ Enterprise API Response:`, data);
      return data;
    } catch (error) {
      logger.error('💥 Enterprise API Request failed:', error);
      throw error;
    }
  }

  // CORRECTED: Authorization endpoints using actual working backend paths
  async getAuthorizationData() {
    try {
      // First try the main dashboard endpoint that we know works
      const dashboardData = await this.request('/api/authorization/dashboard');
      
      // Also get pending actions 
      const pendingActions = await this.request('/api/authorization/pending-actions');
      
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

  // 🏢 ENTERPRISE: Approve action endpoint
  async approveAction(actionId, approvalData = {}) {
    return this.request(`/api/authorization/authorize/${actionId}`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'approve',
        reason: approvalData.reason || 'Approved by administrator',
        ...approvalData
      }),
    });
  }

  // 🏢 ENTERPRISE: Deny action endpoint
  async denyAction(actionId, reason = 'Denied by administrator') {
    return this.request(`/api/authorization/authorize/${actionId}`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'deny',
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
    return this.request('/api/v1/actions');
  }

  async createAgentAction(actionData) {
    return this.request('/api/v1/actions/submit', {
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
    return this.request('/api/api/analytics/dashboard');
  }

  async getRealtimeMetrics() {
    return this.request('/api/analytics/realtime/metrics');
  }

  // Authentication endpoints
  async login(credentials) {
    // 🏢 ENTERPRISE: Cookie-based login
    // Backend sets HttpOnly cookies automatically - no token storage needed
    const response = await this.request('/api/auth/token', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    return response;
  }

  async logout() {
    // 🏢 ENTERPRISE: Cookie-based logout
    // Backend clears cookies automatically
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
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
      return this.request('/api/authorization/create-test-actions', {
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
      { name: 'Pending Actions', endpoint: '/api/authorization/pending-actions' },
      { name: 'Agent Actions', endpoint: '/api/v1/actions' },
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
