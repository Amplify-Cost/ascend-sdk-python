import React, { useState, useEffect } from 'react';
import { AlertTriangle, Users, Lock, TrendingUp, Activity } from 'lucide-react';

export const PolicyImpactAnalysis = ({ policy, API_BASE_URL, getAuthHeaders }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (policy) {
      analyzeImpact();
    }
  }, [policy]);

  const analyzeImpact = async () => {
    setLoading(true);

    try {
      // SEC-076-FE: Call real backend API for impact analysis
      const response = await fetch(
        `${API_BASE_URL}/api/governance/policies/${policy?.id}/impact-analysis`,
        { credentials: "include", headers: getAuthHeaders() }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data.analysis || data);
      } else {
        // SEC-076-FE: Return empty state instead of hardcoded data
        setAnalysis({
          affected_agents: 0,
          affected_users: 0,
          estimated_blocks_per_day: 0,
          affected_resources: [],
          risk_reduction: 0,
          false_positive_risk: 'unknown',
          recommendations: [
            'Impact analysis requires policy deployment history',
            'Deploy to staging first to generate impact data'
          ]
        });
      }
    } catch (error) {
      console.error('Failed to load impact analysis:', error);
      // SEC-076-FE: Empty state on error - NO hardcoded demo data
      setAnalysis({
        affected_agents: 0,
        affected_users: 0,
        estimated_blocks_per_day: 0,
        affected_resources: [],
        risk_reduction: 0,
        false_positive_risk: 'unknown',
        recommendations: ['Unable to analyze impact - API unavailable']
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Activity className="h-6 w-6 text-orange-600" />
        <h3 className="text-2xl font-bold">Impact Analysis</h3>
      </div>

      {/* Impact Warning */}
      <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-6 w-6 text-orange-600 mt-0.5" />
          <div>
            <p className="font-semibold text-orange-900 mb-1">
              Before Deployment
            </p>
            <p className="text-sm text-orange-700">
              This policy will affect {analysis.affected_agents} agents and {analysis.affected_users} users.
              Review the impact analysis below before deploying to production.
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <Users className="h-5 w-5 text-blue-600" />
            <span className="text-sm text-gray-600">Affected Users</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{analysis.affected_users}</div>
          <div className="text-sm text-gray-500 mt-1">May need additional approvals</div>
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <Lock className="h-5 w-5 text-red-600" />
            <span className="text-sm text-gray-600">Est. Blocks/Day</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{analysis.estimated_blocks_per_day}</div>
          <div className="text-sm text-gray-500 mt-1">Based on historical data</div>
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-600">Risk Reduction</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{analysis.risk_reduction}%</div>
          <div className="text-sm text-gray-500 mt-1">Expected security improvement</div>
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <span className="text-sm text-gray-600">False Positive Risk</span>
          </div>
          <div className={`text-3xl font-bold ${
            analysis.false_positive_risk === 'low' ? 'text-green-600' :
            analysis.false_positive_risk === 'medium' ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {analysis.false_positive_risk.toUpperCase()}
          </div>
          <div className="text-sm text-gray-500 mt-1">Likelihood of blocking legitimate actions</div>
        </div>
      </div>

      {/* Affected Resources */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="font-semibold mb-3">Affected Resources</h4>
        <div className="flex flex-wrap gap-2">
          {analysis.affected_resources.map((resource, idx) => (
            <span
              key={idx}
              className="px-3 py-2 bg-purple-100 text-purple-800 rounded-lg text-sm font-medium"
            >
              {resource}
            </span>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="font-semibold mb-3">Deployment Recommendations</h4>
        <div className="space-y-2">
          {analysis.recommendations.map((rec, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </div>
              <p className="text-sm text-gray-700">{rec}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold">
          Deploy to Staging
        </button>
        <button className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold">
          Deploy to Production
        </button>
        <button className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancel
        </button>
      </div>
    </div>
  );
};

export default PolicyImpactAnalysis;
