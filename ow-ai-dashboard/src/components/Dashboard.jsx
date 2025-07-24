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
    console.log("📊 Loading Dashboard");
    const fetchTrends = async () => {
      try {
        console.log("🔍 Fetching dashboard data from:", `${API_BASE_URL}/analytics/trends`);
        const res = await fetch(`${API_BASE_URL}/analytics/trends`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) throw new Error("Failed to fetch analytics data");
        const data = await res.json();
        
        console.log("📊 Dashboard API Response:", data);
        
        // Use the correct key names from API response
        setTrends({
          high_risk_actions_by_day: data.high_risk_actions_by_day || [],
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

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-500">Loading analytics...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <h3 className="font-bold">Error Loading Dashboard</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  
  // Show dashboard even if high_risk_actions_by_day is empty but other data exists
  const hasAnyData = trends && (
    (trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0) ||
    (trends.top_agents && trends.top_agents.length > 0) ||
    (trends.top_tools && trends.top_tools.length > 0) ||
    (trends.enriched_actions && trends.enriched_actions.length > 0)
  );
  
  if (!hasAnyData) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">🛡️ Security Analytics Dashboard</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="text-blue-600 text-4xl mb-4">📊</div>
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Analytics Dashboard Ready</h3>
          <p className="text-blue-700 mb-4">No analytics data available yet. Submit agent actions to populate insights.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div className="bg-white p-4 rounded border">
              <h4 className="font-semibold text-gray-900">🎯 Quick Start</h4>
              <p className="text-sm text-gray-600 mt-2">
                1. Submit agent actions via "Submit Action" tab<br/>
                2. Review alerts in "Alerts" tab<br/>
                3. Generate smart rules<br/>
                4. View analytics here
              </p>
            </div>
            <div className="bg-white p-4 rounded border">
              <h4 className="font-semibold text-gray-900">📈 What You'll See</h4>
              <p className="text-sm text-gray-600 mt-2">
                • High-risk action trends<br/>
                • Top agents and tools<br/>
                • NIST/MITRE compliance data<br/>
                • Security recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">🛡️ Security Analytics Dashboard</h2>
        <div className="text-sm text-gray-500">
          Real-time security monitoring • Enterprise-grade analytics
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High-Risk Actions Chart - Only show if data exists */}
        {trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 High-Risk Actions (Last 7 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends.high_risk_actions_by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
                <YAxis allowDecimals={false} stroke="#6b7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Agents - Show if data exists */}
        {trends.top_agents && trends.top_agents.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🤖 Top Active Agents</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie 
                  data={trends.top_agents} 
                  dataKey="count" 
                  nameKey="agent" 
                  cx="50%" 
                  cy="50%" 
                  outerRadius={80} 
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
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

        {/* Top Tools - Show if data exists */}
        {trends.top_tools && trends.top_tools.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🛠️ Most Used Tools</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie 
                  data={trends.top_tools} 
                  dataKey="count" 
                  nameKey="tool" 
                  cx="50%" 
                  cy="50%" 
                  outerRadius={80} 
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
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

        {/* Enriched Actions - Show if data exists */}
        {trends.enriched_actions && trends.enriched_actions.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 Latest Security Actions</h3>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {trends.enriched_actions.slice(0, 5).map((action, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><strong>Agent:</strong> {action.agent_id}</div>
                    <div><strong>Risk:</strong> 
                      <span className={`ml-1 px-2 py-1 rounded text-xs ${
                        action.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                        action.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {action.risk_level}
                      </span>
                    </div>
                    <div><strong>MITRE:</strong> {action.mitre_tactic || 'N/A'}</div>
                    <div><strong>NIST:</strong> {action.nist_control || 'N/A'}</div>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    <strong>Recommendation:</strong> {action.recommendation || 'No recommendation available'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-green-600 text-2xl mr-3">✅</div>
            <div>
              <h4 className="font-semibold text-green-900">System Status</h4>
              <p className="text-green-700 text-sm">All systems operational</p>
            </div>
          </div>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-blue-600 text-2xl mr-3">🛡️</div>
            <div>
              <h4 className="font-semibold text-blue-900">Authorization</h4>
              <p className="text-blue-700 text-sm">Enterprise protection active</p>
            </div>
          </div>
        </div>
        
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-purple-600 text-2xl mr-3">🤖</div>
            <div>
              <h4 className="font-semibold text-purple-900">AI Monitoring</h4>
              <p className="text-purple-700 text-sm">Real-time analysis enabled</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;