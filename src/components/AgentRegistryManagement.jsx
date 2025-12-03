import React, { useState, useEffect, useCallback } from "react";
import fetchWithAuth from "../utils/fetchWithAuth";
import AgentHealthDashboard from "./AgentHealthDashboard";

/**
 * Enterprise Agent Registry Management
 * =====================================
 *
 * SEC-024: Enterprise Agent Registration & Governance UI
 *
 * Features:
 * - Register and configure AI agents
 * - Activate/suspend agents with audit trail
 * - Configure risk thresholds and policies
 * - Manage MCP server integrations
 * - View agent versions and rollback
 *
 * Banking-Level Security: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
 */
const AgentRegistryManagement = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState("agents");

  // Agents state
  const [agents, setAgents] = useState([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [agentsError, setAgentsError] = useState(null);

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState([]);
  const [mcpLoading, setMcpLoading] = useState(false);

  // Modal states
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showAgentDetailsModal, setShowAgentDetailsModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMcpRegisterModal, setShowMcpRegisterModal] = useState(false);
  const [showMcpEditModal, setShowMcpEditModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedMcpServer, setSelectedMcpServer] = useState(null);
  const [actionLoading, setActionLoading] = useState(null); // Track which agent/server is being acted upon
  const [mcpEditForm, setMcpEditForm] = useState(null);

  // Form states - Enterprise Agent Configuration
  const [registerForm, setRegisterForm] = useState({
    agent_id: "",
    display_name: "",
    description: "",
    agent_type: "supervised",
    // Risk Configuration
    default_risk_score: 50,
    auto_approve_below: 30,
    max_risk_threshold: 80,
    requires_mfa_above: 70,
    // Permissions & Restrictions (Enterprise)
    allowed_action_types: [],
    allowed_resources: "",      // Comma-separated patterns
    blocked_resources: "",      // Comma-separated patterns
    // Notifications (Enterprise)
    alert_on_high_risk: true,
    alert_recipients: "",       // Comma-separated emails
    webhook_url: "",            // Webhook for external integrations
    // MCP Integration
    is_mcp_server: false,
    mcp_server_url: "",
    // Metadata
    tags: ""
  });

  // Edit form state (populated when editing)
  const [editForm, setEditForm] = useState(null);

  // MCP Server registration form - Enterprise configuration
  const [mcpForm, setMcpForm] = useState({
    server_name: "",
    display_name: "",
    description: "",
    server_url: "",
    transport_type: "stdio",
    governance_enabled: true,
    // Governance Settings
    auto_approve_tools: "",      // Comma-separated tool names
    blocked_tools: "",           // Comma-separated tool names
    tool_risk_overrides: ""      // JSON string for tool-specific risk overrides
  });

  // Action types for multi-select
  const actionTypes = [
    { value: "query", label: "Query" },
    { value: "data_access", label: "Data Access" },
    { value: "data_modification", label: "Data Modification" },
    { value: "transaction", label: "Transaction" },
    { value: "recommendation", label: "Recommendation" },
    { value: "communication", label: "Communication" },
    { value: "report_generation", label: "Report Generation" },
    { value: "data_export", label: "Data Export" },
    { value: "system_operation", label: "System Operation" },
    { value: "security_scan", label: "Security Scan" }
  ];

  // Fetch agents
  const fetchAgents = useCallback(async () => {
    try {
      setAgentsLoading(true);
      setAgentsError(null);
      const response = await fetchWithAuth("/api/registry/agents");
      setAgents(response.agents || []);
    } catch (error) {
      console.error("SEC-024: Failed to fetch agents:", error);
      setAgentsError("Failed to load agents. The Agent Registry service may not be deployed yet.");
    } finally {
      setAgentsLoading(false);
    }
  }, []);

  // Fetch MCP servers
  const fetchMcpServers = useCallback(async () => {
    try {
      setMcpLoading(true);
      const response = await fetchWithAuth("/api/registry/mcp-servers");
      setMcpServers(response.servers || []);
    } catch (error) {
      console.error("SEC-024: Failed to fetch MCP servers:", error);
    } finally {
      setMcpLoading(false);
    }
  }, []);

  // Load data on mount
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (activeTab === "mcp") {
      fetchMcpServers();
    }
  }, [activeTab, fetchMcpServers]);

  // Register new agent - Enterprise payload builder
  const handleRegisterAgent = async (e) => {
    e.preventDefault();
    try {
      // Build enterprise-grade payload
      const payload = {
        agent_id: registerForm.agent_id,
        display_name: registerForm.display_name,
        description: registerForm.description,
        agent_type: registerForm.agent_type,
        // Risk Configuration
        default_risk_score: registerForm.default_risk_score,
        auto_approve_below: registerForm.auto_approve_below,
        max_risk_threshold: registerForm.max_risk_threshold,
        requires_mfa_above: registerForm.requires_mfa_above,
        // Permissions (convert comma-separated to arrays)
        allowed_action_types: registerForm.allowed_action_types,
        allowed_resources: registerForm.allowed_resources.split(",").map(r => r.trim()).filter(Boolean),
        blocked_resources: registerForm.blocked_resources.split(",").map(r => r.trim()).filter(Boolean),
        // Notifications
        alert_on_high_risk: registerForm.alert_on_high_risk,
        alert_recipients: registerForm.alert_recipients.split(",").map(e => e.trim()).filter(Boolean),
        webhook_url: registerForm.webhook_url || null,
        // MCP Integration
        is_mcp_server: registerForm.is_mcp_server,
        mcp_server_url: registerForm.mcp_server_url || null,
        // Metadata
        tags: registerForm.tags.split(",").map(t => t.trim()).filter(Boolean)
      };

      await fetchWithAuth("/api/registry/agents", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      setShowRegisterModal(false);
      // Reset form to defaults
      setRegisterForm({
        agent_id: "",
        display_name: "",
        description: "",
        agent_type: "supervised",
        default_risk_score: 50,
        auto_approve_below: 30,
        max_risk_threshold: 80,
        requires_mfa_above: 70,
        allowed_action_types: [],
        allowed_resources: "",
        blocked_resources: "",
        alert_on_high_risk: true,
        alert_recipients: "",
        webhook_url: "",
        is_mcp_server: false,
        mcp_server_url: "",
        tags: ""
      });
      fetchAgents();
    } catch (error) {
      console.error("Failed to register agent:", error);
      alert("Failed to register agent: " + (error.message || "Unknown error"));
    }
  };

  // Activate agent
  const handleActivateAgent = async (agentId) => {
    try {
      await fetchWithAuth(`/api/registry/agents/${agentId}/activate`, {
        method: "POST"
      });
      fetchAgents();
    } catch (error) {
      console.error("Failed to activate agent:", error);
      alert("Failed to activate agent: " + (error.message || "Unknown error"));
    }
  };

  // Suspend agent
  const handleSuspendAgent = async (agentId) => {
    const reason = prompt("Enter reason for suspension:");
    if (!reason) return;

    try {
      setActionLoading(agentId);
      await fetchWithAuth(`/api/registry/agents/${agentId}/suspend?reason=${encodeURIComponent(reason)}`, {
        method: "POST"
      });
      fetchAgents();
    } catch (error) {
      console.error("Failed to suspend agent:", error);
      alert("Failed to suspend agent: " + (error.message || "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  // Delete agent - requires confirmation
  const handleDeleteAgent = async (agentId, displayName) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the agent "${displayName}"?\n\nThis action cannot be undone and will remove:\n- All agent policies\n- All version history\n- All associated audit records\n\nType DELETE to confirm.`
    );
    if (!confirmed) return;

    const reason = prompt("Enter reason for deletion (required for audit trail):");
    if (!reason) {
      alert("Deletion cancelled - reason is required for audit compliance.");
      return;
    }

    try {
      setActionLoading(agentId);
      await fetchWithAuth(`/api/registry/agents/${agentId}`, {
        method: "DELETE",
        body: JSON.stringify({ reason })
      });
      fetchAgents();
      alert("Agent deleted successfully");
    } catch (error) {
      console.error("Failed to delete agent:", error);
      alert("Failed to delete agent: " + (error.message || "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  // View agent details
  const handleViewAgent = async (agentId) => {
    try {
      const response = await fetchWithAuth(`/api/registry/agents/${agentId}`);
      setSelectedAgent(response.agent);
      setShowAgentDetailsModal(true);
    } catch (error) {
      console.error("Failed to fetch agent details:", error);
    }
  };

  // Edit agent - open modal with current data
  const handleEditAgent = async (agentId) => {
    try {
      const response = await fetchWithAuth(`/api/registry/agents/${agentId}`);
      const agent = response.agent;

      // Populate edit form with current agent data
      setEditForm({
        agent_id: agent.agent_id,
        display_name: agent.display_name,
        description: agent.description || "",
        agent_type: agent.agent_type,
        // Risk Configuration
        default_risk_score: agent.risk_config?.default_risk_score || 50,
        auto_approve_below: agent.risk_config?.auto_approve_below || 30,
        max_risk_threshold: agent.risk_config?.max_risk_threshold || 80,
        requires_mfa_above: agent.risk_config?.requires_mfa_above || 70,
        // Permissions
        allowed_action_types: agent.allowed_action_types || [],
        allowed_resources: (agent.allowed_resources || []).join(", "),
        blocked_resources: (agent.blocked_resources || []).join(", "),
        // Notifications
        alert_on_high_risk: agent.alert_on_high_risk ?? true,
        alert_recipients: (agent.alert_recipients || []).join(", "),
        webhook_url: agent.webhook_url || "",
        // MCP Integration
        is_mcp_server: agent.is_mcp_server || false,
        mcp_server_url: agent.mcp_server_url || "",
        // Metadata
        tags: (agent.tags || []).join(", ")
      });
      setShowEditModal(true);
    } catch (error) {
      console.error("Failed to fetch agent for editing:", error);
      alert("Failed to load agent data: " + (error.message || "Unknown error"));
    }
  };

  // Save edited agent
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editForm) return;

    try {
      const payload = {
        display_name: editForm.display_name,
        description: editForm.description,
        agent_type: editForm.agent_type,
        // Risk Configuration
        default_risk_score: editForm.default_risk_score,
        auto_approve_below: editForm.auto_approve_below,
        max_risk_threshold: editForm.max_risk_threshold,
        requires_mfa_above: editForm.requires_mfa_above,
        // Permissions
        allowed_action_types: editForm.allowed_action_types,
        allowed_resources: editForm.allowed_resources.split(",").map(r => r.trim()).filter(Boolean),
        blocked_resources: editForm.blocked_resources.split(",").map(r => r.trim()).filter(Boolean),
        // Notifications
        alert_on_high_risk: editForm.alert_on_high_risk,
        alert_recipients: editForm.alert_recipients.split(",").map(e => e.trim()).filter(Boolean),
        webhook_url: editForm.webhook_url || null,
        // MCP Integration
        is_mcp_server: editForm.is_mcp_server,
        mcp_server_url: editForm.mcp_server_url || null,
        // Metadata
        tags: editForm.tags.split(",").map(t => t.trim()).filter(Boolean)
      };

      await fetchWithAuth(`/api/registry/agents/${editForm.agent_id}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });

      setShowEditModal(false);
      setEditForm(null);
      fetchAgents();
      alert("Agent updated successfully");
    } catch (error) {
      console.error("Failed to update agent:", error);
      alert("Failed to update agent: " + (error.message || "Unknown error"));
    }
  };

  // Register MCP server - Enterprise configuration
  const handleRegisterMcpServer = async (e) => {
    e.preventDefault();
    try {
      // Build enterprise MCP server payload
      const payload = {
        server_name: mcpForm.server_name,
        display_name: mcpForm.display_name,
        description: mcpForm.description,
        server_url: mcpForm.server_url || null,
        transport_type: mcpForm.transport_type,
        governance_enabled: mcpForm.governance_enabled,
        // Governance Settings
        auto_approve_tools: mcpForm.auto_approve_tools.split(",").map(t => t.trim()).filter(Boolean),
        blocked_tools: mcpForm.blocked_tools.split(",").map(t => t.trim()).filter(Boolean),
        tool_risk_overrides: mcpForm.tool_risk_overrides ? JSON.parse(mcpForm.tool_risk_overrides || "{}") : {}
      };

      await fetchWithAuth("/api/registry/mcp-servers", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      setShowMcpRegisterModal(false);
      setMcpForm({
        server_name: "",
        display_name: "",
        description: "",
        server_url: "",
        transport_type: "stdio",
        governance_enabled: true,
        auto_approve_tools: "",
        blocked_tools: "",
        tool_risk_overrides: ""
      });
      fetchMcpServers();
    } catch (error) {
      console.error("Failed to register MCP server:", error);
      alert("Failed to register MCP server: " + (error.message || "Unknown error"));
    }
  };

  // Edit MCP Server - open modal with current data
  const handleEditMcpServer = (server) => {
    setMcpEditForm({
      id: server.id,
      server_name: server.server_name,
      display_name: server.display_name,
      description: server.description || "",
      server_url: server.server_url || "",
      transport_type: server.transport_type || "stdio",
      governance_enabled: server.governance_enabled ?? true,
      auto_approve_tools: (server.auto_approve_tools || []).join(", "),
      blocked_tools: (server.blocked_tools || []).join(", "),
      tool_risk_overrides: server.tool_risk_overrides ? JSON.stringify(server.tool_risk_overrides) : ""
    });
    setShowMcpEditModal(true);
  };

  // Save edited MCP Server
  const handleSaveMcpEdit = async (e) => {
    e.preventDefault();
    if (!mcpEditForm) return;

    try {
      const payload = {
        display_name: mcpEditForm.display_name,
        description: mcpEditForm.description,
        server_url: mcpEditForm.server_url || null,
        transport_type: mcpEditForm.transport_type,
        governance_enabled: mcpEditForm.governance_enabled,
        auto_approve_tools: mcpEditForm.auto_approve_tools.split(",").map(t => t.trim()).filter(Boolean),
        blocked_tools: mcpEditForm.blocked_tools.split(",").map(t => t.trim()).filter(Boolean),
        tool_risk_overrides: mcpEditForm.tool_risk_overrides ? JSON.parse(mcpEditForm.tool_risk_overrides || "{}") : {}
      };

      await fetchWithAuth(`/api/registry/mcp-servers/${mcpEditForm.server_name}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });

      setShowMcpEditModal(false);
      setMcpEditForm(null);
      fetchMcpServers();
      alert("MCP Server updated successfully");
    } catch (error) {
      console.error("Failed to update MCP server:", error);
      alert("Failed to update MCP server: " + (error.message || "Unknown error"));
    }
  };

  // Activate MCP Server
  const handleActivateMcpServer = async (serverName) => {
    try {
      setActionLoading(serverName);
      await fetchWithAuth(`/api/registry/mcp-servers/${serverName}/activate`, {
        method: "POST"
      });
      fetchMcpServers();
    } catch (error) {
      console.error("Failed to activate MCP server:", error);
      alert("Failed to activate MCP server: " + (error.message || "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  // Deactivate MCP Server
  const handleDeactivateMcpServer = async (serverName) => {
    const reason = prompt("Enter reason for deactivating this MCP server:");
    if (!reason) return;

    try {
      setActionLoading(serverName);
      await fetchWithAuth(`/api/registry/mcp-servers/${serverName}/deactivate?reason=${encodeURIComponent(reason)}`, {
        method: "POST"
      });
      fetchMcpServers();
    } catch (error) {
      console.error("Failed to deactivate MCP server:", error);
      alert("Failed to deactivate MCP server: " + (error.message || "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  // Delete MCP Server
  const handleDeleteMcpServer = async (serverName, displayName) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the MCP server "${displayName}"?\n\nThis action cannot be undone and will remove all associated governance rules.`
    );
    if (!confirmed) return;

    try {
      setActionLoading(serverName);
      await fetchWithAuth(`/api/registry/mcp-servers/${serverName}`, {
        method: "DELETE"
      });
      fetchMcpServers();
      alert("MCP Server deleted successfully");
    } catch (error) {
      console.error("Failed to delete MCP server:", error);
      alert("Failed to delete MCP server: " + (error.message || "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case "active": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case "suspended": return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
      case "draft": return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
      case "pending_approval": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  // Get agent type icon
  const getAgentTypeIcon = (type) => {
    switch (type) {
      case "autonomous": return "🤖";
      case "supervised": return "👁️";
      case "advisory": return "💡";
      case "mcp_server": return "🔌";
      default: return "⚙️";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Agent Registry
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Register and manage AI agents with enterprise governance
          </p>
        </div>
        <div className="flex space-x-2">
          {activeTab === "agents" && (
            <button
              onClick={() => setShowRegisterModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              + Register Agent
            </button>
          )}
          {activeTab === "mcp" && (
            <button
              onClick={() => setShowMcpRegisterModal(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              + Register MCP Server
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("agents")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "agents"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            AI Agents ({agents.length})
          </button>
          <button
            onClick={() => setActiveTab("mcp")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "mcp"
                ? "border-purple-500 text-purple-600 dark:text-purple-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            MCP Servers ({mcpServers.length})
          </button>
          <button
            onClick={() => setActiveTab("sdk")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "sdk"
                ? "border-green-500 text-green-600 dark:text-green-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            SDK Integration
          </button>
          <button
            onClick={() => setActiveTab("health")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "health"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            Health Monitoring
          </button>
        </nav>
      </div>

      {/* Agents Tab */}
      {activeTab === "agents" && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {agentsLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading agents...</p>
            </div>
          ) : agentsError ? (
            <div className="p-8 text-center">
              <div className="text-yellow-600 dark:text-yellow-400 text-5xl mb-4">⚠️</div>
              <p className="text-gray-600 dark:text-gray-400">{agentsError}</p>
              <p className="text-sm text-gray-500 mt-2">
                The Agent Registry backend needs to be deployed first.
              </p>
            </div>
          ) : agents.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-gray-400 text-5xl mb-4">🤖</div>
              <p className="text-gray-600 dark:text-gray-400">No agents registered yet</p>
              <button
                onClick={() => setShowRegisterModal(true)}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
              >
                Register your first agent →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Agent</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Risk Config</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Version</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {agents.map((agent) => (
                    <tr key={agent.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="text-2xl mr-3">{getAgentTypeIcon(agent.agent_type)}</span>
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">{agent.display_name}</div>
                            <div className="text-sm text-gray-500 dark:text-gray-400 font-mono">{agent.agent_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="capitalize text-gray-900 dark:text-white">{agent.agent_type}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(agent.status)}`}>
                          {agent.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <div>Auto: &lt;{agent.auto_approve_below}</div>
                        <div>Max: {agent.max_risk_threshold}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        v{agent.version}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex justify-end space-x-2">
                          {/* View Details */}
                          <button
                            onClick={() => handleViewAgent(agent.agent_id)}
                            className="px-3 py-1 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/30 rounded-md transition-colors"
                            title="View agent details"
                          >
                            View
                          </button>

                          {/* Edit Agent */}
                          <button
                            onClick={() => handleEditAgent(agent.agent_id)}
                            className="px-3 py-1 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 rounded-md transition-colors"
                            title="Edit agent configuration"
                          >
                            Edit
                          </button>

                          {/* Activate - for draft status */}
                          {agent.status === "draft" && (
                            <button
                              onClick={() => handleActivateAgent(agent.agent_id)}
                              disabled={actionLoading === agent.agent_id}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
                              title="Activate this agent for production use"
                            >
                              {actionLoading === agent.agent_id ? "..." : "Activate"}
                            </button>
                          )}

                          {/* Suspend - for active status */}
                          {agent.status === "active" && (
                            <button
                              onClick={() => handleSuspendAgent(agent.agent_id)}
                              disabled={actionLoading === agent.agent_id}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50"
                              title="Suspend agent - requires reason for audit trail"
                            >
                              {actionLoading === agent.agent_id ? "..." : "Suspend"}
                            </button>
                          )}

                          {/* Reactivate - for suspended status */}
                          {agent.status === "suspended" && (
                            <button
                              onClick={() => handleActivateAgent(agent.agent_id)}
                              disabled={actionLoading === agent.agent_id}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
                              title="Reactivate suspended agent"
                            >
                              {actionLoading === agent.agent_id ? "..." : "Reactivate"}
                            </button>
                          )}

                          {/* Delete Agent - always available */}
                          <button
                            onClick={() => handleDeleteAgent(agent.agent_id, agent.display_name)}
                            disabled={actionLoading === agent.agent_id}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50"
                            title="Delete agent permanently - requires confirmation and audit reason"
                          >
                            {actionLoading === agent.agent_id ? "..." : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* MCP Servers Tab */}
      {activeTab === "mcp" && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {mcpLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
            </div>
          ) : mcpServers.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-gray-400 text-5xl mb-4">🔌</div>
              <p className="text-gray-600 dark:text-gray-400">No MCP servers registered</p>
              <button
                onClick={() => setShowMcpRegisterModal(true)}
                className="mt-4 text-purple-600 hover:text-purple-700 font-medium"
              >
                Register your first MCP server →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Server</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Transport</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Governance</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tools</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {mcpServers.map((server) => (
                    <tr key={server.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900 dark:text-white">{server.display_name}</div>
                        <div className="text-sm text-gray-500 font-mono">{server.server_name}</div>
                        {server.server_url && (
                          <div className="text-xs text-gray-400 truncate max-w-xs" title={server.server_url}>
                            {server.server_url}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400 uppercase text-xs">{server.transport_type}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${server.governance_enabled ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400"}`}>
                          {server.governance_enabled ? "Enabled" : "Disabled"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                        {(server.discovered_tools || []).length} tools
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${server.is_active ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"}`}>
                          {server.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex justify-end space-x-2">
                          {/* Edit MCP Server */}
                          <button
                            onClick={() => handleEditMcpServer(server)}
                            className="px-3 py-1 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 rounded-md transition-colors"
                            title="Edit MCP server configuration"
                          >
                            Edit
                          </button>

                          {/* Activate/Deactivate */}
                          {server.is_active ? (
                            <button
                              onClick={() => handleDeactivateMcpServer(server.server_name)}
                              disabled={actionLoading === server.server_name}
                              className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md transition-colors disabled:opacity-50"
                              title="Deactivate MCP server - requires reason"
                            >
                              {actionLoading === server.server_name ? "..." : "Deactivate"}
                            </button>
                          ) : (
                            <button
                              onClick={() => handleActivateMcpServer(server.server_name)}
                              disabled={actionLoading === server.server_name}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors disabled:opacity-50"
                              title="Activate MCP server"
                            >
                              {actionLoading === server.server_name ? "..." : "Activate"}
                            </button>
                          )}

                          {/* Delete MCP Server */}
                          <button
                            onClick={() => handleDeleteMcpServer(server.server_name, server.display_name)}
                            disabled={actionLoading === server.server_name}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50"
                            title="Delete MCP server permanently"
                          >
                            {actionLoading === server.server_name ? "..." : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* SDK Integration Tab */}
      {activeTab === "sdk" && (
        <div className="space-y-6">
          {/* Quick Start */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Start Guide</h3>
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">1. Install the SDK</h4>
                <code className="text-sm text-green-600 dark:text-green-400 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                  pip install owkai-sdk
                </code>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">2. Initialize the Client</h4>
                <pre className="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">
{`from owkai_client import OWKAIClient, AuthorizedAgent

client = OWKAIClient(
    api_key="your-api-key",
    base_url="https://pilot.owkai.app"
)

agent = AuthorizedAgent(
    client=client,
    agent_id="my-agent-001",
    display_name="My AI Agent"
)`}
                </pre>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">3. Request Permission</h4>
                <pre className="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">
{`# Register agent (idempotent)
agent.register()

# Request permission before performing actions
result = agent.request_permission(
    action_type="transaction",
    description="Execute stock purchase",
    risk_score=72,
    resource="trading_system"
)

if result.can_proceed:
    # Execute your action
    execute_trade(result.action_id)`}
                </pre>
              </div>
            </div>
          </div>

          {/* API Endpoints */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">API Endpoints</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Method</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Endpoint</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  <tr>
                    <td className="px-4 py-2"><span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">POST</span></td>
                    <td className="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">/api/sdk/agent-action</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">Submit action for authorization</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2"><span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">GET</span></td>
                    <td className="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">/api/agent-action/status/{'{id}'}</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">Check action status</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2"><span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">POST</span></td>
                    <td className="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">/api/registry/agents</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">Register new agent</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2"><span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">GET</span></td>
                    <td className="px-4 py-2 font-mono text-gray-700 dark:text-gray-300">/api/registry/agents</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">List all agents</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Health Monitoring Tab - SEC-050 */}
      {activeTab === "health" && (
        <AgentHealthDashboard />
      )}

      {/* Register Agent Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Register New Agent</h3>
            </div>
            <form onSubmit={handleRegisterAgent} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Agent ID *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., financial-advisor-001"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={registerForm.agent_id}
                    onChange={(e) => setRegisterForm({ ...registerForm, agent_id: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., Financial Advisor AI"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={registerForm.display_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, display_name: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Describe what this agent does..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={registerForm.description}
                  onChange={(e) => setRegisterForm({ ...registerForm, description: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Agent Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={registerForm.agent_type}
                    onChange={(e) => setRegisterForm({ ...registerForm, agent_type: e.target.value })}
                  >
                    <option value="supervised">Supervised (requires approval)</option>
                    <option value="autonomous">Autonomous (auto-approve low risk)</option>
                    <option value="advisory">Advisory (recommendations only)</option>
                    <option value="mcp_server">MCP Server</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., finance, customer-facing"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={registerForm.tags}
                    onChange={(e) => setRegisterForm({ ...registerForm, tags: e.target.value })}
                  />
                </div>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Risk Configuration</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Auto-Approve Below
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={registerForm.auto_approve_below}
                      onChange={(e) => setRegisterForm({ ...registerForm, auto_approve_below: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Actions with risk below this are auto-approved</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max Risk Threshold
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={registerForm.max_risk_threshold}
                      onChange={(e) => setRegisterForm({ ...registerForm, max_risk_threshold: parseInt(e.target.value) })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Actions above this require escalation</p>
                  </div>
                </div>
              </div>

              {/* Allowed Action Types - Multi-select */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Allowed Action Types</h4>
                <p className="text-xs text-gray-500 mb-2">Select which actions this agent is permitted to perform</p>
                <div className="grid grid-cols-3 gap-2">
                  {actionTypes.map((action) => (
                    <label key={action.value} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={registerForm.allowed_action_types.includes(action.value)}
                        onChange={(e) => {
                          const newTypes = e.target.checked
                            ? [...registerForm.allowed_action_types, action.value]
                            : registerForm.allowed_action_types.filter(t => t !== action.value);
                          setRegisterForm({ ...registerForm, allowed_action_types: newTypes });
                        }}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                      <span className="text-gray-700 dark:text-gray-300">{action.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Resource Restrictions */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Resource Restrictions</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Allowed Resources
                    </label>
                    <input
                      type="text"
                      placeholder="/data/*, /reports/*, /public/*"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={registerForm.allowed_resources}
                      onChange={(e) => setRegisterForm({ ...registerForm, allowed_resources: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Comma-separated glob patterns</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Blocked Resources
                    </label>
                    <input
                      type="text"
                      placeholder="/secrets/*, /prod/*, /admin/*"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={registerForm.blocked_resources}
                      onChange={(e) => setRegisterForm({ ...registerForm, blocked_resources: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Agent cannot access these resources</p>
                  </div>
                </div>
              </div>

              {/* Notifications & Alerts */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Notifications & Webhooks</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="alert_on_high_risk"
                      checked={registerForm.alert_on_high_risk}
                      onChange={(e) => setRegisterForm({ ...registerForm, alert_on_high_risk: e.target.checked })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="alert_on_high_risk" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Generate alerts for high-risk actions
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Alert Recipients (Email)
                    </label>
                    <input
                      type="text"
                      placeholder="security@company.com, admin@company.com"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={registerForm.alert_recipients}
                      onChange={(e) => setRegisterForm({ ...registerForm, alert_recipients: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Comma-separated email addresses for alert notifications</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Webhook URL (Optional)
                    </label>
                    <input
                      type="url"
                      placeholder="https://your-service.com/webhooks/agent-alerts"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={registerForm.webhook_url}
                      onChange={(e) => setRegisterForm({ ...registerForm, webhook_url: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">Send agent events to external systems (Slack, PagerDuty, etc.)</p>
                  </div>
                </div>
              </div>

              {/* MCP Server Integration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">MCP Server Integration</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_mcp_server"
                      checked={registerForm.is_mcp_server}
                      onChange={(e) => setRegisterForm({ ...registerForm, is_mcp_server: e.target.checked })}
                      className="h-4 w-4 text-purple-600 border-gray-300 rounded"
                    />
                    <label htmlFor="is_mcp_server" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      This agent connects to an MCP server
                    </label>
                  </div>
                  {registerForm.is_mcp_server && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        MCP Server URL
                      </label>
                      <input
                        type="url"
                        placeholder="http://localhost:3000 or stdio://mcp-server"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                        value={registerForm.mcp_server_url}
                        onChange={(e) => setRegisterForm({ ...registerForm, mcp_server_url: e.target.value })}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  Register Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Agent Details Modal */}
      {showAgentDetailsModal && selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {getAgentTypeIcon(selectedAgent.agent_type)} {selectedAgent.display_name}
                </h3>
                <p className="text-sm text-gray-500 font-mono">{selectedAgent.agent_id}</p>
              </div>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedAgent.status)}`}>
                {selectedAgent.status}
              </span>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Description</h4>
                <p className="text-gray-600 dark:text-gray-400">{selectedAgent.description || "No description provided"}</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Risk Configuration</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Default Risk Score:</span>
                      <span className="font-medium">{selectedAgent.risk_config?.default_risk_score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Auto-Approve Below:</span>
                      <span className="font-medium text-green-600">&lt;{selectedAgent.risk_config?.auto_approve_below}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Max Risk Threshold:</span>
                      <span className="font-medium text-red-600">{selectedAgent.risk_config?.max_risk_threshold}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">MFA Required Above:</span>
                      <span className="font-medium text-orange-600">{selectedAgent.risk_config?.requires_mfa_above}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Audit Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Version:</span>
                      <span className="font-medium">v{selectedAgent.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Created:</span>
                      <span className="font-medium">{selectedAgent.audit?.created_at ? new Date(selectedAgent.audit.created_at).toLocaleDateString() : "N/A"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Created By:</span>
                      <span className="font-medium">{selectedAgent.audit?.created_by || "N/A"}</span>
                    </div>
                    {selectedAgent.audit?.approved_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Approved By:</span>
                        <span className="font-medium">{selectedAgent.audit.approved_by}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {selectedAgent.tags && selectedAgent.tags.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-between">
              <button
                onClick={() => {
                  setShowAgentDetailsModal(false);
                  handleEditAgent(selectedAgent.agent_id);
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                Edit Agent
              </button>
              <button
                onClick={() => setShowAgentDetailsModal(false)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Agent Modal - Enterprise Configuration */}
      {showEditModal && editForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Edit Agent Configuration</h3>
              <p className="text-sm text-gray-500 font-mono mt-1">{editForm.agent_id}</p>
            </div>
            <form onSubmit={handleSaveEdit} className="p-6 space-y-4">
              {/* Basic Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={editForm.display_name}
                    onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Agent Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={editForm.agent_type}
                    onChange={(e) => setEditForm({ ...editForm, agent_type: e.target.value })}
                  >
                    <option value="supervised">Supervised</option>
                    <option value="autonomous">Autonomous</option>
                    <option value="advisory">Advisory</option>
                    <option value="mcp_server">MCP Server</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
              </div>

              {/* Risk Configuration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Risk Configuration</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Default Risk
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={editForm.default_risk_score}
                      onChange={(e) => setEditForm({ ...editForm, default_risk_score: parseInt(e.target.value) || 50 })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Auto-Approve Below
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={editForm.auto_approve_below}
                      onChange={(e) => setEditForm({ ...editForm, auto_approve_below: parseInt(e.target.value) || 30 })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Max Threshold
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={editForm.max_risk_threshold}
                      onChange={(e) => setEditForm({ ...editForm, max_risk_threshold: parseInt(e.target.value) || 80 })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      MFA Above
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={editForm.requires_mfa_above}
                      onChange={(e) => setEditForm({ ...editForm, requires_mfa_above: parseInt(e.target.value) || 70 })}
                    />
                  </div>
                </div>
              </div>

              {/* Allowed Action Types */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Allowed Action Types</h4>
                <div className="grid grid-cols-3 gap-2">
                  {actionTypes.map((action) => (
                    <label key={action.value} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={editForm.allowed_action_types.includes(action.value)}
                        onChange={(e) => {
                          const newTypes = e.target.checked
                            ? [...editForm.allowed_action_types, action.value]
                            : editForm.allowed_action_types.filter(t => t !== action.value);
                          setEditForm({ ...editForm, allowed_action_types: newTypes });
                        }}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                      <span className="text-gray-700 dark:text-gray-300">{action.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Resource Restrictions */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Resource Restrictions</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Allowed Resources
                    </label>
                    <input
                      type="text"
                      placeholder="/data/*, /reports/*"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={editForm.allowed_resources}
                      onChange={(e) => setEditForm({ ...editForm, allowed_resources: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Blocked Resources
                    </label>
                    <input
                      type="text"
                      placeholder="/secrets/*, /prod/*"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={editForm.blocked_resources}
                      onChange={(e) => setEditForm({ ...editForm, blocked_resources: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Notifications */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Notifications & Webhooks</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="edit_alert_on_high_risk"
                      checked={editForm.alert_on_high_risk}
                      onChange={(e) => setEditForm({ ...editForm, alert_on_high_risk: e.target.checked })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="edit_alert_on_high_risk" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Generate alerts for high-risk actions
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Alert Recipients
                      </label>
                      <input
                        type="text"
                        placeholder="security@company.com"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                        value={editForm.alert_recipients}
                        onChange={(e) => setEditForm({ ...editForm, alert_recipients: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Webhook URL
                      </label>
                      <input
                        type="url"
                        placeholder="https://your-service.com/webhooks"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                        value={editForm.webhook_url}
                        onChange={(e) => setEditForm({ ...editForm, webhook_url: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* MCP Integration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">MCP Server Integration</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="edit_is_mcp_server"
                      checked={editForm.is_mcp_server}
                      onChange={(e) => setEditForm({ ...editForm, is_mcp_server: e.target.checked })}
                      className="h-4 w-4 text-purple-600 border-gray-300 rounded"
                    />
                    <label htmlFor="edit_is_mcp_server" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      This agent connects to an MCP server
                    </label>
                  </div>
                  {editForm.is_mcp_server && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        MCP Server URL
                      </label>
                      <input
                        type="text"
                        placeholder="http://localhost:3000"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                        value={editForm.mcp_server_url}
                        onChange={(e) => setEditForm({ ...editForm, mcp_server_url: e.target.value })}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Tags */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="finance, customer-facing"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={editForm.tags}
                  onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditForm(null);
                  }}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MCP Server Register Modal - Enterprise Configuration */}
      {showMcpRegisterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Register MCP Server</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Configure Model Context Protocol server with enterprise governance
              </p>
            </div>
            <form onSubmit={handleRegisterMcpServer} className="p-6 space-y-4">
              {/* Basic Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Server Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., file-operations"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={mcpForm.server_name}
                    onChange={(e) => setMcpForm({ ...mcpForm, server_name: e.target.value })}
                  />
                  <p className="text-xs text-gray-500 mt-1">Unique identifier for this server</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., File Operations Server"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={mcpForm.display_name}
                    onChange={(e) => setMcpForm({ ...mcpForm, display_name: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Describe what this MCP server provides..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={mcpForm.description}
                  onChange={(e) => setMcpForm({ ...mcpForm, description: e.target.value })}
                />
              </div>

              {/* Connection Configuration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Connection Configuration</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Transport Type
                    </label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      value={mcpForm.transport_type}
                      onChange={(e) => setMcpForm({ ...mcpForm, transport_type: e.target.value })}
                    >
                      <option value="stdio">STDIO (Local process)</option>
                      <option value="http">HTTP/HTTPS</option>
                      <option value="websocket">WebSocket</option>
                      <option value="sse">Server-Sent Events (SSE)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Server URL
                    </label>
                    <input
                      type="text"
                      placeholder="http://localhost:3000 or npx -y @mcp/server"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      value={mcpForm.server_url}
                      onChange={(e) => setMcpForm({ ...mcpForm, server_url: e.target.value })}
                    />
                    <p className="text-xs text-gray-500 mt-1">URL or command to start the server</p>
                  </div>
                </div>
              </div>

              {/* Governance Configuration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Governance Settings</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="governance_enabled"
                      checked={mcpForm.governance_enabled}
                      onChange={(e) => setMcpForm({ ...mcpForm, governance_enabled: e.target.checked })}
                      className="h-4 w-4 text-purple-600 border-gray-300 rounded"
                    />
                    <label htmlFor="governance_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Enable governance for this server (recommended for enterprise)
                    </label>
                  </div>

                  {mcpForm.governance_enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Auto-Approve Tools
                        </label>
                        <input
                          type="text"
                          placeholder="read_file, list_directory, get_status"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                          value={mcpForm.auto_approve_tools}
                          onChange={(e) => setMcpForm({ ...mcpForm, auto_approve_tools: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated list of tools to auto-approve (low-risk operations)</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Blocked Tools
                        </label>
                        <input
                          type="text"
                          placeholder="delete_file, execute_command, drop_table"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                          value={mcpForm.blocked_tools}
                          onChange={(e) => setMcpForm({ ...mcpForm, blocked_tools: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated list of tools to always block (critical security)</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Tool Risk Overrides (JSON)
                        </label>
                        <textarea
                          rows={2}
                          placeholder='{"write_file": 70, "send_email": 60}'
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm font-mono"
                          value={mcpForm.tool_risk_overrides}
                          onChange={(e) => setMcpForm({ ...mcpForm, tool_risk_overrides: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Override default risk scores for specific tools</p>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setShowMcpRegisterModal(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                >
                  Register MCP Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit MCP Server Modal - Enterprise Configuration */}
      {showMcpEditModal && mcpEditForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Edit MCP Server</h3>
              <p className="text-sm text-gray-500 font-mono mt-1">{mcpEditForm.server_name}</p>
            </div>
            <form onSubmit={handleSaveMcpEdit} className="p-6 space-y-4">
              {/* Basic Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={mcpEditForm.display_name}
                    onChange={(e) => setMcpEditForm({ ...mcpEditForm, display_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Transport Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    value={mcpEditForm.transport_type}
                    onChange={(e) => setMcpEditForm({ ...mcpEditForm, transport_type: e.target.value })}
                  >
                    <option value="stdio">STDIO (Local process)</option>
                    <option value="http">HTTP/HTTPS</option>
                    <option value="websocket">WebSocket</option>
                    <option value="sse">Server-Sent Events (SSE)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={mcpEditForm.description}
                  onChange={(e) => setMcpEditForm({ ...mcpEditForm, description: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Server URL
                </label>
                <input
                  type="text"
                  placeholder="http://localhost:3000 or npx -y @mcp/server"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  value={mcpEditForm.server_url}
                  onChange={(e) => setMcpEditForm({ ...mcpEditForm, server_url: e.target.value })}
                />
              </div>

              {/* Governance Configuration */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">Governance Settings</h4>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="edit_governance_enabled"
                      checked={mcpEditForm.governance_enabled}
                      onChange={(e) => setMcpEditForm({ ...mcpEditForm, governance_enabled: e.target.checked })}
                      className="h-4 w-4 text-purple-600 border-gray-300 rounded"
                    />
                    <label htmlFor="edit_governance_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Enable governance for this server
                    </label>
                  </div>

                  {mcpEditForm.governance_enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Auto-Approve Tools
                        </label>
                        <input
                          type="text"
                          placeholder="read_file, list_directory, get_status"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                          value={mcpEditForm.auto_approve_tools}
                          onChange={(e) => setMcpEditForm({ ...mcpEditForm, auto_approve_tools: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated list of tools to auto-approve</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Blocked Tools
                        </label>
                        <input
                          type="text"
                          placeholder="delete_file, execute_command, drop_table"
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                          value={mcpEditForm.blocked_tools}
                          onChange={(e) => setMcpEditForm({ ...mcpEditForm, blocked_tools: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated list of tools to always block</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Tool Risk Overrides (JSON)
                        </label>
                        <textarea
                          rows={2}
                          placeholder='{"write_file": 70, "send_email": 60}'
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm font-mono"
                          value={mcpEditForm.tool_risk_overrides}
                          onChange={(e) => setMcpEditForm({ ...mcpEditForm, tool_risk_overrides: e.target.value })}
                        />
                        <p className="text-xs text-gray-500 mt-1">Override default risk scores for specific tools</p>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => {
                    setShowMcpEditModal(false);
                    setMcpEditForm(null);
                  }}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentRegistryManagement;
