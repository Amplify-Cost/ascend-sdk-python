import React, { useEffect, useState } from "react";

const riskColors = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

const Alerts = ({ getAuthHeaders, user }) => {
  const [alerts, setAlerts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskFilter, setRiskFilter] = useState("all");
  const [toolFilter, setToolFilter] = useState("all");
  const [agentFilter, setAgentFilter] = useState("all");

  const [showModal, setShowModal] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");
  const [summaryResult, setSummaryResult] = useState("");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        console.log("🚨 Fetching alerts from:", `${API_BASE_URL}/api/alerts`);
        const res = await fetch(`${API_BASE_URL}/api/alerts`, {
          credentials: "include",
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch alerts");
        const data = await res.json();
        
        // ✅ DEBUG: Log the actual response
        console.log("🚨 Alerts API Response:", data);
        console.log("🚨 Alerts array length:", Array.isArray(data) ? data.length : "Not an array");
        console.log("🚨 First alert:", Array.isArray(data) && data.length > 0 ? data[0] : "No alerts");
        
        setAlerts(Array.isArray(data) ? data : []);
        setError(null);
      } catch (err) {
        console.error("❌ Alert fetch failed", err);
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
    
    if (riskFilter !== "all") {
      filtered = filtered.filter((a) => a.risk_level === riskFilter);
    }
    if (toolFilter !== "all") {
      filtered = filtered.filter((a) => a.tool_name === toolFilter);
    }
    if (agentFilter !== "all") {
      filtered = filtered.filter((a) => a.agent_id === agentFilter);
    }
    
    setFiltered(filtered);
    console.log("🚨 Filtered alerts:", filtered.length);
  }, [riskFilter, toolFilter, agentFilter, alerts]);

  const updateAlertStatus = async (alertId, status) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, {
        credentials: "include",
        method: "PATCH",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      
      if (!res.ok) throw new Error("Failed to update status");
      
      // Update local state
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, status } : alert
      ));
    } catch (err) {
      console.error("Status update error:", err);
    }
  };

  const handleGenerateSummary = async () => {
    setSummaryLoading(true);
    setSummaryError("");
    setSummaryResult("");
    setShowModal(true);
    
    try {
      const alertTexts = filtered.map(
        (a) =>
          `Agent ${a.agent_id} using ${a.tool_name} triggered: ${a.message} (Risk: ${a.risk_level})`
      );
      const res = await fetch(`${API_BASE_URL}/api/alerts/summary`, {
        credentials: "include",
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ alerts: alertTexts }),
      });
      if (!res.ok) throw new Error("Failed to generate summary");
      const data = await res.json();
      setSummaryResult(data.summary || "No summary returned.");
    } catch (err) {
      console.error(err);
      setSummaryError("Error generating summary. Try again.");
    } finally {
      setSummaryLoading(false);
    }
  };

  // Get unique values for filters
  const uniqueTools = [...new Set(alerts.map(a => a.tool_name))];
  const uniqueAgents = [...new Set(alerts.map(a => a.agent_id))];

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading alerts...</div>;
  }

  if (error) {
    return <div className="p-6 text-center text-red-600">{error}</div>;
  }

  return (
    <div className="bg-white border rounded-2xl shadow-md p-6 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Security Alerts</h2>
        <div className="flex gap-2 flex-wrap">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="border p-2 rounded text-sm"
          >
            <option value="all">All Risks</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={toolFilter}
            onChange={(e) => setToolFilter(e.target.value)}
            className="border p-2 rounded text-sm"
          >
            <option value="all">All Tools</option>
            {uniqueTools.map(tool => (
              <option key={tool} value={tool}>{tool}</option>
            ))}
          </select>
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="border p-2 rounded text-sm"
          >
            <option value="all">All Agents</option>
            {uniqueAgents.map(agent => (
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
        <p>Filtered Alerts: {filtered.length}</p>
        <p>API Response: {alerts.length > 0 ? "Has data" : "Empty array"}</p>
      </div>

      {filtered.length === 0 ? (
        <p className="text-gray-600">No alerts found for this filter.</p>
      ) : (
        <div className="space-y-4">
          {filtered.map((alert) => (
            <div
              key={alert.id}
              className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition duration-150"
            >
              <div className="flex justify-between items-center mb-2">
                <div className="text-sm font-semibold text-gray-700">
                  Agent <span className="text-blue-600">{alert.agent_id}</span> triggered a{" "}
                  <span className="font-bold text-red-600">{alert.risk_level}</span> alert
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${
                      riskColors[alert.status || "new"]
                    }`}
                  >
                    {(alert.status || "new").replace("_", " ")}
                  </span>
                  {["admin", "super_admin"].includes(user?.role) && (
                    <select
                      value={alert.status || "new"}
                      onChange={(e) => updateAlertStatus(alert.id, e.target.value)}
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
                <strong>Recommendation:</strong> {alert.recommendation}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {new Date(alert.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full relative">
            <h3 className="text-lg font-semibold mb-4">🧠 Alert Summary</h3>
            {summaryLoading ? (
              <p className="text-sm text-gray-500">Generating summary...</p>
            ) : summaryError ? (
              <p className="text-sm text-red-600">{summaryError}</p>
            ) : (
              <p className="text-sm text-gray-800 whitespace-pre-wrap">
                {summaryResult}
              </p>
            )}
            <button
              onClick={() => setShowModal(false)}
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

export default Alerts;
