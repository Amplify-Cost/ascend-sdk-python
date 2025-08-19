// components/RealTimeAnalyticsDashboard.jsx
// Enterprise Real-Time Analytics Dashboard Component - Master Prompt Aligned Fix
import React, { useState, useEffect, useRef } from 'react';
import { Activity, TrendingUp, Users, Shield, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, Target, BarChart3, PieChart, LineChart, Zap, Clock, Server, Database, Globe, Lock } from 'lucide-react';

// 🎯 MASTER PROMPT FIX: Complete enterprise analytics component
const RealTimeAnalyticsDashboard = ({ getAuthHeaders, user }) => {
  const [realTimeMetrics, setRealTimeMetrics] = useState(null);
  const [predictiveData, setPredictiveData] = useState(null);
  const [systemPerformance, setSystemPerformance] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  // 🎯 MASTER PROMPT: Enhanced authentication with enterprise error handling
  const fetchWithAuth = async (endpoint) => {
    try {
      console.log('🔄 Real-Time Analytics: Fetching', endpoint);
      console.log('🔄 User context:', user?.email, user?.role);
      
      // Use the getAuthHeaders function passed from App.jsx
      const headers = {
        'Content-Type': 'application/json'
      };
      
      console.log('🔄 Auth headers available:', !!headers.Authorization);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || window.location.origin}${endpoint}`, {
        method: 'GET',
        headers: {
          ...headers,
          'X-Enterprise-Client': 'OW-AI-Platform',
          'X-Request-ID': `analytics-${Date.now()}`
        },
        credentials: 'include'
      });

      console.log('🔄 Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error:', response.status, errorText);
        
        // 🎯 MASTER PROMPT: Specific error handling for common issues
        if (response.status === 401) {
          throw new Error('Authentication failed - please log in again');
        } else if (response.status === 403) {
          throw new Error('Access denied - insufficient permissions');
        } else if (response.status === 404) {
          throw new Error('Analytics endpoint not found');
        } else {
          throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
      }

      const data = await response.json();
      console.log('✅ Data received for', endpoint, '- Keys:', Object.keys(data));
      return data;
      
    } catch (error) {
      console.error('❌ Fetch error for', endpoint, ':', error.message);
      throw error;
    }
  };

  // 🎯 MASTER PROMPT: WebSocket connection with proper error handling
  const initializeWebSocket = () => {
    if (!user?.email) {
      console.log('⚠️ No user email available for WebSocket connection');
      return;
    }

    const userEmail = user.email;
    const wsUrl = `${(import.meta.env.VITE_API_URL || window.location.origin).replace('http', 'ws')}/analytics/ws/realtime/${userEmail}`;
    
    try {
      console.log('🔌 Initializing WebSocket:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('🔌 WebSocket connected for real-time analytics');
        setIsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📡 WebSocket message received:', data.type);
          
          if (data.type === 'metrics_update') {
            // Update real-time metrics from WebSocket
            setRealTimeMetrics(prev => ({
              ...prev,
              real_time_overview: {
                ...prev?.real_time_overview,
                active_sessions: data.metrics.active_users || prev?.real_time_overview?.active_sessions
              },
              system_health: {
                ...prev?.system_health,
                cpu_usage: data.metrics.cpu_usage || prev?.system_health?.cpu_usage,
                memory_usage: data.metrics.memory_usage || prev?.system_health?.memory_usage
              },
              performance_metrics: {
                ...prev?.performance_metrics,
                average_response_time: data.metrics.response_time || prev?.performance_metrics?.average_response_time
              }
            }));
          }
        } catch (err) {
          console.error('❌ WebSocket message parse error:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 10 seconds
        setTimeout(() => {
          if (user?.email) {
            initializeWebSocket();
          }
        }, 10000);
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (err) {
      console.error('❌ WebSocket initialization error:', err);
      setIsConnected(false);
    }
  };

  // 🎯 MASTER PROMPT: Enhanced data fetching with enterprise error handling
  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('🔄 Fetching enhanced analytics data...');
      console.log('🔄 User authentication:', !!user, user?.email, user?.role);

      // Check if user is authenticated before making requests
      if (!user) {
        throw new Error('User authentication required');
      }

      // 🎯 MASTER PROMPT: Call your advanced analytics endpoints
      const [metricsResult, predictiveResult, performanceResult] = await Promise.allSettled([
        fetchWithAuth('/analytics/realtime/metrics'),
        fetchWithAuth('/analytics/predictive/trends'),
        fetchWithAuth('/analytics/performance/system')
      ]);

      console.log('🔄 Results:', {
        metrics: metricsResult.status,
        predictive: predictiveResult.status,
        performance: performanceResult.status
      });

      // Process successful results
      if (metricsResult.status === 'fulfilled') {
        setRealTimeMetrics(metricsResult.value);
        console.log('✅ Real-time metrics loaded');
      } else {
        console.error('❌ Failed to load real-time metrics:', metricsResult.reason?.message);
      }

      if (predictiveResult.status === 'fulfilled') {
        setPredictiveData(predictiveResult.value);
        console.log('✅ Predictive data loaded');
      } else {
        console.error('❌ Failed to load predictive data:', predictiveResult.reason?.message);
      }

      if (performanceResult.status === 'fulfilled') {
        setSystemPerformance(performanceResult.value);
        console.log('✅ System performance loaded');
      } else {
        console.error('❌ Failed to load system performance:', performanceResult.reason?.message);
      }

      // If all requests failed, show an error
      if (metricsResult.status === 'rejected' && 
          predictiveResult.status === 'rejected' && 
          performanceResult.status === 'rejected') {
        const firstError = metricsResult.reason?.message || predictiveResult.reason?.message || performanceResult.reason?.message;
        throw new Error(`All analytics endpoints failed: ${firstError}`);
      }

    } catch (err) {
      console.error('❌ Analytics fetch error:', err);
      setError(`Failed to load analytics data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 🎯 MASTER PROMPT: Only fetch data when user is available
  useEffect(() => {
    if (user) {
      console.log('🚀 RealTimeAnalyticsDashboard: User available, fetching data...');
      fetchAnalyticsData();
      
      // Initialize WebSocket for real-time updates
      initializeWebSocket();

      // Refresh data every 30 seconds
      const interval = setInterval(() => {
        if (user) {
          fetchAnalyticsData();
        }
      }, 30000);

      return () => {
        clearInterval(interval);
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    } else {
      console.log('⚠️ RealTimeAnalyticsDashboard: No user available');
      setError('User authentication required');
      setLoading(false);
    }
  }, [user]); // Only depend on user prop

  // 🎯 MASTER PROMPT: Enterprise UI components
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
            trend.includes('+') || trend.includes('Excellent') ? 'text-green-600' : 
            trend.includes('-') || trend.includes('Alert') ? 'text-red-600' : 'text-gray-600'
          }`}>
            <TrendingUp className="h-4 w-4" />
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  );

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

  // 🎯 MASTER PROMPT: Enhanced loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-lg text-gray-600">
                Loading enterprise analytics for {user?.email || 'user'}...
              </span>
            </div>
            <div className="mt-4 text-center text-sm text-gray-500">
              Connecting to real-time monitoring systems...
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 🎯 MASTER PROMPT: Enhanced error state with actionable information
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg border border-red-200 p-8">
            <div className="flex items-center space-x-3 text-red-600">
              <AlertTriangle className="h-8 w-8" />
              <div>
                <h3 className="text-lg font-medium">Analytics Connection Error</h3>
                <p className="text-sm text-red-500">{error}</p>
                <p className="text-xs text-gray-500 mt-2">
                  User: {user?.email || 'Not authenticated'} | Role: {user?.role || 'Unknown'}
                </p>
              </div>
            </div>
            <div className="mt-4 space-x-3">
              <button 
                onClick={fetchAnalyticsData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Retry Connection
              </button>
              <button 
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Refresh Page
              </button>
            </div>
            
            {/* 🎯 MASTER PROMPT: Debug information for troubleshooting */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Debug Information:</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p>API URL: {import.meta.env.VITE_API_URL || window.location.origin}</p>
                <p>Auth Headers: {getAuthHeaders ? 'Available' : 'Not available'}</p>
                <p>User Role: {user?.role || 'Unknown'}</p>
                <p>Endpoints: /analytics/realtime/metrics, /analytics/predictive/trends, /analytics/performance/system</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* 🎯 MASTER PROMPT: Enterprise header with connection status */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Activity className="h-6 w-6 mr-2 text-blue-600" />
                Real-Time Analytics Dashboard
              </h1>
              <p className="text-gray-600">Enterprise monitoring and predictive insights for {user?.email}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                isConnected ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                <span className="text-sm font-medium">{isConnected ? 'Live Data' : 'Polling Mode'}</span>
              </div>
              <span className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* 🎯 MASTER PROMPT: Real-Time Overview Cards */}
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
                trend={(realTimeMetrics.real_time_overview?.recent_high_risk_actions || 0) > 5 ? '+Alert' : 'Normal'}
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
                value={`${Math.round(realTimeMetrics.performance_metrics?.average_response_time || 0)}ms`}
                subtitle="Average"
                trend={(realTimeMetrics.performance_metrics?.average_response_time || 200) < 200 ? 'Excellent' : 'Good'}
              />
            </div>
          </div>
        )}

        {/* 🎯 MASTER PROMPT: System Health Monitoring */}
        {realTimeMetrics?.system_health && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Server className="h-5 w-5 mr-2 text-green-600" />
              System Health
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-4">
                <ProgressBar 
                  label="CPU Usage" 
                  value={realTimeMetrics.system_health.cpu_usage || 0}
                  color={realTimeMetrics.system_health.cpu_usage > 80 ? 'red' : realTimeMetrics.system_health.cpu_usage > 60 ? 'yellow' : 'green'}
                />
                <ProgressBar 
                  label="Memory Usage" 
                  value={realTimeMetrics.system_health.memory_usage || 0}
                  color={realTimeMetrics.system_health.memory_usage > 80 ? 'red' : realTimeMetrics.system_health.memory_usage > 60 ? 'yellow' : 'green'}
                />
              </div>
              <div className="space-y-4">
                <ProgressBar 
                  label="Disk Usage" 
                  value={realTimeMetrics.system_health.disk_usage || 0}
                  color={realTimeMetrics.system_health.disk_usage > 80 ? 'red' : realTimeMetrics.system_health.disk_usage > 60 ? 'yellow' : 'green'}
                />
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Network Latency</span>
                    <span className="text-gray-900 font-medium">{realTimeMetrics.system_health.network_latency || 0}ms</span>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Requests/sec</span>
                    <span className="text-gray-900 font-medium">{(realTimeMetrics.performance_metrics?.requests_per_second || 0).toFixed(1)}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">Error Rate</span>
                    <span className={`font-medium ${(realTimeMetrics.performance_metrics?.error_rate || 0) > 0.05 ? 'text-red-600' : 'text-green-600'}`}>
                      {((realTimeMetrics.performance_metrics?.error_rate || 0) * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 🎯 MASTER PROMPT: Predictive Analytics Section */}
        {predictiveData && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Target className="h-5 w-5 mr-2 text-purple-600" />
              Predictive Analytics
            </h3>
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
                <h4 className="text-md font-medium text-blue-800 mb-3 flex items-center">
                  <Target className="h-4 w-4 mr-2" />
                  Recommended Actions
                </h4>
                <ul className="space-y-2">
                  {predictiveData.risk_predictions.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-2 text-sm text-blue-700">
                      <CheckCircle className="h-4 w-4 mt-0.5 text-blue-500" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* 🎯 MASTER PROMPT: System Performance Details */}
        {systemPerformance && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Database className="h-5 w-5 mr-2 text-indigo-600" />
              Detailed Performance Metrics
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Application Metrics */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Application</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Response</span>
                    <span className="text-sm font-medium">{Math.round(systemPerformance.application_metrics?.response_times?.average || 0)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">P95 Response</span>
                    <span className="text-sm font-medium">{Math.round(systemPerformance.application_metrics?.response_times?.p95 || 0)}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Throughput</span>
                    <span className="text-sm font-medium">{(systemPerformance.application_metrics?.throughput?.requests_per_second || 0).toFixed(1)} RPS</span>
                  </div>
                </div>
              </div>

              {/* Database Metrics */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">Database</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Connections</span>
                    <span className="text-sm font-medium">{systemPerformance.database_metrics?.connections?.active || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Idle Connections</span>
                    <span className="text-sm font-medium">{systemPerformance.database_metrics?.connections?.idle || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Query Time</span>
                    <span className="text-sm font-medium">{(systemPerformance.database_metrics?.query_performance?.average_duration || 0).toFixed(1)}ms</span>
                  </div>
                </div>
              </div>

              {/* System Resources */}
              <div>
                <h4 className="text-md font-medium text-gray-800 mb-4">System Resources</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">CPU Current</span>
                    <span className="text-sm font-medium">{(systemPerformance.system_metrics?.cpu?.current || 0).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Memory Available</span>
                    <span className="text-sm font-medium">{(systemPerformance.system_metrics?.memory?.available || 0).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Storage Used</span>
                    <span className="text-sm font-medium">{(systemPerformance.system_metrics?.storage?.used || 0).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 🎯 MASTER PROMPT: Debug Info when no data loads */}
        {!realTimeMetrics && !predictiveData && !systemPerformance && !loading && !error && (
          <div className="bg-white rounded-lg border border-yellow-200 p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-4 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Diagnostic Information
            </h3>
            <div className="space-y-2 text-sm">
              <p><strong>User:</strong> {user?.email || 'Not authenticated'}</p>
              <p><strong>Role:</strong> {user?.role || 'Unknown'}</p>
              <p><strong>Auth Headers:</strong> {!!getAuthHeaders ? 'Available' : 'Not available'}</p>
              <p><strong>API URL:</strong> {import.meta.env.VITE_API_URL || window.location.origin}</p>
              <p><strong>Expected Endpoints:</strong></p>
              <ul className="ml-4 text-xs text-gray-600">
                <li>• /analytics/realtime/metrics</li>
                <li>• /analytics/predictive/trends</li>
                <li>• /analytics/performance/system</li>
              </ul>
            </div>
            <button 
              onClick={fetchAnalyticsData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry Data Loading
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default RealTimeAnalyticsDashboard;