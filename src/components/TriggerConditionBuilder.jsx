/**
 * 🏢 ENTERPRISE TRIGGER CONDITION BUILDER
 *
 * Phase 1 Frontend Component
 * Builds trigger conditions for automation playbooks with full validation
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState } from 'react';

const TriggerConditionBuilder = ({ value, onChange, errors = {} }) => {
  const [localConditions, setLocalConditions] = useState(value || {
    risk_score: { min: null, max: null },
    action_type: [],
    environment: [],
    business_hours: null,
    weekend: null
  });

  // Action types available in the system
  const ACTION_TYPES = [
    { value: 'database_read', label: '📖 Database Read', category: 'data' },
    { value: 'database_write', label: '✍️ Database Write', category: 'data' },
    { value: 'file_read', label: '📄 File Read', category: 'file' },
    { value: 'file_access', label: '📁 File Access', category: 'file' },
    { value: 'network_scan', label: '🌐 Network Scan', category: 'network' },
    { value: 'api_call', label: '🔌 API Call', category: 'network' },
    { value: 'config_update', label: '⚙️ Config Update', category: 'system' },
    { value: 'user_permission_change', label: '👤 User Permission Change', category: 'security' },
    { value: 'financial_transaction', label: '💰 Financial Transaction', category: 'financial' },
    { value: 'api_key_generation', label: '🔑 API Key Generation', category: 'security' }
  ];

  const ENVIRONMENTS = [
    { value: 'production', label: '🏭 Production', color: 'red' },
    { value: 'staging', label: '🧪 Staging', color: 'yellow' },
    { value: 'development', label: '💻 Development', color: 'green' }
  ];

  const updateCondition = (key, value) => {
    const updated = { ...localConditions, [key]: value };
    setLocalConditions(updated);
    onChange(updated);
  };

  const toggleActionType = (actionType) => {
    const current = localConditions.action_type || [];
    const updated = current.includes(actionType)
      ? current.filter(t => t !== actionType)
      : [...current, actionType];
    updateCondition('action_type', updated);
  };

  const toggleEnvironment = (env) => {
    const current = localConditions.environment || [];
    const updated = current.includes(env)
      ? current.filter(e => e !== env)
      : [...current, env];
    updateCondition('environment', updated);
  };

  const setRiskScore = (field, value) => {
    const numValue = value === '' ? null : parseInt(value);
    updateCondition('risk_score', {
      ...localConditions.risk_score,
      [field]: numValue
    });
  };

  return (
    <div className="space-y-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🎯</span>
        <h4 className="font-semibold text-gray-900">Trigger Conditions</h4>
        <span className="text-xs text-gray-500 ml-auto">
          All conditions must match for playbook to trigger
        </span>
      </div>

      {/* Risk Score Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Risk Score Range (0-100)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Minimum</label>
            <input
              type="number"
              min="0"
              max="100"
              value={localConditions.risk_score?.min ?? ''}
              onChange={(e) => setRiskScore('min', e.target.value)}
              placeholder="e.g., 0"
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.risk_score_min ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Maximum</label>
            <input
              type="number"
              min="0"
              max="100"
              value={localConditions.risk_score?.max ?? ''}
              onChange={(e) => setRiskScore('max', e.target.value)}
              placeholder="e.g., 40"
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                errors.risk_score_max ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
        </div>
        {(localConditions.risk_score?.min !== null || localConditions.risk_score?.max !== null) && (
          <div className="mt-2 text-xs text-gray-600">
            {localConditions.risk_score?.min !== null && localConditions.risk_score?.max !== null ? (
              <>
                Will match actions with risk score between{' '}
                <span className="font-semibold">{localConditions.risk_score.min}</span> and{' '}
                <span className="font-semibold">{localConditions.risk_score.max}</span>
              </>
            ) : localConditions.risk_score?.min !== null ? (
              <>
                Will match actions with risk score ≥{' '}
                <span className="font-semibold">{localConditions.risk_score.min}</span>
              </>
            ) : (
              <>
                Will match actions with risk score ≤{' '}
                <span className="font-semibold">{localConditions.risk_score.max}</span>
              </>
            )}
          </div>
        )}
        {errors.risk_score && (
          <p className="text-xs text-red-600 mt-1">{errors.risk_score}</p>
        )}
      </div>

      {/* Action Types */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Action Types
          {localConditions.action_type?.length > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({localConditions.action_type.length} selected)
            </span>
          )}
        </label>
        <div className="grid grid-cols-2 gap-2">
          {ACTION_TYPES.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => toggleActionType(type.value)}
              className={`px-3 py-2 text-sm border rounded-lg text-left transition-all ${
                localConditions.action_type?.includes(type.value)
                  ? 'bg-blue-50 border-blue-500 text-blue-900 font-medium'
                  : 'bg-white border-gray-300 text-gray-700 hover:border-blue-300'
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
        {localConditions.action_type?.length === 0 && (
          <p className="text-xs text-gray-500 mt-2">
            Select at least one action type, or leave empty to match all types
          </p>
        )}
        {errors.action_type && (
          <p className="text-xs text-red-600 mt-1">{errors.action_type}</p>
        )}
      </div>

      {/* Environment */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Environment
          {localConditions.environment?.length > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({localConditions.environment.length} selected)
            </span>
          )}
        </label>
        <div className="flex gap-2">
          {ENVIRONMENTS.map((env) => (
            <button
              key={env.value}
              type="button"
              onClick={() => toggleEnvironment(env.value)}
              className={`flex-1 px-3 py-2 text-sm border rounded-lg transition-all ${
                localConditions.environment?.includes(env.value)
                  ? 'bg-blue-50 border-blue-500 text-blue-900 font-medium'
                  : 'bg-white border-gray-300 text-gray-700 hover:border-blue-300'
              }`}
            >
              {env.label}
            </button>
          ))}
        </div>
        {localConditions.environment?.length === 0 && (
          <p className="text-xs text-gray-500 mt-2">
            Select target environments, or leave empty to match all
          </p>
        )}
        {errors.environment && (
          <p className="text-xs text-red-600 mt-1">{errors.environment}</p>
        )}
      </div>

      {/* Time-Based Conditions */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Time-Based Conditions
        </label>
        <div className="space-y-2">
          <label className="flex items-center gap-2 p-3 bg-white border border-gray-300 rounded-lg cursor-pointer hover:border-blue-300 transition-colors">
            <input
              type="checkbox"
              checked={localConditions.business_hours === true}
              onChange={(e) => {
                if (e.target.checked) {
                  updateCondition('business_hours', true);
                  updateCondition('weekend', null);
                } else {
                  updateCondition('business_hours', null);
                }
              }}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div className="flex-1">
              <span className="text-sm text-gray-900">🕐 Business Hours Only</span>
              <p className="text-xs text-gray-500">
                Mon-Fri, 9am-5pm EST
              </p>
            </div>
          </label>

          <label className="flex items-center gap-2 p-3 bg-white border border-gray-300 rounded-lg cursor-pointer hover:border-blue-300 transition-colors">
            <input
              type="checkbox"
              checked={localConditions.weekend === true}
              onChange={(e) => {
                if (e.target.checked) {
                  updateCondition('weekend', true);
                  updateCondition('business_hours', null);
                } else {
                  updateCondition('weekend', null);
                }
              }}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div className="flex-1">
              <span className="text-sm text-gray-900">📅 Weekends Only</span>
              <p className="text-xs text-gray-500">
                Saturday & Sunday
              </p>
            </div>
          </label>
        </div>
        {localConditions.business_hours === true && localConditions.weekend === true && (
          <p className="text-xs text-red-600 mt-2">
            ⚠️ Cannot select both business hours and weekends
          </p>
        )}
      </div>

      {/* Condition Summary */}
      {(localConditions.risk_score?.min !== null ||
        localConditions.risk_score?.max !== null ||
        localConditions.action_type?.length > 0 ||
        localConditions.environment?.length > 0 ||
        localConditions.business_hours !== null ||
        localConditions.weekend !== null) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">ℹ️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900 mb-1">
                Trigger Summary
              </p>
              <p className="text-xs text-blue-700">
                This playbook will trigger when <strong>ALL</strong> of the following conditions match:
              </p>
              <ul className="text-xs text-blue-700 mt-2 space-y-1 ml-4 list-disc">
                {(localConditions.risk_score?.min !== null || localConditions.risk_score?.max !== null) && (
                  <li>
                    Risk score: {localConditions.risk_score?.min ?? '0'} - {localConditions.risk_score?.max ?? '100'}
                  </li>
                )}
                {localConditions.action_type?.length > 0 && (
                  <li>Action type is one of: {localConditions.action_type.join(', ')}</li>
                )}
                {localConditions.environment?.length > 0 && (
                  <li>Environment is one of: {localConditions.environment.join(', ')}</li>
                )}
                {localConditions.business_hours === true && (
                  <li>During business hours (Mon-Fri, 9am-5pm EST)</li>
                )}
                {localConditions.weekend === true && (
                  <li>During weekends (Sat-Sun)</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TriggerConditionBuilder;
