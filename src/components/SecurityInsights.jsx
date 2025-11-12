/**
 * SecurityInsights Component - Enterprise Edition
 * Professional analytics dashboard for security insights
 *
 * Refactored: 2025-11-12
 * Changes: Enterprise theme, enhanced visualizations, loading/error states
 */

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
  Legend,
} from "recharts";

// Enterprise components
import EnterpriseCard from "./enterprise/EnterpriseCard";
import SkeletonCard, { ChartSkeleton } from "./enterprise/SkeletonCard";
import ErrorCard from "./enterprise/ErrorCard";
import EmptyCard, { SuccessEmpty } from "./enterprise/EmptyCard";
import ENTERPRISE_THEME, { getRiskColor, getRiskLabel } from "./enterprise/EnterpriseTheme";

const SecurityInsights = ({ getAuthHeaders }) => {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log("🔍 Fetching insights from:", `${API_BASE_URL}/api/analytics/trends`);
      const res = await fetch(`${API_BASE_URL}/api/analytics/trends`, {
        credentials: "include",
        headers: getAuthHeaders(),
      });

      if (!res.ok) {
        throw new Error(`API returned ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      console.log("📊 SecurityInsights API Response:", data);

      setTrends({
        high_risk_actions_by_day: data.high_risk_actions_by_day || [],
        top_agents: data.top_agents || [],
        top_tools: data.top_tools || [],
        enriched_actions: data.enriched_actions || [],
      });
    } catch (err) {
      console.error("SecurityInsights fetch error:", err);
      setError(err.message || "Failed to load insights data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [getAuthHeaders]);

  // Loading state
  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="mb-6">
          <h2
            className="text-2xl font-bold"
            style={{
              color: ENTERPRISE_THEME.ui.text,
              fontSize: ENTERPRISE_THEME.typography.fontSize['2xl'],
            }}
          >
            Security Insights
          </h2>
          <p
            className="mt-1"
            style={{
              color: ENTERPRISE_THEME.ui.textMuted,
              fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
            }}
          >
            Comprehensive analytics and behavior tracking
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard variant="chart" />
          <SkeletonCard variant="chart" />
          <SkeletonCard variant="chart" />
          <SkeletonCard variant="list" className="lg:col-span-2" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2
            className="text-2xl font-bold"
            style={{ color: ENTERPRISE_THEME.ui.text }}
          >
            Security Insights
          </h2>
        </div>
        <ErrorCard
          title="Failed to Load Analytics Data"
          message={error}
          onRetry={fetchInsights}
          showDetails={true}
          details={{ error, timestamp: new Date().toISOString() }}
        />
      </div>
    );
  }

  // Check if any data exists
  const hasAnyData =
    trends &&
    (trends.high_risk_actions_by_day?.length > 0 ||
      trends.top_agents?.length > 0 ||
      trends.top_tools?.length > 0 ||
      trends.enriched_actions?.length > 0);

  // Empty state
  if (!hasAnyData) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2
            className="text-2xl font-bold"
            style={{ color: ENTERPRISE_THEME.ui.text }}
          >
            Security Insights
          </h2>
        </div>
        <SuccessEmpty
          title="No Security Insights Yet"
          message="Submit agent actions to populate this dashboard with analytics, trends, and behavior insights."
        />
      </div>
    );
  }

  // Enterprise chart colors
  const CHART_COLORS = Object.values(ENTERPRISE_THEME.chart);

  // Custom tooltip for bar chart
  const CustomBarTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div
          className="p-3 rounded-lg shadow-lg"
          style={{
            backgroundColor: 'white',
            border: `1px solid ${ENTERPRISE_THEME.ui.border}`,
          }}
        >
          <p
            className="font-medium"
            style={{ color: ENTERPRISE_THEME.ui.text }}
          >
            {payload[0].payload.date}
          </p>
          <p
            className="text-sm mt-1"
            style={{ color: ENTERPRISE_THEME.status.danger }}
          >
            High-Risk Actions: <strong>{payload[0].value}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  // Custom tooltip for pie charts
  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div
          className="p-3 rounded-lg shadow-lg"
          style={{
            backgroundColor: 'white',
            border: `1px solid ${ENTERPRISE_THEME.ui.border}`,
          }}
        >
          <p
            className="font-medium"
            style={{ color: ENTERPRISE_THEME.ui.text }}
          >
            {data.name}
          </p>
          <p
            className="text-sm mt-1"
            style={{ color: ENTERPRISE_THEME.ui.textSecondary }}
          >
            Count: <strong>{data.value}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h2
          className="text-2xl font-bold"
          style={{
            color: ENTERPRISE_THEME.ui.text,
            fontSize: ENTERPRISE_THEME.typography.fontSize['2xl'],
          }}
        >
          Security Insights
        </h2>
        <p
          className="mt-1"
          style={{
            color: ENTERPRISE_THEME.ui.textMuted,
            fontSize: ENTERPRISE_THEME.typography.fontSize.sm,
          }}
        >
          Real-time analytics and behavioral intelligence for agent actions
        </p>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High-Risk Action Trends */}
        {trends.high_risk_actions_by_day && trends.high_risk_actions_by_day.length > 0 && (
          <EnterpriseCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            }
            title="High-Risk Action Trends"
            subtitle="Last 7 days"
            variant="danger"
            footer={
              <span>
                Total: <strong>{trends.high_risk_actions_by_day.reduce((sum, d) => sum + d.count, 0)}</strong> high-risk actions
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends.high_risk_actions_by_day}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={ENTERPRISE_THEME.status.danger} stopOpacity={0.8} />
                    <stop offset="100%" stopColor={ENTERPRISE_THEME.status.danger} stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={ENTERPRISE_THEME.ui.border} />
                <XAxis
                  dataKey="date"
                  stroke={ENTERPRISE_THEME.ui.textMuted}
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  allowDecimals={false}
                  stroke={ENTERPRISE_THEME.ui.textMuted}
                  style={{ fontSize: '12px' }}
                />
                <Tooltip content={<CustomBarTooltip />} />
                <Bar
                  dataKey="count"
                  fill="url(#barGradient)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </EnterpriseCard>
        )}

        {/* Most Active Agents */}
        {trends.top_agents && trends.top_agents.length > 0 && (
          <EnterpriseCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            }
            title="Most Active Agents"
            subtitle={`Top ${trends.top_agents.length} agents by action count`}
            variant="info"
            footer={
              <span>
                Total agents: <strong>{trends.top_agents.length}</strong>
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trends.top_agents}
                  dataKey="count"
                  nameKey="agent"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {trends.top_agents.map((_, index) => (
                    <Cell key={`agent-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </EnterpriseCard>
        )}

        {/* Most Used Tools */}
        {trends.top_tools && trends.top_tools.length > 0 && (
          <EnterpriseCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
            title="Most Used Tools"
            subtitle="Tool distribution by usage count"
            variant="success"
            footer={
              <span>
                Total tools: <strong>{trends.top_tools.length}</strong>
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trends.top_tools}
                  dataKey="count"
                  nameKey="tool"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {trends.top_tools.map((_, index) => (
                    <Cell key={`tool-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </EnterpriseCard>
        )}

        {/* Detailed Agent Behavior Insights */}
        {trends.enriched_actions && trends.enriched_actions.length > 0 && (
          <EnterpriseCard
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
            title="Detailed Agent Behavior Insights"
            subtitle={`Latest ${Math.min(5, trends.enriched_actions.length)} high-priority actions`}
            variant="warning"
            className="lg:col-span-2"
            footer={
              <span>
                Showing <strong>{Math.min(5, trends.enriched_actions.length)}</strong> of{' '}
                <strong>{trends.enriched_actions.length}</strong> total actions
              </span>
            }
          >
            <div className="space-y-4">
              {trends.enriched_actions.slice(0, 5).map((action, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border transition-all hover:shadow-md"
                  style={{
                    backgroundColor: ENTERPRISE_THEME.ui.background,
                    borderColor: ENTERPRISE_THEME.ui.border,
                    borderRadius: ENTERPRISE_THEME.radius.md,
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Agent ID */}
                      <div className="flex items-center space-x-2 mb-2">
                        <span
                          className="text-sm font-medium"
                          style={{ color: ENTERPRISE_THEME.ui.textSecondary }}
                        >
                          Agent:
                        </span>
                        <span
                          className="font-semibold"
                          style={{ color: ENTERPRISE_THEME.ui.text }}
                        >
                          {action.agent_id}
                        </span>
                      </div>

                      {/* Risk Level Badge */}
                      <div className="flex items-center space-x-4 mb-2">
                        <div className="flex items-center space-x-2">
                          <span
                            className="text-sm"
                            style={{ color: ENTERPRISE_THEME.ui.textSecondary }}
                          >
                            Risk:
                          </span>
                          <span
                            className="px-2 py-1 text-xs font-semibold rounded"
                            style={{
                              backgroundColor: `${action.risk_level === 'HIGH' ? ENTERPRISE_THEME.status.danger : action.risk_level === 'MEDIUM' ? ENTERPRISE_THEME.status.warning : ENTERPRISE_THEME.status.success}20`,
                              color: action.risk_level === 'HIGH' ? ENTERPRISE_THEME.status.danger : action.risk_level === 'MEDIUM' ? ENTERPRISE_THEME.status.warning : ENTERPRISE_THEME.status.success,
                            }}
                          >
                            {action.risk_level}
                          </span>
                        </div>

                        {/* MITRE Tactic */}
                        {action.mitre_tactic && (
                          <div className="flex items-center space-x-2">
                            <span
                              className="text-xs"
                              style={{ color: ENTERPRISE_THEME.ui.textMuted }}
                            >
                              MITRE:
                            </span>
                            <span
                              className="text-xs font-mono px-2 py-0.5 rounded"
                              style={{
                                backgroundColor: ENTERPRISE_THEME.ui.background,
                                color: ENTERPRISE_THEME.ui.textSecondary,
                              }}
                            >
                              {action.mitre_tactic}
                            </span>
                          </div>
                        )}

                        {/* NIST Control */}
                        {action.nist_control && (
                          <div className="flex items-center space-x-2">
                            <span
                              className="text-xs"
                              style={{ color: ENTERPRISE_THEME.ui.textMuted }}
                            >
                              NIST:
                            </span>
                            <span
                              className="text-xs font-mono px-2 py-0.5 rounded"
                              style={{
                                backgroundColor: ENTERPRISE_THEME.ui.background,
                                color: ENTERPRISE_THEME.ui.textSecondary,
                              }}
                            >
                              {action.nist_control}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Recommendation */}
                      {action.recommendation && (
                        <div className="mt-2">
                          <p
                            className="text-sm"
                            style={{ color: ENTERPRISE_THEME.ui.textSecondary }}
                          >
                            <span className="font-medium">Recommendation:</span>{' '}
                            {action.recommendation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </EnterpriseCard>
        )}
      </div>
    </div>
  );
};

export default SecurityInsights;
