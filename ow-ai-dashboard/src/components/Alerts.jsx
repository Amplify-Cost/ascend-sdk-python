import React, { useEffect, useState } from "react";

const riskColors = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

const Alerts = ({ getAuthHeaders }) => {
  const [alerts, setAlerts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [riskFilter, setRiskFilter] = useState("all");

  const [showModal, setShowModal] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");
  const [summaryResult, setSummaryResult] = useState("");

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch("http://localhost:8000/alerts", {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch alerts");
        const data = await res.json();
        console.log("🔍 Alerts data:", data);
        setAlerts(data);
        setFiltered(data);
      } catch (err) {
        console.error("Alert fetch failed", err);
      }
    };
    fetchAlerts();
  }, [getAuthHeaders]);

  useEffect(() => {
    if (riskFilter === "all") {
      setFiltered(alerts);
    } else {
      setFiltered(alerts.filter((a) => a.risk_level === riskFilter));
    }
  }, [riskFilter, alerts]);

  const handleGenerateSummary = async () => {
    setSummaryLoading(true);
    setSummaryError("");
    setSummaryResult("");
    try {
      const alertTexts = filtered.map(
        (a) =>
          `Agent ${a.agent_id} using ${a.tool_name} triggered: ${a.message} (Risk: ${a.risk_level})`
      );
      const res = await fetch("http://localhost:8000/alerts/summary", {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ alerts: alertTexts }),
      });
      if (!res.ok) throw new Error("Failed to generate summary");
      const data = await res.json();
      setSummaryResult(data.summary);
    } catch (err) {
      setSummaryError("Error generating summary. Try again.");
    } finally {
      setSummaryLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Security Alerts</h2>
        <div className="flex space-x-2">
          <select
            className="border p-2 rounded text-sm"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="all">All Risks</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <button
            onClick={() => {
              setShowModal(true);
              handleGenerateSummary();
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 transition"
          >
            🧠 Generate Summary
          </button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="text-gray-600">No alerts found for this filter.</p>
      ) : (
        <div className="space-y-4">
          {filtered.map((alert) => (
            <div
              key={alert.id}
              className="border border-gray-200 rounded-lg shadow-sm p-4 bg-white"
            >
              <div className="flex items-center justify-between">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    riskColors[alert.risk_level] || "bg-gray-100 text-gray-800"
                  }`}
                >
                  {alert.risk_level?.toUpperCase() || "UNKNOWN"}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="mt-2 text-sm text-gray-800">
                <strong>Agent:</strong> {alert.agent_id} <br />
                <strong>Tool:</strong> {alert.tool_name} <br />
                <strong>Message:</strong> {alert.message}
              </p>
              <div className="mt-2 text-sm text-gray-600 space-y-1">
                <p>
                  <strong>MITRE:</strong> {alert.mitre_tactic} / {alert.mitre_technique}
                </p>
                <p>
                  <strong>NIST:</strong> {alert.nist_control} - {alert.nist_description}
                </p>
                <p>
                  <strong>Recommendation:</strong>{" "}
                  {alert.recommendation || "N/A"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl shadow-xl relative">
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
              className="absolute top-2 right-3 text-gray-400 hover:text-gray-600 text-xl"
            >
              &times;
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Alerts;
