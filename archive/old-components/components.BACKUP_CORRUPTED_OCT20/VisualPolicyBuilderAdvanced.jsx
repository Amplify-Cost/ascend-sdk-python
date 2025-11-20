import React, { useState } from 'react';
import { Shield, Plus, X, Code2, Eye } from 'lucide-react';
import logger from '../utils/logger.js';

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

  const conditionOptions = [
    { key: 'environment', label: 'Environment', values: ['production', 'staging', 'development'] },
    { key: 'time_window', label: 'Time Window', values: ['business_hours', 'after_hours', 'weekends'] },
    { key: 'user_role', label: 'User Role', values: ['admin', 'developer', 'analyst', 'viewer'] },
    { key: 'approval_required', label: 'Requires Approval', values: ['true', 'false'] }
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
    setPolicy(prev => ({
      ...prev,
      conditions: [...prev.conditions, { key, value }]
    }));
  };

  const removeCondition = (index) => {
    setPolicy(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }));
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
      setCompiledPreview(data);
      setShowPreview(true);
    } catch (error) {
      logger.error('Compilation failed:', error);
    }
  };

  const handleSave = async () => {
    if (!policy.policy_name || !policy.natural_language) {
      alert('Please fill in policy name and description');
      return;
    }
    
    // Generate natural language from structured inputs if not provided
    let description = policy.natural_language;
    if (!description && policy.actions.length > 0 && policy.resources.length > 0) {
      const effectText = policy.effect === 'deny' ? 'Block' : 
                        policy.effect === 'permit' ? 'Allow' : 
                        'Require approval for';
      description = `${effectText} ${policy.actions.join(', ')} operations on ${policy.resources.join(', ')}`;
    }

    await onSave({
      policy_name: policy.policy_name,
      description: description
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Advanced Policy Builder
        </h3>
        <button
          onClick={compilePreview}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          <Eye className="h-4 w-4" />
          Preview
        </button>
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

      {/* Conditions */}
      <div className="mt-6">
        <label className="block text-sm font-medium mb-3">Conditions (Optional)</label>
        <div className="space-y-2">
          {policy.conditions.map((condition, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
              <span className="text-sm font-medium">{condition.key}:</span>
              <span className="text-sm">{condition.value}</span>
              <button onClick={() => removeCondition(idx)} className="ml-auto">
                <X className="h-4 w-4 text-red-600" />
              </button>
            </div>
          ))}
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
    </div>
  );
};

export default VisualPolicyBuilderAdvanced;
