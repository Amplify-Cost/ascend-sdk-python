/**
 * 🏢 ENTERPRISE ACTION CONFIGURATOR
 *
 * Phase 1 Frontend Component
 * Configures automated actions for playbooks with parameter validation
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState } from 'react';

const ActionConfigurator = ({ value, onChange, errors = {} }) => {
  const [localActions, setLocalActions] = useState(value || []);

  const ACTION_TYPES = [
    {
      value: 'approve',
      label: '✅ Auto-Approve',
      description: 'Automatically approve the action',
      parameters: [],
      category: 'decision'
    },
    {
      value: 'deny',
      label: '❌ Auto-Deny',
      description: 'Automatically deny the action',
      parameters: [],
      category: 'decision'
    },
    {
      value: 'escalate_approval',
      label: '⬆️ Escalate Approval',
      description: 'Escalate to higher approval level',
      parameters: [
        {
          name: 'level',
          label: 'Escalation Level',
          type: 'select',
          required: true,
          options: [
            { value: 'L1', label: 'L1 - Team Lead' },
            { value: 'L2', label: 'L2 - Manager' },
            { value: 'L3', label: 'L3 - Director' },
            { value: 'L4', label: 'L4 - VP/Executive' }
          ]
        },
        {
          name: 'reason',
          label: 'Escalation Reason',
          type: 'text',
          required: false,
          placeholder: 'Why is this being escalated?'
        }
      ],
      category: 'escalation'
    },
    {
      value: 'notify',
      label: '📧 Send Notification',
      description: 'Send email notification to recipients',
      parameters: [
        {
          name: 'recipients',
          label: 'Recipients (comma-separated emails)',
          type: 'text',
          required: true,
          placeholder: 'security@company.com, ops@company.com',
          validate: (value) => {
            if (!value) return 'Recipients are required';
            const emails = value.split(',').map(e => e.trim());
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const invalid = emails.filter(e => !emailRegex.test(e));
            if (invalid.length > 0) {
              return `Invalid email addresses: ${invalid.join(', ')}`;
            }
            return null;
          }
        },
        {
          name: 'subject',
          label: 'Email Subject',
          type: 'text',
          required: false,
          placeholder: 'Action notification'
        }
      ],
      category: 'notification'
    },
    {
      value: 'stakeholder_notification',
      label: '📢 Stakeholder Notification',
      description: 'Notify key stakeholders',
      parameters: [
        {
          name: 'recipients',
          label: 'Stakeholder Emails (comma-separated)',
          type: 'text',
          required: true,
          placeholder: 'ciso@company.com, cto@company.com',
          validate: (value) => {
            if (!value) return 'Recipients are required';
            const emails = value.split(',').map(e => e.trim());
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const invalid = emails.filter(e => !emailRegex.test(e));
            if (invalid.length > 0) {
              return `Invalid email addresses: ${invalid.join(', ')}`;
            }
            return null;
          }
        },
        {
          name: 'subject',
          label: 'Notification Subject',
          type: 'text',
          required: false,
          placeholder: 'High-priority action notification'
        }
      ],
      category: 'notification'
    },
    {
      value: 'temporary_quarantine',
      label: '🔒 Temporary Quarantine',
      description: 'Quarantine action for review',
      parameters: [
        {
          name: 'duration_minutes',
          label: 'Quarantine Duration (minutes)',
          type: 'number',
          required: true,
          min: 1,
          max: 1440,
          placeholder: '30',
          validate: (value) => {
            const num = parseInt(value);
            if (isNaN(num)) return 'Duration must be a number';
            if (num < 1 || num > 1440) return 'Duration must be between 1-1440 minutes';
            return null;
          }
        },
        {
          name: 'reason',
          label: 'Quarantine Reason',
          type: 'text',
          required: false,
          placeholder: 'Pending security review'
        }
      ],
      category: 'security'
    },
    {
      value: 'risk_assessment',
      label: '🔍 Risk Assessment',
      description: 'Perform deep risk analysis',
      parameters: [
        {
          name: 'deep_scan',
          label: 'Perform Deep Scan',
          type: 'checkbox',
          required: false,
          default: false
        },
        {
          name: 'include_context',
          label: 'Include Action Context',
          type: 'checkbox',
          required: false,
          default: true
        }
      ],
      category: 'analysis'
    },
    {
      value: 'log',
      label: '📝 Log Event',
      description: 'Log action to audit trail',
      parameters: [],
      category: 'audit'
    },
    {
      value: 'webhook',
      label: '🔗 Webhook Call',
      description: 'Call external webhook URL',
      parameters: [
        {
          name: 'url',
          label: 'Webhook URL',
          type: 'text',
          required: true,
          placeholder: 'https://api.example.com/webhook',
          validate: (value) => {
            if (!value) return 'URL is required';
            try {
              new URL(value);
              if (!value.startsWith('http://') && !value.startsWith('https://')) {
                return 'URL must start with http:// or https://';
              }
              return null;
            } catch {
              return 'Invalid URL format';
            }
          }
        },
        {
          name: 'method',
          label: 'HTTP Method',
          type: 'select',
          required: false,
          default: 'POST',
          options: [
            { value: 'GET', label: 'GET' },
            { value: 'POST', label: 'POST' },
            { value: 'PUT', label: 'PUT' }
          ]
        }
      ],
      category: 'integration'
    }
  ];

  const addAction = () => {
    const newAction = {
      type: '',
      parameters: {},
      enabled: true,
      order: localActions.length + 1
    };
    const updated = [...localActions, newAction];
    setLocalActions(updated);
    onChange(updated);
  };

  const removeAction = (index) => {
    const updated = localActions.filter((_, i) => i !== index);
    // Re-order remaining actions
    const reordered = updated.map((action, i) => ({ ...action, order: i + 1 }));
    setLocalActions(reordered);
    onChange(reordered);
  };

  const updateAction = (index, field, value) => {
    const updated = [...localActions];
    updated[index] = { ...updated[index], [field]: value };

    // If type changed, reset parameters
    if (field === 'type') {
      updated[index].parameters = {};
      const actionType = ACTION_TYPES.find(a => a.value === value);
      // Set default parameters
      if (actionType?.parameters) {
        actionType.parameters.forEach(param => {
          if (param.default !== undefined) {
            updated[index].parameters[param.name] = param.default;
          }
        });
      }
    }

    setLocalActions(updated);
    onChange(updated);
  };

  const updateActionParameter = (index, paramName, value) => {
    const updated = [...localActions];
    updated[index].parameters = {
      ...updated[index].parameters,
      [paramName]: value
    };
    setLocalActions(updated);
    onChange(updated);
  };

  const moveAction = (index, direction) => {
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === localActions.length - 1) return;

    const updated = [...localActions];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [updated[index], updated[targetIndex]] = [updated[targetIndex], updated[index]];

    // Update order numbers
    updated.forEach((action, i) => {
      action.order = i + 1;
    });

    setLocalActions(updated);
    onChange(updated);
  };

  const getActionTypeInfo = (actionType) => {
    return ACTION_TYPES.find(a => a.value === actionType);
  };

  const renderParameterInput = (actionIndex, param, value) => {
    const paramError = errors[`action_${actionIndex}_${param.name}`];

    switch (param.type) {
      case 'select':
        return (
          <select
            value={value || param.default || ''}
            onChange={(e) => updateActionParameter(actionIndex, param.name, e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              paramError ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">-- Select {param.label} --</option>
            {param.options?.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={value ?? param.default ?? false}
              onChange={(e) => updateActionParameter(actionIndex, param.name, e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{param.label}</span>
          </label>
        );

      case 'number':
        return (
          <input
            type="number"
            min={param.min}
            max={param.max}
            value={value || ''}
            onChange={(e) => updateActionParameter(actionIndex, param.name, e.target.value)}
            placeholder={param.placeholder}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              paramError ? 'border-red-500' : 'border-gray-300'
            }`}
          />
        );

      case 'text':
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => updateActionParameter(actionIndex, param.name, e.target.value)}
            placeholder={param.placeholder}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              paramError ? 'border-red-500' : 'border-gray-300'
            }`}
          />
        );
    }
  };

  return (
    <div className="space-y-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">⚡</span>
          <h4 className="font-semibold text-gray-900">Automated Actions</h4>
          {localActions.length > 0 && (
            <span className="text-xs text-gray-500">
              ({localActions.length} action{localActions.length !== 1 ? 's' : ''})
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={addAction}
          disabled={localActions.length >= 10}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          + Add Action
        </button>
      </div>

      {localActions.length === 0 && (
        <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <p className="text-gray-500 text-sm mb-2">No actions configured</p>
          <p className="text-gray-400 text-xs">Click "Add Action" to configure automated responses</p>
        </div>
      )}

      {localActions.map((action, index) => {
        const actionInfo = getActionTypeInfo(action.type);

        return (
          <div key={index} className="bg-white border border-gray-300 rounded-lg p-4">
            <div className="flex items-start gap-3">
              {/* Order Badge */}
              <div className="flex flex-col gap-1 mt-1">
                <button
                  type="button"
                  onClick={() => moveAction(index, 'up')}
                  disabled={index === 0}
                  className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Move up"
                >
                  ▲
                </button>
                <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                  {index + 1}
                </span>
                <button
                  type="button"
                  onClick={() => moveAction(index, 'down')}
                  disabled={index === localActions.length - 1}
                  className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Move down"
                >
                  ▼
                </button>
              </div>

              {/* Action Configuration */}
              <div className="flex-1 space-y-3">
                {/* Action Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Action Type {index === 0 && <span className="text-red-500">*</span>}
                  </label>
                  <select
                    value={action.type}
                    onChange={(e) => updateAction(index, 'type', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                      !action.type ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">-- Select Action --</option>
                    {Object.entries(
                      ACTION_TYPES.reduce((acc, type) => {
                        if (!acc[type.category]) acc[type.category] = [];
                        acc[type.category].push(type);
                        return acc;
                      }, {})
                    ).map(([category, types]) => (
                      <optgroup key={category} label={category.toUpperCase()}>
                        {types.map(type => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                  {actionInfo && (
                    <p className="text-xs text-gray-500 mt-1">{actionInfo.description}</p>
                  )}
                </div>

                {/* Action Parameters */}
                {actionInfo?.parameters && actionInfo.parameters.length > 0 && (
                  <div className="space-y-2 bg-gray-50 p-3 rounded border border-gray-200">
                    <p className="text-xs font-medium text-gray-700 mb-2">Parameters</p>
                    {actionInfo.parameters.map(param => (
                      <div key={param.name}>
                        {param.type !== 'checkbox' && (
                          <label className="block text-xs text-gray-600 mb-1">
                            {param.label}
                            {param.required && <span className="text-red-500 ml-1">*</span>}
                          </label>
                        )}
                        {renderParameterInput(index, param, action.parameters[param.name])}
                        {errors[`action_${index}_${param.name}`] && (
                          <p className="text-xs text-red-600 mt-1">
                            {errors[`action_${index}_${param.name}`]}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Enabled Toggle */}
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={action.enabled}
                    onChange={(e) => updateAction(index, 'enabled', e.target.checked)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Action enabled {!action.enabled && <span className="text-gray-500">(will be skipped)</span>}
                  </span>
                </label>
              </div>

              {/* Remove Button */}
              <button
                type="button"
                onClick={() => removeAction(index)}
                className="text-red-500 hover:text-red-700 text-xl mt-1"
                title="Remove action"
              >
                ×
              </button>
            </div>
          </div>
        );
      })}

      {localActions.length >= 10 && (
        <p className="text-xs text-gray-500 text-center">
          Maximum of 10 actions reached
        </p>
      )}

      {localActions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-700">
            <strong>💡 Tip:</strong> Actions execute in the order shown (top to bottom).
            Use the ▲▼ buttons to reorder actions.
          </p>
        </div>
      )}
    </div>
  );
};

export default ActionConfigurator;
