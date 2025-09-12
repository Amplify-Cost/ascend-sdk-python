/**
 * Enterprise API Service Layer
 * Maps frontend API calls to correct backend endpoints
 * Maintains 100% functionality while fixing endpoint routing
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    return this.request(`/agent-action/${actionId}/approve`, {
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
