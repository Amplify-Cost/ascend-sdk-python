/**
 * SEC-053: ENTERPRISE POLICY TEMPLATE LIBRARY
 *
 * Phase 3 Frontend Component - Enterprise Polish
 * Pre-built policy templates for rapid compliance deployment
 * Aligned with Datadog/Wiz.io/Splunk enterprise patterns
 *
 * Features:
 * - Multi-compliance framework filtering (SOC2, PCI-DSS, HIPAA, GDPR, NIST)
 * - Severity-based filtering (CRITICAL, HIGH, MEDIUM, LOW)
 * - Full-text search across template names and descriptions
 * - Policy preview with conditions and effects
 * - One-click template deployment
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-12-02
 * Compliance: SOC 2 CC6.1, NIST AC-3, PCI-DSS 7.1
 */

import React, { useState, useEffect, useCallback } from 'react';

const PolicyTemplateLibrary = ({ onSelectTemplate, onClose, getAuthHeaders, API_BASE_URL }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompliance, setSelectedCompliance] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [expandedTemplate, setExpandedTemplate] = useState(null);

  // SEC-053: Compliance frameworks aligned with enterprise standards
  const COMPLIANCE_FRAMEWORKS = [
    { value: 'all', label: 'All Frameworks', icon: '📚' },
    { value: 'SOC2', label: 'SOC 2', icon: '🔒' },
    { value: 'PCI-DSS', label: 'PCI-DSS', icon: '💳' },
    { value: 'HIPAA', label: 'HIPAA', icon: '🏥' },
    { value: 'GDPR', label: 'GDPR', icon: '🇪🇺' },
    { value: 'NIST', label: 'NIST', icon: '🏛️' },
    { value: 'SOX', label: 'SOX', icon: '📊' }
  ];

  // SEC-053: Severity levels for risk-based filtering
  const SEVERITY_LEVELS = [
    { value: 'all', label: 'All Severities', color: 'gray' },
    { value: 'CRITICAL', label: 'Critical', color: 'red' },
    { value: 'HIGH', label: 'High', color: 'orange' },
    { value: 'MEDIUM', label: 'Medium', color: 'yellow' },
    { value: 'LOW', label: 'Low', color: 'green' }
  ];

  // SEC-053: Policy effect descriptions
  const EFFECT_DESCRIPTIONS = {
    'DENY': { label: 'Block', color: 'bg-red-100 text-red-800', icon: '🚫' },
    'REQUIRE_APPROVAL': { label: 'Require Approval', color: 'bg-yellow-100 text-yellow-800', icon: '✋' },
    'ALLOW': { label: 'Allow', color: 'bg-green-100 text-green-800', icon: '✅' },
    'AUDIT': { label: 'Audit Only', color: 'bg-blue-100 text-blue-800', icon: '📝' }
  };

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // SEC-053: Build query parameters for search
      const params = new URLSearchParams();
      if (selectedCompliance !== 'all') {
        params.append('compliance', selectedCompliance);
      }
      if (selectedSeverity !== 'all') {
        params.append('severity', selectedSeverity);
      }
      if (searchQuery.trim()) {
        params.append('q', searchQuery.trim());
      }

      const queryString = params.toString();
      const url = `${API_BASE_URL}/api/governance/policies/templates/search${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(url, {
        credentials: 'include',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || 'Failed to load policy templates');
      }
    } catch (err) {
      console.error('SEC-053: Error fetching policy templates:', err);
      setError(err.message || 'Network error while loading templates');
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL, getAuthHeaders, selectedCompliance, selectedSeverity, searchQuery]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // SEC-053: Debounced search to avoid excessive API calls
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchTemplates();
    }, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': 'bg-red-100 text-red-800 border-red-200',
      'HIGH': 'bg-orange-100 text-orange-800 border-orange-200',
      'MEDIUM': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'LOW': 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getEffectInfo = (effect) => {
    return EFFECT_DESCRIPTIONS[effect] || EFFECT_DESCRIPTIONS['AUDIT'];
  };

  /**
   * SEC-053: Generate unique policy ID from template
   * Pattern aligned with enterprise naming conventions
   */
  const generatePolicyId = (templateId) => {
    const timestamp = Date.now().toString(36);
    return `pol-${templateId}-${timestamp}`;
  };

  /**
   * SEC-053: Convert template to policy format for creation
   */
  const handleUseTemplate = (template) => {
    const policyData = {
      id: generatePolicyId(template.id),
      name: template.name,
      description: template.description,
      resource_types: template.resource_types || [],
      actions: template.actions || [],
      effect: template.effect || 'REQUIRE_APPROVAL',
      severity: template.severity || 'MEDIUM',
      compliance_frameworks: template.compliance_frameworks || [],
      conditions: template.conditions || {},
      is_active: true,
      template_id: template.id
    };

    onSelectTemplate(policyData);
    onClose();
  };

  const toggleExpandTemplate = (templateId) => {
    setExpandedTemplate(expandedTemplate === templateId ? null : templateId);
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="policy-template-library-title"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 id="policy-template-library-title" className="text-2xl font-semibold text-gray-900">
                Policy Template Library
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Pre-built compliance policies for rapid deployment. Aligned with enterprise security standards.
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl leading-none p-2 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="Close template library"
            >
              &times;
            </button>
          </div>

          {/* Search Bar */}
          <div className="mb-4">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates by name or description..."
                className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Search policy templates"
              />
              <svg
                className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            {/* Compliance Framework Filter */}
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Compliance Framework
              </label>
              <div className="flex flex-wrap gap-2">
                {COMPLIANCE_FRAMEWORKS.map(framework => (
                  <button
                    key={framework.value}
                    onClick={() => setSelectedCompliance(framework.value)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      selectedCompliance === framework.value
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                    aria-pressed={selectedCompliance === framework.value}
                  >
                    <span className="mr-1">{framework.icon}</span>
                    {framework.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Severity Filter */}
            <div className="min-w-[150px]">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Severity Level
              </label>
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Filter by severity"
              >
                {SEVERITY_LEVELS.map(level => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Templates Grid */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {loading && (
            <div className="text-center py-12" role="status" aria-live="polite">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-4">Loading policy templates...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center" role="alert">
              <p className="text-red-800 font-medium">Failed to load templates</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={fetchTemplates}
                className="mt-3 px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {!loading && !error && templates.length === 0 && (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <div className="text-5xl mb-4">📋</div>
              <p className="text-gray-600 font-medium">No templates found</p>
              <p className="text-gray-500 text-sm mt-1">
                Try adjusting your filters or search query
              </p>
              <button
                onClick={() => {
                  setSelectedCompliance('all');
                  setSelectedSeverity('all');
                  setSearchQuery('');
                }}
                className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Clear all filters
              </button>
            </div>
          )}

          {!loading && !error && templates.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {templates.map((template) => {
                const effectInfo = getEffectInfo(template.effect);
                const isExpanded = expandedTemplate === template.id;

                return (
                  <div
                    key={template.id}
                    className="bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-md transition-all"
                  >
                    {/* Template Header */}
                    <div className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg text-gray-900">{template.name}</h4>
                          <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(template.severity)}`}>
                          {template.severity}
                        </span>
                      </div>

                      {/* Effect Badge */}
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${effectInfo.color}`}>
                          {effectInfo.icon} {effectInfo.label}
                        </span>
                      </div>

                      {/* Compliance Frameworks */}
                      <div className="flex flex-wrap gap-1 mb-3">
                        {(template.compliance_frameworks || []).map((framework, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium"
                          >
                            {framework}
                          </span>
                        ))}
                      </div>

                      {/* Expandable Details */}
                      <button
                        onClick={() => toggleExpandTemplate(template.id)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                        aria-expanded={isExpanded}
                      >
                        {isExpanded ? 'Hide Details' : 'View Details'}
                        <svg
                          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="px-5 pb-5 border-t border-gray-100 pt-4 bg-gray-50">
                        {/* Resource Types */}
                        <div className="mb-3">
                          <p className="text-xs font-medium text-gray-700 mb-1">Resource Types:</p>
                          <div className="flex flex-wrap gap-1">
                            {(template.resource_types || []).map((resource, idx) => (
                              <code
                                key={idx}
                                className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs font-mono"
                              >
                                {resource}
                              </code>
                            ))}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="mb-3">
                          <p className="text-xs font-medium text-gray-700 mb-1">Actions:</p>
                          <div className="flex flex-wrap gap-1">
                            {(template.actions || []).map((action, idx) => (
                              <code
                                key={idx}
                                className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-mono"
                              >
                                {action}
                              </code>
                            ))}
                          </div>
                        </div>

                        {/* Conditions */}
                        {template.conditions && Object.keys(template.conditions).length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs font-medium text-gray-700 mb-1">Conditions:</p>
                            <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                              {JSON.stringify(template.conditions, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Button */}
                    <div className="px-5 pb-5">
                      <button
                        onClick={() => handleUseTemplate(template)}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                      >
                        Use This Template
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-600">
              Templates can be customized after selection. Compliance tags are preserved.
            </p>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>Showing {templates.length} template{templates.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicyTemplateLibrary;
