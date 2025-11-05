import React, { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Trash2,
  ArrowUpDown,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from './ToastNotification';

/**
 * Enterprise Policy Bulk Operations Manager
 *
 * Features:
 * - Bulk enable/disable policies
 * - Bulk priority updates
 * - Bulk deletion with backup
 * - Confirmation modals for safety
 * - Detailed operation results
 *
 * @param {Object} props
 * @param {Array} props.selectedPolicies - Array of selected policy objects
 * @param {Function} props.onBulkComplete - Callback after bulk operation completes
 * @param {Function} props.onClearSelection - Callback to clear policy selection
 * @param {string} props.API_BASE_URL - Base URL for API calls
 * @param {Function} props.getAuthHeaders - Authentication headers provider
 */
export const PolicyBulkActions = ({
  selectedPolicies,
  onBulkComplete,
  onClearSelection,
  API_BASE_URL,
  getAuthHeaders
}) => {
  // State
  const [action, setAction] = useState(null);
  const [reason, setReason] = useState('');
  const [newPriority, setNewPriority] = useState(100);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Hooks
  const { isDarkMode } = useTheme();
  const { toast } = useToast();

  // Don't render if no policies selected
  if (!selectedPolicies || selectedPolicies.length === 0) {
    return null;
  }

  /**
   * Open bulk action modal
   */
  const openBulkAction = (actionType) => {
    setAction(actionType);
    setReason('');
    setNewPriority(100);
    setShowModal(true);
  };

  /**
   * Get action title
   */
  const getActionTitle = () => {
    const titles = {
      enable: 'Enable Policies',
      disable: 'Disable Policies',
      priority: 'Update Priority',
      delete: 'Delete Policies'
    };
    return titles[action] || 'Bulk Action';
  };

  /**
   * Get action verb for toast
   */
  const getActionVerb = () => {
    const verbs = {
      enable: 'enabled',
      disable: 'disabled',
      priority: 'updated',
      delete: 'deleted'
    };
    return verbs[action] || 'processed';
  };

  /**
   * Execute bulk operation
   */
  const executeBulkAction = async () => {
    // Validation
    if (!action) return;

    if ((action === 'enable' || action === 'disable' || action === 'delete') && !reason.trim()) {
      toast.error('Please provide a reason for this operation', 'Reason Required');
      return;
    }

    try {
      setLoading(true);

      const policyIds = selectedPolicies.map(p => p.id);
      let endpoint, body;

      switch (action) {
        case 'enable':
        case 'disable':
          endpoint = '/api/governance/policies/bulk-update-status';
          body = {
            policy_ids: policyIds,
            new_status: action === 'enable' ? 'active' : 'inactive',
            reason: reason
          };
          break;

        case 'priority':
          endpoint = '/api/governance/policies/bulk-update-priority';
          body = {
            updates: policyIds.map(id => ({
              policy_id: id,
              priority: newPriority
            }))
          };
          break;

        case 'delete':
          endpoint = '/api/governance/policies/bulk-delete';
          body = {
            policy_ids: policyIds,
            confirmation: 'DELETE',
            create_backup: true
          };
          break;

        default:
          throw new Error('Invalid action');
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        credentials: "include",
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Bulk operation failed`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Bulk operation failed');
      }

      // Success feedback
      const count = result.updated_count || result.deleted_count || 0;
      const actionVerb = getActionVerb();

      toast.success(
        `Successfully ${actionVerb} ${count} ${count === 1 ? 'policy' : 'policies'}`,
        'Bulk Operation Complete'
      );

      // Show backup info for delete
      if (action === 'delete' && result.backup) {
        toast.info(
          `Backup created: ${result.backup.backup_name}`,
          'Backup Saved'
        );
      }

      // Close modal and refresh
      setShowModal(false);
      onBulkComplete();
    } catch (error) {
      toast.error(error.message || 'Bulk operation failed', 'Error');
      console.error('Bulk operation error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toolbar */}
      <div className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 shadow-2xl rounded-lg p-4 flex items-center gap-4 z-50 ${
        isDarkMode ? 'bg-slate-800 border border-slate-600' : 'bg-white border border-gray-300'
      }`}>
        {/* Selection Count */}
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-500" />
          <span className="font-semibold">
            {selectedPolicies.length} selected
          </span>
        </div>

        <div className={`h-6 w-px ${isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}></div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => openBulkAction('enable')}
            className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center gap-1 text-sm font-medium"
            aria-label="Enable selected policies"
          >
            <CheckCircle className="h-4 w-4" />
            Enable
          </button>

          <button
            onClick={() => openBulkAction('disable')}
            className="px-3 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors flex items-center gap-1 text-sm font-medium"
            aria-label="Disable selected policies"
          >
            <XCircle className="h-4 w-4" />
            Disable
          </button>

          <button
            onClick={() => openBulkAction('priority')}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-1 text-sm font-medium"
            aria-label="Update priority of selected policies"
          >
            <ArrowUpDown className="h-4 w-4" />
            Priority
          </button>

          <button
            onClick={() => openBulkAction('delete')}
            className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors flex items-center gap-1 text-sm font-medium"
            aria-label="Delete selected policies"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </div>

        <div className={`h-6 w-px ${isDarkMode ? 'bg-gray-600' : 'bg-gray-300'}`}></div>

        {/* Cancel Button */}
        <button
          onClick={onClearSelection}
          className={`px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm ${
            isDarkMode ? 'text-gray-300' : 'text-gray-600'
          }`}
          aria-label="Clear selection"
        >
          Cancel
        </button>
      </div>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div
            className={`max-w-md w-full rounded-lg p-6 ${
              isDarkMode ? 'bg-slate-800' : 'bg-white'
            }`}
            role="dialog"
            aria-modal="true"
            aria-labelledby="bulk-action-title"
          >
            {/* Modal Header */}
            <h3 id="bulk-action-title" className="text-xl font-bold mb-4 flex items-center gap-2">
              {action === 'delete' && <AlertTriangle className="h-6 w-6 text-red-500" />}
              {getActionTitle()}
            </h3>

            {/* Affected Policies */}
            <div className="mb-4">
              <p className={`text-sm mb-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                This will affect <strong>{selectedPolicies.length}</strong> {selectedPolicies.length === 1 ? 'policy' : 'policies'}:
              </p>
              <div className={`max-h-32 overflow-auto rounded p-3 ${
                isDarkMode ? 'bg-slate-700' : 'bg-gray-50'
              }`}>
                <ul className="space-y-1 text-sm">
                  {selectedPolicies.map(policy => (
                    <li key={policy.id} className="flex items-center gap-2">
                      <Shield className="h-3 w-3 text-blue-500 flex-shrink-0" />
                      <span className="truncate">{policy.policy_name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Priority Input (for priority action) */}
            {action === 'priority' && (
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  New Priority (1-1000)
                </label>
                <input
                  type="number"
                  value={newPriority}
                  onChange={(e) => setNewPriority(parseInt(e.target.value) || 100)}
                  min="1"
                  max="1000"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isDarkMode
                      ? 'bg-slate-700 border-slate-600 text-white'
                      : 'bg-white border-gray-300'
                  }`}
                />
                <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Higher priority = evaluated first
                </p>
              </div>
            )}

            {/* Reason Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Reason {action !== 'priority' && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows="3"
                placeholder={`Enter reason for ${action === 'priority' ? 'updating priority' : action + 'ing these policies'}...`}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                  isDarkMode
                    ? 'bg-slate-700 border-slate-600 text-white placeholder-gray-400'
                    : 'bg-white border-gray-300 placeholder-gray-500'
                }`}
                required={action !== 'priority'}
              />
              {action !== 'priority' && (
                <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Required for audit trail
                </p>
              )}
            </div>

            {/* Delete Warning */}
            {action === 'delete' && (
              <div className={`p-3 rounded-lg mb-4 ${
                isDarkMode ? 'bg-red-900 bg-opacity-20 border border-red-500' : 'bg-red-50 border border-red-300'
              }`}>
                <p className="text-sm flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <span>
                    This will soft-delete the selected policies. A backup will be created automatically.
                    You can restore them later using the import feature.
                  </span>
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                disabled={loading}
                className={`px-4 py-2 border rounded-lg transition-colors ${
                  isDarkMode
                    ? 'border-slate-600 hover:bg-slate-700'
                    : 'border-gray-300 hover:bg-gray-50'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                Cancel
              </button>
              <button
                onClick={executeBulkAction}
                disabled={loading || (action !== 'priority' && !reason.trim())}
                className={`px-4 py-2 rounded-lg transition-colors font-medium flex items-center gap-2 ${
                  action === 'delete'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-blue-600 hover:bg-blue-700'
                } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    Confirm {action === 'delete' ? 'Delete' : action === 'enable' ? 'Enable' : action === 'disable' ? 'Disable' : 'Update'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PolicyBulkActions;
