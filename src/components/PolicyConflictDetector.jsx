import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Shield,
  RefreshCw,
  XCircle,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from './ToastNotification';

/**
 * Enterprise Policy Conflict Detection Dashboard
 *
 * Features:
 * - System-wide conflict analysis
 * - Severity-based conflict visualization
 * - Detailed conflict descriptions
 * - Actionable resolution suggestions
 * - Real-time conflict scanning
 *
 * @param {Object} props
 * @param {string} props.API_BASE_URL - Base URL for API calls
 * @param {Function} props.getAuthHeaders - Authentication headers provider
 */
export const PolicyConflictDetector = ({ API_BASE_URL, getAuthHeaders }) => {
  // State management
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastScan, setLastScan] = useState(null);
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [expandedConflicts, setExpandedConflicts] = useState(new Set());

  // Hooks
  const { isDarkMode } = useTheme();
  const { toast } = useToast();

  // Auto-scan on component mount
  useEffect(() => {
    analyzeConflicts();
  }, []);

  /**
   * Analyze all policies for conflicts
   */
  const analyzeConflicts = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/conflicts/analyze`,
        {
          credentials: "include",
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to analyze conflicts`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Analysis failed');
      }

      setConflicts(data.conflicts || []);
      setLastScan(new Date());

      // User feedback
      if (data.total_conflicts > 0) {
        const criticalCount = data.critical || 0;
        const highCount = data.high || 0;

        if (criticalCount > 0) {
          toast.error(
            `Found ${data.total_conflicts} conflicts (${criticalCount} critical)`,
            'Critical Conflicts Detected'
          );
        } else if (highCount > 0) {
          toast.warning(
            `Found ${data.total_conflicts} conflicts (${highCount} high priority)`,
            'Conflicts Detected'
          );
        } else {
          toast.warning(`Found ${data.total_conflicts} conflicts`, 'Conflicts Detected');
        }
      } else {
        toast.success('No policy conflicts detected', 'All Clear');
      }
    } catch (error) {
      toast.error(error.message || 'Failed to analyze conflicts', 'Error');
      console.error('Conflict analysis error:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get color scheme for severity level
   */
  const getSeverityColors = (severity) => {
    const colorMap = {
      critical: {
        bg: isDarkMode ? 'bg-red-900 border-red-500' : 'bg-red-50 border-red-500',
        text: isDarkMode ? 'text-red-100' : 'text-red-900',
        badge: 'bg-red-500 text-white',
        icon: 'text-red-500'
      },
      high: {
        bg: isDarkMode ? 'bg-orange-900 border-orange-500' : 'bg-orange-50 border-orange-500',
        text: isDarkMode ? 'text-orange-100' : 'text-orange-900',
        badge: 'bg-orange-500 text-white',
        icon: 'text-orange-500'
      },
      medium: {
        bg: isDarkMode ? 'bg-yellow-900 border-yellow-500' : 'bg-yellow-50 border-yellow-500',
        text: isDarkMode ? 'text-yellow-100' : 'text-yellow-900',
        badge: 'bg-yellow-500 text-white',
        icon: 'text-yellow-500'
      },
      low: {
        bg: isDarkMode ? 'bg-blue-900 border-blue-500' : 'bg-blue-50 border-blue-500',
        text: isDarkMode ? 'text-blue-100' : 'text-blue-900',
        badge: 'bg-blue-500 text-white',
        icon: 'text-blue-500'
      }
    };
    return colorMap[severity] || colorMap.medium;
  };

  /**
   * Get severity icon
   */
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="h-5 w-5" />;
      case 'high':
        return <AlertTriangle className="h-5 w-5" />;
      case 'medium':
        return <Info className="h-5 w-5" />;
      case 'low':
        return <CheckCircle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  /**
   * Toggle conflict expansion
   */
  const toggleConflictExpansion = (index) => {
    setExpandedConflicts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (date) => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} mins ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return date.toLocaleDateString();
  };

  /**
   * Calculate conflict summary
   */
  const getConflictSummary = () => {
    const summary = {
      total: conflicts.length,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    conflicts.forEach(conflict => {
      const severity = conflict.severity || 'medium';
      summary[severity] = (summary[severity] || 0) + 1;
    });

    return summary;
  };

  const summary = getConflictSummary();

  return (
    <div className={`space-y-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold mb-2">Policy Conflict Detection</h2>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Last scan: {formatTimestamp(lastScan)}
          </p>
        </div>
        <button
          onClick={analyzeConflicts}
          disabled={loading}
          className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg'
          }`}
          aria-label="Analyze all policies for conflicts"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Scanning...' : 'Analyze All Policies'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Conflicts */}
        <div className={`p-6 rounded-xl border-2 ${
          isDarkMode
            ? 'bg-slate-700 border-slate-600'
            : 'bg-white border-gray-300'
        }`}>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Total Conflicts
          </p>
          <p className="text-3xl font-bold mt-2">{summary.total}</p>
          <Shield className={`h-8 w-8 mt-3 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`} />
        </div>

        {/* Critical */}
        <div className={`p-6 rounded-xl border-2 ${
          isDarkMode
            ? 'bg-slate-700 border-red-500'
            : 'bg-white border-red-300'
        }`}>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Critical
          </p>
          <p className="text-3xl font-bold mt-2 text-red-500">{summary.critical}</p>
          <XCircle className="h-8 w-8 mt-3 text-red-500" />
        </div>

        {/* High */}
        <div className={`p-6 rounded-xl border-2 ${
          isDarkMode
            ? 'bg-slate-700 border-orange-500'
            : 'bg-white border-orange-300'
        }`}>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            High Priority
          </p>
          <p className="text-3xl font-bold mt-2 text-orange-500">{summary.high}</p>
          <AlertTriangle className="h-8 w-8 mt-3 text-orange-500" />
        </div>

        {/* Medium */}
        <div className={`p-6 rounded-xl border-2 ${
          isDarkMode
            ? 'bg-slate-700 border-yellow-500'
            : 'bg-white border-yellow-300'
        }`}>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Medium Priority
          </p>
          <p className="text-3xl font-bold mt-2 text-yellow-500">{summary.medium}</p>
          <Info className="h-8 w-8 mt-3 text-yellow-500" />
        </div>
      </div>

      {/* Conflicts List */}
      <div className={`rounded-lg border ${
        isDarkMode ? 'bg-slate-700 border-slate-600' : 'bg-white border-gray-300'
      }`}>
        <div className="p-6">
          <h3 className="text-xl font-bold mb-4">
            {conflicts.length === 0
              ? 'No Conflicts Detected'
              : `Detected Conflicts (${conflicts.length})`
            }
          </h3>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4 border-blue-600"></div>
              <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>
                Analyzing policies for conflicts...
              </p>
            </div>
          ) : conflicts.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className={`h-16 w-16 mx-auto mb-4 ${
                isDarkMode ? 'text-green-400' : 'text-green-600'
              }`} />
              <p className="text-lg font-medium">All policies are compatible!</p>
              <p className={`text-sm mt-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                No conflicting policies were found in your system.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {conflicts.map((conflict, index) => {
                const colors = getSeverityColors(conflict.severity);
                const isExpanded = expandedConflicts.has(index);

                return (
                  <div
                    key={index}
                    className={`border-2 rounded-lg p-4 transition-all ${colors.bg} ${colors.text}`}
                  >
                    {/* Conflict Header */}
                    <div
                      className="flex items-start justify-between cursor-pointer"
                      onClick={() => toggleConflictExpansion(index)}
                      role="button"
                      tabIndex={0}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          toggleConflictExpansion(index);
                        }
                      }}
                      aria-expanded={isExpanded}
                      aria-label={`Conflict between ${conflict.policy1?.name} and ${conflict.policy2?.name}`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={colors.icon}>
                            {getSeverityIcon(conflict.severity)}
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${colors.badge}`}>
                            {conflict.severity}
                          </span>
                          <span className="text-sm font-medium opacity-75">
                            {conflict.conflict_type?.replace(/_/g, ' ').toUpperCase()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-3">
                          <div>
                            <p className="text-xs opacity-75 mb-1">Policy 1:</p>
                            <p className="font-semibold">{conflict.policy1?.name}</p>
                            <p className="text-xs opacity-75">ID: {conflict.policy1?.id}</p>
                          </div>
                          <div>
                            <p className="text-xs opacity-75 mb-1">Policy 2:</p>
                            <p className="font-semibold">{conflict.policy2?.name}</p>
                            <p className="text-xs opacity-75">ID: {conflict.policy2?.id}</p>
                          </div>
                        </div>

                        <p className="text-sm leading-relaxed">
                          {conflict.description}
                        </p>
                      </div>

                      <button
                        className="ml-4 p-1 rounded hover:bg-black hover:bg-opacity-10"
                        aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5" />
                        ) : (
                          <ChevronDown className="h-5 w-5" />
                        )}
                      </button>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-current border-opacity-20">
                        <h4 className="font-semibold mb-3 flex items-center gap-2">
                          <Info className="h-4 w-4" />
                          Resolution Suggestions:
                        </h4>
                        <ul className="space-y-2">
                          {(conflict.resolution_suggestions || []).map((suggestion, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="mt-1">•</span>
                              <span className="text-sm">{suggestion}</span>
                            </li>
                          ))}
                        </ul>

                        <div className="mt-4 text-xs opacity-75">
                          Detected at: {new Date(conflict.detected_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Help Section */}
      <div className={`rounded-lg border p-6 ${
        isDarkMode
          ? 'bg-blue-900 bg-opacity-20 border-blue-500'
          : 'bg-blue-50 border-blue-300'
      }`}>
        <h3 className="font-semibold mb-2 flex items-center gap-2">
          <Info className="h-5 w-5 text-blue-500" />
          About Conflict Detection
        </h3>
        <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          The conflict detector analyzes all active policies to identify potential contradictions,
          priority issues, and resource hierarchy conflicts. Critical conflicts should be resolved
          before deploying policies to production.
        </p>
      </div>
    </div>
  );
};

export default PolicyConflictDetector;
