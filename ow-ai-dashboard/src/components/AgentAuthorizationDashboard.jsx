import React, { useState, useEffect } from "react";

const AgentAuthorizationDashboard = ({ getAuthHeaders, user }) => {
  const [pendingActions, setPendingActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAction, setSelectedAction] = useState(null);
  const [reviewNotes, setReviewNotes] = useState("");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  useEffect(() => {
    fetchPendingActions();
    // Refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchPendingActions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPendingActions = async () => {
    try {
      console.log("🔐 Fetching pending actions from:", `${API_BASE_URL}/agent-control/pending-actions`);
      
      const response = await fetch(`${API_BASE_URL}/agent-control/pending-actions`, {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch pending actions: ${response.status}`);
      }

      const data = await response.json();
      console.log("🔐 Pending actions data:", data);
      
      setPendingActions(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      console.error("❌ Error fetching pending actions:", err);
      setError("Failed to load pending actions");
      setPendingActions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorization = async (actionId, decision) => {
    try {
      console.log(`🔐 ${decision === 'approved' ? 'Approving' : 'Denying'} action:`, actionId);
      
      const response = await fetch(`${API_BASE_URL}/agent-control/authorize/${actionId}`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          decision: decision,
          notes: reviewNotes
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to ${decision} action`);
      }

      const result = await response.json();
      console.log("✅ Authorization result:", result);

      // Remove the action from pending list
      setPendingActions(prev => prev.filter(action => action.id !== actionId));
      setSelectedAction(null);
      setReviewNotes("");

      // Show success message
      alert(`✅ Action ${decision} successfully!`);
      
    } catch (err) {
      console.error(`❌ Error ${decision} action:`, err);
      alert(`❌ Failed to ${decision} action. Please try again.`);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading authorization requests...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">🛡️ Agent Authorization Center</h1>
        <p className="text-gray-600">Review and authorize pending agent actions in real-time</p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-800">{pendingActions.length}</div>
            <div className="text-sm text-yellow-600">Pending Actions</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-800">
              {pendingActions.filter(a => a.risk_level === 'high' || a.risk_level === 'critical').length}
            </div>
            <div className="text-sm text-blue-600">High Risk</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-800">Real-time</div>
            <div className="text-sm text-green-600">Monitoring Active</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800 font-medium">⚠️ Error</div>
          <div className="text-red-600">{error}</div>
          <button 
            onClick={fetchPendingActions}
            className="mt-2 text-sm bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded"
          >
            Retry
          </button>
        </div>
      )}

      {pendingActions.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">🎉</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Actions</h3>
          <p className="text-gray-500">All agent actions have been reviewed. The system is secure.</p>
          <button 
            onClick={fetchPendingActions}
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            Refresh
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {pendingActions.map((action) => (
            <div key={action.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Agent {action.agent_id}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(action.risk_level)}`}>
                        {action.risk_level?.toUpperCase() || 'UNKNOWN'} RISK
                      </span>
                      {action.ai_risk_score && (
                        <span className="text-sm text-gray-500">
                          Risk Score: {action.ai_risk_score}/100
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mb-2">
                      <strong>Action:</strong> {action.action_type} | <strong>Requested:</strong> {formatTimeAgo(action.requested_at)}
                    </div>
                    <p className="text-gray-700 mb-3">{action.description || 'No description provided'}</p>
                    
                    {(action.nist_control || action.mitre_tactic) && (
                      <div className="flex gap-4 text-xs">
                        {action.nist_control && (
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            NIST: {action.nist_control}
                          </span>
                        )}
                        {action.mitre_tactic && (
                          <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
                            MITRE: {action.mitre_tactic}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => setSelectedAction(action)}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm transition-colors"
                    >
                      Review
                    </button>
                    <button
                      onClick={() => handleAuthorization(action.id, 'approved')}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors"
                    >
                      ✅ Approve
                    </button>
                    <button
                      onClick={() => handleAuthorization(action.id, 'denied')}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors"
                    >
                      ❌ Deny
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      {selectedAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Review Agent Action</h3>
                <button
                  onClick={() => setSelectedAction(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Agent ID</label>
                    <div className="text-lg font-mono bg-gray-100 p-2 rounded">{selectedAction.agent_id}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Risk Level</label>
                    <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(selectedAction.risk_level)}`}>
                      {selectedAction.risk_level?.toUpperCase()}
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Action Type</label>
                  <div className="text-lg bg-gray-100 p-2 rounded">{selectedAction.action_type}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <div className="bg-gray-100 p-3 rounded">{selectedAction.description || 'No description provided'}</div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Review Notes</label>
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows="3"
                    placeholder="Add your review notes here..."
                  />
                </div>
              </div>
              
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setSelectedAction(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAuthorization(selectedAction.id, 'denied')}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                >
                  ❌ Deny Action
                </button>
                <button
                  onClick={() => handleAuthorization(selectedAction.id, 'approved')}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                >
                  ✅ Approve Action
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentAuthorizationDashboard;