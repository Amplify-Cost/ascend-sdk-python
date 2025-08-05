import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";
import { useTheme } from "../contexts/ThemeContext";

const Dashboard = ({ getAuthHeaders }) => {
  const { isDarkMode } = useTheme();
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
      <div className={`p-6 text-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-white text-gray-900'
      }`}>
        <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${
          isDarkMode ? 'border-blue-400' : 'border-blue-600'
        }`}></div>
        <p className={isDarkMode ? 'text-slate-400' : 'text-gray-500'}>Loading analytics...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`p-6 text-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-900' : 'bg-white'
      }`}>
        <div className={`border px-4 py-3 rounded transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-red-900/20 border-red-500 text-red-400' 
            : 'bg-red-100 border-red-400 text-red-700'
        }`}>
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
      <div className={`p-6 transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-900' : 'bg-gray-50'
      }`}>
        <h2 className={`text-2xl font-semibold mb-6 transition-colors duration-300 ${
          isDarkMode ? 'text-slate-100' : 'text-gray-900'
        }`}>
          🛡️ Security Analytics Dashboard
        </h2>
        <div className={`border rounded-lg p-6 text-center transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-blue-900/20 border-blue-500/30 text-blue-300' 
            : 'bg-blue-50 border-blue-200 text-blue-700'
        }`}>
          <div className={`text-4xl mb-4 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>📊</div>
          <h3 className={`text-lg font-semibold mb-2 ${
            isDarkMode ? 'text-blue-200' : 'text-blue-900'
          }`}>
            Analytics Dashboard Ready
          </h3>
          <p className={`mb-4 ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
            No analytics data available yet. Submit agent actions to populate insights.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div className={`p-4 rounded border transition-colors duration-300 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600' 
                : 'bg-white border-gray-200'
            }`}>
              <h4 className={`font-semibold ${isDarkMode ? 'text-slate-100' : 'text-gray-900'}`}>
                🎯 Quick Start
              </h4>
              <p className={`text-sm mt-2 ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
                1. Submit agent actions via "Submit Action" tab<br/>
                2. Review alerts in "Alerts" tab<br/>
                3. Generate smart rules<br/>
                4. View analytics here
              </p>
            </div>
            <div className={`p-4 rounded border transition-colors duration-300 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600' 
                : 'bg-white border-gray-200'
            }`}>
              <h4 className={`font-semibold ${isDarkMode ? 'text-slate-100' : 'text-gray-900'}`}>
                📈 What You'll See
              </h4>
              <p className={`text-sm mt-2 ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}>
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

  const COLORS = isDarkMode 
    ? ["#60a5fa", "#f87171", "#34d399", "#fbbf24", "#a78bfa"]
    : ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];

  // Chart colors for dark mode
  const chartColors = {
    grid: isDarkMode ? '#374151' : '#f3f4f6',
    axis: isDarkMode ? '#9ca3af' : '#6b7280',
    tooltip: {
      bg: isDarkMode ? '#1f2937' : '#ffffff',
      border: isDarkMode ? '#374151' : '#e5e7eb',
      text: isDarkMode ? '#f9fafb' : '#111827'
    }
  };

  return (
    <div className={`p-6 space-y-6 transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-900' : 'bg-gray-50'
    }`}>
      <div className="flex items-center justify-between">
        <h2 className={`text-2xl font-semibold transition-colors duration-300 ${
          isDarkMode ? 'text-slate-100' : 'text-gray-900'
        }`}>
          🛡️ Security Analytics Dashboard
        </h2>
        <div className={`text-sm transition-colors duration-300 ${
          isDarkMode ? 'text-slate-400' : 'text-gray-500'
        }`}>
          Real-time security monitoring • Enterprise-grade analytics
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High-Risk Actions Chart - Only show if data exists */}
        {trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0 && (
          <div className={`p-6 rounded-lg shadow-sm border transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-slate-800 border-slate-700' 
              : 'bg-white border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-100' : 'text-gray-900'
            }`}>
              📈 High-Risk Actions (Last 7 Days)
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends.high_risk_actions_by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis dataKey="date" stroke={chartColors.axis} fontSize={12} />
                <YAxis allowDecimals={false} stroke={chartColors.axis} fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: chartColors.tooltip.bg,
                    border: `1px solid ${chartColors.tooltip.border}`,
                    borderRadius: '8px',
                    color: chartColors.tooltip.text,
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Agents - Show if data exists */}
        {trends.top_agents && trends.top_agents.length > 0 && (
          <div className={`p-6 rounded-lg shadow-sm border transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-slate-800 border-slate-700' 
              : 'bg-white border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-100' : 'text-gray-900'
            }`}>
              🤖 Top Active Agents
            </h3>
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
                  labelStyle={{ fill: isDarkMode ? '#f1f5f9' : '#1e293b', fontSize: '12px' }}
                >
                  {trends.top_agents.map((_, index) => (
                    <Cell key={`agent-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: chartColors.tooltip.bg,
                    border: `1px solid ${chartColors.tooltip.border}`,
                    borderRadius: '8px',
                    color: chartColors.tooltip.text
                  }}
                />
                <Legend wrapperStyle={{ color: isDarkMode ? '#f1f5f9' : '#1e293b' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Tools - Show if data exists */}
        {trends.top_tools && trends.top_tools.length > 0 && (
          <div className={`p-6 rounded-lg shadow-sm border transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-slate-800 border-slate-700' 
              : 'bg-white border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-100' : 'text-gray-900'
            }`}>
              🛠️ Most Used Tools
            </h3>
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
                  labelStyle={{ fill: isDarkMode ? '#f1f5f9' : '#1e293b', fontSize: '12px' }}
                >
                  {trends.top_tools.map((_, index) => (
                    <Cell key={`tool-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: chartColors.tooltip.bg,
                    border: `1px solid ${chartColors.tooltip.border}`,
                    borderRadius: '8px',
                    color: chartColors.tooltip.text
                  }}
                />
                <Legend wrapperStyle={{ color: isDarkMode ? '#f1f5f9' : '#1e293b' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Enriched Actions - Show if data exists */}
        {trends.enriched_actions && trends.enriched_actions.length > 0 && (
          <div className={`p-6 rounded-lg shadow-sm border transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-slate-800 border-slate-700' 
              : 'bg-white border-gray-200'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-100' : 'text-gray-900'
            }`}>
              🔍 Latest Security Actions
            </h3>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {trends.enriched_actions.slice(0, 5).map((action, index) => (
                <div key={index} className={`p-3 rounded-lg border-l-4 border-blue-500 transition-colors duration-300 ${
                  isDarkMode ? 'bg-slate-700' : 'bg-gray-50'
                }`}>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className={isDarkMode ? 'text-slate-200' : 'text-gray-800'}>
                      <strong>Agent:</strong> {action.agent_id}
                    </div>
                    <div className={isDarkMode ? 'text-slate-200' : 'text-gray-800'}>
                      <strong>Risk:</strong> 
                      <span className={`ml-1 px-2 py-1 rounded text-xs ${
                        action.risk_level === 'high' 
                          ? isDarkMode ? 'bg-red-900/50 text-red-300' : 'bg-red-100 text-red-800'
                          : action.risk_level === 'medium' 
                          ? isDarkMode ? 'bg-yellow-900/50 text-yellow-300' : 'bg-yellow-100 text-yellow-800'
                          : isDarkMode ? 'bg-green-900/50 text-green-300' : 'bg-green-100 text-green-800'
                      }`}>
                        {action.risk_level}
                      </span>
                    </div>
                    <div className={isDarkMode ? 'text-slate-200' : 'text-gray-800'}>
                      <strong>MITRE:</strong> {action.mitre_tactic || 'N/A'}
                    </div>
                    <div className={isDarkMode ? 'text-slate-200' : 'text-gray-800'}>
                      <strong>NIST:</strong> {action.nist_control || 'N/A'}
                    </div>
                  </div>
                  <div className={`mt-2 text-sm transition-colors duration-300 ${
                    isDarkMode ? 'text-slate-300' : 'text-gray-600'
                  }`}>
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
        <div className={`border rounded-lg p-4 transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-green-900/20 border-green-500/30' 
            : 'bg-green-50 border-green-200'
        }`}>
          <div className="flex items-center">
            <div className={`text-2xl mr-3 ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>✅</div>
            <div>
              <h4 className={`font-semibold ${isDarkMode ? 'text-green-300' : 'text-green-900'}`}>
                System Status
              </h4>
              <p className={`text-sm ${isDarkMode ? 'text-green-400' : 'text-green-700'}`}>
                All systems operational
              </p>
            </div>
          </div>
        </div>
        
        <div className={`border rounded-lg p-4 transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-blue-900/20 border-blue-500/30' 
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center">
            <div className={`text-2xl mr-3 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>🛡️</div>
            <div>
              <h4 className={`font-semibold ${isDarkMode ? 'text-blue-300' : 'text-blue-900'}`}>
                Authorization
              </h4>
              <p className={`text-sm ${isDarkMode ? 'text-blue-400' : 'text-blue-700'}`}>
                Enterprise protection active
              </p>
            </div>
          </div>
        </div>
        
        <div className={`border rounded-lg p-4 transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-purple-900/20 border-purple-500/30' 
            : 'bg-purple-50 border-purple-200'
        }`}>
          <div className="flex items-center">
            <div className={`text-2xl mr-3 ${isDarkMode ? 'text-purple-400' : 'text-purple-600'}`}>🤖</div>
            <div>
              <h4 className={`font-semibold ${isDarkMode ? 'text-purple-300' : 'text-purple-900'}`}>
                AI Monitoring
              </h4>
              <p className={`text-sm ${isDarkMode ? 'text-purple-400' : 'text-purple-700'}`}>
                Real-time analysis enabled
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;