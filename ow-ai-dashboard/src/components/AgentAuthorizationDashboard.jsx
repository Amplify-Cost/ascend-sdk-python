import React, { useState, useEffect } from "react";

const AdvancedAuthorizationDashboard = ({ getAuthHeaders, user }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [selectedAction, setSelectedAction] = useState(null);
  const [approvalMetrics, setApprovalMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("pending");
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [emergencyJustification, setEmergencyJustification] = useState("");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  useEffect(() => {
    fetchDashboardData();
    fetchPendingActions();
    fetchApprovalMetrics();
    
    // Auto-refresh every 30 seconds for real-time updates
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchPendingActions();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/approval-dashboard`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    }
  };

  const fetchPendingActions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/pending-actions`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setPendingActions(data);
      }
      setError(null);
    } catch (err) {
      console.error("Error fetching pending actions:", err);
      setError("Failed to load pending actions");
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovalMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/metrics/approval-performance`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setApprovalMetrics(data);
      }
    } catch (err) {
      console.error("Error fetching metrics:", err);
    }
  };

  const handleApproval = async (actionId, decision, notes = "", conditions = null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/authorize/${actionId}`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          decision: decision,
          notes: notes,
          conditions: conditions,
          approval_duration: conditions?.duration || null
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Approval result:", result);
        
        // Remove action from pending list
        setPendingActions(prev => prev.filter(action => action.id !== actionId));
        setSelectedAction(null);
        
        // Refresh dashboard data
        fetchDashboardData();
        
        alert(`✅ Action ${decision} successfully!`);
      } else {
        const error = await response.json();
        alert(`❌ Failed to ${decision} action: ${error.detail}`);
      }
    } catch (err) {
      console.error(`Error ${decision} action:`, err);
      alert(`❌ Failed to ${decision} action. Please try again.`);
    }
  };

  const handleEmergencyOverride = async (actionId) => {
    if (!emergencyJustification.trim()) {
      alert("Emergency justification is required");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/emergency-override/${actionId}`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ justification: emergencyJustification })
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Emergency override result:", result);
        
        setPendingActions(prev => prev.filter(action => action.id !== actionId));
        setShowEmergencyModal(false);
        setEmergencyJustification("");
        setSelectedAction(null);
        
        alert("🚨 EMERGENCY OVERRIDE GRANTED - This action has been logged for audit");
      } else {
        const error = await response.json();
        alert(`❌ Emergency override failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Emergency override error:", err);
      alert("❌ Emergency override failed. Please try again.");
    }
  };

  const getRiskBadgeColor = (riskScore) => {
    if (riskScore >= 80) return "bg-red-100 text-red-800 border-red-200";
    if (riskScore >= 60) return "bg-orange-100 text-orange-800 border-orange-200";
    if (riskScore >= 40) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-green-100 text-green-800 border-green-200";
  };

  const getWorkflowStageLabel = (stage) => {
    const stages = {
      "initial": "Initial Review",
      "level_1": "Level 1 Approval",
      "level_2": "Level 2 Approval", 
      "level_3": "Executive Approval",
      "emergency_queue": "Emergency Queue"
    };
    return stages[stage] || stage;
  };

  const formatTimeRemaining = (timeString) => {
    if (!timeString) return "No deadline";
    
    const match = timeString.match(/(\d+):(\d+):(\d+)/);
    if (!match) return timeString;
    
    const hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    
    if (hours < 0 || minutes < 0) return "⚠️ OVERDUE";
    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    return `${minutes}m remaining`;
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading Advanced Authorization Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          🛡️ Enterprise Authorization Center
        </h1>
        <p className="text-gray-600">Multi-level approval workflows with emergency procedures</p>
      </div>

      {/* Dashboard Summary Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Pending Actions</h3>
                <p className="text-2xl font-bold">{dashboardData.pending_summary.total_pending}</p>
              </div>
              <div className="text-3xl opacity-80">📋</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Critical Risk</h3>
                <p className="text-2xl font-bold">{dashboardData.pending_summary.critical_pending}</p>
              </div>
              <div className="text-3xl opacity-80">🚨</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Emergency Queue</h3>
                <p className="text-2xl font-bold">{dashboardData.pending_summary.emergency_pending}</p>
              </div>
              <div className="text-3xl opacity-80">⚡</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Your Level</h3>
                <p className="text-2xl font-bold">L{dashboardData.user_info.approval_level}</p>
              </div>
              <div className="text-3xl opacity-80">👤</div>
            </div>
          </div>
        </div>
      )}

      {/* User Authority Info */}
      {dashboardData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-900 mb-2">Your Authorization Authority</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-blue-700 font-medium">Approval Level:</span>
              <span className="ml-2 text-blue-900">Level {dashboardData.user_info.approval_level}</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Max Risk Score:</span>
              <span className="ml-2 text-blue-900">{dashboardData.user_info.max_risk_approval}</span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">Emergency Override:</span>
              <span className="ml-2 text-blue-900">
                {dashboardData.user_info.is_emergency_approver ? "✅ Authorized" : "❌ Not Authorized"}
              </span>
            </div>
            <div>
              <span className="text-blue-700 font-medium">24h Activity:</span>
              <span className="ml-2 text-blue-900">{dashboardData.recent_activity.approvals_last_24h} approvals</span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {["pending", "metrics", "workflows"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab === "pending" && "📋 Pending Actions"}
              {tab === "metrics" && "📊 Performance Metrics"}
              {tab === "workflows" && "⚙️ Workflow Management"}
            </button>
          ))}
        </nav>
      </div>

      {/* Pending Actions Tab */}
      {activeTab === "pending" && (
        <div>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="text-red-800 font-medium">⚠️ Error</div>
              <div className="text-red-600">{error}</div>
            </div>
          )}

          {pendingActions.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Authorizations</h3>
              <p className="text-gray-500">All agent actions have been reviewed. System is secure.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingActions.map((action) => (
                <div key={action.id} className="bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            Agent {action.agent_id}
                          </h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskBadgeColor(action.ai_risk_score)}`}>
                            RISK {action.ai_risk_score}/100
                          </span>
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            {getWorkflowStageLabel(action.workflow_stage)}
                          </span>
                          {action.is_emergency && (
                            <span className="bg-red-500 text-white px-2 py-1 rounded text-xs font-bold animate-pulse">
                              🚨 EMERGENCY
                            </span>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600 mb-3">
                          <div><strong>Action:</strong> {action.action_type}</div>
                          <div><strong>Target:</strong> {action.target_system || 'Unknown'}</div>
                          <div><strong>Approval Level:</strong> {action.current_approval_level}/{action.required_approval_level}</div>
                          <div><strong>Time Remaining:</strong> 
                            <span className={action.time_remaining && action.time_remaining.includes('OVERDUE') ? 'text-red-600 font-bold' : ''}>
                              {formatTimeRemaining(action.time_remaining)}
                            </span>
                          </div>
                        </div>
                        
                        <p className="text-gray-700 mb-3">{action.description}</p>
                        
                        {action.contextual_risk_factors && action.contextual_risk_factors.length > 0 && (
                          <div className="mb-3">
                            <strong className="text-sm text-gray-600">Risk Factors:</strong>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {action.contextual_risk_factors.map((factor, index) => (
                                <span key={index} className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">
                                  {factor}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex flex-col gap-2 ml-4 min-w-0">
                        <button
                          onClick={() => setSelectedAction(action)}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded text-sm transition-colors"
                        >
                          📋 Review Details
                        </button>
                        
                        {action.ai_risk_score <= (dashboardData?.user_info?.max_risk_approval || 50) && (
                          <>
                            <button
                              onClick={() => handleApproval(action.id, 'approved', 'Quick approval')}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              ✅ Approve
                            </button>
                            <button
                              onClick={() => handleApproval(action.id, 'denied', 'Quick denial')}
                              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                              ❌ Deny
                            </button>
                          </>
                        )}
                        
                        {action.required_approval_level > 1 && (
                          <button
                            onClick={() => handleApproval(action.id, 'escalated', 'Escalating to next level', {escalate_to_level: action.current_approval_level + 2})}
                            className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1 rounded text-sm transition-colors"
                          >
                            ⬆️ Escalate
                          </button>
                        )}
                        
                        {dashboardData?.user_info?.is_emergency_approver && (
                          <button
                            onClick={() => {
                              setSelectedAction(action);
                              setShowEmergencyModal(true);
                            }}
                            className="bg-red-800 hover:bg-red-900 text-white px-3 py-1 rounded text-sm transition-colors border-2 border-red-600"
                          >
                            🚨 Emergency Override
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {/* Quick action buttons for high-priority items */}
                    {action.ai_risk_score >= 80 && (
                      <div className="bg-red-50 border border-red-200 rounded p-3 mt-3">
                        <div className="flex items-center justify-between">
                          <div className="text-red-800 font-medium">
                            🚨 CRITICAL RISK ACTION - Immediate attention required
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleApproval(action.id, 'conditional_approved', 'Conditional approval with monitoring', {duration: 60, monitoring: true})}
                              className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-xs"
                            >
                              ⏰ Conditional Approve (1h)
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Performance Metrics Tab */}
      {activeTab === "metrics" && approvalMetrics && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Decision Breakdown */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Decision Breakdown</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Approved:</span>
                  <span className="font-semibold text-green-600">{approvalMetrics.decision_breakdown.approved}</span>
                </div>
                <div className="flex justify-between">
                  <span>Denied:</span>
                  <span className="font-semibold text-red-600">{approvalMetrics.decision_breakdown.denied}</span>
                </div>
                <div className="flex justify-between">
                  <span>Emergency Overrides:</span>
                  <span className="font-semibold text-orange-600">{approvalMetrics.decision_breakdown.emergency_overrides}</span>
                </div>
                <div className="flex justify-between">
                  <span>Approval Rate:</span>
                  <span className="font-semibold">{approvalMetrics.decision_breakdown.approval_rate.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Performance</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Avg Processing Time:</span>
                  <span className="font-semibold">
                    {approvalMetrics.performance_metrics.average_processing_time_minutes 
                      ? `${approvalMetrics.performance_metrics.average_processing_time_minutes} min`
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Risk Score:</span>
                  <span className="font-semibold">{approvalMetrics.performance_metrics.average_risk_score}</span>
                </div>
                <div className="flex justify-between">
                  <span>SLA Compliance:</span>
                  <span className={`font-semibold ${approvalMetrics.performance_metrics.sla_compliance_rate >= 80 ? 'text-green-600' : 'text-red-600'}`}>
                    {approvalMetrics.performance_metrics.sla_compliance_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Risk Analysis */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Risk Analysis</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>High Risk Requests:</span>
                  <span className="font-semibold text-red-600">{approvalMetrics.risk_analysis.high_risk_requests}</span>
                </div>
                <div className="flex justify-between">
                  <span>Emergency Requests:</span>
                  <span className="font-semibold text-orange-600">{approvalMetrics.risk_analysis.emergency_requests}</span>
                </div>
                <div className="flex justify-between">
                  <span>After Hours:</span>
                  <span className="font-semibold">{approvalMetrics.risk_analysis.after_hours_requests}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Period Summary */}
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-2">📈 {approvalMetrics.period_summary.days_analyzed}-Day Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-purple-100">Total Requests:</span>
                <span className="ml-2 text-2xl font-bold">{approvalMetrics.period_summary.total_requests}</span>
              </div>
              <div>
                <span className="text-purple-100">Completion Rate:</span>
                <span className="ml-2 text-2xl font-bold">{approvalMetrics.period_summary.completion_rate.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Management Tab */}
      {activeTab === "workflows" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Approval Workflow Configuration</h3>
            <p className="text-gray-600 mb-4">Configure custom approval workflows based on risk levels and action types.</p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">Current Workflow Rules</h4>
              <div className="space-y-2 text-sm text-blue-800">
                <div>• <strong>Risk 90-100 (Critical):</strong> 3-level approval (Security → Senior → Executive)</div>
                <div>• <strong>Risk 70-89 (High):</strong> 2-level approval (Security → Senior)</div>
                <div>• <strong>Risk 50-69 (Medium):</strong> Dual approval (2 Security staff)</div>
                <div>• <strong>Risk 0-49 (Low):</strong> Single approval</div>
                <div>• <strong>Emergency Override:</strong> Available for authorized personnel</div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-semibold text-yellow-900 mb-2">⚡ Emergency Procedures</h4>
              <div className="text-sm text-yellow-800">
                <p>Emergency overrides are available for critical situations and will:</p>
                <ul className="list-disc list-inside mt-2 ml-4">
                  <li>Immediately approve the action</li>
                  <li>Create high-priority audit alerts</li>
                  <li>Require detailed justification</li>
                  <li>Trigger executive notification</li>
                  <li>Be subject to post-action review</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Review Modal */}
      {selectedAction && !showEmergencyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-semibold">🔍 Authorization Review</h3>
                <button
                  onClick={() => setSelectedAction(null)}
                  className="text-gray-400 hover:text-gray-600 text-3xl"
                >
                  ×
                </button>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column - Basic Info */}
                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Agent Information</h4>
                    <div className="space-y-2 text-sm">
                      <div><strong>Agent ID:</strong> {selectedAction.agent_id}</div>
                      <div><strong>Action Type:</strong> {selectedAction.action_type}</div>
                      <div><strong>Target System:</strong> {selectedAction.target_system || 'Unknown'}</div>
                      <div><strong>Requested:</strong> {new Date(selectedAction.requested_at).toLocaleString()}</div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Risk Assessment</h4>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <strong>Risk Score:</strong>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskBadgeColor(selectedAction.ai_risk_score)}`}>
                          {selectedAction.ai_risk_score}/100
                        </span>
                      </div>
                      <div><strong>Workflow Stage:</strong> {getWorkflowStageLabel(selectedAction.workflow_stage)}</div>
                      <div><strong>Approval Progress:</strong> {selectedAction.current_approval_level}/{selectedAction.required_approval_level}</div>
                    </div>
                  </div>
                </div>

                {/* Right Column - Description & Risk Factors */}
                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Description</h4>
                    <p className="text-sm text-gray-700">{selectedAction.description}</p>
                  </div>

                  {selectedAction.contextual_risk_factors && selectedAction.contextual_risk_factors.length > 0 && (
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2 text-yellow-900">Risk Factors</h4>
                      <div className="space-y-1">
                        {selectedAction.contextual_risk_factors.map((factor, index) => (
                          <div key={index} className="text-sm text-yellow-800">• {factor}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-3 justify-end mt-6 pt-6 border-t">
                <button
                  onClick={() => setSelectedAction(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                
                {selectedAction.ai_risk_score <= (dashboardData?.user_info?.max_risk_approval || 50) && (
                  <>
                    <button
                      onClick={() => handleApproval(selectedAction.id, 'denied', 'Detailed review - denied')}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
                    >
                      ❌ Deny Action
                    </button>
                    <button
                      onClick={() => handleApproval(selectedAction.id, 'conditional_approved', 'Conditional approval with 2-hour limit', {duration: 120})}
                      className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md"
                    >
                      ⏰ Conditional Approve (2h)
                    </button>
                    <button
                      onClick={() => handleApproval(selectedAction.id, 'approved', 'Detailed review - approved')}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md"
                    >
                      ✅ Approve Action
                    </button>
                  </>
                )}
                
                {dashboardData?.user_info?.is_emergency_approver && (
                  <button
                    onClick={() => setShowEmergencyModal(true)}
                    className="px-4 py-2 bg-red-800 hover:bg-red-900 text-white rounded-md border-2 border-red-600"
                  >
                    🚨 Emergency Override
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Emergency Override Modal */}
      {showEmergencyModal && selectedAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">🚨</div>
                <h3 className="text-xl font-bold text-red-900">EMERGENCY OVERRIDE</h3>
                <p className="text-red-700 text-sm mt-2">This action will be logged and audited</p>
              </div>
              
              <div className="bg-red-50 p-4 rounded-lg mb-4">
                <h4 className="font-semibold text-red-900 mb-2">Action Details</h4>
                <div className="text-sm text-red-800">
                  <div><strong>Agent:</strong> {selectedAction.agent_id}</div>
                  <div><strong>Action:</strong> {selectedAction.action_type}</div>
                  <div><strong>Risk Score:</strong> {selectedAction.ai_risk_score}/100</div>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Emergency Justification *
                </label>
                <textarea
                  value={emergencyJustification}
                  onChange={(e) => setEmergencyJustification(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  rows="4"
                  placeholder="Provide detailed justification for emergency override..."
                />
              </div>
              
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => {
                    setShowEmergencyModal(false);
                    setEmergencyJustification("");
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleEmergencyOverride(selectedAction.id)}
                  disabled={!emergencyJustification.trim()}
                  className="px-4 py-2 bg-red-800 hover:bg-red-900 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  🚨 EXECUTE OVERRIDE
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedAuthorizationDashboard;