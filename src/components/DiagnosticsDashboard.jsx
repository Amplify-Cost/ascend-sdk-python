/**
 * SEC-076: Enterprise Diagnostics Dashboard
 * ==========================================
 *
 * Industry-aligned health monitoring dashboard with SIEM export.
 * Patterns from: Wiz.io, Splunk, Datadog
 *
 * Features:
 * - API Health Check
 * - Database Status
 * - Integration Tests
 * - Full Diagnostic Run
 * - SIEM Export (Splunk/Datadog)
 * - Diagnostic History
 *
 * Compliance: SOC 2 CC7.2, PCI-DSS 10.2, HIPAA 164.312, NIST AU-6
 * Author: Ascend Engineer
 * Date: 2025-12-04
 */

import React, { useState, useCallback } from 'react';
import { fetchWithAuth } from '../utils/fetchWithAuth';

const DiagnosticsDashboard = () => {
  const [loading, setLoading] = useState({});
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState('splunk_cim');
  const [exportLoading, setExportLoading] = useState(false);
  const [error, setError] = useState(null);

  // Severity color mapping (Splunk-compatible)
  const getSeverityColor = (severity) => {
    const colors = {
      INFO: 'text-green-600 bg-green-100',
      WARNING: 'text-yellow-600 bg-yellow-100',
      ERROR: 'text-red-600 bg-red-100',
      CRITICAL: 'text-red-800 bg-red-200',
      EMERGENCY: 'text-white bg-red-700'
    };
    return colors[severity] || 'text-gray-600 bg-gray-100';
  };

  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      success: 'text-green-600',
      warning: 'text-yellow-600',
      failure: 'text-red-600',
      healthy: 'text-green-600',
      degraded: 'text-yellow-600',
      unhealthy: 'text-red-600'
    };
    return colors[status] || 'text-gray-600';
  };

  // Health score color
  const getHealthScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  // Run diagnostic check
  const runDiagnostic = useCallback(async (type) => {
    setLoading(prev => ({ ...prev, [type]: true }));
    setError(null);

    const endpoints = {
      api: '/api/diagnostics/api',
      database: '/api/diagnostics/database',
      integrations: '/api/diagnostics/integrations',
      full: '/api/diagnostics/health'
    };

    try {
      const data = await fetchWithAuth(endpoints[type]);
      setResults({
        type,
        ...data,
        timestamp: new Date().toLocaleString()
      });
    } catch (err) {
      console.error(`SEC-076: Diagnostic ${type} failed:`, err);
      setError(`Failed to run ${type} diagnostic: ${err.message || 'Unknown error'}`);
    } finally {
      setLoading(prev => ({ ...prev, [type]: false }));
    }
  }, []);

  // Fetch diagnostic history
  const fetchHistory = useCallback(async () => {
    setLoading(prev => ({ ...prev, history: true }));
    try {
      const data = await fetchWithAuth('/api/diagnostics/history?limit=10');
      setHistory(data.history || []);
      setShowHistory(true);
    } catch (err) {
      console.error('SEC-076: Failed to fetch history:', err);
      setError('Failed to load diagnostic history');
    } finally {
      setLoading(prev => ({ ...prev, history: false }));
    }
  }, []);

  // Export to SIEM
  const exportToSIEM = useCallback(async () => {
    setExportLoading(true);
    try {
      const data = await fetchWithAuth('/api/diagnostics/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: exportFormat,
          include_details: true
        })
      });

      // Download as JSON file
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `diagnostics_${exportFormat}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setShowExportModal(false);
    } catch (err) {
      console.error('SEC-076: SIEM export failed:', err);
      setError('Failed to export diagnostics');
    } finally {
      setExportLoading(false);
    }
  }, [exportFormat]);

  return (
    <div className="space-y-4">
      {/* Diagnostic Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <button
          onClick={() => runDiagnostic('api')}
          disabled={loading.api}
          className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors disabled:opacity-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h5 className="font-medium text-gray-900">API Health Check</h5>
              <p className="text-sm text-gray-600">Test endpoint connectivity</p>
            </div>
            {loading.api ? (
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <span className="text-xl">🔍</span>
            )}
          </div>
        </button>

        <button
          onClick={() => runDiagnostic('database')}
          disabled={loading.database}
          className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors disabled:opacity-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h5 className="font-medium text-gray-900">Database Status</h5>
              <p className="text-sm text-gray-600">Check DB performance</p>
            </div>
            {loading.database ? (
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <span className="text-xl">🗄️</span>
            )}
          </div>
        </button>

        <button
          onClick={() => runDiagnostic('integrations')}
          disabled={loading.integrations}
          className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors disabled:opacity-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h5 className="font-medium text-gray-900">Integration Tests</h5>
              <p className="text-sm text-gray-600">Validate connections</p>
            </div>
            {loading.integrations ? (
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <span className="text-xl">🔗</span>
            )}
          </div>
        </button>

        <button
          onClick={() => runDiagnostic('full')}
          disabled={loading.full}
          className="p-4 border border-blue-200 bg-blue-50 rounded-lg hover:bg-blue-100 text-left transition-colors disabled:opacity-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h5 className="font-medium text-blue-900">Full Diagnostic</h5>
              <p className="text-sm text-blue-700">Complete health check</p>
            </div>
            {loading.full ? (
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <span className="text-xl">📊</span>
            )}
          </div>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <span className="text-red-500 mr-2">⚠️</span>
            <span className="text-red-700">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Results Panel */}
      {results && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <h5 className="font-semibold text-lg">
                {results.type === 'full' ? 'Full System Diagnostic' :
                 results.type === 'api' ? 'API Health Check' :
                 results.type === 'database' ? 'Database Status' : 'Integration Tests'}
              </h5>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(results.severity)}`}>
                {results.severity}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              <span className="mr-4">Correlation ID: {results.correlation_id?.slice(0, 20)}...</span>
              <span>{results.duration_ms}ms</span>
            </div>
          </div>

          {/* Health Score */}
          <div className="flex items-center space-x-6 mb-4">
            <div className={`text-4xl font-bold ${getHealthScoreColor(results.health_score)}`}>
              {results.health_score?.toFixed(1)}
            </div>
            <div>
              <div className="text-sm text-gray-500">Health Score</div>
              <div className={`font-medium ${getStatusColor(results.status)}`}>
                {results.status?.toUpperCase()}
              </div>
            </div>
            <div className="flex-1">
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    results.health_score >= 80 ? 'bg-green-500' :
                    results.health_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${results.health_score}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Component Details */}
          {results.components && (
            <div className="border-t pt-4 mt-4">
              <h6 className="font-medium mb-3">Component Status</h6>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(results.components).map(([name, data]) => (
                  <div key={name} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium capitalize">{name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        data.status === 'healthy' ? 'bg-green-100 text-green-700' :
                        data.status === 'degraded' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {data.status}
                      </span>
                    </div>
                    <div className="text-lg font-semibold">{data.score}</div>
                    {data.latency_ms !== undefined && (
                      <div className="text-xs text-gray-500">{data.latency_ms}ms latency</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Remediation Suggestions */}
          {results.remediation && results.remediation.length > 0 && (
            <div className="border-t pt-4 mt-4">
              <h6 className="font-medium mb-3 text-yellow-700">Remediation Suggestions</h6>
              <div className="space-y-2">
                {results.remediation.map((item, idx) => (
                  <div key={idx} className="flex items-start p-3 bg-yellow-50 rounded-lg">
                    <span className="flex-shrink-0 w-6 h-6 bg-yellow-200 rounded-full flex items-center justify-center text-yellow-800 text-sm font-medium mr-3">
                      {item.priority}
                    </span>
                    <div>
                      <div className="font-medium text-yellow-900">{item.action}</div>
                      <div className="text-sm text-yellow-700">
                        Component: {item.component} | Impact: {item.impact}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="text-xs text-gray-400 mt-4 pt-4 border-t">
            Run at: {results.timestamp}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center space-x-4">
        <button
          onClick={fetchHistory}
          disabled={loading.history}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {loading.history ? 'Loading...' : '📜 View History'}
        </button>

        <button
          onClick={() => setShowExportModal(true)}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          📤 Export to SIEM
        </button>
      </div>

      {/* History Panel */}
      {showHistory && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h5 className="font-semibold">Diagnostic History</h5>
            <button
              onClick={() => setShowHistory(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {history.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No diagnostic history available</p>
          ) : (
            <div className="space-y-2">
              {history.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(item.severity)}`}>
                      {item.severity}
                    </span>
                    <span className="font-medium capitalize">{item.type}</span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className={getHealthScoreColor(item.health_score)}>
                      Score: {item.health_score}
                    </span>
                    <span>{item.duration_ms}ms</span>
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h5 className="text-lg font-semibold mb-4">Export to SIEM</h5>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="splunk_cim">Splunk CIM</option>
                <option value="datadog_metrics">Datadog Metrics</option>
                <option value="generic_json">Generic JSON</option>
              </select>
            </div>

            <div className="p-3 bg-blue-50 rounded-lg mb-4 text-sm text-blue-700">
              <strong>SEC-076:</strong> Exported data includes correlation IDs,
              health scores, and component details for SIEM ingestion.
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={exportToSIEM}
                disabled={exportLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {exportLoading ? 'Exporting...' : 'Export'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosticsDashboard;
