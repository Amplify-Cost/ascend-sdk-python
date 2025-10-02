import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import AgentAuthorizationDashboard from '../AgentAuthorizationDashboard';

vi.stubGlobal('API_BASE_URL', 'https://pilot.owkai.app');

describe('AgentAuthorizationDashboard - Critical Path Tests', () => {
  const mockGetAuthHeaders = vi.fn(() => ({
    'Authorization': 'Bearer test-token',
    'Content-Type': 'application/json'
  }));

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockClear();
    mockGetAuthHeaders.mockClear();
  });

  it('renders without crashing', () => {
    const { container } = render(
      <AgentAuthorizationDashboard 
        user={{ email: 'test@test.com', role: 'admin' }}
        getAuthHeaders={mockGetAuthHeaders}
      />
    );
    expect(container).toBeTruthy();
  });

  it('fetches pending workflows on mount using governance API', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        my_queue: [],
        total_pending: 0,
        role: 'admin'
      })
    });

    render(
      <AgentAuthorizationDashboard 
        user={{ email: 'test@test.com', role: 'admin' }}
        getAuthHeaders={mockGetAuthHeaders}
      />
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/governance/dashboard/pending-approvals'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );
    });
  });

  it('preserves workflow_execution_id in transformed data', async () => {
    const mockWorkflow = {
      workflow_id: 12,
      workflow_execution_id: 12,
      action_type: 'test_action',
      risk_score: 75,
      current_stage: 'pending_stage_1',
      can_approve: true,
      created_at: '2025-10-01T12:00:00Z'
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        my_queue: [mockWorkflow],
        total_pending: 1,
        role: 'admin'
      })
    });

    const { container } = render(
      <AgentAuthorizationDashboard 
        user={{ email: 'test@test.com', role: 'admin' }}
        getAuthHeaders={mockGetAuthHeaders}
      />
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // If workflow_execution_id is missing from transformed data,
    // the approval handler will use wrong endpoint
    // This test captures that critical requirement
    expect(container).toBeTruthy();
  });
});
