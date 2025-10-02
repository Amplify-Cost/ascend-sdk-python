/**
 * Unified Approval Service
 * Consolidates all approval-related API calls across:
 * - Legacy authorization system
 * - Phase 3 governance workflows
 * - MCP server governance
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://pilot.owkai.app';

class ApprovalService {
  constructor(getAuthHeaders) {
    this.getAuthHeaders = getAuthHeaders;
  }

  /**
   * Phase 3: Fetch pending workflows from governance API
   */
  async fetchPendingWorkflows() {
    const response = await fetch(
      `${API_BASE_URL}/api/governance/dashboard/pending-approvals`,
      {
        method: 'GET',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch pending workflows: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Phase 3: Approve or deny a workflow
   */
  async approveWorkflow(workflowExecutionId, decision, notes = '', conditions = null) {
    const response = await fetch(
      `${API_BASE_URL}/api/governance/workflows/${workflowExecutionId}/approve`,
      {
        method: 'POST',
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          decision,
          notes,
          conditions,
          approval_duration: conditions?.duration || null,
          execute_immediately: true
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Approval failed');
    }

    return response.json();
  }

  /**
   * Legacy: Fetch dashboard metrics
   */
  async fetchDashboardMetrics() {
    const response = await fetch(
      `${API_BASE_URL}/api/authorization/dashboard`,
      {
        method: 'GET',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch dashboard: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Legacy: Fetch approval performance metrics
   */
  async fetchApprovalMetrics() {
    const response = await fetch(
      `${API_BASE_URL}/api/authorization/metrics/approval-performance`,
      {
        method: 'GET',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Fetch execution history
   */
  async fetchExecutionHistory(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(
      `${API_BASE_URL}/api/authorization/execution-history?${params}`,
      {
        method: 'GET',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch execution history: ${response.status}`);
    }

    return response.json();
  }
}

export default ApprovalService;
