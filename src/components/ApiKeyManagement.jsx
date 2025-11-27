import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, Eye, EyeOff, Copy, Check, AlertTriangle, Shield, Clock, Activity } from 'lucide-react';

/**
 * 🏢 SEC-013: Enterprise API Key Management Component
 * Banking-Level Security: PCI-DSS 8.3.1, HIPAA 164.312(d), SOC 2 CC6.1
 *
 * Features:
 * - Generate API keys with SHA-256 hashing
 * - View and revoke keys with audit trail
 * - Usage statistics and analytics
 * - Multi-tenant isolation (organization_id filtering)
 */
const ApiKeyManagement = ({ API_BASE_URL, getAuthHeaders }) => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [generatingKey, setGeneratingKey] = useState(false);
  const [selectedKeyUsage, setSelectedKeyUsage] = useState(null);

  // Form state for new key generation
  const [newKeyForm, setNewKeyForm] = useState({
    name: '',
    description: '',
    expires_in_days: 90
  });

  // Load existing keys on mount
  useEffect(() => {
    loadKeys();
  }, []);

  const loadKeys = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/keys/list`, {
        credentials: 'include',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to load API keys');
      }

      const data = await response.json();
      setKeys(data.keys || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load API keys:', err);
      setError('Failed to load API keys. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateKey = async () => {
    if (!newKeyForm.name.trim()) {
      alert('Please provide a name for the API key');
      return;
    }

    try {
      setGeneratingKey(true);
      const response = await fetch(`${API_BASE_URL}/api/keys/generate`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newKeyForm.name,
          description: newKeyForm.description,
          expires_in_days: newKeyForm.expires_in_days || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate API key');
      }

      const data = await response.json();
      setNewKeyResult(data);
      setShowGenerateForm(false);
      setNewKeyForm({ name: '', description: '', expires_in_days: 90 });
      await loadKeys(); // Refresh the list
    } catch (err) {
      console.error('Failed to generate API key:', err);
      alert(`Failed to generate API key: ${err.message}`);
    } finally {
      setGeneratingKey(false);
    }
  };

  const revokeKey = async (keyId, keyName) => {
    if (!confirm(`Are you sure you want to revoke the API key "${keyName}"?\n\nThis action cannot be undone and any applications using this key will stop working.`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/keys/${keyId}/revoke`, {
        method: 'DELETE',
        credentials: 'include',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to revoke API key');
      }

      await loadKeys(); // Refresh the list
      alert('API key revoked successfully');
    } catch (err) {
      console.error('Failed to revoke API key:', err);
      alert('Failed to revoke API key. Please try again.');
    }
  };

  const loadKeyUsage = async (keyId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/keys/${keyId}/usage`, {
        credentials: 'include',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to load key usage');
      }

      const data = await response.json();
      setSelectedKeyUsage(data);
    } catch (err) {
      console.error('Failed to load key usage:', err);
      alert('Failed to load usage statistics');
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    } catch (err) {
      alert('Failed to copy to clipboard');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-lg font-semibold flex items-center gap-2">
            <Key className="h-5 w-5 text-blue-600" />
            API Key Management
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            Generate and manage API keys for SDK integration. Keys are hashed using SHA-256 for security.
          </p>
        </div>
        <button
          onClick={() => setShowGenerateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Generate New Key
        </button>
      </div>

      {/* Compliance Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h5 className="font-medium text-blue-900">Banking-Level Security</h5>
            <p className="text-sm text-blue-700 mt-1">
              API keys are stored using SHA-256 hashing with random salt. Full audit trail for PCI-DSS 8.3.1 and SOC 2 CC6.1 compliance.
              All key operations are logged with user identity, timestamp, and IP address.
            </p>
          </div>
        </div>
      </div>

      {/* New Key Result (shown only once after generation) */}
      {newKeyResult && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <h5 className="font-bold text-yellow-900 text-lg">Save Your API Key Now!</h5>
              <p className="text-sm text-yellow-800 mt-1 mb-4">
                This is the only time you will see the full API key. Copy it now and store it securely.
              </p>

              <div className="bg-white p-4 rounded-lg border border-yellow-300">
                <label className="block text-xs text-gray-600 mb-1">Your API Key:</label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 p-3 bg-gray-100 rounded font-mono text-sm break-all">
                    {newKeyResult.api_key}
                  </code>
                  <button
                    onClick={() => copyToClipboard(newKeyResult.api_key)}
                    className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                  >
                    {copiedKey ? (
                      <>
                        <Check className="h-4 w-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{newKeyResult.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Expires:</span>
                  <span className="ml-2 font-medium">{formatDate(newKeyResult.expires_at)}</span>
                </div>
              </div>

              <button
                onClick={() => setNewKeyResult(null)}
                className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                I've Saved My Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Key Form */}
      {showGenerateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h5 className="font-semibold mb-4 flex items-center gap-2">
            <Plus className="h-4 w-4 text-green-600" />
            Generate New API Key
          </h5>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Key Name *
              </label>
              <input
                type="text"
                value={newKeyForm.name}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, name: e.target.value })}
                placeholder="e.g., Production SDK Key"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                value={newKeyForm.description}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, description: e.target.value })}
                placeholder="What is this key used for?"
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expiration
              </label>
              <select
                value={newKeyForm.expires_in_days}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, expires_in_days: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
                <option value="">Never expires</option>
              </select>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={generateKey}
                disabled={generatingKey}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
              >
                {generatingKey ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Key className="h-4 w-4" />
                    Generate Key
                  </>
                )}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Key Usage Modal */}
      {selectedKeyUsage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h5 className="font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                API Key Usage: {selectedKeyUsage.key_prefix}...
              </h5>
              <button
                onClick={() => setSelectedKeyUsage(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                &times;
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-700">
                  {selectedKeyUsage.statistics?.total_requests || 0}
                </div>
                <div className="text-sm text-blue-600">Total Requests</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-700">
                  {selectedKeyUsage.statistics?.success_rate || 0}%
                </div>
                <div className="text-sm text-green-600">Success Rate</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-purple-700">
                  {formatDate(selectedKeyUsage.statistics?.last_used_at)}
                </div>
                <div className="text-sm text-purple-600">Last Used</div>
              </div>
            </div>

            {selectedKeyUsage.recent_activity?.length > 0 && (
              <div>
                <h6 className="font-medium mb-2">Recent Activity</h6>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left">Time</th>
                        <th className="px-3 py-2 text-left">Endpoint</th>
                        <th className="px-3 py-2 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedKeyUsage.recent_activity.slice(0, 10).map((activity, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{formatDate(activity.timestamp)}</td>
                          <td className="px-3 py-2 font-mono text-xs">{activity.endpoint}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              activity.status < 400 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {activity.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Existing Keys List */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200">
          <h5 className="font-semibold">Your API Keys ({keys.length})</h5>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">
            Loading API keys...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">
            {error}
            <button onClick={loadKeys} className="ml-2 text-blue-600 hover:underline">
              Retry
            </button>
          </div>
        ) : keys.length === 0 ? (
          <div className="p-8 text-center">
            <Key className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="text-gray-500">No API keys yet</p>
            <p className="text-sm text-gray-400 mt-1">Generate your first API key to integrate with the SDK</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {keys.map((key) => (
              <div key={key.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h6 className="font-medium">{key.name}</h6>
                      {key.is_active ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded">
                          Revoked
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      <code className="bg-gray-100 px-2 py-0.5 rounded font-mono text-xs">
                        {key.key_prefix}...
                      </code>
                    </p>
                    {key.description && (
                      <p className="text-sm text-gray-500 mt-1">{key.description}</p>
                    )}
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Created: {formatDate(key.created_at)}
                      </span>
                      {key.expires_at && (
                        <span className="flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          Expires: {formatDate(key.expires_at)}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        Used: {key.usage_count || 0} times
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => loadKeyUsage(key.id)}
                      className="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded text-sm"
                    >
                      Usage
                    </button>
                    {key.is_active && (
                      <button
                        onClick={() => revokeKey(key.id, key.name)}
                        className="px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm flex items-center gap-1"
                      >
                        <Trash2 className="h-3 w-3" />
                        Revoke
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeyManagement;
