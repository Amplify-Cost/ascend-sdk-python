import React, { useState } from 'react';
import { TestTube, Play, Check, X, AlertTriangle } from 'lucide-react';

export const PolicyTester = ({ API_BASE_URL, getAuthHeaders }) => {
  const [testInput, setTestInput] = useState({
    agent_id: 'test-agent-001',
    action_type: 'database_write',
    target: 'production_database',
    context: {}
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runTest = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/enforce`,
        {
          method: 'POST',
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify(testInput)
        }
      );
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Test failed:', error);
      setResult({ error: 'Test failed' });
    } finally {
      setLoading(false);
    }
  };

  const actionTypes = [
    'database_read', 'database_write', 'database_delete',
    'file_read', 'file_write', 'file_delete',
    's3_read', 's3_write', 's3_delete',
    'api_call', 'execute_code'
  ];

  const targetSystems = [
    'production_database', 'staging_database',
    'production_s3', 'staging_s3',
    'external_api', 'internal_api'
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <TestTube className="h-6 w-6 text-green-600" />
        <h3 className="text-2xl font-bold">Policy Testing Sandbox</h3>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-semibold mb-4">Test Configuration</h4>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Agent ID</label>
              <input
                type="text"
                value={testInput.agent_id}
                onChange={e => setTestInput({...testInput, agent_id: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Action Type</label>
              <select
                value={testInput.action_type}
                onChange={e => setTestInput({...testInput, action_type: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg"
              >
                {actionTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Target System</label>
            <select
              value={testInput.target}
              onChange={e => setTestInput({...testInput, target: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {targetSystems.map(sys => (
                <option key={sys} value={sys}>{sys}</option>
              ))}
            </select>
          </div>

          <button
            onClick={runTest}
            disabled={loading}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2 font-semibold"
          >
            <Play className="h-5 w-5" />
            {loading ? 'Testing...' : 'Run Test'}
          </button>
        </div>
      </div>

      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold mb-4">Test Results</h4>
          
          <div className={`p-4 rounded-lg border-2 ${
            result.decision === 'ALLOW' ? 'bg-green-50 border-green-300' :
            result.decision === 'DENY' ? 'bg-red-50 border-red-300' :
            'bg-yellow-50 border-yellow-300'
          }`}>
            <div className="flex items-center gap-3 mb-3">
              {result.decision === 'ALLOW' && <Check className="h-6 w-6 text-green-600" />}
              {result.decision === 'DENY' && <X className="h-6 w-6 text-red-600" />}
              {result.decision === 'REQUIRE_APPROVAL' && <AlertTriangle className="h-6 w-6 text-yellow-600" />}
              <span className="text-xl font-bold">Decision: {result.decision}</span>
            </div>

            {result.policies_triggered?.length > 0 && (
              <div className="mt-4">
                <div className="font-medium mb-2">Triggered Policies:</div>
                {result.policies_triggered.map((policy, idx) => (
                  <div key={idx} className="bg-white rounded p-3 mb-2">
                    <div className="font-medium">{policy.policy_name}</div>
                    <div className="text-sm text-gray-600">Effect: {policy.effect}</div>
                  </div>
                ))}
              </div>
            )}

            {result.evaluation_time_ms !== undefined && (
              <div className="mt-3 text-sm text-gray-600">
                Evaluation time: {result.evaluation_time_ms}ms
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyTester;
