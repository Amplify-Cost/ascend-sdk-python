import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";

const Dashboard = ({ getAuthHeaders }) => {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        console.log("🔍 Fetching dashboard data from:", `${API_BASE_URL}/analytics/trends`);
        const res = await fetch(`${API_BASE_URL}/analytics/trends`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch analytics data");
        const data = await res.json();
        
        // ✅ DEBUG: Log the actual response
        console.log("📊 Dashboard API Response:", data);
        console.log("📊 High risk daily:", data.high_risk_daily);
        console.log("📊 Top agents:", data.top_agents);
        console.log("📊 Top tools:", data.top_tools);
        
        setTrends({
          high_risk_actions_by_day: data.high_risk_daily || [],
          top_agents: data.top_agents || [],
          top_tools: data.top_tools || [],
          enriched_actions: data.enriched_actions || []
        });
        
        // ✅ DEBUG: Log what we set
        console.log("📊 Trends state set to:", {
          high_risk_actions_by_day: data.high_risk_daily || [],
          top_agents: data.top_agents || [],
          top_tools: data.top_tools || [],
          enriched_actions: data.enriched_actions || []
        });
        
      } catch (err) {
        console.error("❌ Dashboard fetch error:", err);
        setError("Failed to load analytics data.");
      } finally {
        setLoading(false);
      }
    };
    fetchTrends();
  }, [getAuthHeaders]);

  if (loading) return <div className="p-4 text-center text-gray-500">Loading analytics...</div>;
  if (error) return <div className="p-4 text-center text-red-600">{error}</div>;
  
  // ✅ DEBUG: Show what data we have
  console.log("📊 Current trends state:", trends);
  console.log("📊 High risk actions length:", trends?.high_risk_actions_by_day?.length);
  
  if (!trends || trends.high_risk_actions_by_day.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        <p>No analytics available yet. Submit agent actions to populate insights.</p>
        <p className="text-xs mt-2">Debug: trends = {JSON.stringify(trends)}</p>
      </div>
    );
  }

  const COLORS = ["#ff6b6b", "#feca57", "#1dd1a1", "#5f27cd", "#48dbfb"];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold">Security Analytics Overview</h2>
      
      {/* ✅ DEBUG: Show data info */}
      <div className="text-xs text-gray-500 bg-gray-100 p-2 rounded">
        <p>High Risk Actions: {trends.high_risk_actions_by_day.length} items</p>
        <p>Top Agents: {trends.top_agents.length} items</p>
        <p>Top Tools: {trends.top_tools.length} items</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* High-Risk Actions Chart */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-bold mb-2">High-Risk Actions (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trends.high_risk_actions_by_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#ff6b6b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Agents */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-bold mb-2">Top Agents</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={trends.top_agents} dataKey="count" nameKey="agent" cx="50%" cy="50%" outerRadius={80} label>
                {trends.top_agents.map((_, index) => (
                  <Cell key={`agent-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Tools */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-bold mb-2">Top Tools</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={trends.top_tools} dataKey="count" nameKey="tool" cx="50%" cy="50%" outerRadius={80} label>
                {trends.top_tools.map((_, index) => (
                  <Cell key={`tool-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Enriched Actions */}
        {trends.enriched_actions && trends.enriched_actions.length > 0 && (
          <div className="bg-white p-4 rounded shadow">
            <h3 className="font-bold mb-2">Latest Enriched Actions</h3>
            <ul className="text-sm divide-y divide-gray-200">
              {trends.enriched_actions.map((action, index) => (
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

export default Dashboard;