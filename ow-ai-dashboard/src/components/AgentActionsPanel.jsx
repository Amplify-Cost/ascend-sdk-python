import React, { useEffect, useState } from "react";

const AgentActionsPanel = ({ getAuthHeaders, user }) => {
  const [agentActions, setAgentActions] = useState([]);
  const [error, setError] = useState(null);
  const [selectedAction, setSelectedAction] = useState(null);
  const [auditLogs, setAuditLogs] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [generatedRule, setGeneratedRule] = useState(null);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editedRule, setEditedRule] = useState({
    condition: "",
    action: "",
    justification: "",
  });
  const [loading, setLoading] = useState(false);

  const actionsPerPage = 5;
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const fetchAgentActions = async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching agent actions...");
      
      const headers = await getAuthHeaders();
      console.log("🔑 Using auth headers:", headers);
      
      const response = await fetch(`${API_BASE_URL}/agent-actions`, {
        headers: headers,
      });
      
      console.log("📡 Agent actions response status:", response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("📦 Agent actions data received:", data);
      
      setAgentActions(data);
      setError(null);
    } catch (err) {
      console.error("❌ Failed to load agent actions:", err);
      setError(`Failed to load agent actions: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateActionStatus = async (id, statusType) => {
    try {
      console.log(`🎯 Starting ${statusType} for action ${id}`);
      setLoading(true);
      
      // Get fresh auth headers
      const headers = await getAuthHeaders();
      console.log("🔑 Auth headers for action:", headers);
      
      const requestUrl = `${API_BASE_URL}/agent-action/${id}/${statusType}`;
      console.log("📡 Making request to:", requestUrl);
      
      const response = await fetch(requestUrl, {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });
      
      console.log(`📊 ${statusType} response status:`, response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log(`✅ ${statusType} successful:`, result);
        
        // Show success message
        alert(`✅ Action ${statusType.replace('-', ' ')} successful!`);
        
        // Refresh the agent actions list
        await fetchAgentActions();
        
      } else {
        const errorText = await response.text();
        console.error(`❌ ${statusType} failed:`, {
          status: response.status,
          statusText: response.statusText,
          errorText: errorText
        });
        
        // More specific error message
        if (response.status === 404) {
          alert(`❌ Agent action not found. It may have been already processed.`);
        } else if (response.status === 403) {
          alert(`❌ Access denied. Admin privileges required for ${statusType}.`);
        } else {
          alert(`❌ Failed to ${statusType.replace("-", " ")} action: ${response.status} - ${errorText}`);
        }
      }
    } catch (err) {
      console.error(`💥 Network error during ${statusType}:`, err);
      alert(`❌ Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateSmartRule = async (action) => {
    try {
      console.log("🤖 Generating smart rule for action:", action);
      setLoading(true);
      
      const headers = await getAuthHeaders();
      
      const res = await fetch(`${API_BASE_URL}/smart-rules/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: JSON.stringify({
          agent_id: action.agent_id,
          action_type: action.action_type,
          description: action.description || "",
        }),
      });
      
      if (res.ok) {
        const rule = await res.json();
        console.log("🎯 Generated rule:", rule);
        setGeneratedRule(rule);
        setEditedRule(rule);
        setShowRuleModal(true);
      } else {
        const errorText = await res.text();
        console.error("❌ Smart rule generation failed:", res.status, errorText);
        alert(`❌ Failed to generate smart rule: ${res.status} - ${errorText}`);
      }
    } catch (err) {
      console.error("💥 Rule generation error:", err);
      alert(`❌ Network error generating smart rule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const approveRule = async () => {
    try {
      console.log("📋 Approving rule:", editedRule);
      setLoading(true);
      
      // Transform the rule data to match your Rule model exactly
      const ruleData = {
        description: editedRule.description || `Smart rule for ${editedRule.action_type || 'agent action'}`,
        condition: editedRule.condition || "default condition",
        action: editedRule.action || "alert_admin", 
        risk_level: editedRule.risk_level || "Medium",
        recommendation: editedRule.recommendation || "Review this action",
        justification: editedRule.justification || "Generated by smart rule system"
      };

      console.log("📤 Sending rule data:", ruleData);

      const headers = await getAuthHeaders();
      
      const res = await fetch(`${API_BASE_URL}/rules`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: JSON.stringify(ruleData),
      });

      const responseText = await res.text();
      console.log("📊 Rule approval response:", res.status, responseText);

      if (res.ok) {
        alert("✅ Rule approved and saved.");
        setShowRuleModal(false);
        setGeneratedRule(null);
      } else {
        console.error("❌ Rule approval failed:", res.status, responseText);
        alert(`❌ Failed to approve rule: ${res.status} - ${responseText}`);
      }
    } catch (err) {
      console.error("💥 Rule approval error:", err);
      alert(`❌ Network error approving rule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Create database records if they don't exist
  const createSampleRecords = async () => {
    try {
      console.log("🏗️ Creating sample database records...");
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/admin/create-sample-agent-actions`, {
        method: 'POST'
      });
      
      const result = await response.json();
      console.log("📦 Sample records result:", result);
      
      if (result.status === 'success') {
        alert("✅ Sample records created! Refreshing data...");
        await fetchAgentActions();
      } else {
        alert(`⚠️ ${result.message}`);
      }
    } catch (err) {
      console.error("❌ Failed to create sample records:", err);
      alert(`❌ Error creating records: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentActions();
  }, []);

  const start = (currentPage - 1) * actionsPerPage;
  const currentActions = agentActions.slice(start, start + actionsPerPage);
  const totalPages = Math.ceil(agentActions.length / actionsPerPage);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Agent Actions</h2>
        <div className="flex gap-2">
          <button
            onClick={createSampleRecords}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? "⏳" : "🏗️"} Create Sample Records
          </button>
          <button
            onClick={fetchAgentActions}
            disabled={loading}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
          >
            {loading ? "⏳" : "🔄"} Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
          ⏳ Loading...
        </div>
      )}

      {currentActions.length === 0 && !loading ? (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          <p>📭 No agent actions found.</p>
          <p className="text-sm mt-2">Click "Create Sample Records" to add test data for the enterprise system.</p>
        </div>
      ) : (
        <>
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-100 text-sm text-left text-gray-700">
                <tr>
                  <th className="p-3">ID</th>
                  <th className="p-3">Agent ID</th>
                  <th className="p-3">Action Type</th>
                  <th className="p-3">Risk Level</th>
                  <th className="p-3">Summary</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentActions.map((action) => (
                  <tr key={action.id} className="border-t hover:bg-gray-50 text-sm">
                    <td className="p-3 font-mono text-blue-600">#{action.id}</td>
                    <td className="p-3">{action.agent_id}</td>
                    <td className="p-3">{action.action_type}</td>
                    <td className="p-3">
                      <span className={`capitalize px-2 py-1 rounded text-xs ${
                        action.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                        action.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {action.risk_level}
                      </span>
                    </td>
                    <td className="p-3 text-gray-700 max-w-xs truncate">
                      {action.summary || <span className="italic text-gray-400">No summary</span>}
                    </td>
                    <td className="p-3">
                      <span className={`capitalize px-2 py-1 rounded text-xs ${
                        action.status === 'approved' ? 'bg-green-100 text-green-800' :
                        action.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        action.status === 'false_positive' ? 'bg-purple-100 text-purple-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {action.status || "pending"}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="flex gap-1 flex-wrap justify-center">
                        <button
                          onClick={() => setSelectedAction(action)}
                          className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          👁️ View
                        </button>
                        
                        {user?.role === "admin" && action.status === "pending" && (
                          <>
                            <button
                              onClick={async () => {
                                console.log(`🎯 Admin clicked approve for action ${action.id}`);
                                await updateActionStatus(action.id, "approve");
                              }}
                              disabled={loading}
                              className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                            >
                              ✅ Approve
                            </button>
                            <button
                              onClick={async () => {
                                console.log(`🎯 Admin clicked reject for action ${action.id}`);
                                await updateActionStatus(action.id, "reject");
                              }}
                              disabled={loading}
                              className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                            >
                              ❌ Reject
                            </button>
                            <button
                              onClick={async () => {
                                console.log(`🎯 Admin clicked false-positive for action ${action.id}`);
                                await updateActionStatus(action.id, "false-positive");
                              }}
                              disabled={loading}
                              className="px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
                            >
                              ⚠️ False Positive
                            </button>
                          </>
                        )}
                        
                        {user?.role === "admin" && (
                          <button
                            onClick={() => generateSmartRule(action)}
                            disabled={loading}
                            className="px-2 py-1 text-xs bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:opacity-50"
                          >
                            🤖 Smart Rule
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between mt-4 items-center">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              className="px-3 py-1 bg-gray-200 text-gray-800 rounded disabled:opacity-50"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages} ({agentActions.length} total actions)
            </span>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="px-3 py-1 bg-gray-200 text-gray-800 rounded disabled:opacity-50"
            >
              Next →
            </button>
          </div>

          {/* Action Details Modal */}
          {selectedAction && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-2xl relative max-h-96 overflow-auto">
                <button
                  onClick={() => setSelectedAction(null)}
                  className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✖
                </button>
                <h3 className="text-xl font-semibold mb-4">🔍 Action Details</h3>
                <div className="bg-gray-100 p-4 rounded overflow-auto max-h-64">
                  <pre className="text-sm whitespace-pre-wrap">
                    {JSON.stringify(selectedAction, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Smart Rule Modal */}
          {showRuleModal && (
            <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded shadow-lg w-full max-w-lg">
                <h3 className="text-lg font-semibold mb-4">🤖 Generated Smart Rule</h3>
                
                <label className="block text-sm mb-1 font-medium">Condition</label>
                <textarea
                  value={editedRule.condition || ""}
                  onChange={(e) => setEditedRule({ ...editedRule, condition: e.target.value })}
                  className="w-full mb-2 p-2 border rounded"
                  rows="3"
                  placeholder="Rule condition logic..."
                />
                
                <label className="block text-sm mb-1 font-medium">Action</label>
                <textarea
                  value={editedRule.action || ""}
                  onChange={(e) => setEditedRule({ ...editedRule, action: e.target.value })}
                  className="w-full mb-2 p-2 border rounded"
                  rows="2"
                  placeholder="Action to take when rule matches..."
                />
                
                <label className="block text-sm mb-1 font-medium">Justification</label>
                <textarea
                  value={editedRule.justification || ""}
                  onChange={(e) => setEditedRule({ ...editedRule, justification: e.target.value })}
                  className="w-full mb-4 p-2 border rounded"
                  rows="3"
                  placeholder="Business justification for this rule..."
                />
                
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowRuleModal(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={approveRule}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? "⏳ Saving..." : "✅ Approve Rule"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Debug Info */}
      {user?.role === "admin" && (
        <div className="mt-6 p-4 bg-gray-100 rounded text-xs">
          <p><strong>🔧 Debug Info:</strong></p>
          <p>API URL: {API_BASE_URL}</p>
          <p>User: {user?.email} ({user?.role})</p>
          <p>Actions loaded: {agentActions.length}</p>
          <p>Current page: {currentPage}/{totalPages}</p>
        </div>
      )}
    </div>
  );
};

export default AgentActionsPanel;