import React, { useEffect, useState } from "react";
import { PolicyDecisionBadge, PolicyFusionDisplay } from './shared/PolicyFusionDisplay';

const AgentActionsPanel = ({ getAuthHeaders, user }) => {
  const [agentActions, setAgentActions] = useState([]);
  const [error, setError] = useState(null);
  const [selectedAction, setSelectedAction] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // 🚀 ENTERPRISE: Fetch live agent actions from database
  const fetchAgentActions = async () => {
    try {
      console.log("🔄 Fetching LIVE agent actions from database...");
      setRefreshing(true);
      
      const headers = await getAuthHeaders();
      console.log("🔑 Using auth headers:", Object.keys(headers));
      
      const response = await fetch(`${API_BASE_URL}/api/v1/actions`, {
        credentials: "include",
        method: "GET",
        headers
      });
      
      console.log("📡 Agent actions response status:", response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log("📦 LIVE agent actions data received:", data);
        setAgentActions(data);
        setError(null);
      } else {
        const errorText = await response.text();
        console.error("❌ Failed to fetch agent actions:", response.status, errorText);
        setError(`Failed to fetch agent actions: ${response.status}`);
      }
    } catch (err) {
      console.error("💥 Network error fetching agent actions:", err);
      setError(`Network error: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  };

  // 🟢 ENTERPRISE: Approve action with live database update
  const updateActionStatus = async (id, statusType) => {
    try {
      console.log(`🎯 ${["admin", "super_admin"].includes(user?.role) ? 'Admin' : 'User'} clicked ${statusType} for action ${id}`);
      console.log(`🎯 Starting ${statusType} for action ${id}`);
      setLoading(true);
      
      const headers = await getAuthHeaders();
      console.log("🔑 Auth headers for action:", Object.keys(headers));
      console.log(`📡 Making request to: ${API_BASE_URL}/agent-action/${id}/${statusType}`);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/actions/${id}/${statusType}`, {
        credentials: "include",
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
        
        // 🚀 ENTERPRISE: Show success message and refresh live data
        alert(`✅ Enterprise Action ${statusType.replace('-', ' ')} successful!\n\nAction ID: ${id}\nProcessed by: ${result.approved_by || result.rejected_by || result.reviewed_by}\nAudit Trail: ${result.enterprise_audit}`);
        
        // Immediately refresh to show live database status
        await fetchAgentActions();
        
      } else {
        const errorData = await response.json().catch(() => ({ message: "Unknown error" }));
        console.error(`❌ ${statusType} failed:`, errorData);
        alert(`❌ Enterprise ${statusType.replace("-", " ")} failed: ${errorData.message || response.status}`);
      }
    } catch (err) {
      console.error(`💥 Network error during ${statusType}:`, err);
      alert(`❌ Network error during ${statusType}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 🏗️ ENTERPRISE: Create enterprise sample records
  const createSampleRecords = async () => {
    try {
      console.log("🏗️ Creating enterprise sample database records...");
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/admin/create-sample-agent-actions-enterprise`, {
        credentials: "include",
        method: 'POST'
      });
      
      const result = await response.json();
      console.log("📦 Enterprise sample records result:", result);
      
      if (result.status === 'success') {
        alert(`✅ Enterprise sample records created!\n\nCreated: ${result.count} actions\nIDs: ${result.action_ids.join(', ')}\nEnterprise Ready: ${result.enterprise_ready}\n\nRefreshing live data...`);
        await fetchAgentActions();
      } else {
        alert(`⚠️ ${result.message}`);
      }
    } catch (err) {
      console.error("❌ Failed to create enterprise sample records:", err);
      alert(`❌ Error creating enterprise records: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 📊 ENTERPRISE: Get enterprise status
  const checkEnterpriseStatus = async () => {
    try {
      console.log("📊 Checking enterprise readiness status...");
      
      const response = await fetch(`${API_BASE_URL}/admin/enterprise-status`);
      const status = await response.json();
      
      console.log("🏢 Enterprise Status:", status);
      
      if (status.enterprise_readiness) {
        alert(`🏢 ENTERPRISE STATUS REPORT\n\nReadiness: ${status.enterprise_readiness}\nDatabase Records: ${status.database_records.agent_actions} actions, ${status.database_records.users} users\nProcessed Actions: ${status.database_records.processed_actions}\nNext Milestone: ${status.next_milestone}\n\nStatus: ${status.status}`);
      }
    } catch (err) {
      console.error("❌ Failed to check enterprise status:", err);
      alert(`❌ Error checking enterprise status: ${err.message}`);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchAgentActions();
  }, []);

  // 🎨 ENTERPRISE: Status badge with live database status
  const getStatusBadge = (action) => {
    const status = action.status?.toLowerCase() || 'pending';
    
    const statusConfig = {
      'approved': { color: 'bg-green-100 text-green-800', icon: '✅', label: 'APPROVED' },
      'rejected': { color: 'bg-red-100 text-red-800', icon: '❌', label: 'REJECTED' },
      'false_positive': { color: 'bg-yellow-100 text-yellow-800', icon: '⚠️', label: 'FALSE POSITIVE' },
      'pending': { color: 'bg-blue-100 text-blue-800', icon: '⏳', label: 'PENDING' }
    };
    
    const config = statusConfig[status] || statusConfig['pending'];
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.icon} {config.label}
      </span>
    );
  };

  // 🎨 ENTERPRISE: Risk level badge
  const getRiskBadge = (riskLevel) => {
    const risk = riskLevel?.toLowerCase() || 'medium';
    const riskConfig = {
      'high': { color: 'bg-red-500 text-white', icon: '🔴' },
      'medium': { color: 'bg-yellow-500 text-white', icon: '🟡' },
      'low': { color: 'bg-green-500 text-white', icon: '🟢' }
    };
    
    const config = riskConfig[risk] || riskConfig['medium'];
    
    return (
      <span className={`px-2 py-1 text-xs font-bold rounded ${config.color}`}>
        {config.icon} {risk.toUpperCase()}
      </span>
    );
  };

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="text-red-600 mb-4">
          <h3 className="font-semibold">❌ Error Loading Agent Actions</h3>
          <p className="text-sm">{error}</p>
        </div>
        <button
          onClick={fetchAgentActions}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm"
        >
          🔄 Retry Loading
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      {/* 🏢 ENTERPRISE HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">
            🛡️ Enterprise Agent Actions
          </h2>
          <p className="text-sm text-gray-600">
            Live database integration • Real-time approval workflows • Enterprise audit trails
          </p>
        </div>
        
        {/* 🔧 ENTERPRISE ADMIN CONTROLS */}
        {["admin", "super_admin"].includes(user?.role) && (
          <div className="flex space-x-2">
            <button
              onClick={checkEnterpriseStatus}
              disabled={loading}
              className="bg-purple-600 text-white px-3 py-1 rounded text-xs hover:bg-purple-700 disabled:opacity-50"
            >
              📊 Enterprise Status
            </button>
            <button
              onClick={createSampleRecords}
              disabled={loading}
              className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700 disabled:opacity-50"
            >
              🏗️ Create Sample Records
            </button>
            <button
              onClick={fetchAgentActions}
              disabled={refreshing}
              className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 disabled:opacity-50"
            >
              {refreshing ? '⏳ Refreshing...' : '🔄 Refresh Live Data'}
            </button>
          </div>
        )}
      </div>

      {/* 📊 ENTERPRISE METRICS BAR */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">{agentActions.length}</div>
            <div className="text-xs text-gray-600">Total Actions</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {agentActions.filter(a => a.status === 'approved').length}
            </div>
            <div className="text-xs text-gray-600">Approved</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {agentActions.filter(a => a.status === 'rejected').length}
            </div>
            <div className="text-xs text-gray-600">Rejected</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-600">
              {agentActions.filter(a => a.status === 'pending').length}
            </div>
            <div className="text-xs text-gray-600">Pending</div>
          </div>
        </div>
      </div>

      {/* 📋 ENTERPRISE ACTIONS TABLE */}
      {agentActions.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-4">
            <div className="text-4xl mb-2">🤖</div>
            <h3 className="font-semibold">No Agent Actions Found</h3>
            <p className="text-sm">Create sample records to get started with enterprise testing</p>
          </div>
          {["admin", "super_admin"].includes(user?.role) && (
            <button
              onClick={createSampleRecords}
              disabled={loading}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? '⏳ Creating...' : '🏗️ Create Enterprise Sample Data'}
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-700">ID</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Agent</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Action Type</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Risk Level</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Policy Decision</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Description</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Reviewed By</th>
                {["admin", "super_admin"].includes(user?.role) && (
                  <th className="px-4 py-3 text-left font-medium text-gray-700">Enterprise Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agentActions.map((action) => (
                <tr key={action.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-blue-600 font-semibold">
                    #{action.id}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{action.agent_id}</div>
                    <div className="text-xs text-gray-500">{action.tool_name}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {action.action_type?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getRiskBadge(action.risk_level)}
                  </td>
                  <td className="px-4 py-3">
                    {action.policy_evaluated ? (
                      <PolicyDecisionBadge decision={action.policy_decision} />
                    ) : (
                      <span className="text-gray-400 text-xs">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(action)}
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <div className="truncate" title={action.description}>
                      {action.description}
                    </div>
                    {action.summary && (
                      <div className="text-xs text-gray-500 truncate" title={action.summary}>
                        {action.summary}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {action.reviewed_by ? (
                      <div>
                        <div className="text-xs font-medium">{action.reviewed_by}</div>
                        {action.reviewed_at && (
                          <div className="text-xs text-gray-500">
                            {new Date(action.reviewed_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-xs">Not reviewed</span>
                    )}
                  </td>
                  {["admin", "super_admin"].includes(user?.role) && (
                    <td className="px-4 py-3">
                      {action.status === 'pending' ? (
                        <div className="flex space-x-1">
                          <button
                            onClick={() => updateActionStatus(action.id, "approve")}
                            disabled={loading}
                            className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                          >
                            {loading ? '⏳' : '✅'} Approve
                          </button>
                          <button
                            onClick={() => updateActionStatus(action.id, "reject")}
                            disabled={loading}
                            className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                          >
                            {loading ? '⏳' : '❌'} Reject
                          </button>
                          <button
                            onClick={() => updateActionStatus(action.id, "false-positive")}
                            disabled={loading}
                            className="px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
                          >
                            {loading ? '⏳' : '⚠️'} False+
                          </button>
                        </div>
                      ) : (
                        <div className="text-xs text-gray-500">
                          ✅ Processed
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 🔍 ENTERPRISE ACTION DETAILS MODAL */}
      {selectedAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                🛡️ Enterprise Action Details - #{selectedAction.id}
              </h3>
              <button
                onClick={() => setSelectedAction(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Agent ID</label>
                  <p className="text-sm text-gray-900">{selectedAction.agent_id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Action Type</label>
                  <p className="text-sm text-gray-900">{selectedAction.action_type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Risk Level</label>
                  <p className="text-sm text-gray-900">{getRiskBadge(selectedAction.risk_level)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className="text-sm text-gray-900">{getStatusBadge(selectedAction)}</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="text-sm text-gray-900">{selectedAction.description}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Enterprise Controls</label>
                <div className="bg-gray-50 p-3 rounded text-xs space-y-1">
                  <p><strong>MITRE Tactic:</strong> {selectedAction.mitre_tactic}</p>
                  <p><strong>MITRE Technique:</strong> {selectedAction.mitre_technique}</p>
                  <p><strong>NIST Control:</strong> {selectedAction.nist_control}</p>
                  <p><strong>NIST Description:</strong> {selectedAction.nist_description}</p>
                  <p><strong>Risk Score:</strong> {selectedAction.risk_score}/100</p>
                </div>
              </div>

              {/* Option 4: Policy Fusion Analysis */}
              {selectedAction.policy_evaluated && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Policy Fusion Analysis</label>
                  <PolicyFusionDisplay
                    policyEvaluated={selectedAction.policy_evaluated}
                    policyDecision={selectedAction.policy_decision}
                    policyRiskScore={selectedAction.policy_risk_score}
                    baseRiskScore={selectedAction.risk_score}
                    riskFusionFormula={selectedAction.risk_fusion_formula}
                    variant="detailed"
                  />
                </div>
              )}

              {selectedAction.reviewed_by && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Review Information</label>
                  <div className="bg-green-50 p-3 rounded text-xs">
                    <p><strong>Reviewed By:</strong> {selectedAction.reviewed_by}</p>
                    <p><strong>Reviewed At:</strong> {new Date(selectedAction.reviewed_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedAction(null)}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentActionsPanel;