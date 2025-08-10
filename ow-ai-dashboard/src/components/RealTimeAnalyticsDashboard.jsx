// components/RealTimeAnalyticsDashboard.jsx
// Enterprise Real-Time Analytics Dashboard Component - Fixed Syntax
import React, { useState, useEffect, useRef } from 'react';
import { Activity, TrendingUp, Users, Shield, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, Target, BarChart3, PieChart, LineChart } from 'lucide-react';

const RealTimeAnalyticsDashboard = () => {
  const [realTimeMetrics, setRealTimeMetrics] = useState(null);
  const [predictiveData, setPredictiveData] = useState(null);
  const [systemPerformance, setSystemPerformance] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  // Get auth token from localStorage
  const getAuthToken = () => {
    return localStorage.getItem('access_token');
  };

  // Enhanced fetch with authentication
  const fetchWithAuth = async (endpoint) => {
    const token = getAuthToken();
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://owai-production.up.railway.app'}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-Enterprise-Client': 'OW-AI-Platform'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  };

  // 🔧 TEMPORARY: WebSocket function commented out to fix 403 errors
  /*
  const initializeWebSocket = () => {
    const userEmail = localStorage.getItem('user_email') || 'admin@example.com';
    const wsUrl = `${(import.meta.env.VITE_API_URL || 'https://owai-production.up.railway.app').replace('http', 'ws')}/analytics/ws/realtime/${userEmail}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('🔌 WebSocket connected for real-time analytics');
        setIsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'metrics_update') {
            // Update real-time metrics from WebSocket
            setRealTimeMetrics(prev => ({
              ...prev,
              real_time_overview: {
                ...prev?.real_time_overview,
                active_sessions: data.metrics.active_users
              },
              system_health: {
                ...prev?.system_health,
                cpu_usage: data.metrics.cpu_usage,
                memory_usage: data.metrics.memory_usage
              },
              performance_metrics: {
                ...prev?.performance_metrics,
                average_response_time: data.metrics.response_time
              }
            }));
          }
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (err) {
      console.error('WebSocket initialization error:', err);
      setIsConnected(false);
    }
  };
  */

  // Fetch initial data
  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Fetching enhanced analytics data...');

      const [metricsData, predictiveData, performanceData] = await Promise.allSettled([
        fetchWithAuth('/analytics/realtime/metrics'),
        fetchWithAuth('/analytics/predictive/trends'),
        fetchWithAuth('/analytics/performance/system')
      ]);

      if (metricsData.status === 'fulfilled') {
        setRealTimeMetrics(metricsData.value);
        console.log('✅ Real-time metrics loaded');
      } else {
        console.error('❌ Failed to load real-time metrics:', metricsData.reason);
      }

      if (predictiveData.status === 'fulfilled') {
        setPredictiveData(predictiveData.value);
        console.log('✅ Predictive data loaded');
      } else {
        console.error('❌ Failed to load predictive data:', predictiveData.reason);
      }

      if (performanceData.status === 'fulfilled') {
        setSystemPerformance(performanceData.value);
        console.log('✅ System performance loaded');
      } else {
        console.error('❌ Failed to load system performance:', performanceData.reason);
      }

      setError(null);
    } catch (err) {
      console.error('❌ Analytics fetch error:', err);
      setError('Failed to load analytics data. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Initialize component
  useEffect(() => {
    fetchAnalyticsData();
    // 🔧 TEMPORARY: WebSocket commented out to fix 403 errors
    // initializeWebSocket();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchAnalyticsData, 30000);

    return () => {
      clearInterval(interval);
      // 🔧 TEMPORARY: WebSocket cleanup commented out
      // if (wsRef.current) {
      //   wsRef.current.close();
      // }
    };
  }, []);

  // Status indicator component
  const StatusIndicator = ({ status, label }) => {
    const getStatusColor = () => {
      switch (status) {
        case 'healthy':
        case 'excellent':
        case 'normal':
        case 'optimal':
          return 'text-green-600 bg-green-100';
        case 'warning':
        case 'acceptable':
          return 'text-yellow-600 bg-yellow-100';
        case 'critical':
        case 'error':
          return 'text-red-600 bg-red-100';
        default:
          return 'text-gray-600 bg-gray-100';
      }
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
        {status} {label}
      </span>
    );
  };

  // Metric card component
  const MetricCard = ({ icon: Icon, title, value, subtitle, trend, status }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Icon className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        </div>
        {status && <StatusIndicator status={status} />}
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        {trend && (
          <div className={`flex items-center space-x-1 text-sm ${
            trend.startsWith('+') ? 'text-green-600' : trend.startsWith('-') ? 'text-red-600' : 'text-gray-600'
          }`}>
            <TrendingUp className="h-4 w-4" />
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  );

  // Progress bar component
  const ProgressBar = ({ label, value, max = 100, color = 'blue' }) => {
    const percentage = Math.min((value / max) * 100, 100);
    const colorClasses = {
      blue: 'bg-blue-600',
      green: 'bg-green-600',
      yellow: 'bg-yellow-600',
      red: 'bg-red-600'
    };

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-700">{label}</span>
          <span className="text-gray-900 font-medium">{value.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${colorClasses[color]}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-lg text-gray-600">Loading enhanced analytics...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg border border-red-200 p-8">
            <div className="flex items-center space-x-3 text-red-600">
              <AlertTriangle className="h-8 w-8" />
              <div>
                <h3 className="text-lg font-medium">Analytics Error</h3>
                <p className="text-sm text-red-500">{error}</p>
              </div>
            </div>
            <button 
              onClick={fetchAnalyticsData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Real-Time Analytics Dashboard</h1>
              <p className="text-gray-600">Enterprise monitoring and predictive insights</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium">{isConnected ? 'Live' : 'Disconnected'}</span>
              </div>
              <span className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* Real-Time Overview */}
        {realTimeMetrics && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Real-Time Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                icon={Users}
                title="Active Sessions"
                value={realTimeMetrics.real_time_overview?.active_sessions || 0}
                subtitle="Current users"
                status={realTimeMetrics.status}
              />
              <MetricCard
                icon={Shield}
                title="High-Risk Actions"
                value={realTimeMetrics.real_time_overview?.recent_high_risk_actions || 0}
                subtitle="Last hour"
                trend={realTimeMetrics.real_time_overview?.recent_high_risk_actions > 5 ? '+Alert' : 'Normal'}
              />
              <MetricCard
                icon={Activity}
                title="Active Agents"
                value={realTimeMetrics.real_time_overview?.active_agents || 0}
                subtitle="Currently running"
              />
              <MetricCard
                icon={BarChart3}
                title="Response Time"
                value={`${realTimeMetrics.performance_metrics?.average_response_time?.toFixed(0) || 0}ms`}
                subtitle="Average"
                trend={realTimeMetrics.performance_metrics?.average_response_time < 200 ? 'Excellent' : 'Good'}
              />
            </div>
          </div>
        )}

        {/* System Health */}
        {realTimeMetrics?.system_health && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">System Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-4">
                <ProgressBar 
                  label="CPU Usage" 
                  value={realTimeMetrics.system_health.cpu_usage}
                  color={realTimeMetrics.system_health.cpu_usage > 80 ? 'red' : realTimeMetrics.system_health.cpu_usage > 60 ? 'yellow' : 'green'}
                />
                <ProgressBar 
                  label="Memory Usage" 
                  value={realTimeMetrics.system_health.memory_usage}
                  color={realTimeMetrics.system_health.memory_usage > 80 ? 'red' : realTimeMetrics.system_health.memory_usage > 60 ? 'yellow' : 'green'}
                />
              </div>
              <div className="space-y-4">
                <ProgressBar 
                  label="Disk Usage" 
                  value={realTimeMetrics.system_health.disk_usage}
                  color={realTimeMetrics.system_health.disk_usage > 80 ? 'red' : realTimeMetrics.system_health.disk_usage > 60 ? 'yellow' : 'green'}
                />
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Network Latency</span>
                    <span className="text-gray-900 font-medium">{realTimeMetrics.system_health.network_latency}ms</span>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Requests/sec</span>
                    <span className="text-gray-900 font-medium">{realTimeMetrics.performance_metrics?.requests_per_second?.toFixed(1) || 0}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Error Rate</span>
                    <span className={`font-medium ${realTimeMetrics.performance_metrics?.error_rate > 0.05 ? 'text-red-600' : 'text-green-600'}`}>
                      {((realTimeMetrics.performance_metrics?.error_rate || 0) * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Predictive Analytics */}
        {predictiveData && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Predictive Analytics</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Risk Forecast */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Risk Forecast (Next 7 Days)</h4>
                <div className="space-y-3">
                  {predictiveData.risk_forecast?.slice(0, 5).map((forecast, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600">{new Date(forecast.date).toLocaleDateString()}</span>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium">{forecast.predicted_high_risk} risks</span>
                        <div className={`px-2 py-1 rounded text-xs ${
                          forecast.confidence > 0.8 ? 'bg-green-100 text-green-700' : 
                          forecast.confidence > 0.6 ? 'bg-yellow-100 text-yellow-700' : 
                          'bg-red-100 text-red-700'
                        }`}>
                          {Math.round(forecast.confidence * 100)}% confidence
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent Workload Forecast */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Agent Workload Forecast</h4>
                <div className="space-y-3">
                  {predictiveData.agent_workload_forecast?.map((agent, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-800">{agent.agent}</span>
                        <span className="text-sm text-gray-600">{agent.predicted_actions} actions</span>
                      </div>
                      <ProgressBar 
                        label="Capacity Utilization" 
                        value={agent.capacity_utilization * 100}
                        color={agent.capacity_utilization > 0.8 ? 'red' : agent.capacity_utilization > 0.6 ? 'yellow' : 'green'}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Strategic Recommendations */}
            {predictiveData.risk_predictions?.recommended_actions && (
              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <h4 className="text-md font-medium text-blue-800 mb-3">Recommended Actions</h4>
                <ul className="space-y-2">
                  {predictiveData.risk_predictions.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-2 text-sm text-blue-700">
                      <Target className="h-4 w-4 mt-0.5 text-blue-500" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* System Performance Details */}
        {systemPerformance && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Detailed Performance Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Application Metrics */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Application</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Response</span>
                    <span className="text-sm font-medium">{systemPerformance.application_metrics?.response_times?.average?.toFixed(0)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">P95 Response</span>
                    <span className="text-sm font-medium">{systemPerformance.application_metrics?.response_times?.p95?.toFixed(0)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Throughput</span>
                    <span className="text-sm font-medium">{systemPerformance.application_metrics?.throughput?.requests_per_second?.toFixed(1)} RPS</span>
                  </div>
                </div>
              </div>

              {/* Database Metrics */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Database</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Connections</span>
                    <span className="text-sm font-medium">{systemPerformance.database_metrics?.connections?.active}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Idle Connections</span>
                    <span className="text-sm font-medium">{systemPerformance.database_metrics?.connections?.idle}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Query Time</span>
                    <span className="text-sm font-medium">{systemPerformance.database_metrics?.query_performance?.average_duration?.toFixed(1)}ms</span>
                  </div>
                </div>
              </div>

              {/* System Resources */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">System Resources</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">CPU Current</span>
                    <span className="text-sm font-medium">{systemPerformance.system_metrics?.cpu?.current?.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Memory Available</span>
                    <span className="text-sm font-medium">{systemPerformance.system_metrics?.memory?.available?.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Storage Used</span>
                    <span className="text-sm font-medium">{systemPerformance.system_metrics?.storage?.used?.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default RealTimeAnalyticsDashboard;