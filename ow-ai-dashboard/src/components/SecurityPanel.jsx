import React, { useEffect, useState } from "react";

const SecurityPanel = ({ getAuthHeaders }) => {
  const [findings, setFindings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    const fetchSecurityFindings = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/security-findings`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch security findings");
        const data = await res.json();
        setFindings(data);
      } catch (err) {
        console.error("Error fetching findings:", err);
        setError("Could not load security insights.");
      } finally {
        setLoading(false);
      }
    };

    fetchSecurityFindings();
  }, [getAuthHeaders]);

  if (loading) return <p className="text-gray-500 text-sm">Loading findings...</p>;
  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!findings) return null;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
      <h2 className="text-2xl font-semibold text-gray-800">Security Insights</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-gray-100 rounded-xl text-center">
          <p className="text-sm text-gray-500">Total Agent Actions</p>
          <p className="text-2xl font-bold text-blue-600">{findings.total_actions}</p>
        </div>
        <div className="p-4 bg-gray-100 rounded-xl text-center">
          <p className="text-sm text-gray-500">Total Alerts</p>
          <p className="text-2xl font-bold text-red-600">{findings.total_alerts}</p>
        </div>
        <div className="p-4 bg-gray-100 rounded-xl text-center">
          <p className="text-sm text-gray-500">High Risk Actions</p>
          <p className="text-2xl font-bold text-orange-500">{findings.risk_distribution.high}</p>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Recent High-Risk Alerts</h3>
        {findings.recent_alerts.length === 0 ? (
          <p className="text-sm text-gray-500">No recent alerts.</p>
        ) : (
          <ul className="space-y-2">
            {findings.recent_alerts.map((alert) => (
              <li
                key={alert.id}
                className="p-3 bg-red-50 border border-red-200 rounded-lg"
              >
                <p className="text-sm text-gray-700">
                  <strong>Agent:</strong> {alert.agent_id}<br />
                  <strong>Action:</strong> {alert.action_type}<br />
                  <strong>Description:</strong> {alert.description}<br />
                  <strong>Risk:</strong> <span className="text-red-600 font-semibold">{alert.risk_level}</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">{new Date(alert.timestamp).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SecurityPanel;