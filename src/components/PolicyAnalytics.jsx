import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Shield, AlertCircle, Activity } from 'lucide-react';

export const PolicyAnalytics = ({ API_BASE_URL, getAuthHeaders }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/engine-metrics`,
        { credentials: "include", headers: getAuthHeaders() }
      );
      const data = await response.json();
      // SEC-076-FE: Unwrap metrics from response structure {success, metrics, message}
      setMetrics(data.metrics || data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-6">Loading analytics...</div>;

  const totalEvaluations = metrics?.total_evaluations || 0;
  const denials = metrics?.denials || 0;
  const approvals = metrics?.approvals_required || 0;
  const allows = totalEvaluations - denials - approvals;
  const denialRate = totalEvaluations > 0 ? ((denials / totalEvaluations) * 100).toFixed(1) : 0;
  const cacheHitRate = metrics?.total_evaluations > 0 
    ? ((metrics.cache_hits / metrics.total_evaluations) * 100).toFixed(1) 
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-blue-600" />
          Policy Analytics
        </h3>
        <button
          onClick={loadMetrics}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          icon={Activity}
          label="Total Evaluations"
          value={totalEvaluations.toLocaleString()}
          color="blue"
        />
        <MetricCard
          icon={Shield}
          label="Allowed"
          value={allows.toLocaleString()}
          color="green"
          percentage={totalEvaluations > 0 ? ((allows / totalEvaluations) * 100).toFixed(1) : 0}
        />
        <MetricCard
          icon={AlertCircle}
          label="Denied"
          value={denials.toLocaleString()}
          color="red"
          percentage={denialRate}
        />
        <MetricCard
          icon={TrendingUp}
          label="Approvals Required"
          value={approvals.toLocaleString()}
          color="yellow"
          percentage={totalEvaluations > 0 ? ((approvals / totalEvaluations) * 100).toFixed(1) : 0}
        />
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-semibold mb-4">Performance</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="border rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Cache Hit Rate</div>
            <div className="text-2xl font-bold text-green-600">{cacheHitRate}%</div>
            <div className="text-xs text-gray-500 mt-1">
              {metrics?.cache_hits || 0} cached / {totalEvaluations} total
            </div>
          </div>
          <div className="border rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Active Policies</div>
            <div className="text-2xl font-bold text-blue-600">{metrics?.loaded_policies || 0}</div>
            <div className="text-xs text-gray-500 mt-1">Currently enforcing</div>
          </div>
        </div>
      </div>

      {/* Policy Effectiveness Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-semibold mb-4">Policy Decision Distribution</h4>
        <div className="space-y-3">
          <PolicyBar label="Allowed" count={allows} total={totalEvaluations} color="green" />
          <PolicyBar label="Denied" count={denials} total={totalEvaluations} color="red" />
          <PolicyBar label="Approval Required" count={approvals} total={totalEvaluations} color="yellow" />
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ icon: Icon, label, value, color, percentage }) => {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600'
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        {percentage && (
          <span className="text-sm font-medium text-gray-600">{percentage}%</span>
        )}
      </div>
      <div className="text-sm text-gray-600">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  );
};

const PolicyBar = ({ label, count, total, color }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  const colors = {
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500'
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{label}</span>
        <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full ${colors[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default PolicyAnalytics;
