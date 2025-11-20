import React, { useState } from 'react';
import { Shield, Plus, X, Check } from 'lucide-react';

/**
 * Visual Policy Builder with structured inputs
 */
export const VisualPolicyBuilder = ({ onSave, onCancel }) => {
  const [policy, setPolicy] = useState({
    policy_name: '',
    effect: 'deny',
    actions: [],
    resources: [],
    description: ''
  });

  const [newAction, setNewAction] = useState('');
  const [newResource, setNewResource] = useState('');

  const actionOptions = [
    'read', 'write', 'delete', 'modify', 'create', 'execute', 'export'
  ];

  const resourceOptions = [
    'database:production:*',
    'database:staging:*',
    's3://*',
    'financial:*',
    'pii:*',
    'api:external:*'
  ];

  const addAction = (action) => {
    if (action && !policy.actions.includes(action)) {
      setPolicy({...policy, actions: [...policy.actions, action]});
      setNewAction('');
    }
  };

  const addResource = (resource) => {
    if (resource && !policy.resources.includes(resource)) {
      setPolicy({...policy, resources: [...policy.resources, resource]});
      setNewResource('');
    }
  };

  const removeAction = (action) => {
    setPolicy({...policy, actions: policy.actions.filter(a => a !== action)});
  };

  const removeResource = (resource) => {
    setPolicy({...policy, resources: policy.resources.filter(r => r !== resource)});
  };

  const handleSubmit = () => {
    if (!policy.policy_name || !policy.description) {
      alert('Please fill in policy name and description');
      return;
    }
    onSave(policy);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Shield className="h-6 w-6 text-blue-600" />
        Visual Policy Builder
      </h3>

      <div className="space-y-6">
        {/* Policy Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Policy Name *
          </label>
          <input
            type="text"
            value={policy.policy_name}
            onChange={e => setPolicy({...policy, policy_name: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., Production Database Access Control"
          />
        </div>

        {/* Effect */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Policy Effect *
          </label>
          <div className="grid grid-cols-3 gap-3">
            {['deny', 'permit', 'require_approval'].map(effect => (
              <button
                key={effect}
                onClick={() => setPolicy({...policy, effect})}
                className={`px-4 py-3 rounded-lg border-2 transition-all ${
                  policy.effect === effect
                    ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
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

        {/* Actions */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Actions (what operations does this policy control?)
          </label>
          <div className="flex gap-2 mb-3">
            <select
              value={newAction}
              onChange={e => addAction(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select an action...</option>
              {actionOptions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
            <button
              onClick={() => addAction(newAction)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {policy.actions.map(action => (
              <span
                key={action}
                className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
              >
                {action}
                <button onClick={() => removeAction(action)}>
                  <X className="h-4 w-4 hover:text-blue-900" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Resources */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Resources (what systems/data does this apply to?)
          </label>
          <div className="flex gap-2 mb-3">
            <select
              value={newResource}
              onChange={e => addResource(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a resource...</option>
              {resourceOptions.map(resource => (
                <option key={resource} value={resource}>{resource}</option>
              ))}
            </select>
            <button
              onClick={() => addResource(newResource)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {policy.resources.map(resource => (
              <span
                key={resource}
                className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium"
              >
                {resource}
                <button onClick={() => removeResource(resource)}>
                  <X className="h-4 w-4 hover:text-purple-900" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Natural Language Description *
          </label>
          <textarea
            rows={4}
            value={policy.description}
            onChange={e => setPolicy({...policy, description: e.target.value})}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Describe what this policy does in plain English..."
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t">
          <button
            onClick={handleSubmit}
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
    </div>
  );
};

export default VisualPolicyBuilder;
