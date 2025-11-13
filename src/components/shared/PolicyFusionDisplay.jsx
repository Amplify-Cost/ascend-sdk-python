/**
 * PolicyFusionDisplay - Reusable component for Option 4 Hybrid Layered Architecture
 * Displays policy evaluation results and risk fusion calculations
 *
 * Purpose: Shows how the final risk score was calculated using:
 * - Policy Engine Risk (80% weight)
 * - CVSS Risk (20% weight)
 * - Intelligent Safety Rules
 *
 * Usage:
 * - variant="detailed": Full card with all info (for modals/expanded views)
 * - variant="badge": Compact badge (for table cells)
 * - variant="inline": Horizontal layout (for card headers)
 *
 * Backend Integration: POST /api/agent-actions returns these fields:
 * - policy_evaluated (boolean)
 * - policy_decision (string: ALLOW, DENY, REQUIRE_APPROVAL)
 * - policy_risk_score (int 0-100)
 * - risk_fusion_formula (string: e.g., "(20 × 0.8) + (25 × 0.2) = 21.0")
 */

import React, { useState } from 'react';

/**
 * Policy Decision Badge - Shows ALLOW/DENY/REQUIRE_APPROVAL status
 */
export const PolicyDecisionBadge = ({ decision }) => {
  if (!decision) {
    return (
      <span className="px-2 py-1 text-xs font-semibold rounded-md bg-gray-100 text-gray-600 border border-gray-300">
        Unknown
      </span>
    );
  }

  const styles = {
    ALLOW: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      border: 'border-green-300',
      label: 'Allowed'
    },
    DENY: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-300',
      label: 'Denied'
    },
    REQUIRE_APPROVAL: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      border: 'border-yellow-300',
      label: 'Requires Approval'
    },
  };

  const style = styles[decision] || {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-300',
    label: decision
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-md border ${style.bg} ${style.text} ${style.border}`}>
      {style.label}
    </span>
  );
};

/**
 * Main Policy Fusion Display Component
 */
export const PolicyFusionDisplay = ({
  policyEvaluated = false,
  policyDecision = null,
  policyRiskScore = null,
  baseRiskScore = null,
  riskFusionFormula = null,
  variant = 'detailed' // 'detailed', 'badge', 'inline'
}) => {
  const [showFormula, setShowFormula] = useState(false);

  // If policy wasn't evaluated, show minimal indicator
  if (!policyEvaluated) {
    if (variant === 'badge') {
      return (
        <span className="px-2 py-1 text-xs rounded-md bg-gray-100 text-gray-600">
          No Policy
        </span>
      );
    }
    if (variant === 'inline') {
      return null; // Don't show anything
    }
    // detailed variant
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
        <p className="text-sm text-gray-600">Policy evaluation not available for this action</p>
      </div>
    );
  }

  // Badge variant (for table cells)
  if (variant === 'badge') {
    return (
      <div className="flex items-center space-x-2">
        <PolicyDecisionBadge decision={policyDecision} />
        {policyRiskScore !== null && (
          <span className="text-xs text-gray-600">
            ({policyRiskScore})
          </span>
        )}
      </div>
    );
  }

  // Inline variant (for card headers)
  if (variant === 'inline') {
    return (
      <div className="flex items-center space-x-2">
        <PolicyDecisionBadge decision={policyDecision} />
        {riskFusionFormula && (
          <button
            onClick={() => setShowFormula(!showFormula)}
            className="text-xs text-purple-600 hover:text-purple-800 underline focus:outline-none"
            title="View risk fusion calculation"
          >
            View Fusion
          </button>
        )}
        {showFormula && riskFusionFormula && (
          <div className="absolute z-10 mt-24 bg-white border border-purple-300 rounded-lg shadow-lg p-3 text-xs">
            <p className="font-mono text-purple-900">{riskFusionFormula}</p>
            <button
              onClick={() => setShowFormula(false)}
              className="mt-2 text-purple-600 hover:text-purple-800"
            >
              Close
            </button>
          </div>
        )}
      </div>
    );
  }

  // Detailed variant (for expanded views/modals)
  return (
    <div className="bg-white border border-purple-200 rounded-lg p-4">
      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
        <svg className="w-4 h-4 mr-2 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
          <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
        </svg>
        Policy Evaluation & Risk Fusion
      </h4>

      {/* Decision Status */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <span className="text-sm text-gray-600 font-medium">Policy Decision:</span>
        <PolicyDecisionBadge decision={policyDecision} />
      </div>

      {/* Risk Scores Comparison */}
      {(baseRiskScore !== null || policyRiskScore !== null) && (
        <div className="space-y-3 mb-4">
          {baseRiskScore !== null && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-600">Final Risk Score:</span>
                <span className="text-sm font-semibold">{baseRiskScore}/100</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    baseRiskScore >= 85 ? 'bg-red-600' :
                    baseRiskScore >= 60 ? 'bg-orange-500' :
                    baseRiskScore >= 40 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(baseRiskScore, 100)}%` }}
                />
              </div>
            </div>
          )}

          {policyRiskScore !== null && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-600">Policy Risk Score:</span>
                <span className="text-sm font-semibold text-purple-600">
                  {policyRiskScore}/100
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-purple-600 transition-all"
                  style={{ width: `${Math.min(policyRiskScore, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fusion Formula */}
      {riskFusionFormula && (
        <div className="bg-purple-50 border border-purple-200 rounded p-3">
          <button
            onClick={() => setShowFormula(!showFormula)}
            className="text-xs font-medium text-purple-800 flex items-center justify-between w-full hover:text-purple-900 transition-colors"
          >
            <span className="flex items-center">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              Risk Fusion Calculation
            </span>
            <span className="text-purple-600">{showFormula ? '▼' : '▶'}</span>
          </button>

          {showFormula && (
            <div className="mt-3 pt-3 border-t border-purple-200">
              <p className="text-xs font-mono text-purple-900 bg-white p-2 rounded border border-purple-100">
                {riskFusionFormula}
              </p>
              <div className="mt-3 text-xs text-purple-700 space-y-1">
                <p><strong>Formula:</strong> (Policy Risk × 0.8) + (CVSS Risk × 0.2)</p>
                <p className="text-purple-600">
                  Combines context-aware policy evaluation (80% weight) with technical CVSS assessment (20% weight)
                </p>
              </div>
              <div className="mt-3 pt-3 border-t border-purple-200">
                <p className="text-xs font-medium text-purple-800 mb-1">Safety Rules Applied:</p>
                <ul className="text-xs text-purple-700 space-y-1 list-disc list-inside">
                  <li>CRITICAL CVSS: minimum score = 85</li>
                  <li>DENY policy: score = 100 (absolute block)</li>
                  <li>ALLOW + Safe CVSS: maximum score = 40</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PolicyFusionDisplay;
