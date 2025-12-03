import React, { useState, useEffect, useCallback } from "react";
import fetchWithAuth from "../utils/fetchWithAuth";

/**
 * SEC-051: Enterprise Integration Health Dashboard
 * =================================================
 *
 * Datadog-style integration health monitoring with:
 * - Real-time health status overview
 * - Integration status table with filtering
 * - Problem integrations requiring attention
 * - Performance metrics (latency, uptime)
 *
 * Banking-Level Security: SOC 2 CC7.1, NIST SI-4, PCI-DSS 10.6
 */
const IntegrationHealthDashboard = () => {
  // State
  const [healthSummary, setHealthSummary] = useState(null);
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [testingId, setTestingId] = useState(null);
  const [testResult, setTestResult] = useState(null);

  // Fetch health summary
  const fetchHealthSummary = useCallback(async () => {
    try {
      const data = await fetchWithAuth("/api/integrations/health/summary");
      setHealthSummary(data);
      // SEC-051: Clear any previous health summary error on success
      setError(null);
    } catch (err) {
      console.error("SEC-051: Failed to fetch health summary:", err);
      // SEC-051: Notify user of health summary fetch failure
      setError("Failed to load health summary. Please try refreshing.");
    }
  }, []);

  // Fetch integrations list
  const fetchIntegrations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("health_status", statusFilter);
      if (typeFilter !== "all") params.append("integration_type", typeFilter);

      const url = `/api/integrations${params.toString() ? `?${params.toString()}` : ""}`;
      const data = await fetchWithAuth(url);
      setIntegrations(data.integrations || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("SEC-051: Failed to fetch integrations:", err);
      setError("Failed to load integrations. The service may still be deploying.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter]);

  // Test integration connection
  const testConnection = async (integrationId) => {
    setTestingId(integrationId);
    setTestResult(null);
    try {
      const result = await fetchWithAuth(`/api/integrations/${integrationId}/health-check`, {
        method: "POST"
      });
      setTestResult({ id: integrationId, success: result.is_healthy, data: result });
      // Refresh data after test
      await fetchHealthSummary();
      await fetchIntegrations();
    } catch (err) {
      setTestResult({ id: integrationId, success: false, error: err.message });
    } finally {
      setTestingId(null);
    }
  };

  // Initial load
  useEffect(() => {
    fetchHealthSummary();
    fetchIntegrations();
  }, [fetchHealthSummary, fetchIntegrations]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchHealthSummary();
      fetchIntegrations();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchHealthSummary, fetchIntegrations]);

  // Health status color mapping
  const getStatusColor = (status) => {
    const colors = {
      healthy: { bg: "#dcfce7", text: "#166534", border: "#86efac" },
      degraded: { bg: "#fef3c7", text: "#92400e", border: "#fcd34d" },
      unhealthy: { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" },
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

  // Integration type display names
  const typeDisplayNames = {
    webhook: "Webhook",
    slack: "Slack",
    teams: "Microsoft Teams",
    servicenow: "ServiceNow",
    siem: "SIEM",
    splunk: "Splunk",
    qradar: "QRadar",
    sentinel: "Microsoft Sentinel",
    compliance: "Compliance",
    email: "Email",
    custom: "Custom"
  };

  // Styles
  const styles = {
    container: {
      padding: "24px",
      backgroundColor: "#f9fafb",
      minHeight: "100%"
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
    overviewGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
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
      textAlign: "center",
      cursor: "pointer",
      transition: "transform 0.1s"
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
    filterRow: {
      display: "flex",
      gap: "12px",
      marginBottom: "16px",
      alignItems: "center"
    },
    filterSelect: {
      padding: "8px 12px",
      borderRadius: "6px",
      border: "1px solid #d1d5db",
      fontSize: "14px",
      backgroundColor: "white"
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
    testButton: {
      padding: "6px 12px",
      backgroundColor: "#f3f4f6",
      border: "1px solid #d1d5db",
      borderRadius: "4px",
      fontSize: "12px",
      cursor: "pointer"
    },
    emptyState: {
      textAlign: "center",
      padding: "48px",
      color: "#6b7280"
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
    }),
    refreshInfo: {
      fontSize: "12px",
      color: "#9ca3af"
    }
  };

  const summary = healthSummary?.summary || {};
  const metrics = healthSummary?.metrics || {};
  const problemIntegrations = healthSummary?.problem_integrations || [];

  // Render loading state
  if (loading && integrations.length === 0) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: "center", padding: "48px" }}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p style={{ marginTop: "16px", color: "#6b7280" }}>Loading integration health data...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>
            <span style={{ fontSize: "28px" }}>&#128268;</span>
            Integration Health Dashboard
          </h1>
          <p style={styles.subtitle}>
            SEC-051: Real-time monitoring of integration connectivity and performance
          </p>
        </div>
        <div style={styles.controls}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", color: "#6b7280" }}>
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
              style={{ ...styles.filterSelect, marginLeft: "4px" }}
              disabled={!autoRefresh}
            >
              <option value={15}>15s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
              <option value={120}>2m</option>
            </select>
          </div>
          <button
            onClick={() => { fetchHealthSummary(); fetchIntegrations(); }}
            style={styles.refreshButton}
          >
            <span>&#8635;</span> Refresh
          </button>
          {lastRefresh && (
            <span style={styles.refreshInfo}>
              Updated: {formatTimeAgo(lastRefresh)}
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
          <div style={styles.statLabel}>Health Score</div>
          <div style={styles.healthBar}>
            <div style={styles.healthBarFill(summary.health_score || 0)} />
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{summary.total_integrations || 0}</div>
          <div style={styles.statLabel}>Total Integrations</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{metrics.avg_latency_ms || "-"}</div>
          <div style={styles.statLabel}>Avg Latency (ms)</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{metrics.avg_uptime_percent ? `${metrics.avg_uptime_percent}%` : "-"}</div>
          <div style={styles.statLabel}>Avg Uptime (30d)</div>
        </div>
      </div>

      {/* Status Cards - WCAG 2.1 AA Accessible */}
      <div style={styles.statusGrid} role="group" aria-label="Integration health status filters">
        <div
          role="button"
          tabIndex={0}
          aria-label={`Filter by healthy integrations. ${summary.healthy || 0} integrations. ${statusFilter === "healthy" ? "Currently active." : "Click to filter."}`}
          aria-pressed={statusFilter === "healthy"}
          style={styles.statusCard("healthy")}
          onClick={() => setStatusFilter(statusFilter === "healthy" ? "all" : "healthy")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setStatusFilter(statusFilter === "healthy" ? "all" : "healthy");
            }
          }}
        >
          <div style={styles.statusCount("healthy")}>{summary.healthy || 0}</div>
          <div style={styles.statusLabel("healthy")}>Healthy</div>
        </div>
        <div
          role="button"
          tabIndex={0}
          aria-label={`Filter by degraded integrations. ${summary.degraded || 0} integrations. ${statusFilter === "degraded" ? "Currently active." : "Click to filter."}`}
          aria-pressed={statusFilter === "degraded"}
          style={styles.statusCard("degraded")}
          onClick={() => setStatusFilter(statusFilter === "degraded" ? "all" : "degraded")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setStatusFilter(statusFilter === "degraded" ? "all" : "degraded");
            }
          }}
        >
          <div style={styles.statusCount("degraded")}>{summary.degraded || 0}</div>
          <div style={styles.statusLabel("degraded")}>Degraded</div>
        </div>
        <div
          role="button"
          tabIndex={0}
          aria-label={`Filter by unhealthy integrations. ${summary.unhealthy || 0} integrations. ${statusFilter === "unhealthy" ? "Currently active." : "Click to filter."}`}
          aria-pressed={statusFilter === "unhealthy"}
          style={styles.statusCard("unhealthy")}
          onClick={() => setStatusFilter(statusFilter === "unhealthy" ? "all" : "unhealthy")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setStatusFilter(statusFilter === "unhealthy" ? "all" : "unhealthy");
            }
          }}
        >
          <div style={styles.statusCount("unhealthy")}>{summary.unhealthy || 0}</div>
          <div style={styles.statusLabel("unhealthy")}>Unhealthy</div>
        </div>
        <div
          role="button"
          tabIndex={0}
          aria-label={`Filter by unknown status integrations. ${summary.unknown || 0} integrations. ${statusFilter === "unknown" ? "Currently active." : "Click to filter."}`}
          aria-pressed={statusFilter === "unknown"}
          style={styles.statusCard("unknown")}
          onClick={() => setStatusFilter(statusFilter === "unknown" ? "all" : "unknown")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setStatusFilter(statusFilter === "unknown" ? "all" : "unknown");
            }
          }}
        >
          <div style={styles.statusCount("unknown")}>{summary.unknown || 0}</div>
          <div style={styles.statusLabel("unknown")}>Unknown</div>
        </div>
      </div>

      {/* Problem Integrations Alert */}
      {problemIntegrations.length > 0 && (
        <div style={{
          ...styles.section,
          backgroundColor: "#fef2f2",
          border: "1px solid #fca5a5"
        }}>
          <h2 style={{ ...styles.sectionTitle, color: "#991b1b" }}>
            <span>&#9888;</span>
            Integrations Requiring Attention ({problemIntegrations.length})
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {problemIntegrations.map((integration) => (
              <div
                key={integration.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px",
                  backgroundColor: "white",
                  borderRadius: "6px",
                  border: "1px solid #fecaca"
                }}
              >
                <div>
                  <strong style={{ color: "#111827" }}>{integration.display_name || integration.integration_name}</strong>
                  <span style={{ marginLeft: "8px", color: "#6b7280", fontSize: "13px" }}>
                    ({typeDisplayNames[integration.integration_type] || integration.integration_type})
                  </span>
                  <div style={{ fontSize: "13px", color: "#7f1d1d", marginTop: "4px" }}>
                    {integration.consecutive_failures > 0 && `${integration.consecutive_failures} consecutive failures`}
                    {integration.consecutive_failures > 0 && integration.last_health_check && " • "}
                    {integration.last_health_check && `Last check: ${formatTimeAgo(integration.last_health_check)}`}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={styles.statusBadge(integration.health_status)}>
                    {integration.health_status}
                  </span>
                  <button
                    onClick={() => testConnection(integration.id)}
                    disabled={testingId === integration.id}
                    style={{
                      ...styles.testButton,
                      opacity: testingId === integration.id ? 0.5 : 1
                    }}
                  >
                    {testingId === integration.id ? "Testing..." : "Test"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Integration Status Table */}
      <div style={styles.section}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ ...styles.sectionTitle, marginBottom: 0 }}>
            <span>&#128279;</span>
            All Integrations
          </h2>
          <div style={styles.filterRow}>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={styles.filterSelect}
            >
              <option value="all">All Status</option>
              <option value="healthy">Healthy</option>
              <option value="degraded">Degraded</option>
              <option value="unhealthy">Unhealthy</option>
              <option value="unknown">Unknown</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={styles.filterSelect}
            >
              <option value="all">All Types</option>
              <option value="siem">SIEM</option>
              <option value="slack">Slack</option>
              <option value="teams">Teams</option>
              <option value="servicenow">ServiceNow</option>
              <option value="webhook">Webhook</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </div>

        {error ? (
          <div style={styles.emptyState}>
            <p style={{ color: "#991b1b" }}>{error}</p>
            <button onClick={fetchIntegrations} style={{ ...styles.refreshButton, marginTop: "12px" }}>
              Retry
            </button>
          </div>
        ) : integrations.length === 0 ? (
          <div style={styles.emptyState}>
            <h3>No Integrations Found</h3>
            <p>Configure your first integration to start monitoring its health.</p>
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Integration</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Uptime (30d)</th>
                <th style={styles.th}>Last Check</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {integrations.map((integration) => (
                <tr key={integration.id}>
                  <td style={styles.td}>
                    <strong>{integration.display_name || integration.integration_name}</strong>
                    {integration.description && (
                      <div style={{ fontSize: "12px", color: "#6b7280" }}>
                        {integration.description.substring(0, 50)}
                        {integration.description.length > 50 && "..."}
                      </div>
                    )}
                  </td>
                  <td style={styles.td}>
                    {typeDisplayNames[integration.integration_type] || integration.integration_type}
                  </td>
                  <td style={styles.td}>
                    <span style={styles.statusBadge(integration.health_status)}>
                      <span style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: "currentColor"
                      }} />
                      {integration.health_status || "unknown"}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {integration.uptime_percent_30d != null
                      ? `${integration.uptime_percent_30d}%`
                      : "-"}
                  </td>
                  <td style={styles.td}>
                    {formatTimeAgo(integration.last_health_check)}
                  </td>
                  <td style={styles.td}>
                    <button
                      onClick={() => testConnection(integration.id)}
                      disabled={testingId === integration.id}
                      style={{
                        ...styles.testButton,
                        opacity: testingId === integration.id ? 0.5 : 1
                      }}
                    >
                      {testingId === integration.id ? "Testing..." : "Test Connection"}
                    </button>
                    {testResult && testResult.id === integration.id && (
                      <span style={{
                        marginLeft: "8px",
                        fontSize: "12px",
                        color: testResult.success ? "#16a34a" : "#dc2626"
                      }}>
                        {testResult.success ? "✓ Passed" : "✗ Failed"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Compliance Footer */}
      <div style={{
        textAlign: "center",
        padding: "16px",
        color: "#9ca3af",
        fontSize: "12px"
      }}>
        SEC-051: Enterprise Integration Health Monitoring | SOC 2 CC7.1 | NIST SI-4 | PCI-DSS 10.6
      </div>
    </div>
  );
};

export default IntegrationHealthDashboard;
