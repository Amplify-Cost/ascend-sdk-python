import {

import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area
} from "recharts";

// Modern metric card component
const MetricCard = ({ title, value, change, changeType, icon, color, trend }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <div className={`p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-lg ${
      isDarkMode 
        ? 'bg-slate-700 border-slate-600 hover:border-slate-500' 
        : 'bg-white border-gray-300 hover:border-gray-400 shadow-sm'
    }`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`text-sm font-medium transition-colors duration-300 ${
            isDarkMode ? 'text-slate-300' : 'text-gray-700'
          }`}>
            {title}
          </p>
          <p className={`text-2xl font-bold mt-2 transition-colors duration-300 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {value}
          </p>
          {change && (
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${
                changeType === 'positive' 
                  ? 'text-green-400' 
                  : changeType === 'negative' 
                  ? 'text-red-400' 
                  : 'text-gray-400'
              }`}>
                {changeType === 'positive' ? '↗' : changeType === 'negative' ? '↘' : '→'} {change}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
      {trend && (
        <div className="mt-4 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend}>
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke={color.includes('blue') ? '#60a5fa' : '#34d399'} 
                fill={color.includes('blue') ? '#60a5fa20' : '#34d39920'} 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// Activity feed component
const ActivityFeed = ({ activities }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <div className={`p-6 rounded-xl border transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-slate-700 border-slate-600' 
        : 'bg-white border-gray-300 shadow-sm'
    }`}>
      <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        🔍 Recent Activities
      </h3>
      <div className="space-y-4 max-h-80 overflow-y-auto">
        {activities.map((activity, index) => (
          <div key={index} className={`flex items-start space-x-3 p-3 rounded-lg transition-colors duration-300 ${
            isDarkMode ? 'bg-slate-600/50' : 'bg-gray-100 border border-gray-200'
          }`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
              activity.type === 'alert' 
                ? 'bg-red-100 text-red-600' 
                : activity.type === 'approval'
                ? 'bg-green-100 text-green-600'
                : 'bg-blue-100 text-blue-600'
            }`}>
              {activity.type === 'alert' ? '⚠️' : activity.type === 'approval' ? '✅' : '🔍'}
            </div>
            <div className="flex-1">
              <p className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {activity.title}
              </p>
              <p className={`text-xs mt-1 transition-colors duration-300 ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                {activity.time} • {activity.agent}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Quick action buttons
const QuickActions = () => {
  const { isDarkMode } = useTheme();
  
  const actions = [
    { label: 'Submit Action', icon: '📤', color: 'bg-blue-500 hover:bg-blue-600' },
    { label: 'Create Alert', icon: '🚨', color: 'bg-red-500 hover:bg-red-600' },
    { label: 'Generate Rule', icon: '⚡', color: 'bg-purple-500 hover:bg-purple-600' },
    { label: 'View Reports', icon: '📊', color: 'bg-green-500 hover:bg-green-600' },
  ];
  
  return (
    <div className={`p-6 rounded-xl border transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-slate-700 border-slate-600' 
        : 'bg-white border-gray-300 shadow-sm'
    }`}>
      <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        ⚡ Quick Actions
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action, index) => (
          <button
            key={index}
            className={`p-4 rounded-lg text-white font-medium transition-all duration-200 hover:scale-105 hover:shadow-lg ${action.color}`}
          >
            <div className="text-2xl mb-2">{action.icon}</div>
            <div className="text-sm">{action.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

const Dashboard = ({ getAuthHeaders }) => {
  const { isDarkMode } = useTheme();
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Mock trend data for metric cards
  const mockTrendData = [
    { value: 45 }, { value: 52 }, { value: 48 }, { value: 61 }, { value: 55 }, { value: 67 }, { value: 73 }
  ];

  // Mock recent activities
  const recentActivities = [
    {
      type: 'alert',
      title: 'High-risk action detected',
      time: '2 min ago',
      agent: 'security-scanner-01'
    },
    {
      type: 'approval',
      title: 'Database scan approved',
      time: '5 min ago',
      agent: 'vulnerability-scanner'
    },
    {
      type: 'info',
      title: 'New rule generated',
      time: '12 min ago',
      agent: 'ai-rule-engine'
    },
    {
      type: 'alert',
      title: 'Unusual network activity',
      time: '18 min ago',
      agent: 'network-monitor'
    }
  ];

  useEffect(() => {
    logger.debug("📊 Loading Dashboard");
    const fetchTrends = async () => {
      try {
        logger.debug("🔍 Fetching dashboard data from: /analytics/trends");
        const res = await fetchWithAuth('/analytics/trends');

        if (!res.ok) throw new Error("Failed to fetch analytics data");
        const data = await res.json();
        
        logger.debug("📊 Dashboard API Response:", data);
        
        setTrends({
          high_risk_actions_by_day: data.high_risk_actions_by_day || [],
          top_agents: data.top_agents || [],
          top_tools: data.top_tools || [],
          enriched_actions: data.enriched_actions || []
        });
        
      } catch (err) {
        logger.error("❌ Dashboard fetch error:", err);
        setError("Failed to load analytics data.");
      } finally {
        setLoading(false);
      }
    };
    fetchTrends();
  }, [getAuthHeaders]);

  if (loading) {
    return (
      <div className={`p-6 transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}>
        <div className="animate-pulse space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1,2,3,4].map(i => (
              <div key={i} className={`h-32 rounded-xl ${
                isDarkMode ? 'bg-slate-700' : 'bg-gray-200'
              }`}></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1,2].map(i => (
              <div key={i} className={`h-80 rounded-xl ${
                isDarkMode ? 'bg-slate-700' : 'bg-gray-200'
              }`}></div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`p-6 text-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}>
        <div className={`max-w-md mx-auto p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-red-900/30 border-red-400 text-red-300' 
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-bold mb-2">Dashboard Error</h3>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const COLORS = isDarkMode 
    ? ["#60a5fa", "#f87171", "#34d399", "#fbbf24", "#a78bfa"]
    : ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];

  const chartColors = {
    grid: isDarkMode ? '#475569' : '#f3f4f6',
    axis: isDarkMode ? '#cbd5e1' : '#6b7280',
    tooltip: {
      bg: isDarkMode ? '#334155' : '#ffffff',
      border: isDarkMode ? '#475569' : '#e5e7eb',
      text: isDarkMode ? '#ffffff' : '#111827'
    }
  };

  return (
    <div className={`p-6 space-y-6 transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold transition-colors duration-300 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            🛡️ Security Command Center
          </h1>
          <p className={`text-lg mt-2 transition-colors duration-300 ${
            isDarkMode ? 'text-slate-300' : 'text-gray-700'
          }`}>
            Real-time enterprise security monitoring and AI agent oversight
          </p>
        </div>
        <div className={`px-4 py-2 rounded-lg transition-colors duration-300 ${
          isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-200 text-green-900 font-medium'
        }`}>
          <span className="animate-pulse">●</span> All Systems Operational
        </div>
      </div>

      {/* KPI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Agents"
          value="47"
          change="+12% this week"
          changeType="positive"
          icon="🤖"
          color="bg-blue-100 text-blue-600"
          trend={mockTrendData}
        />
        <MetricCard
          title="Actions Today"
          value="1,247"
          change="+5.2% vs yesterday"
          changeType="positive"
          icon="⚡"
          color="bg-green-100 text-green-600"
        />
        <MetricCard
          title="High-Risk Events"
          value="23"
          change="-18% this week"
          changeType="positive"
          icon="🚨"
          color="bg-red-100 text-red-600"
        />
        <MetricCard
          title="Avg Response Time"
          value="2.3m"
          change="-0.8m faster"
          changeType="positive"
          icon="⏱️"
          color="bg-purple-100 text-purple-600"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Charts Section - Takes 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* High-Risk Actions Trend */}
          {trends?.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0 && (
            <div className={`p-6 rounded-xl border transition-colors duration-300 ${
              isDarkMode 
                ? 'bg-slate-700 border-slate-600' 
                : 'bg-white border-gray-300 shadow-sm'
            }`}>
              <div className="flex items-center justify-between mb-6">
                <h3 className={`text-xl font-semibold transition-colors duration-300 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  📈 Security Trends (Last 7 Days)
                </h3>
                <div className={`px-3 py-1 rounded-full text-sm ${
                  isDarkMode ? 'bg-slate-600 text-slate-200' : 'bg-gray-200 text-gray-800 font-medium'
                }`}>
                  Live Data
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trends.high_risk_actions_by_day}>
                  <defs>
                    <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                  <XAxis dataKey="date" stroke={chartColors.axis} fontSize={12} />
                  <YAxis allowDecimals={false} stroke={chartColors.axis} fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: chartColors.tooltip.bg,
                      border: `1px solid ${chartColors.tooltip.border}`,
                      borderRadius: '12px',
                      color: chartColors.tooltip.text,
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#ef4444" 
                    fillOpacity={1} 
                    fill="url(#colorRisk)"
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Agent Activity */}
          {trends?.top_agents && trends.top_agents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className={`p-6 rounded-xl border transition-colors duration-300 ${
                isDarkMode 
                  ? 'bg-slate-700 border-slate-600' 
                  : 'bg-white border-gray-300 shadow-sm'
              }`}>
                <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  🤖 Top Active Agents
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie 
                      data={trends.top_agents} 
                      dataKey="count" 
                      nameKey="agent" 
                      cx="50%" 
                      cy="50%" 
                      outerRadius={80} 
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelStyle={{ fill: isDarkMode ? '#f1f5f9' : '#1e293b', fontSize: '11px' }}
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
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {trends?.top_tools && trends.top_tools.length > 0 && (
                <div className={`p-6 rounded-xl border transition-colors duration-300 ${
                  isDarkMode 
                    ? 'bg-slate-700 border-slate-600' 
                    : 'bg-white border-gray-300 shadow-sm'
                }`}>
                  <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    🛠️ Tool Usage
                  </h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={trends.top_tools} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                      <XAxis type="number" stroke={chartColors.axis} fontSize={11} />
                      <YAxis dataKey="tool" type="category" stroke={chartColors.axis} fontSize={11} width={80} />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: chartColors.tooltip.bg,
                          border: `1px solid ${chartColors.tooltip.border}`,
                          borderRadius: '8px',
                          color: chartColors.tooltip.text
                        }}
                      />
                      <Bar dataKey="count" fill="#60a5fa" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar - Takes 1 column */}
        <div className="space-y-6">
          <QuickActions />
          <ActivityFeed activities={recentActivities} />
          
          {/* System Health */}
          <div className={`p-6 rounded-xl border transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-slate-700 border-slate-600' 
              : 'bg-white border-gray-300 shadow-sm'
          }`}>
            <h3 className={`text-lg font-semibold mb-4 transition-colors duration-300 ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              🌡️ System Health
            </h3>
            <div className="space-y-4">
              {[
                { name: 'API Response', value: 98, color: 'bg-green-500' },
                { name: 'Database', value: 95, color: 'bg-green-500' },
                { name: 'Agent Network', value: 92, color: 'bg-yellow-500' },
                { name: 'Alert System', value: 100, color: 'bg-green-500' }
              ].map((metric, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between">
                    <span className={`text-sm font-medium ${
                      isDarkMode ? 'text-slate-200' : 'text-gray-800'
                    }`}>
                      {metric.name}
                    </span>
                    <span className={`text-sm font-bold ${
                      isDarkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      {metric.value}%
                    </span>
                  </div>
                  <div className={`w-full bg-gray-200 rounded-full h-2 ${
                    isDarkMode ? 'bg-slate-600' : 'bg-gray-300'
                  }`}>
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${metric.color}`}
                      style={{ width: `${metric.value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Latest Security Actions */}
      {trends?.enriched_actions && trends.enriched_actions.length > 0 && (
        <div className={`p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-slate-700 border-slate-600' 
            : 'bg-white border-gray-300 shadow-sm'
        }`}>
          <h3 className={`text-xl font-semibold mb-6 transition-colors duration-300 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            🔍 Latest Security Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trends.enriched_actions.slice(0, 6).map((action, index) => (
              <div key={index} className={`p-4 rounded-lg border-l-4 transition-all duration-200 hover:scale-105 ${
                action.risk_level === 'high' 
                  ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                  : action.risk_level === 'medium' 
                  ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                  : 'border-green-500 bg-green-50 dark:bg-green-900/20'
              } ${isDarkMode ? 'bg-slate-600' : 'bg-gray-100 border border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                    action.risk_level === 'high' 
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
                      : action.risk_level === 'medium' 
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
                      : 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                  }`}>
                    {action.risk_level?.toUpperCase()}
                  </span>
                  <span className={`text-xs ${
                    isDarkMode ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    {action.mitre_tactic || 'N/A'}
                  </span>
                </div>
                <p className={`text-sm font-medium mb-1 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  {action.agent_id}
                </p>
                <p className={`text-xs ${
                  isDarkMode ? 'text-slate-300' : 'text-gray-700'
                }`}>
                  {action.recommendation || 'Monitoring for suspicious activity'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
