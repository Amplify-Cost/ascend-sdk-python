import React, { useState, useEffect } from 'react';
import { History, GitBranch, RotateCcw, Eye, Clock } from 'lucide-react';

export const PolicyVersionControl = ({ policyId, API_BASE_URL, getAuthHeaders }) => {
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compareVersions, setCompareVersions] = useState([null, null]);

  useEffect(() => {
    loadVersionHistory();
  }, [policyId]);

  const loadVersionHistory = async () => {
    // Mock data for now - replace with actual API call
    const mockVersions = [
      {
        version: 3,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        created_by: 'admin@enterprise.com',
        changes: 'Updated risk level from medium to high',
        policy_data: { policy_name: 'Production DB Access', risk_level: 'high' }
      },
      {
        version: 2,
        created_at: new Date(Date.now() - 172800000).toISOString(),
        created_by: 'security@enterprise.com',
        changes: 'Added condition for business hours',
        policy_data: { policy_name: 'Production DB Access', risk_level: 'medium' }
      },
      {
        version: 1,
        created_at: new Date(Date.now() - 604800000).toISOString(),
        created_by: 'admin@enterprise.com',
        changes: 'Initial policy creation',
        policy_data: { policy_name: 'Production DB Access', risk_level: 'medium' }
      }
    ];
    setVersions(mockVersions);
  };

  const rollbackToVersion = async (version) => {
    if (!confirm(`Are you sure you want to rollback to version ${version}? This will create a new version.`)) {
      return;
    }
    
    try {
      // API call to rollback
      alert(`Rolled back to version ${version} successfully`);
      loadVersionHistory();
    } catch (error) {
      alert('Rollback failed');
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="h-6 w-6 text-blue-600" />
          <h3 className="text-2xl font-bold">Version History</h3>
        </div>
        <button
          onClick={() => setCompareMode(!compareMode)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
            compareMode 
              ? 'bg-blue-600 text-white' 
              : 'border border-gray-300 hover:bg-gray-50'
          }`}
        >
          <GitBranch className="h-4 w-4" />
          Compare Versions
        </button>
      </div>

      {compareMode ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Select two versions to compare</h4>
          <div className="grid grid-cols-2 gap-4">
            {[0, 1].map(idx => (
              <div key={idx}>
                <label className="block text-sm font-medium mb-2">
                  Version {idx + 1}
                </label>
                <select
                  className="w-full px-3 py-2 border rounded-lg"
                  value={compareVersions[idx] || ''}
                  onChange={e => {
                    const newVersions = [...compareVersions];
                    newVersions[idx] = parseInt(e.target.value);
                    setCompareVersions(newVersions);
                  }}
                >
                  <option value="">Select version...</option>
                  {versions.map(v => (
                    <option key={v.version} value={v.version}>
                      Version {v.version} - {formatTimestamp(v.created_at)}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          {compareVersions[0] && compareVersions[1] && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="font-medium mb-2">Differences:</div>
              <div className="text-sm text-gray-600">
                Version comparison would show here
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {versions.map((version) => (
            <div
              key={version.version}
              className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                      v{version.version}
                    </span>
                    <span className="text-gray-600 text-sm flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {formatTimestamp(version.created_at)}
                    </span>
                  </div>
                  
                  <p className="text-gray-700 mb-2">{version.changes}</p>
                  
                  <div className="text-sm text-gray-600">
                    By: {version.created_by}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => setSelectedVersion(version)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    title="View Details"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  {version.version !== versions[0]?.version && (
                    <button
                      onClick={() => rollbackToVersion(version.version)}
                      className="p-2 text-orange-600 hover:bg-orange-50 rounded"
                      title="Rollback"
                    >
                      <RotateCcw className="h-5 w-5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedVersion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold">Version {selectedVersion.version} Details</h3>
                <button
                  onClick={() => setSelectedVersion(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Created</div>
                  <div className="font-medium">{new Date(selectedVersion.created_at).toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Author</div>
                  <div className="font-medium">{selectedVersion.created_by}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Changes</div>
                  <div className="font-medium">{selectedVersion.changes}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Policy Data</div>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded text-sm overflow-x-auto">
                    {JSON.stringify(selectedVersion.policy_data, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyVersionControl;
