import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";

const SecurityInsights = ({ getAuthHeaders }) => {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        console.log("🔍 Fetching insights from:", `${API_BASE_URL}/analytics/trends`);
        const res = await fetch(`${API_BASE_URL}/analytics/trends`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch insights data");
        const data = await res.json();
        
        console.log("📊 SecurityInsights API Response:", data);
        
        setTrends({
          high_risk_actions_by_day: data.high_risk_actions_by_day || [],
          top_agents: data.top_agents || [],
          top_tools: data.top_tools || [],
          enriched_actions: data.enriched_actions || []
        });
      } catch (err) {
        console.error("SecurityInsights fetch error:", err);
        setError("Failed to load insights data.");
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, [getAuthHeaders]);

  if (loading) {
    return <div className="p-4 text-center text-gray-500">Loading security insights...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-red-600">{error}</div>;
  }

  // ✅ FIX: Check if ANY data exists, not just high_risk_actions_by_day
  const hasAnyData = trends && (
    (trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0) ||
    (trends.top_agents && trends.top_agents.length > 0) ||
    (trends.top_tools && trends.top_tools.length > 0) ||
    (trends.enriched_actions && trends.enriched_actions.length > 0)
  );

  if (!hasAnyData) {
    return (
      <div className="p-4 text-center text-gray-400">
        <p>No insights available yet. Submit more agent actions to populate this view.</p>
        <p className="text-xs mt-2">Debug: {JSON.stringify(trends)}</p>
      </div>
    );
  }

  const COLORS = ["#1dd1a1", "#ff6b6b", "#5f27cd", "#feca57", "#48dbfb"];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold">Security Insights</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Only show High-Risk Trends if data exists */}
        {trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0 && (
          <div className="bg-white p-4 rounded shadow">
            <h3 className="font-bold mb-2">High-Risk Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends.high_risk_actions_by_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#1dd1a1" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Show Most Active Agents if data exists */}
        {trends.top_agents && trends.top_agents.length > 0 && (
          <div className="bg-white p-4 rounded shadow">
            <h3 className="font-bold mb-2">Most Active Agents</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trends.top_agents}
                  dataKey="count"
                  nameKey="agent"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {trends.top_agents.map((_, index) => (
                    <Cell key={`agent-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Show Most Used Tools if data exists */}
        {trends.top_tools && trends.top_tools.length > 0 && (
          <div className="bg-white p-4 rounded shadow">
            <h3 className="font-bold mb-2">Most Used Tools</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trends.top_tools}
                  dataKey="count"
                  nameKey="tool"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {trends.top_tools.map((_, index) => (
                    <Cell key={`tool-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Show Detailed Insights if data exists */}
        {trends.enriched_actions && trends.enriched_actions.length > 0 && (
          <div className="bg-white p-4 rounded shadow col-span-full">
            <h3 className="font-bold mb-2">Detailed Insights on Agent Behavior</h3>
            <ul className="text-sm divide-y divide-gray-200">
              {trends.enriched_actions.slice(0, 5).map((action, index) => (
                <li key={index} className="py-2">
                  <p><strong>Agent:</strong> {action.agent_id}</p>
                  <p><strong>Risk:</strong> {action.risk_level}</p>
                  <p><strong>MITRE:</strong> {action.mitre_tactic}</p>
                  <p><strong>NIST:</strong> {action.nist_control}</p>
                  <p><strong>Recommendation:</strong> {action.recommendation}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityInsights;