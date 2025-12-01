import React, { useState, useEffect, useCallback } from "react";
import fetchWithAuth from "../utils/fetchWithAuth";

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
  const [showMcpRegisterModal, setShowMcpRegisterModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);

  // Form states
  const [registerForm, setRegisterForm] = useState({
    agent_id: "",
    display_name: "",
    description: "",
    agent_type: "supervised",
    default_risk_score: 50,
    auto_approve_below: 30,
    max_risk_threshold: 80,
    requires_mfa_above: 70,
    allowed_action_types: [],
    alert_on_high_risk: true,
    tags: ""
  });

  const [mcpForm, setMcpForm] = useState({
    server_name: "",
    display_name: "",
    description: "",
    transport_type: "stdio",
    governance_enabled: true
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

  // Register new agent
  const handleRegisterAgent = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...registerForm,
        tags: registerForm.tags.split(",").map(t => t.trim()).filter(Boolean)
      };

      await fetchWithAuth("/api/registry/agents", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      setShowRegisterModal(false);
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
        alert_on_high_risk: true,
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
      await fetchWithAuth(`/api/registry/agents/${agentId}/suspend?reason=${encodeURIComponent(reason)}`, {
        method: "POST"
      });
      fetchAgents();
    } catch (error) {
      console.error("Failed to suspend agent:", error);
      alert("Failed to suspend agent: " + (error.message || "Unknown error"));
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

  // Register MCP server
  const handleRegisterMcpServer = async (e) => {
    e.preventDefault();
    try {
      await fetchWithAuth("/api/registry/mcp-servers", {
        method: "POST",
        body: JSON.stringify(mcpForm)
      });

      setShowMcpRegisterModal(false);
      setMcpForm({
        server_name: "",
        display_name: "",
        description: "",
        transport_type: "stdio",
        governance_enabled: true
      });
      fetchMcpServers();
    } catch (error) {
      console.error("Failed to register MCP server:", error);
      alert("Failed to register MCP server: " + (error.message || "Unknown error"));
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
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm space-x-2">
                        <button
                          onClick={() => handleViewAgent(agent.agent_id)}
                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                        >
                          View
                        </button>
                        {agent.status === "draft" && (
                          <button
                            onClick={() => handleActivateAgent(agent.agent_id)}
                            className="text-green-600 hover:text-green-800 dark:text-green-400"
                          >
                            Activate
                          </button>
                        )}
                        {agent.status === "active" && (
                          <button
                            onClick={() => handleSuspendAgent(agent.agent_id)}
                            className="text-red-600 hover:text-red-800 dark:text-red-400"
                          >
                            Suspend
                          </button>
                        )}
                        {agent.status === "suspended" && (
                          <button
                            onClick={() => handleActivateAgent(agent.agent_id)}
                            className="text-green-600 hover:text-green-800 dark:text-green-400"
                          >
                            Reactivate
                          </button>
                        )}
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
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {mcpServers.map((server) => (
                    <tr key={server.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900 dark:text-white">{server.display_name}</div>
                        <div className="text-sm text-gray-500 font-mono">{server.server_name}</div>
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">{server.transport_type}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${server.governance_enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                          {server.governance_enabled ? "Enabled" : "Disabled"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                        {(server.discovered_tools || []).length} tools
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${server.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                          {server.is_active ? "Active" : "Inactive"}
                        </span>
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
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
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

      {/* MCP Server Register Modal */}
      {showMcpRegisterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Register MCP Server</h3>
            </div>
            <form onSubmit={handleRegisterMcpServer} className="p-6 space-y-4">
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
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Transport Type
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  value={mcpForm.transport_type}
                  onChange={(e) => setMcpForm({ ...mcpForm, transport_type: e.target.value })}
                >
                  <option value="stdio">STDIO</option>
                  <option value="http">HTTP</option>
                  <option value="websocket">WebSocket</option>
                </select>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="governance_enabled"
                  checked={mcpForm.governance_enabled}
                  onChange={(e) => setMcpForm({ ...mcpForm, governance_enabled: e.target.checked })}
                  className="h-4 w-4 text-purple-600 border-gray-300 rounded"
                />
                <label htmlFor="governance_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable governance for this server
                </label>
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
                  Register Server
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
