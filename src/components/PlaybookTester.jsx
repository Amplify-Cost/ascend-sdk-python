/**
 * 🏢 ENTERPRISE PLAYBOOK TESTER
 *
 * Phase 2 Frontend Component
 * Dry-run testing interface for playbook debugging
 *
 * Author: Donald King (OW-kai Enterprise)
 * Date: 2025-11-18
 */

import React, { useState } from 'react';

const PlaybookTester = ({ playbook, onClose, getAuthHeaders, API_BASE_URL }) => {
  const [testData, setTestData] = useState({
    risk_score: 50,
    action_type: '',
    environment: 'production',
    agent_id: '',
    timestamp: new Date().toISOString()
  });

  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);

  const ACTION_TYPES = [
    'database_read',
    'database_write',
    'file_read',
    'file_access',
    'network_scan',
    'api_call',
    'config_update',
    'user_permission_change',
    'financial_transaction',
    'api_key_generation'
  ];

  const handleTest = async () => {
    try {
      setTesting(true);
      setError(null);
      setTestResult(null);

      const response = await fetch(
        `${API_BASE_URL}/api/authorization/automation/playbooks/${playbook.id}/test`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ test_data: testData })
        }
      );

      if (response.ok) {
        const result = await response.json();
        setTestResult(result);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Test failed');
      }
    } catch (err) {
      console.error('Error testing playbook:', err);
      setError(err.message);
    } finally {
      setTesting(false);
    }
  };

  const getRiskScoreColor = (score) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-semibold">🧪 Test Playbook</h3>
              <p className="text-sm text-gray-600 mt-1">
                Playbook: <span className="font-medium">{playbook.name}</span> ({playbook.id})
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6 grid grid-cols-2 gap-6">
          {/* Left Column: Test Data Input */}
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-4">📝 Test Data</h4>

              {/* Risk Score */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk Score: <span className={`font-bold ${getRiskScoreColor(testData.risk_score)}`}>
                    {testData.risk_score}
                  </span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={testData.risk_score}
                  onChange={(e) => setTestData({...testData, risk_score: parseInt(e.target.value)})}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0 (Low)</span>
                  <span>50 (Medium)</span>
                  <span>100 (Critical)</span>
                </div>
              </div>

              {/* Action Type */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action Type
                </label>
                <select
                  value={testData.action_type}
                  onChange={(e) => setTestData({...testData, action_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Select Action Type --</option>
                  {ACTION_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Environment */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Environment
                </label>
                <select
                  value={testData.environment}
                  onChange={(e) => setTestData({...testData, environment: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </select>
              </div>

              {/* Agent ID */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agent ID (Optional)
                </label>
                <input
                  type="text"
                  value={testData.agent_id}
                  onChange={(e) => setTestData({...testData, agent_id: e.target.value})}
                  placeholder="e.g., analytics-agent"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Test Button */}
              <button
                onClick={handleTest}
                disabled={testing}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
              >
                {testing ? '🔄 Testing...' : '🧪 Run Test'}
              </button>
            </div>

            {/* Current Trigger Conditions */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="font-semibold text-blue-900 mb-2">🎯 Playbook Triggers</h4>
              <div className="text-sm text-blue-800 space-y-1">
                {playbook.trigger_conditions?.risk_score && (
                  <div>
                    • Risk score: {playbook.trigger_conditions.risk_score.min || 0} - {playbook.trigger_conditions.risk_score.max || 100}
                  </div>
                )}
                {playbook.trigger_conditions?.action_type && playbook.trigger_conditions.action_type.length > 0 && (
                  <div>
                    • Action types: {playbook.trigger_conditions.action_type.join(', ')}
                  </div>
                )}
                {playbook.trigger_conditions?.environment && playbook.trigger_conditions.environment.length > 0 && (
                  <div>
                    • Environments: {playbook.trigger_conditions.environment.join(', ')}
                  </div>
                )}
                {playbook.trigger_conditions?.business_hours && (
                  <div>• Business hours only</div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Test Results */}
          <div className="space-y-4">
            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-red-600 text-xl">❌</span>
                  <div>
                    <h4 className="font-semibold text-red-900">Test Error</h4>
                    <p className="text-sm text-red-800 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Test Results */}
            {testResult && (
              <>
                {/* Match Status */}
                <div className={`rounded-lg p-4 border-2 ${
                  testResult.matches
                    ? 'bg-green-50 border-green-500'
                    : 'bg-red-50 border-red-500'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="text-3xl">
                      {testResult.matches ? '✅' : '❌'}
                    </span>
                    <div>
                      <h4 className={`font-bold text-lg ${
                        testResult.matches ? 'text-green-900' : 'text-red-900'
                      }`}>
                        {testResult.matches ? 'Match Found!' : 'No Match'}
                      </h4>
                      <p className={`text-sm ${
                        testResult.matches ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {testResult.matches
                          ? 'This playbook would trigger for this action'
                          : 'This playbook would NOT trigger for this action'
                        }
                      </p>
                    </div>
                  </div>
                </div>

                {/* Matched Conditions */}
                {testResult.matched_conditions && testResult.matched_conditions.length > 0 && (
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <h4 className="font-semibold text-green-900 mb-2">✅ Matched Conditions</h4>
                    <ul className="text-sm text-green-800 space-y-1">
                      {testResult.matched_conditions.map((condition, idx) => (
                        <li key={idx}>• {condition}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Failed Conditions */}
                {testResult.failed_conditions && testResult.failed_conditions.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                    <h4 className="font-semibold text-red-900 mb-2">❌ Failed Conditions</h4>
                    <ul className="text-sm text-red-800 space-y-1">
                      {testResult.failed_conditions.map((condition, idx) => (
                        <li key={idx}>• {condition}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Would Execute Actions */}
                {testResult.would_execute_actions && testResult.would_execute_actions.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <h4 className="font-semibold text-blue-900 mb-2">⚡ Would Execute</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      {testResult.would_execute_actions.map((action, idx) => (
                        <li key={idx}>
                          {idx + 1}. {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Debugging Tips */}
                {!testResult.matches && (
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <h4 className="font-semibold text-yellow-900 mb-2">💡 Debugging Tips</h4>
                    <ul className="text-sm text-yellow-800 space-y-1">
                      <li>• Check if risk score is within trigger range</li>
                      <li>• Verify action type matches trigger conditions</li>
                      <li>• Ensure environment matches if specified</li>
                      <li>• Check business hours/weekend conditions</li>
                    </ul>
                  </div>
                )}
              </>
            )}

            {/* Initial State */}
            {!testResult && !error && (
              <div className="bg-gray-50 rounded-lg p-8 border-2 border-dashed border-gray-300 text-center">
                <span className="text-6xl mb-4 block">🧪</span>
                <p className="text-gray-600 font-medium">Configure test data and click "Run Test"</p>
                <p className="text-gray-500 text-sm mt-2">
                  Test results will appear here
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <p className="text-xs text-gray-600">
              💡 <strong>Note:</strong> This is a dry-run test. No actions will be executed.
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlaybookTester;
