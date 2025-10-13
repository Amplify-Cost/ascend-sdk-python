// Enterprise API Service Layer
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  // Set authentication token
  setAuthToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  // Clear authentication
  clearAuth() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Generic request handler
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      }
    };

    // Add auth token if available
    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      
      // Handle auth errors
      if (response.status === 401) {
        this.clearAuth();
        window.location.href = '/login';
        throw new Error('Authentication required');
      }

      // Handle other errors
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Request failed: ${response.statusText}`);
      }

      // Return parsed response
      return await response.json();
    } catch (error) {
      console.error(`API Error: ${endpoint}`, error);
      throw error;
    }
  }

  // AUTH ENDPOINTS
  async login(email, password) {
    const response = await this.request('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.setAuthToken(response.access_token);
    return response;
  }

  async logout() {
    this.clearAuth();
  }

  // ALERT ENDPOINTS
  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/api/alerts${query ? '?' + query : ''}`);
  }

  async createAlert(alertData) {
    return this.request('/api/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData)
    });
  }

  async acknowledgeAlert(alertId, comment) {
    return this.request(`/api/alerts/${alertId}/acknowledge`, {
      method: 'PUT',
      body: JSON.stringify({ comment })
    });
  }

  async deleteAlert(alertId) {
    return this.request(`/api/alerts/${alertId}`, {
      method: 'DELETE'
    });
  }

  // POLICY ENDPOINTS
  async getPolicies() {
    return this.request('/api/governance/policies');
  }

  async createPolicy(policyData) {
    return this.request('/api/governance/create-policy', {
      method: 'POST',
      body: JSON.stringify(policyData)
    });
  }

  async evaluatePolicy(evaluationData) {
    return this.request('/api/governance/policies/evaluate-realtime', {
      method: 'POST',
      body: JSON.stringify(evaluationData)
    });
  }

  async updatePolicy(policyId, policyData) {
    return this.request(`/api/governance/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify(policyData)
    });
  }

  async deletePolicy(policyId) {
    return this.request(`/api/governance/policies/${policyId}`, {
      method: 'DELETE'
    });
  }

  // SMART RULES ENDPOINTS
  async getSmartRules() {
    return this.request('/api/smart-rules');
  }

  async generateSmartRule(naturalLanguage) {
    return this.request('/api/smart-rules/generate-from-nl', {
      method: 'POST',
      body: JSON.stringify({ natural_language: naturalLanguage })
    });
  }

  // USER ENDPOINTS
  async getUserProfile() {
    return this.request('/api/users/profile');
  }

  async getUsers() {
    return this.request('/api/users');
  }
}

// Export singleton instance
export default new ApiService();
