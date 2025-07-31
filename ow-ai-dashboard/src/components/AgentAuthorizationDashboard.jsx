import React, { useState, useEffect } from "react";

const AgentAuthorizationDashboard = ({ getAuthHeaders, user }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [selectedAction, setSelectedAction] = useState(null);
  const [approvalMetrics, setApprovalMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("pending");
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [emergencyJustification, setEmergencyJustification] = useState("");

  // New workflow management state
  const [workflows, setWorkflows] = useState({});
  const [editingWorkflow, setEditingWorkflow] = useState(null);
  const [message, setMessage] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  // Fixed useEffect for real-time updates
  useEffect(() => {
    // Fetch initial data
    fetchPendingActions().then(() => {
      // After pending actions are loaded, update dashboard and metrics
      fetchDashboardData();
      fetchApprovalMetrics();
    });
    
    if (activeTab === "workflows") {
      fetchWorkflows();
    }
        
    // Real-time refresh every 15 seconds for more responsive updates
    const interval = setInterval(() => {
      fetchPendingActions().then(() => {
        fetchDashboardData();
        fetchApprovalMetrics();
      });
      
      if (activeTab === "workflows") {
        fetchWorkflows();
      }
    }, 15000); // Reduced from 30 seconds to 15 seconds
        
    return () => clearInterval(interval);
  }, [activeTab]);

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

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/approval-dashboard`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        
        // Calculate real-time metrics from pending actions
        const totalPending = pendingActions.length;
        const criticalPending = pendingActions.filter(action => 
          action.ai_risk_score >= 80 || action.risk_level === "high"
        ).length;
        const emergencyPending = pendingActions.filter(action => 
          action.is_emergency || action.ai_risk_score >= 90
        ).length;
        
        // Override static numbers with real-time calculations
        const enhancedData = {
          ...data,
          pending_summary: {
            total_pending: totalPending,
            critical_pending: criticalPending,
            emergency_pending: emergencyPending
          },
          enterprise_metrics: {
            ...data.enterprise_metrics,
            total_pending: totalPending,
            critical_pending: criticalPending,
            high_risk_pending: pendingActions.filter(action => 
              action.ai_risk_score >= 70
            ).length,
            emergency_pending: emergencyPending,
            overdue_count: pendingActions.filter(action => 
              action.time_remaining && action.time_remaining.includes('OVERDUE')
            ).length,
            escalated_count: pendingActions.filter(action => 
              action.current_approval_level > 0
            ).length
          }
        };
        
        setDashboardData(enhancedData);
        console.log("📊 Real-time dashboard data updated:", enhancedData);
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    }
  };

  const fetchApprovalMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/metrics/approval-performance`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        
        // Add real-time calculations for better accuracy
        const totalActions = data.decision_breakdown.approved + 
                            data.decision_breakdown.denied + 
                            data.decision_breakdown.pending;
        
        const realTimeApprovalRate = totalActions > 0 
          ? (data.decision_breakdown.approved / totalActions * 100)
          : 0;
        
        // Calculate real-time processing metrics
        const currentPendingCount = pendingActions.length;
        const avgRiskScore = pendingActions.length > 0 
          ? Math.round(pendingActions.reduce((sum, action) => sum + action.ai_risk_score, 0) / pendingActions.length)
          : data.performance_metrics.average_risk_score;
        
        const enhancedMetrics = {
          ...data,
          decision_breakdown: {
            ...data.decision_breakdown,
            approval_rate: realTimeApprovalRate,
            pending: currentPendingCount
          },
          performance_metrics: {
            ...data.performance_metrics,
            average_risk_score: avgRiskScore,
            current_pending_count: currentPendingCount
          },
          risk_analysis: {
            ...data.risk_analysis,
            current_high_risk: pendingActions.filter(action => action.ai_risk_score >= 70).length,
            current_critical_risk: pendingActions.filter(action => action.ai_risk_score >= 90).length
          },
          real_time_stats: {
            last_updated: new Date().toISOString(),
            live_pending_count: currentPendingCount,
            live_high_risk_count: pendingActions.filter(action => action.ai_risk_score >= 70).length,
            live_critical_count: pendingActions.filter(action => action.ai_risk_score >= 90).length,
            actions_requiring_escalation: pendingActions.filter(action => 
              action.required_approval_level > action.current_approval_level + 1
            ).length
          }
        };
        
        setApprovalMetrics(enhancedMetrics);
        console.log("📈 Real-time metrics updated:", enhancedMetrics);
      }
    } catch (err) {
      console.error("Error fetching metrics:", err);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/workflow-config`, {
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data.workflows || {});
      }
      setError(null);
    } catch (err) {
      console.error("Error fetching workflows:", err);
      setError("Failed to load workflow configuration");
    }
  };

  const updateWorkflow = async (workflowId, updates) => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-control/workflow-config`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: workflowId,
          updates: updates
        })
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`✅ ${result.message}`);
        fetchWorkflows(); // Refresh data
        setEditingWorkflow(null);
      } else {
        const errorData = await response.json();
        setError(`❌ Failed to update workflow: ${errorData.detail}`);
      }
    } catch (err) {
      console.error("Error updating workflow:", err);
      setError("❌ Failed to update workflow. Please try again.");
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
        console.log("✅ Approval result:", result);
                
        // Remove action from pending list immediately for real-time UI update
        setPendingActions(prev => {
          const updated = prev.filter(action => action.id !== actionId);
          console.log(`📊 Pending actions updated: ${prev.length} → ${updated.length}`);
          return updated;
        });
        
        setSelectedAction(null);
                
        // Immediately update dashboard and metrics with new counts
        setTimeout(() => {
          fetchDashboardData();
          fetchApprovalMetrics();
        }, 100); // Small delay to ensure state update
                
        // Show success message with real-time update confirmation
        setMessage(`✅ Action ${decision} successfully! Metrics updated in real-time.`);
        setTimeout(() => setMessage(null), 3000);
        
      } else {
        const error = await response.json();
        setError(`❌ Failed to ${decision} action: ${error.detail}`);
      }
    } catch (err) {
      console.error(`Error ${decision} action:`, err);
      setError(`❌ Failed to ${decision} action. Please try again.`);
    }
  };

  const handleEmergencyOverride = async (actionId) => {
    if (!emergencyJustification.trim()) {
      setError("Emergency justification is required");
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
        console.log("🚨 Emergency override result:", result);
                
        // Immediate UI updates for real-time feedback
        setPendingActions(prev => {
          const updated = prev.filter(action => action.id !== actionId);
          console.log(`🚨 Emergency override: ${prev.length} → ${updated.length} pending actions`);
          return updated;
        });
        
        setShowEmergencyModal(false);
        setEmergencyJustification("");
        setSelectedAction(null);
                
        // Update metrics to reflect emergency override immediately
        setTimeout(() => {
          fetchApprovalMetrics();
          fetchDashboardData();
        }, 100);
                
        setMessage("🚨 EMERGENCY OVERRIDE GRANTED - Metrics updated in real-time. This action has been logged for audit.");
        setTimeout(() => setMessage(null), 5000);
        
      } else {
        const error = await response.json();
        setError(`❌ Emergency override failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Emergency override error:", err);
      setError("❌ Emergency override failed. Please try again.");
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
      "initial_review": "Initial Review",
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

  // Workflow Editor Component
  const WorkflowEditor = ({ workflowId, workflow, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
      name: workflow.name,
      approval_levels: workflow.approval_levels,
      timeout_hours: workflow.timeout_hours,
      escalation_minutes: workflow.escalation_minutes,
      emergency_override: workflow.emergency_override,
      approvers: workflow.approvers.join(', ')
    });

    const handleSave = () => {
      const updates = {
        ...formData,
        approvers: formData.approvers.split(',').map(email => email.trim()).filter(email => email)
      };
      onSave(workflowId, updates);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-semibold text-gray-900">⚙️ Edit Workflow</h3>
              <button
                onClick={onCancel}
                className="text-gray-400 hover:text-gray-600 text-3xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Required Approval Levels
                </label>
                <select
                  value={formData.approval_levels}
                  onChange={(e) => setFormData({...formData, approval_levels: parseInt(e.target.value)})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={1}>1 Level (Single Approval)</option>
                  <option value={2}>2 Levels (Dual Approval)</option>
                  <option value={3}>3 Levels (Executive Approval)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timeout Hours (Action expires after)
                </label>
                <input
                  type="number"
                  min="1"
                  max="72"
                  value={formData.timeout_hours}
                  onChange={(e) => setFormData({...formData, timeout_hours: parseInt(e.target.value)})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Auto-Escalation Time (minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="1440"
                  value={formData.escalation_minutes}
                  onChange={(e) => setFormData({...formData, escalation_minutes: parseInt(e.target.value)})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={formData.emergency_override}
                    onChange={(e) => setFormData({...formData, emergency_override: e.target.checked})}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    🚨 Enable Emergency Override
                  </span>
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Allows authorized users to bypass approval workflow in critical situations
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Approvers (email addresses, comma-separated)
                </label>
                <textarea
                  value={formData.approvers}
                  onChange={(e) => setFormData({...formData, approvers: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="security@company.com, admin@company.com, executive@company.com"
                />
              </div>

              <div className="flex gap-3 justify-end pt-6 border-t">
                <button
                  onClick={onCancel}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
                >
                  💾 Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const getRiskLevelColor = (workflowId) => {
    if (workflowId === 'risk_90_100') return 'bg-red-100 border-red-300 text-red-800';
    if (workflowId === 'risk_70_89') return 'bg-orange-100 border-orange-300 text-orange-800';
    if (workflowId === 'risk_50_69') return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    return 'bg-green-100 border-green-300 text-green-800';
  };

  const getRiskLevelIcon = (workflowId) => {
    if (workflowId === 'risk_90_100') return '🚨';
    if (workflowId === 'risk_70_89') return '⚠️';
    if (workflowId === 'risk_50_69') return '⚡';
    return '✅';
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

      {/* Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <div className="text-green-800">{message}</div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Pending Actions Tab */}
      {activeTab === "pending" && (
        <div>
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
          {/* Real-Time Status Banner */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-800 font-medium">📊 Live Metrics</span>
              </div>
              <div className="text-sm text-green-700">
                Last Updated: {approvalMetrics.real_time_stats ? 
                  new Date(approvalMetrics.real_time_stats.last_updated).toLocaleTimeString() : 
                  'Loading...'
                }
              </div>
            </div>
          </div>

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

          {/* Live Metrics Display */}
          {approvalMetrics.live_metrics && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h4 className="font-semibold text-blue-900 mb-3">📊 Live Action Tracking</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h5 className="font-medium text-blue-800 mb-2">Demo Actions:</h5>
                  <div className="space-y-1 text-blue-700">
                    <div>Approved: {approvalMetrics.live_metrics.demo_actions.approved}</div>
                    <div>Denied: {approvalMetrics.live_metrics.demo_actions.denied}</div>
                    <div>Emergency: {approvalMetrics.live_metrics.demo_actions.emergency}</div>
                  </div>
                </div>
                <div>
                  <h5 className="font-medium text-blue-800 mb-2">Database Actions:</h5>
                  <div className="space-y-1 text-blue-700">
                    <div>Approved: {approvalMetrics.live_metrics.database_actions.approved}</div>
                    <div>Denied: {approvalMetrics.live_metrics.database_actions.denied}</div>
                    <div>Pending: {approvalMetrics.live_metrics.database_actions.pending}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Interactive Workflow Management Tab */}
      {activeTab === "workflows" && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Interactive Workflow Configuration</h3>
            <p className="text-gray-600 mb-4">
              Configure custom approval workflows based on risk levels and action types. 
              {user?.role === 'admin' ? ' Click "Edit" to modify any workflow.' : ' Admin access required to modify workflows.'}
            </p>
          </div>

          {/* Workflow Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(workflows).map(([workflowId, workflow]) => (
              <div key={workflowId} className={`border-2 rounded-lg p-6 ${getRiskLevelColor(workflowId)}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getRiskLevelIcon(workflowId)}</span>
                    <div>
                      <h4 className="text-lg font-semibold">{workflow.name}</h4>
                      <p className="text-sm opacity-75">Risk Range: {workflowId.replace('risk_', '').replace('_', '-')}</p>
                    </div>
                  </div>

                  {user?.role === 'admin' && (
                    <button
                      onClick={() => setEditingWorkflow({ workflowId, workflow })}
                      className="bg-white bg-opacity-50 hover:bg-opacity-75 text-gray-800 px-3 py-1 rounded text-sm transition-colors"
                    >
                      ✏️ Edit
                    </button>
                  )}
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Approval Levels:</span>
                    <span className="font-semibold">{workflow.approval_levels}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="font-medium">Timeout:</span>
                    <span className="font-semibold">{workflow.timeout_hours}h</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="font-medium">Auto-Escalation:</span>
                    <span className="font-semibold">{workflow.escalation_minutes}m</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="font-medium">Emergency Override:</span>
                    <span className="font-semibold">
                      {workflow.emergency_override ? '✅ Enabled' : '❌ Disabled'}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-current border-opacity-20">
                    <span className="font-medium">Approvers:</span>
                    <div className="mt-1 space-y-1">
                      {workflow.approvers.map((approver, index) => (
                        <div key={index} className="text-xs bg-white bg-opacity-30 px-2 py-1 rounded">
                          👤 {approver}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Emergency Procedures Info */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h4 className="font-semibold text-yellow-900 mb-2">⚡ Emergency Procedures</h4>
            <div className="text-sm text-yellow-800">
              <p className="mb-3">Emergency overrides are available for critical situations and will:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Immediately approve the action</li>
                <li>Create high-priority audit alerts</li>
                <li>Require detailed justification</li>
                <li>Trigger executive notification</li>
                <li>Be subject to post-action review</li>
              </ul>
            </div>
          </div>

          {/* Current Workflow Summary */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h4 className="font-semibold text-blue-900 mb-3">📊 Current Workflow Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-blue-700 font-medium">Total Workflows:</span>
                <span className="ml-2 text-blue-900 font-semibold">{Object.keys(workflows).length}</span>
              </div>
              <div>
                <span className="text-blue-700 font-medium">Emergency Enabled:</span>
                <span className="ml-2 text-blue-900 font-semibold">
                  {Object.values(workflows).some(w => w.emergency_override) ? '✅ Yes' : '❌ No'}
                </span>
              </div>
              <div>
                <span className="text-blue-700 font-medium">Max Approval Levels:</span>
                <span className="ml-2 text-blue-900 font-semibold">
                  {Object.keys(workflows).length > 0 ? Math.max(...Object.values(workflows).map(w => w.approval_levels)) : 0}
                </span>
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

      {/* Workflow Editor Modal */}
      {editingWorkflow && (
        <WorkflowEditor
          workflowId={editingWorkflow.workflowId}
          workflow={editingWorkflow.workflow}
          onSave={updateWorkflow}
          onCancel={() => {
            setEditingWorkflow(null);
            setMessage(null);
            setError(null);
          }}
        />
      )}
    </div>
  );
};

export default AgentAuthorizationDashboard;