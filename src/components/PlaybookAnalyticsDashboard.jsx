/**
 * 🏢 ENTERPRISE PLAYBOOK ANALYTICS DASHBOARD
 *
 * Phase 3 Frontend Component
 * Comprehensive performance analytics and business impact metrics
 *
 * Business Value:
 * - ROI tracking and cost savings visualization
 * - Performance optimization insights
 * - Trend analysis for continuous improvement
 * - Executive-ready reporting
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState, useEffect } from 'react';

const PlaybookAnalyticsDashboard = ({ playbook, onClose, getAuthHeaders, API_BASE_URL }) => {
  const [analytics, setAnalytics] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    fetchAnalytics();
    fetchPerformance();
  }, [playbook.id, timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/analytics?days=${timeRange}`,
        {
          credentials: 'include',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        setError('Failed to load analytics');
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/performance`,
        {
          credentials: 'include',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPerformance(data);
      }
    } catch (err) {
      console.error('Error fetching performance:', err);
    }
  };

  const getHealthScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getHealthScoreLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-2xl font-semibold">📊 Analytics Dashboard</h3>
              <p className="text-sm text-gray-600 mt-1">
                Playbook: <span className="font-medium">{playbook.name}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl"
            >
              ×
            </button>
          </div>

          {/* Time Range Selector */}
          <div className="flex gap-2">
            {[7, 14, 30, 60, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  timeRange === days
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {days} Days
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-4">Loading analytics...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800">❌ {error}</p>
            </div>
          )}

          {!loading && !error && analytics && performance && (
            <div className="space-y-6">
              {/* Health Score Card */}
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm opacity-90">Overall Health Score</p>
                    <h2 className={`text-5xl font-bold mt-2 ${getHealthScoreColor(performance.health_score)}`}>
                      {performance.health_score.toFixed(0)}
                    </h2>
                    <p className="text-lg mt-1 opacity-90">{getHealthScoreLabel(performance.health_score)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm opacity-90">Trending</p>
                    <div className="text-4xl mt-2">
                      {performance.trending_up ? '📈' : '📉'}
                    </div>
                    <p className="text-sm mt-1 opacity-90">
                      {performance.trending_up ? 'Improving' : 'Declining'}
                    </p>
                  </div>
                </div>

                {/* Alerts */}
                {performance.alerts && performance.alerts.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white border-opacity-30">
                    <p className="text-sm font-medium mb-2">⚠️ Active Alerts</p>
                    <div className="space-y-1">
                      {performance.alerts.map((alert, idx) => (
                        <p key={idx} className="text-sm bg-white bg-opacity-20 rounded px-3 py-1">
                          {alert}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Total Executions */}
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Total Executions</p>
                  <p className="text-3xl font-bold text-gray-900">{analytics.total_executions}</p>
                  <p className="text-xs text-gray-500 mt-1">Last {timeRange} days</p>
                </div>

                {/* Success Rate */}
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Success Rate</p>
                  <p className="text-3xl font-bold text-green-600">
                    {analytics.success_rate_percent.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {analytics.successful_executions} / {analytics.total_executions}
                  </p>
                </div>

                {/* Cost Savings */}
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Cost Savings</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {formatCurrency(analytics.total_cost_savings)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Last {timeRange} days</p>
                </div>

                {/* Manual Approvals Avoided */}
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-xs text-gray-600 mb-1">Manual Approvals Avoided</p>
                  <p className="text-3xl font-bold text-purple-600">{analytics.manual_approvals_avoided}</p>
                  <p className="text-xs text-gray-500 mt-1">Automation impact</p>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h4 className="font-semibold text-lg mb-4">⚡ Performance Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Average Duration</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatDuration(analytics.avg_duration_ms)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Min Duration</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatDuration(analytics.min_duration_ms)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Max Duration</p>
                    <p className="text-2xl font-bold text-red-600">
                      {formatDuration(analytics.max_duration_ms)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">P50 (Median)</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatDuration(analytics.p50_duration_ms)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">P95</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {formatDuration(analytics.p95_duration_ms)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">P99</p>
                    <p className="text-2xl font-bold text-red-600">
                      {formatDuration(analytics.p99_duration_ms)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Recent Performance (24h & 7d) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Last 24 Hours */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-3">📅 Last 24 Hours</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-800">Executions:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {performance.last_24h_executions}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-800">Success Rate:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {performance.last_24h_success_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-800">Avg Duration:</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {formatDuration(performance.last_24h_avg_duration_ms)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Last 7 Days */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-semibold text-purple-900 mb-3">📊 Last 7 Days</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-800">Executions:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {performance.last_7d_executions}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-800">Success Rate:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {performance.last_7d_success_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-purple-800">Cost Savings:</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {formatCurrency(performance.last_7d_cost_savings)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Most Common Triggers */}
              {analytics.most_common_triggers && analytics.most_common_triggers.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-lg mb-4">🎯 Most Common Triggers</h4>
                  <div className="space-y-2">
                    {analytics.most_common_triggers.map((trigger, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-100 rounded-full h-8 overflow-hidden">
                          <div
                            className="bg-blue-500 h-full flex items-center px-3 text-white text-sm font-medium"
                            style={{
                              width: `${(trigger.count / analytics.total_executions) * 100}%`,
                              minWidth: '100px'
                            }}
                          >
                            {trigger.trigger}
                          </div>
                        </div>
                        <span className="text-sm font-semibold text-gray-700 w-16 text-right">
                          {trigger.count}x
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Execution Trend Chart (Simple Bar Chart) */}
              {analytics.executions_by_day && analytics.executions_by_day.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-lg mb-4">📈 Execution Trend</h4>
                  <div className="flex items-end gap-1 h-48">
                    {analytics.executions_by_day.map((day, idx) => {
                      const maxCount = Math.max(...analytics.executions_by_day.map(d => d.count));
                      const height = maxCount > 0 ? (day.count / maxCount) * 100 : 0;
                      return (
                        <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                          <div
                            className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors"
                            style={{ height: `${height}%`, minHeight: day.count > 0 ? '4px' : '0px' }}
                            title={`${new Date(day.date).toLocaleDateString()}: ${day.count} executions`}
                          ></div>
                          {idx % Math.ceil(analytics.executions_by_day.length / 10) === 0 && (
                            <p className="text-xs text-gray-500 transform rotate-45 origin-top-left mt-2">
                              {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Success Rate Trend */}
              {analytics.success_rate_by_day && analytics.success_rate_by_day.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-lg mb-4">✅ Success Rate Trend</h4>
                  <div className="flex items-end gap-1 h-48">
                    {analytics.success_rate_by_day.map((day, idx) => {
                      const height = day.success_rate;
                      const color = height >= 90 ? 'bg-green-500' : height >= 70 ? 'bg-yellow-500' : 'bg-red-500';
                      return (
                        <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                          <div
                            className={`w-full ${color} rounded-t hover:opacity-80 transition-opacity`}
                            style={{ height: `${height}%`, minHeight: '2px' }}
                            title={`${new Date(day.date).toLocaleDateString()}: ${day.success_rate.toFixed(1)}%`}
                          ></div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between mt-2 text-xs text-gray-600">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {!loading && !error && (!analytics || analytics.total_executions === 0) && (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-600">No analytics data available yet</p>
              <p className="text-sm text-gray-500 mt-2">Execute the playbook to start collecting metrics</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-600">
              💡 <strong>Pro Tip:</strong> Use analytics to optimize playbook configuration and maximize ROI
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaybookAnalyticsDashboard;
