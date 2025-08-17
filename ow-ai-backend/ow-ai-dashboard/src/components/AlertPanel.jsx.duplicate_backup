import React, { useEffect, useState } from "react";

const AlertPanel = ({ getAuthHeaders, user }) => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [summaryError, setSummaryError] = useState("");

  const [riskFilter, setRiskFilter] = useState("all");
  const [toolFilter, setToolFilter] = useState("all");
  const [agentFilter, setAgentFilter] = useState("all");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        console.log("🚨 Fetching alerts from:", `${API_BASE_URL}/alerts`);
        const res = await fetch(`${API_BASE_URL}/alerts`, {
          credentials: "include",
        headers: getAuthHeaders(),
        });
        
        console.log("🚨 Alerts response status:", res.status);
        
        if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`);
        const data = await res.json();
        
        // ✅ DEBUG: Log the actual response
        console.log("🚨 Alerts API Response:", data);
        console.log("🚨 Alerts array length:", Array.isArray(data) ? data.length : "Not an array");
        console.log("🚨 First alert:", Array.isArray(data) && data.length > 0 ? data[0] : "No alerts");
        
        setAlerts(Array.isArray(data) ? data : []);
        setError(null);
      } catch (err) {
        console.error("❌ Error fetching alerts:", err);
        setError("Could not load alerts.");
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, [getAuthHeaders]);

  useEffect(() => {
    let filtered = [...alerts];
    if (riskFilter !== "all") filtered = filtered.filter((a) => a.risk_level === riskFilter);
    if (toolFilter !== "all") filtered = filtered.filter((a) => a.tool_name === toolFilter);
    if (agentFilter !== "all") filtered = filtered.filter((a) => a.agent_id === agentFilter);
    
    console.log("🚨 Filtered alerts:", filtered.length);
    setFilteredAlerts(filtered);
  }, [alerts, riskFilter, toolFilter, agentFilter]);

  const statusColor = (status) => {
    switch (status) {
      case "new": return "bg-yellow-100 text-yellow-800";
      case "in_review": return "bg-blue-100 text-blue-800";
      case "resolved": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const handleGenerateSummary = async () => {
    setSummary("");
    setSummaryError("");
    setSummaryLoading(true);
    setShowSummaryModal(true);
    try {
      const alertTexts = filteredAlerts.map(
        (a) => `Agent ${a.agent_id} using ${a.tool_name} triggered: ${a.message} (Risk: ${a.risk_level})`
      );
      const res = await fetch(`${API_BASE_URL}/alerts/summary`, {
        method: "POST",
        credentials: "include",
        credentials: "include",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ alerts: alertTexts }),
      });
      if (!res.ok) throw new Error("Failed to generate summary");
      const data = await res.json();
      setSummary(data.summary || "No summary returned.");
    } catch (err) {
      console.error(err);
      setSummaryError("Error generating summary. Try again.");
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error("Failed to update status");
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, status: newStatus } : alert
        )
      );
    } catch (err) {
      console.error("Status update error:", err);
    }
  };

  const uniqueAgents = [...new Set(alerts.map((a) => a.agent_id))];
  const uniqueTools = [...new Set(alerts.map((a) => a.tool_name))];

  return (
    <div className="bg-white border rounded-2xl shadow-md p-6 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Security Alerts</h2>
        <div className="flex gap-2 flex-wrap">
          <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className="border p-2 rounded text-sm">
            <option value="all">All Risks</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={toolFilter} onChange={(e) => setToolFilter(e.target.value)} className="border p-2 rounded text-sm">
            <option value="all">All Tools</option>
            {uniqueTools.map((tool) => (
              <option key={tool} value={tool}>{tool}</option>
            ))}
          </select>
          <select value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)} className="border p-2 rounded text-sm">
            <option value="all">All Agents</option>
            {uniqueAgents.map((agent) => (
              <option key={agent} value={agent}>{agent}</option>
            ))}
          </select>
          <button
            onClick={handleGenerateSummary}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700 transition"
          >
            🧠 Generate Summary
          </button>
        </div>
      </div>

      {/* ✅ DEBUG: Show alert counts */}
      <div className="text-xs text-gray-500 bg-gray-100 p-2 rounded mb-4">
        <p>Total Alerts: {alerts.length}</p>
        <p>Filtered Alerts: {filteredAlerts.length}</p>
        <p>API Response: {alerts.length > 0 ? "Has data" : "Empty array"}</p>
        <p>API URL: {API_BASE_URL}/alerts</p>
      </div>

      {loading && <p className="text-sm text-gray-500">Loading alerts...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}
      {!loading && filteredAlerts.length === 0 && !error && (
        <p className="text-gray-600 text-sm">No alerts found for the current filter.</p>
      )}

      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div key={alert.id} className="border rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition duration-150">
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm font-semibold text-gray-700">
                Agent <span className="text-blue-600">{alert.agent_id}</span> triggered a{" "}
                <span className="font-bold text-red-600">{alert.risk_level}</span> alert
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded-full ${statusColor(alert.status)}`}>
                  {(alert.status || "new").replace("_", " ")}
                </span>
                {user?.role === "admin" && (
                  <select
                    value={alert.status || "new"}
                    onChange={(e) => handleStatusChange(alert.id, e.target.value)}
                    className="text-xs border rounded px-2 py-1"
                  >
                    <option value="new">New</option>
                    <option value="in_review">In Review</option>
                    <option value="resolved">Resolved</option>
                  </select>
                )}
              </div>
            </div>
            <div className="text-sm text-gray-700">
              <strong>Action:</strong> {alert.action_type} <br />
              <strong>Tool:</strong> {alert.tool_name} <br />
              <strong>Message:</strong> {alert.message} <br />
              <strong>Recommendation:</strong> {alert.recommendation}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {new Date(alert.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>

      {showSummaryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full relative">
            <h3 className="text-lg font-semibold mb-4">🧠 Alert Summary</h3>
            {summaryLoading ? (
              <p className="text-sm text-gray-500">Generating summary...</p>
            ) : summaryError ? (
              <p className="text-sm text-red-600">{summaryError}</p>
            ) : (
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{summary}</p>
            )}
            <button
              onClick={() => setShowSummaryModal(false)}
              className="absolute top-2 right-3 text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertPanel;