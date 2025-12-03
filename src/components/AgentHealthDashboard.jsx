import React, { useState, useEffect, useCallback } from "react";
import fetchWithAuth from "../utils/fetchWithAuth";

/**
 * SEC-050: Enterprise Agent Health Monitoring Dashboard
 * ======================================================
 *
 * Datadog-style agent health monitoring with:
 * - Real-time health status overview
 * - Performance metrics visualization
 * - Problem agent identification
 * - Recent health status changes
 *
 * Banking-Level Security: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6
 */
const AgentHealthDashboard = () => {
  // State
  const [healthSummary, setHealthSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentDetails, setAgentDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  // Fetch health summary
  const fetchHealthSummary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchWithAuth("/api/agents/health/summary");
      setHealthSummary(data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("SEC-050: Failed to fetch health summary:", err);
      setError("Failed to load agent health data. The service may still be deploying.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch agent details
  const fetchAgentDetails = useCallback(async (agentId) => {
    try {
      setDetailsLoading(true);
      const data = await fetchWithAuth(`/api/agents/health/${agentId}`);
      setAgentDetails(data);
    } catch (err) {
      console.error("SEC-050: Failed to fetch agent details:", err);
      setAgentDetails(null);
    } finally {
      setDetailsLoading(false);
    }
  }, []);

  // Trigger manual health check
  const triggerHealthCheck = async () => {
    try {
      await fetchWithAuth("/api/agents/health/check", { method: "POST" });
      await fetchHealthSummary();
    } catch (err) {
      console.error("SEC-050: Failed to trigger health check:", err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchHealthSummary();
  }, [fetchHealthSummary]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchHealthSummary();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchHealthSummary]);

  // Load agent details when selected
  useEffect(() => {
    if (selectedAgent) {
      fetchAgentDetails(selectedAgent);
    }
  }, [selectedAgent, fetchAgentDetails]);

  // Health status color mapping
  const getStatusColor = (status) => {
    const colors = {
      online: { bg: "#dcfce7", text: "#166534", border: "#86efac" },
      degraded: { bg: "#fef3c7", text: "#92400e", border: "#fcd34d" },
      offline: { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" },
      unknown: { bg: "#f3f4f6", text: "#6b7280", border: "#d1d5db" }
    };
    return colors[status] || colors.unknown;
  };

  // Health score color
  const getScoreColor = (score) => {
    if (score >= 90) return "#16a34a";
    if (score >= 70) return "#ca8a04";
    if (score >= 50) return "#ea580c";
    return "#dc2626";
  };

  // Format time ago
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return "Never";
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Styles
  const styles = {
    container: {
      padding: "24px",
      backgroundColor: "#f9fafb",
      minHeight: "100vh"
    },
    header: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "24px"
    },
    title: {
      fontSize: "24px",
      fontWeight: "600",
      color: "#111827",
      margin: 0,
      display: "flex",
      alignItems: "center",
      gap: "12px"
    },
    subtitle: {
      fontSize: "14px",
      color: "#6b7280",
      margin: "4px 0 0 0"
    },
    controls: {
      display: "flex",
      alignItems: "center",
      gap: "16px"
    },
    refreshButton: {
      padding: "8px 16px",
      backgroundColor: "#4f46e5",
      color: "white",
      border: "none",
      borderRadius: "6px",
      fontSize: "14px",
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      gap: "8px"
    },
    autoRefreshToggle: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      fontSize: "14px",
      color: "#6b7280"
    },
    overviewGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
      gap: "16px",
      marginBottom: "24px"
    },
    statCard: {
      backgroundColor: "white",
      borderRadius: "8px",
      padding: "20px",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
    },
    statValue: {
      fontSize: "32px",
      fontWeight: "700",
      marginBottom: "4px"
    },
    statLabel: {
      fontSize: "14px",
      color: "#6b7280"
    },
    statusGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: "16px",
      marginBottom: "24px"
    },
    statusCard: (status) => ({
      backgroundColor: getStatusColor(status).bg,
      borderRadius: "8px",
      padding: "16px",
      border: `1px solid ${getStatusColor(status).border}`,
      textAlign: "center"
    }),
    statusCount: (status) => ({
      fontSize: "36px",
      fontWeight: "700",
      color: getStatusColor(status).text
    }),
    statusLabel: (status) => ({
      fontSize: "14px",
      color: getStatusColor(status).text,
      textTransform: "capitalize"
    }),
    section: {
      backgroundColor: "white",
      borderRadius: "8px",
      padding: "20px",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      marginBottom: "24px"
    },
    sectionTitle: {
      fontSize: "18px",
      fontWeight: "600",
      color: "#111827",
      marginBottom: "16px",
      display: "flex",
      alignItems: "center",
      gap: "8px"
    },
    table: {
      width: "100%",
      borderCollapse: "collapse"
    },
    th: {
      textAlign: "left",
      padding: "12px",
      borderBottom: "2px solid #e5e7eb",
      fontSize: "12px",
      fontWeight: "600",
      color: "#6b7280",
      textTransform: "uppercase"
    },
    td: {
      padding: "12px",
      borderBottom: "1px solid #f3f4f6",
      fontSize: "14px",
      color: "#111827"
    },
    statusBadge: (status) => ({
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
      padding: "4px 10px",
      borderRadius: "9999px",
      fontSize: "12px",
      fontWeight: "500",
      backgroundColor: getStatusColor(status).bg,
      color: getStatusColor(status).text
    }),
    agentRow: {
      cursor: "pointer",
      transition: "background-color 0.15s"
    },
    detailsPanel: {
      backgroundColor: "#f9fafb",
      borderRadius: "8px",
      padding: "20px",
      marginTop: "16px"
    },
    metricsGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: "16px",
      marginTop: "16px"
    },
    metricCard: {
      backgroundColor: "white",
      borderRadius: "6px",
      padding: "16px",
      textAlign: "center"
    },
    metricValue: {
      fontSize: "24px",
      fontWeight: "600",
      color: "#111827"
    },
    metricLabel: {
      fontSize: "12px",
      color: "#6b7280",
      marginTop: "4px"
    },
    emptyState: {
      textAlign: "center",
      padding: "48px",
      color: "#6b7280"
    },
    loadingSpinner: {
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      padding: "48px"
    },
    errorState: {
      backgroundColor: "#fef2f2",
      border: "1px solid #fca5a5",
      borderRadius: "8px",
      padding: "16px",
      color: "#991b1b",
      textAlign: "center"
    },
    changesList: {
      listStyle: "none",
      padding: 0,
      margin: 0,
      maxHeight: "200px",
      overflowY: "auto"
    },
    changeItem: {
      display: "flex",
      alignItems: "center",
      gap: "12px",
      padding: "8px 0",
      borderBottom: "1px solid #f3f4f6",
      fontSize: "13px"
    },
    refreshInfo: {
      fontSize: "12px",
      color: "#9ca3af"
    },
    healthBar: {
      width: "100%",
      height: "8px",
      backgroundColor: "#e5e7eb",
      borderRadius: "4px",
      overflow: "hidden",
      marginTop: "8px"
    },
    healthBarFill: (score) => ({
      width: `${score}%`,
      height: "100%",
      backgroundColor: getScoreColor(score),
      borderRadius: "4px",
      transition: "width 0.5s ease"
    })
  };

  // Render loading state
  if (loading && !healthSummary) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingSpinner}>
          <div className="spinner" />
          <span style={{ marginLeft: "12px", color: "#6b7280" }}>Loading agent health data...</span>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && !healthSummary) {
    return (
      <div style={styles.container}>
        <div style={styles.errorState}>
          <p>{error}</p>
          <button onClick={fetchHealthSummary} style={{ ...styles.refreshButton, marginTop: "12px" }}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = healthSummary?.summary || {};
  const metrics = healthSummary?.metrics || {};
  const problemAgents = healthSummary?.problem_agents || [];
  const recentChanges = healthSummary?.recent_changes || [];

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>
            <span style={{ fontSize: "28px" }}>&#128200;</span>
            Agent Health Monitoring
          </h1>
          <p style={styles.subtitle}>
            SEC-050: Real-time monitoring of agent connectivity and performance
          </p>
        </div>
        <div style={styles.controls}>
          <div style={styles.autoRefreshToggle}>
            <input
              type="checkbox"
              id="autoRefresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <label htmlFor="autoRefresh">Auto-refresh</label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              style={{
                marginLeft: "8px",
                padding: "4px 8px",
                borderRadius: "4px",
                border: "1px solid #d1d5db",
                fontSize: "13px"
              }}
              disabled={!autoRefresh}
            >
              <option value={15}>15s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
              <option value={120}>2m</option>
            </select>
          </div>
          <button onClick={triggerHealthCheck} style={styles.refreshButton}>
            <span>&#8635;</span> Refresh Now
          </button>
          {lastRefresh && (
            <span style={styles.refreshInfo}>
              Last updated: {formatTimeAgo(lastRefresh)}
            </span>
          )}
        </div>
      </div>

      {/* Health Score Overview */}
      <div style={styles.overviewGrid}>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: getScoreColor(summary.health_score || 0) }}>
            {summary.health_score || 0}%
          </div>
          <div style={styles.statLabel}>Overall Health Score</div>
          <div style={styles.healthBar}>
            <div style={styles.healthBarFill(summary.health_score || 0)} />
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{summary.total_agents || 0}</div>
          <div style={styles.statLabel}>Total Agents</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{metrics.total_requests_24h?.toLocaleString() || 0}</div>
          <div style={styles.statLabel}>Requests (24h)</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{metrics.avg_response_time_ms || 0}ms</div>
          <div style={styles.statLabel}>Avg Response Time</div>
        </div>
      </div>

      {/* Status Cards */}
      <div style={styles.statusGrid}>
        <div style={styles.statusCard("online")}>
          <div style={styles.statusCount("online")}>{summary.online || 0}</div>
          <div style={styles.statusLabel("online")}>Online</div>
        </div>
        <div style={styles.statusCard("degraded")}>
          <div style={styles.statusCount("degraded")}>{summary.degraded || 0}</div>
          <div style={styles.statusLabel("degraded")}>Degraded</div>
        </div>
        <div style={styles.statusCard("offline")}>
          <div style={styles.statusCount("offline")}>{summary.offline || 0}</div>
          <div style={styles.statusLabel("offline")}>Offline</div>
        </div>
        <div style={styles.statusCard("unknown")}>
          <div style={styles.statusCount("unknown")}>{summary.unknown || 0}</div>
          <div style={styles.statusLabel("unknown")}>Unknown</div>
        </div>
      </div>

      {/* Problem Agents */}
      {problemAgents.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>
            <span style={{ color: "#dc2626" }}>&#9888;</span>
            Agents Requiring Attention
          </h2>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Agent</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Last Heartbeat</th>
                <th style={styles.th}>Missed</th>
                <th style={styles.th}>Last Error</th>
              </tr>
            </thead>
            <tbody>
              {problemAgents.map((agent) => (
                <tr
                  key={agent.agent_id}
                  style={styles.agentRow}
                  onClick={() => setSelectedAgent(agent.agent_id)}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#f9fafb"}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = "transparent"}
                >
                  <td style={styles.td}>
                    <strong>{agent.display_name}</strong>
                    <br />
                    <span style={{ fontSize: "12px", color: "#6b7280" }}>{agent.agent_id}</span>
                  </td>
                  <td style={styles.td}>
                    <span style={styles.statusBadge(agent.health_status)}>
                      <span style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: "currentColor"
                      }} />
                      {agent.health_status}
                    </span>
                  </td>
                  <td style={styles.td}>{formatTimeAgo(agent.last_heartbeat)}</td>
                  <td style={styles.td}>{agent.missed_heartbeats}</td>
                  <td style={{ ...styles.td, maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {agent.last_error || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Agent Details Panel */}
      {selectedAgent && agentDetails && (
        <div style={styles.section}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={styles.sectionTitle}>
              <span>&#128300;</span>
              Agent Details: {agentDetails.display_name}
            </h2>
            <button
              onClick={() => setSelectedAgent(null)}
              style={{
                background: "none",
                border: "none",
                fontSize: "20px",
                cursor: "pointer",
                color: "#6b7280"
              }}
            >
              &times;
            </button>
          </div>

          {detailsLoading ? (
            <div style={{ textAlign: "center", padding: "24px", color: "#6b7280" }}>
              Loading agent details...
            </div>
          ) : (
            <div style={styles.detailsPanel}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                <div>
                  <h4 style={{ margin: "0 0 12px 0", color: "#374151" }}>Health Status</h4>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Status:</strong>{" "}
                    <span style={styles.statusBadge(agentDetails.health?.current_status)}>
                      {agentDetails.health?.current_status}
                    </span>
                  </p>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Last Heartbeat:</strong> {formatTimeAgo(agentDetails.health?.last_heartbeat)}
                  </p>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Heartbeat Interval:</strong> {agentDetails.health?.heartbeat_interval_seconds}s
                  </p>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Uptime (24h):</strong> {agentDetails.health?.uptime_percent_24h}%
                  </p>
                </div>
                <div>
                  <h4 style={{ margin: "0 0 12px 0", color: "#374151" }}>Agent Info</h4>
                  <p style={{ margin: "4px 0" }}>
                    <strong>ID:</strong> {agentDetails.agent_id}
                  </p>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Type:</strong> {agentDetails.agent_type}
                  </p>
                  <p style={{ margin: "4px 0" }}>
                    <strong>Status:</strong> {agentDetails.status}
                  </p>
                </div>
              </div>

              <div style={styles.metricsGrid}>
                <div style={styles.metricCard}>
                  <div style={styles.metricValue}>{agentDetails.metrics?.avg_response_time_ms || 0}ms</div>
                  <div style={styles.metricLabel}>Avg Response Time</div>
                </div>
                <div style={styles.metricCard}>
                  <div style={styles.metricValue}>{agentDetails.metrics?.error_rate_percent || 0}%</div>
                  <div style={styles.metricLabel}>Error Rate</div>
                </div>
                <div style={styles.metricCard}>
                  <div style={styles.metricValue}>{agentDetails.metrics?.total_requests_24h?.toLocaleString() || 0}</div>
                  <div style={styles.metricLabel}>Requests (24h)</div>
                </div>
              </div>

              {agentDetails.errors?.last_error && (
                <div style={{
                  marginTop: "16px",
                  padding: "12px",
                  backgroundColor: "#fef2f2",
                  borderRadius: "6px",
                  border: "1px solid #fca5a5"
                }}>
                  <strong style={{ color: "#991b1b" }}>Last Error:</strong>
                  <p style={{ margin: "8px 0 0 0", color: "#7f1d1d", fontSize: "13px" }}>
                    {agentDetails.errors.last_error}
                  </p>
                  <span style={{ fontSize: "11px", color: "#9ca3af" }}>
                    {formatTimeAgo(agentDetails.errors.last_error_at)}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Recent Status Changes */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>
          <span>&#128197;</span>
          Recent Status Changes (24h)
        </h2>
        {recentChanges.length === 0 ? (
          <div style={styles.emptyState}>
            <p>No status changes in the last 24 hours</p>
          </div>
        ) : (
          <ul style={styles.changesList}>
            {recentChanges.map((change, index) => (
              <li key={index} style={styles.changeItem}>
                <span style={{
                  ...styles.statusBadge(change.previous_status),
                  fontSize: "11px",
                  padding: "2px 6px"
                }}>
                  {change.previous_status}
                </span>
                <span style={{ color: "#6b7280" }}>&#8594;</span>
                <span style={{
                  ...styles.statusBadge(change.new_status),
                  fontSize: "11px",
                  padding: "2px 6px"
                }}>
                  {change.new_status}
                </span>
                <span style={{ color: "#6b7280", flex: 1 }}>{change.agent_id}</span>
                <span style={{ color: "#9ca3af", fontSize: "12px" }}>
                  {formatTimeAgo(change.timestamp)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Empty state if no agents */}
      {summary.total_agents === 0 && (
        <div style={styles.section}>
          <div style={styles.emptyState}>
            <h3>No Agents Registered</h3>
            <p>Register your first agent to start monitoring its health.</p>
            <p style={{ fontSize: "13px", color: "#9ca3af" }}>
              Go to Agent Registry &gt; Register New Agent to get started.
            </p>
          </div>
        </div>
      )}

      {/* Compliance Footer */}
      <div style={{
        textAlign: "center",
        padding: "16px",
        color: "#9ca3af",
        fontSize: "12px"
      }}>
        SEC-050: Enterprise Agent Health Monitoring | SOC 2 CC7.1 | NIST SI-4 | PCI-DSS 10.6
      </div>
    </div>
  );
};

export default AgentHealthDashboard;
