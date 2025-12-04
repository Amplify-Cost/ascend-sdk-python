import React, { useState } from 'react';
import { Shield, Plus, X, Code2, Eye, ChevronDown, BookOpen } from 'lucide-react';
import PolicyTemplateLibrary from './PolicyTemplateLibrary';

/**
 * 🏢 SEC-012: Enterprise Policy Builder with Conditions Support
 * Banking-Level Security: NIST AC-3, PCI-DSS 7.1, SOC 2 CC6.1
 *
 * Features:
 * - Visual condition builder with dropdown selectors
 * - Full policy data submission (actions, resources, conditions)
 * - Compliance-ready structured policies
 */
export const VisualPolicyBuilderAdvanced = ({ onSave, onCancel, API_BASE_URL, getAuthHeaders }) => {
  const [policy, setPolicy] = useState({
    policy_name: '',
    effect: 'deny',
    actions: [],
    resources: [],
    conditions: [],
    natural_language: '',
    risk_level: 'medium'
  });
  const [showPreview, setShowPreview] = useState(false);
  const [compiledPreview, setCompiledPreview] = useState(null);
  // 🏢 SEC-012: State for condition selector
  const [selectedConditionKey, setSelectedConditionKey] = useState('');
  const [selectedConditionValue, setSelectedConditionValue] = useState('');
  // 🏢 SEC-053: State for template library modal
  const [showTemplateLibrary, setShowTemplateLibrary] = useState(false);

  const actionOptions = [
    { value: 'read', label: 'Read', icon: '👁️' },
    { value: 'write', label: 'Write', icon: '✍️' },
    { value: 'delete', label: 'Delete', icon: '🗑️' },
    { value: 'modify', label: 'Modify', icon: '✏️' },
    { value: 'create', label: 'Create', icon: '➕' },
    { value: 'execute', label: 'Execute', icon: '⚡' },
    { value: 'export', label: 'Export', icon: '📤' }
  ];

  const resourceTemplates = [
    { value: 'database:production:*', label: 'Production Database', icon: '🗄️' },
    { value: 'database:staging:*', label: 'Staging Database', icon: '🔧' },
    { value: 's3://*', label: 'S3 Buckets', icon: '☁️' },
    { value: 'financial:*', label: 'Financial Data', icon: '💰' },
    { value: 'pii:*', label: 'PII Data', icon: '🔒' },
    { value: 'api:external:*', label: 'External APIs', icon: '🌐' }
  ];

  // SEC-019: Enterprise condition options for policy enforcement
  // Banking-Level: NIST AC-3, PCI-DSS 7.1 - Fine-grained access control
  const conditionOptions = [
    { key: 'environment', label: 'Environment', values: ['production', 'staging', 'development'] },
    { key: 'time_window', label: 'Time Window', values: ['business_hours', 'after_hours', 'weekends'] },
    { key: 'user_role', label: 'User Role', values: ['admin', 'developer', 'analyst', 'viewer'] },
    { key: 'approval_required', label: 'Requires Approval', values: ['true', 'false'] },
    // SEC-019: Risk-based conditions for enterprise workflows
    { key: 'risk_score_min', label: 'Min Risk Score', values: ['0', '30', '50', '70', '90'] },
    { key: 'risk_score_max', label: 'Max Risk Score', values: ['29', '49', '69', '89', '100'] },
    { key: 'action_category', label: 'Action Category', values: ['read', 'write', 'delete', 'execute', 'admin'] },
    { key: 'data_sensitivity', label: 'Data Sensitivity', values: ['public', 'internal', 'confidential', 'restricted', 'pii'] },
    { key: 'approver_email', label: 'Approver Email', values: ['admin@acmecorp.test', 'security@acmecorp.test', 'manager@acmecorp.test'] }
  ];

  const toggleAction = (action) => {
    setPolicy(prev => ({
      ...prev,
      actions: prev.actions.includes(action)
        ? prev.actions.filter(a => a !== action)
        : [...prev.actions, action]
    }));
  };

  const toggleResource = (resource) => {
    setPolicy(prev => ({
      ...prev,
      resources: prev.resources.includes(resource)
        ? prev.resources.filter(r => r !== resource)
        : [...prev.resources, resource]
    }));
  };

  const addCondition = (key, value) => {
    // 🏢 SEC-012: Prevent duplicate conditions
    const exists = policy.conditions.some(c => c.key === key && c.value === value);
    if (exists) {
      return; // Don't add duplicates
    }
    setPolicy(prev => ({
      ...prev,
      conditions: [...prev.conditions, { key, value }]
    }));
  };

  // 🏢 SEC-012: Handler for adding condition from dropdowns
  const handleAddCondition = () => {
    if (selectedConditionKey && selectedConditionValue) {
      addCondition(selectedConditionKey, selectedConditionValue);
      setSelectedConditionKey('');
      setSelectedConditionValue('');
    }
  };

  // 🏢 SEC-012: Get available values for selected condition key
  const getConditionValues = () => {
    const option = conditionOptions.find(c => c.key === selectedConditionKey);
    return option ? option.values : [];
  };

  const removeCondition = (index) => {
    setPolicy(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }));
  };

  /**
   * SEC-053: Handle template selection from PolicyTemplateLibrary
   * Populates the form with template data while allowing customization
   */
  const handleSelectTemplate = (templateData) => {
    // Convert template conditions object to array format
    const conditionsArray = templateData.conditions
      ? Object.entries(templateData.conditions).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      : [];

    // Map template effect to policy builder format
    const effectMap = {
      'DENY': 'deny',
      'ALLOW': 'permit',
      'REQUIRE_APPROVAL': 'require_approval',
      'AUDIT': 'permit'
    };

    // Map template severity to risk level
    const riskMap = {
      'CRITICAL': 'high',
      'HIGH': 'high',
      'MEDIUM': 'medium',
      'LOW': 'low'
    };

    setPolicy({
      policy_name: templateData.name,
      effect: effectMap[templateData.effect] || 'require_approval',
      actions: templateData.actions || [],
      resources: templateData.resource_types || [],
      conditions: conditionsArray,
      natural_language: templateData.description || '',
      risk_level: riskMap[templateData.severity] || 'medium'
    });

    // Close template library after selection
    setShowTemplateLibrary(false);
  };

  const compilePreview = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/compile`,
        {
          method: 'POST',
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            natural_language: policy.natural_language,
            risk_level: policy.risk_level
          })
        }
      );
      const data = await response.json();

      // Handle user-friendly error messages from backend
      if (data.success === false) {
        const errorMessage = data.error || 'Compilation failed';
        const suggestion = data.suggestion || '';
        alert(`${errorMessage}\n\n${suggestion}`);
        return;
      }

      setCompiledPreview(data);
      setShowPreview(true);
    } catch (error) {
      console.error('Compilation failed:', error);
      alert('Unable to compile policy. Please check your network connection and try again.');
    }
  };

  const handleSave = async () => {
    // 🏢 SEC-012: Enterprise validation
    if (!policy.policy_name || !policy.policy_name.trim()) {
      alert('Please provide a policy name');
      return;
    }

    // Generate description from natural language OR structured inputs
    let description = policy.natural_language;

    // If no natural language provided, generate from structured fields
    if (!description || !description.trim()) {
      if (policy.actions.length > 0 && policy.resources.length > 0) {
        const effectText = policy.effect === 'deny' ? 'Block' :
                          policy.effect === 'permit' ? 'Allow' :
                          'Require approval for';
        description = `${effectText} ${policy.actions.join(', ')} operations on ${policy.resources.join(', ')}`;

        // 🏢 SEC-012: Add conditions to description for audit trail
        if (policy.conditions.length > 0) {
          const conditionText = policy.conditions.map(c => `${c.key}=${c.value}`).join(', ');
          description += ` when ${conditionText}`;
        }
      } else {
        alert('Please either:\n• Fill in the natural language description, OR\n• Select at least one action and one resource');
        return;
      }
    }

    // 🏢 SEC-012: Send COMPLETE policy data for enterprise compliance
    // Banking-Level: Full structured policy enables NIST AC-3, PCI-DSS 7.1 enforcement
    await onSave({
      policy_name: policy.policy_name,
      description: description,
      effect: policy.effect,
      actions: policy.actions,
      resources: policy.resources,
      conditions: policy.conditions.reduce((acc, c) => {
        acc[c.key] = c.value;
        return acc;
      }, {}),
      risk_level: policy.risk_level
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Advanced Policy Builder
        </h3>
        <div className="flex items-center gap-3">
          {/* SEC-053: Template Library Button */}
          <button
            onClick={() => setShowTemplateLibrary(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            aria-label="Open policy template library"
          >
            <BookOpen className="h-4 w-4" />
            From Template
          </button>
          <button
            onClick={compilePreview}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Eye className="h-4 w-4" />
            Preview
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column - Basic Info */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Policy Name *</label>
            <input
              type="text"
              value={policy.policy_name}
              onChange={e => setPolicy({...policy, policy_name: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Descriptive name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Effect *</label>
            <div className="space-y-2">
              {['deny', 'permit', 'require_approval'].map(effect => (
                <button
                  key={effect}
                  onClick={() => setPolicy({...policy, effect})}
                  className={`w-full px-4 py-2 rounded-lg border-2 text-left transition-all ${
                    policy.effect === effect
                      ? 'border-blue-500 bg-blue-50 font-semibold'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  {effect === 'deny' && '🚫 Deny'}
                  {effect === 'permit' && '✅ Permit'}
                  {effect === 'require_approval' && '⏰ Require Approval'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Risk Level</label>
            <select
              value={policy.risk_level}
              onChange={e => setPolicy({...policy, risk_level: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        {/* Middle Column - Actions & Resources */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-3">Actions</label>
            <div className="space-y-2">
              {actionOptions.map(action => (
                <button
                  key={action.value}
                  onClick={() => toggleAction(action.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-left transition-all ${
                    policy.actions.includes(action.value)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <span className="mr-2">{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Resources & Conditions */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-3">Resources</label>
            <div className="space-y-2">
              {resourceTemplates.map(resource => (
                <button
                  key={resource.value}
                  onClick={() => toggleResource(resource.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-left transition-all text-sm ${
                    policy.resources.includes(resource.value)
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <span className="mr-2">{resource.icon}</span>
                  {resource.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 🏢 SEC-012: Enterprise Conditions Builder */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <label className="block text-sm font-medium mb-3 flex items-center gap-2">
          <Shield className="h-4 w-4 text-purple-600" />
          Policy Conditions (Access Control)
        </label>
        <p className="text-xs text-gray-500 mb-4">
          Define when this policy applies. Required for PCI-DSS 7.1 and NIST AC-3 compliance.
        </p>

        {/* Condition Selector UI */}
        <div className="flex gap-3 mb-4">
          {/* Condition Type Dropdown */}
          <div className="flex-1">
            <label className="block text-xs text-gray-600 mb-1">Condition Type</label>
            <select
              value={selectedConditionKey}
              onChange={(e) => {
                setSelectedConditionKey(e.target.value);
                setSelectedConditionValue(''); // Reset value when key changes
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="">Select condition type...</option>
              {conditionOptions.map(opt => (
                <option key={opt.key} value={opt.key}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Condition Value Dropdown */}
          <div className="flex-1">
            <label className="block text-xs text-gray-600 mb-1">Condition Value</label>
            <select
              value={selectedConditionValue}
              onChange={(e) => setSelectedConditionValue(e.target.value)}
              disabled={!selectedConditionKey}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select value...</option>
              {getConditionValues().map(val => (
                <option key={val} value={val}>
                  {val.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          {/* Add Condition Button */}
          <div className="flex items-end">
            <button
              onClick={handleAddCondition}
              disabled={!selectedConditionKey || !selectedConditionValue}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add
            </button>
          </div>
        </div>

        {/* Active Conditions List */}
        <div className="space-y-2">
          {policy.conditions.length === 0 ? (
            <div className="text-sm text-gray-500 italic py-2">
              No conditions added. Policy will apply to all matching actions.
            </div>
          ) : (
            <>
              <div className="text-xs text-gray-600 font-medium mb-2">
                Active Conditions ({policy.conditions.length}):
              </div>
              {policy.conditions.map((condition, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-white p-3 rounded-lg border border-purple-200 shadow-sm">
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded font-medium">
                    {conditionOptions.find(c => c.key === condition.key)?.label || condition.key}
                  </span>
                  <span className="text-gray-500">=</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium">
                    {condition.value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <button
                    onClick={() => removeCondition(idx)}
                    className="ml-auto p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Remove condition"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* Natural Language Description */}
      <div className="mt-6">
        <label className="block text-sm font-medium mb-2">
          Natural Language Description *
        </label>
        <textarea
          rows={3}
          value={policy.natural_language}
          onChange={e => setPolicy({...policy, natural_language: e.target.value})}
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="Describe what this policy does in plain English..."
        />
      </div>

      {/* Preview Panel */}
      {showPreview && compiledPreview && (
        <div className="mt-6 p-4 bg-gray-900 rounded-lg">
          <div className="flex items-center gap-2 mb-3 text-white">
            <Code2 className="h-5 w-5" />
            <span className="font-semibold">Compiled Policy</span>
          </div>
          <pre className="text-sm text-green-400 overflow-x-auto">
            {JSON.stringify(compiledPreview, null, 2)}
          </pre>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 mt-6 pt-6 border-t">
        <button
          onClick={handleSave}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
        >
          Create Policy
        </button>
        <button
          onClick={onCancel}
          className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>

      {/* SEC-053: Policy Template Library Modal */}
      {showTemplateLibrary && (
        <PolicyTemplateLibrary
          onSelectTemplate={handleSelectTemplate}
          onClose={() => setShowTemplateLibrary(false)}
          getAuthHeaders={getAuthHeaders}
          API_BASE_URL={API_BASE_URL}
        />
      )}
    </div>
  );
};

export default VisualPolicyBuilderAdvanced;
