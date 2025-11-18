/**
 * 🏢 ENTERPRISE PLAYBOOK VERSION HISTORY
 *
 * Phase 3 Frontend Component
 * Complete version control with rollback, comparison, and audit trail
 *
 * Business Value:
 * - Compliance audit trails (SOX, PCI-DSS)
 * - Rollback capability for failed deployments
 * - Performance comparison across versions
 * - Team collaboration with change tracking
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState, useEffect } from 'react';

const PlaybookVersionHistory = ({ playbook, onClose, getAuthHeaders, API_BASE_URL }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [showRollbackConfirm, setShowRollbackConfirm] = useState(null);
  const [rollbackReason, setRollbackReason] = useState('');

  useEffect(() => {
    fetchVersions();
  }, [playbook.id]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/versions`,
        {
          credentials: 'include',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setVersions(data);
      } else {
        setError('Failed to load version history');
      }
    } catch (err) {
      console.error('Error fetching versions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) {
      alert('Please select exactly 2 versions to compare');
      return;
    }

    try {
      const [versionA, versionB] = selectedVersions.map(id =>
        versions.find(v => v.id === id).version_number
      );

      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/versions/compare?version_a=${versionA}&version_b=${versionB}`,
        {
          credentials: 'include',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setComparison(data);
      }
    } catch (err) {
      console.error('Error comparing versions:', err);
      setError('Failed to compare versions');
    }
  };

  const handleRollback = async (versionId) => {
    if (!rollbackReason || rollbackReason.trim().length < 10) {
      alert('Please provide a detailed rollback reason (minimum 10 characters)');
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/rollback`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            version_id: versionId,
            rollback_reason: rollbackReason
          })
        }
      );

      if (response.ok) {
        alert('✅ Rollback successful! Playbook reverted to selected version.');
        setShowRollbackConfirm(null);
        setRollbackReason('');
        fetchVersions();
      } else {
        const errorData = await response.json();
        alert(`❌ Rollback failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error rolling back:', err);
      alert('❌ Rollback failed: ' + err.message);
    }
  };

  const toggleVersionSelection = (versionId) => {
    if (selectedVersions.includes(versionId)) {
      setSelectedVersions(selectedVersions.filter(id => id !== versionId));
    } else if (selectedVersions.length < 2) {
      setSelectedVersions([...selectedVersions, versionId]);
    } else {
      // Replace oldest selection
      setSelectedVersions([selectedVersions[1], versionId]);
    }
  };

  const getChangeTypeIcon = (changeType) => {
    const icons = {
      CREATE: '🎨',
      UPDATE: '✏️',
      ROLLBACK: '↩️',
      CLONE: '📋'
    };
    return icons[changeType] || '📝';
  };

  const getChangeTypeColor = (changeType) => {
    const colors = {
      CREATE: 'bg-green-100 text-green-800',
      UPDATE: 'bg-blue-100 text-blue-800',
      ROLLBACK: 'bg-orange-100 text-orange-800',
      CLONE: 'bg-purple-100 text-purple-800'
    };
    return colors[changeType] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-2xl font-semibold">📜 Version History</h3>
              <p className="text-sm text-gray-600 mt-1">
                Playbook: <span className="font-medium">{playbook.name}</span> ({playbook.id})
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl"
            >
              ×
            </button>
          </div>

          {/* Action Bar */}
          <div className="flex gap-2">
            <button
              onClick={handleCompareVersions}
              disabled={selectedVersions.length !== 2}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
            >
              🔍 Compare Selected ({selectedVersions.length}/2)
            </button>
            <button
              onClick={() => {
                setComparison(null);
                setSelectedVersions([]);
              }}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 text-sm"
            >
              Clear Selection
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-4">Loading version history...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800">❌ {error}</p>
            </div>
          )}

          {/* Comparison View */}
          {comparison && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-blue-900">
                  🔍 Version Comparison
                </h4>
                <button
                  onClick={() => setComparison(null)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Close
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-white rounded p-3">
                  <p className="text-sm font-medium text-gray-700">Version {comparison.version_a_number}</p>
                  <p className="text-xs text-gray-600">ID: {comparison.version_a_id}</p>
                </div>
                <div className="bg-white rounded p-3">
                  <p className="text-sm font-medium text-gray-700">Version {comparison.version_b_number}</p>
                  <p className="text-xs text-gray-600">ID: {comparison.version_b_id}</p>
                </div>
              </div>

              {/* Differences */}
              {Object.keys(comparison.differences).length > 0 ? (
                <div className="bg-white rounded-lg p-4 space-y-3">
                  <h5 className="font-semibold text-gray-900">Changes Detected:</h5>
                  {Object.entries(comparison.differences).map(([field, change]) => (
                    <div key={field} className="border-l-4 border-orange-400 pl-3">
                      <p className="text-sm font-medium text-gray-900 capitalize">{field.replace('_', ' ')}</p>
                      <div className="grid grid-cols-2 gap-2 mt-1 text-xs">
                        <div className="bg-red-50 p-2 rounded">
                          <p className="text-red-700 font-medium">Before:</p>
                          <p className="text-gray-700">{JSON.stringify(change.before, null, 2).substring(0, 100)}...</p>
                        </div>
                        <div className="bg-green-50 p-2 rounded">
                          <p className="text-green-700 font-medium">After:</p>
                          <p className="text-gray-700">{JSON.stringify(change.after, null, 2).substring(0, 100)}...</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No differences found between versions.</p>
              )}

              {/* Performance Comparison */}
              <div className="bg-white rounded-lg p-4 mt-4">
                <h5 className="font-semibold text-gray-900 mb-3">Performance Comparison:</h5>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-600 mb-2">Version {comparison.version_a_number}</p>
                    <div className="space-y-1 text-sm">
                      <p>Executions: {comparison.performance_comparison.version_a.executions}</p>
                      <p>Success Rate: {comparison.performance_comparison.version_a.success_rate.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 mb-2">Version {comparison.version_b_number}</p>
                    <div className="space-y-1 text-sm">
                      <p>Executions: {comparison.performance_comparison.version_b.executions}</p>
                      <p>Success Rate: {comparison.performance_comparison.version_b.success_rate.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Version Timeline */}
          {!loading && !error && versions.length > 0 && (
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className={`border rounded-lg p-4 transition-all ${
                    version.is_current
                      ? 'border-green-500 bg-green-50'
                      : selectedVersions.includes(version.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    {/* Version Info */}
                    <div className="flex items-start gap-3 flex-1">
                      {/* Selection Checkbox */}
                      <input
                        type="checkbox"
                        checked={selectedVersions.includes(version.id)}
                        onChange={() => toggleVersionSelection(version.id)}
                        className="mt-1 h-4 w-4 text-blue-600 rounded"
                      />

                      <div className="flex-1">
                        {/* Header */}
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-2xl">{getChangeTypeIcon(version.change_type)}</span>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-lg">Version {version.version_number}</h4>
                              {version.version_tag && (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-800 text-xs rounded">
                                  {version.version_tag}
                                </span>
                              )}
                              {version.is_current && (
                                <span className="px-2 py-0.5 bg-green-600 text-white text-xs rounded font-medium">
                                  CURRENT
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">{version.name}</p>
                          </div>
                        </div>

                        {/* Change Info */}
                        <div className="mb-3">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getChangeTypeColor(version.change_type)}`}>
                            {version.change_type}
                          </span>
                          {version.change_summary && (
                            <p className="text-sm text-gray-700 mt-2">{version.change_summary}</p>
                          )}
                        </div>

                        {/* Changed Fields */}
                        {version.changed_fields && version.changed_fields.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs font-medium text-gray-600 mb-1">Changed Fields:</p>
                            <div className="flex flex-wrap gap-1">
                              {version.changed_fields.map((field, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                                  {field}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Performance Metrics */}
                        <div className="grid grid-cols-4 gap-3 text-xs">
                          <div className="bg-white rounded p-2">
                            <p className="text-gray-600">Executions</p>
                            <p className="font-semibold text-lg">{version.execution_count}</p>
                          </div>
                          <div className="bg-white rounded p-2">
                            <p className="text-gray-600">Success</p>
                            <p className="font-semibold text-lg text-green-600">{version.success_count}</p>
                          </div>
                          <div className="bg-white rounded p-2">
                            <p className="text-gray-600">Failures</p>
                            <p className="font-semibold text-lg text-red-600">{version.failure_count}</p>
                          </div>
                          <div className="bg-white rounded p-2">
                            <p className="text-gray-600">Success Rate</p>
                            <p className="font-semibold text-lg">
                              {version.execution_count > 0
                                ? ((version.success_count / version.execution_count) * 100).toFixed(1)
                                : 0}%
                            </p>
                          </div>
                        </div>

                        {/* Metadata */}
                        <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                          <p>Created: {formatDate(version.created_at)}</p>
                          {version.rolled_back_at && (
                            <p className="text-orange-600 font-medium mt-1">
                              ↩️ Rolled back: {formatDate(version.rolled_back_at)} - {version.rollback_reason}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    {!version.is_current && (
                      <button
                        onClick={() => setShowRollbackConfirm(version.id)}
                        className="px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700 text-sm font-medium"
                      >
                        ↩️ Rollback
                      </button>
                    )}
                  </div>

                  {/* Rollback Confirmation */}
                  {showRollbackConfirm === version.id && (
                    <div className="mt-4 pt-4 border-t border-gray-300 bg-orange-50 rounded p-3">
                      <p className="font-semibold text-orange-900 mb-2">⚠️ Confirm Rollback</p>
                      <p className="text-sm text-orange-800 mb-3">
                        This will revert the playbook to version {version.version_number}. This action creates a new version and is fully auditable.
                      </p>
                      <textarea
                        value={rollbackReason}
                        onChange={(e) => setRollbackReason(e.target.value)}
                        placeholder="Enter rollback reason (minimum 10 characters)..."
                        className="w-full px-3 py-2 border border-orange-300 rounded-lg mb-2 text-sm"
                        rows="2"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleRollback(version.id)}
                          disabled={!rollbackReason || rollbackReason.trim().length < 10}
                          className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:bg-gray-300 text-sm font-medium"
                        >
                          Confirm Rollback
                        </button>
                        <button
                          onClick={() => {
                            setShowRollbackConfirm(null);
                            setRollbackReason('');
                          }}
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-100 text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {!loading && !error && versions.length === 0 && (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600">No version history available yet</p>
              <p className="text-sm text-gray-500 mt-2">Versions will appear here after playbook updates</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-600">
              💡 <strong>Tip:</strong> Select 2 versions to compare changes and performance
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaybookVersionHistory;
