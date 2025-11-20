import { describe, it, expect, beforeEach, vi } from 'vitest';
import ApprovalService from '../ApprovalService';

describe('ApprovalService', () => {
  const mockGetAuthHeaders = vi.fn(() => ({
    'Authorization': 'Bearer test-token'
  }));

  let service;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    service = new ApprovalService(mockGetAuthHeaders);
  });

  it('fetches pending workflows using governance API', async () => {
    const mockData = {
      my_queue: [],
      total_pending: 0,
      role: 'admin'
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const result = await service.fetchPendingWorkflows();

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/governance/dashboard/pending-approvals'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token'
        })
      })
    );
    expect(result).toEqual(mockData);
  });

  it('approves workflow with correct endpoint', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    await service.approveWorkflow(12, 'approved', 'Looks good');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/governance/workflows/12/approve'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"decision":"approved"')
      })
    );
  });
});
