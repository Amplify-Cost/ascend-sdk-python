import React from 'react';

/**
 * 🏢 ENTERPRISE: Policy Decision Badge Component
 *
 * Displays policy evaluation results from UnifiedPolicyEvaluationService
 * Shows decision from EnterpriseRealTimePolicyEngine (same engine for both agent and MCP actions)
 *
 * Features:
 * - Policy decision display (ALLOW, DENY, REQUIRE_APPROVAL, ESCALATE, CONDITIONAL)
 * - Policy risk score (0-100 from 4-category comprehensive scoring)
 * - Visual indicators matching decision type
 * - Works for BOTH agent and MCP actions
 *
 * Usage: <PolicyDecisionBadge action={actionData} />
 *
 * @param {Object} action - Action with policy_evaluated, policy_decision, policy_risk_score fields
 */
export const PolicyDecisionBadge = ({ action, showDetails = false }) => {
  // Check if policy was evaluated
  if (!action || !action.policy_evaluated) {
    return (
      <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 border border-gray-300">
        ⏳ Not Evaluated
      </span>
    );
  }

  // Map policy decisions to colors and icons
  const decisionConfig = {
    'ALLOW': {
      color: 'bg-green-100 text-green-800 border-green-300',
      icon: '✅',
      label: 'ALLOW'
    },
    'DENY': {
      color: 'bg-red-100 text-red-800 border-red-300',
      icon: '❌',
      label: 'DENY'
    },
    'REQUIRE_APPROVAL': {
      color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      icon: '⏰',
      label: 'APPROVAL'
    },
    'ESCALATE': {
      color: 'bg-orange-100 text-orange-800 border-orange-300',
      icon: '⬆️',
      label: 'ESCALATE'
    },
    'CONDITIONAL': {
      color: 'bg-blue-100 text-blue-800 border-blue-300',
      icon: '🔀',
      label: 'CONDITIONAL'
    }
  };

  const config = decisionConfig[action.policy_decision] || decisionConfig['REQUIRE_APPROVAL'];

  return (
    <div className="inline-flex items-center gap-2">
      {/* Policy Decision Badge */}
      <span className={`px-2 py-1 rounded text-xs font-medium border ${config.color}`}>
        {config.icon} {config.label}
      </span>

      {/* Policy Risk Score (if available) */}
      {action.policy_risk_score !== null && action.policy_risk_score !== undefined && showDetails && (
        <span className="text-xs text-gray-600">
          Policy Risk: <span className="font-semibold">{action.policy_risk_score}/100</span>
        </span>
      )}

      {/* Tooltip showing this is from unified policy engine */}
      {showDetails && (
        <span className="text-xs text-gray-500 italic" title="Evaluated by EnterpriseRealTimePolicyEngine">
          🏢 Unified Engine
        </span>
      )}
    </div>
  );
};

/**
 * 🏢 ENTERPRISE: Policy Details Card Component
 *
 * Displays comprehensive policy evaluation details
 * Shows full 4-category risk breakdown and recommendations
 *
 * Usage: <PolicyDetailsCard action={actionData} />
 */
export const PolicyDetailsCard = ({ action }) => {
  if (!action || !action.policy_evaluated) {
    return null;
  }

  // Get risk level color
  const getRiskLevelColor = (score) => {
    if (score >= 90) return 'text-red-600';
    if (score >= 70) return 'text-orange-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded p-4 mt-3">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-800">🏢 Policy Evaluation Results</h4>
        <PolicyDecisionBadge action={action} showDetails={false} />
      </div>

      <div className="space-y-2 text-sm">
        {/* Policy Risk Score */}
        <div className="flex justify-between">
          <span className="text-gray-600">Policy Risk Score:</span>
          <span className={`font-semibold ${getRiskLevelColor(action.policy_risk_score)}`}>
            {action.policy_risk_score}/100
          </span>
        </div>

        {/* Risk Fusion Formula (for agent actions with CVSS) */}
        {action.risk_fusion_formula && (
          <div className="flex justify-between">
            <span className="text-gray-600">Risk Fusion:</span>
            <span className="text-xs font-mono text-gray-500" title={action.risk_fusion_formula}>
              {action.risk_fusion_formula.includes('hybrid') ? '80% CVSS + 20% Policy' : 'Policy Only'}
            </span>
          </div>
        )}

        {/* Evaluated By */}
        <div className="flex justify-between">
          <span className="text-gray-600">Evaluated By:</span>
          <span className="text-xs text-gray-500">EnterpriseRealTimePolicyEngine</span>
        </div>

        {/* Action Source */}
        <div className="flex justify-between">
          <span className="text-gray-600">Action Source:</span>
          <span className="text-xs">
            {action.action_source === 'agent' && '🤖 Agent Action'}
            {action.action_source === 'mcp_server' && '🔌 MCP Server'}
          </span>
        </div>
      </div>

      {/* Info note */}
      <div className="mt-3 pt-3 border-t border-gray-300">
        <p className="text-xs text-gray-500 italic">
          ✅ Both agent and MCP actions use the same unified policy engine for consistent governance
        </p>
      </div>
    </div>
  );
};

export default PolicyDecisionBadge;
