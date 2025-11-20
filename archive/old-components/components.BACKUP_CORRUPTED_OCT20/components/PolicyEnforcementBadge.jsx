import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import logger from '../utils/logger.js';

/**
 * PolicyEnforcementBadge - Shows real-time policy status for an action
 * 
 * Usage: <PolicyEnforcementBadge action={actionData} />
 * 
 * Displays inline badge showing if action would be:
 * - ✅ ALLOWED (green)
 * - ❌ DENIED (red) 
 * - ⏰ REQUIRES APPROVAL (yellow)
 */
export const PolicyEnforcementBadge = ({ action, onPolicyCheck }) => {
  const [policyStatus, setPolicyStatus] = useState(null);
  const [checking, setChecking] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    checkPolicy();
  }, [action]);

  const checkPolicy = async () => {
    if (!action) return;
    
    setChecking(true);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/governance/policies/enforce`,
        {
          agent_id: action.agent_id || 'web-ui',
          action_type: action.action_type,
          target: action.target || action.target_system || 'unknown',
          context: action.context || {}
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setPolicyStatus(response.data);
      if (onPolicyCheck) {
        onPolicyCheck(response.data);
      }
    } catch (error) {
      logger.error('Policy check failed:', error);
      setPolicyStatus({
        allowed: true,
        decision: 'ALLOW',
        policies_triggered: [],
        error: true
      });
    } finally {
      setChecking(false);
    }
  };

  if (checking) {
    return (
      <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
        <Shield className="h-3 w-3 mr-1 animate-spin" />
        Checking...
      </span>
    );
  }

  if (!policyStatus) return null;

  const getStatusConfig = () => {
    if (policyStatus.decision === 'DENY') {
      return {
        icon: XCircle,
        color: 'bg-red-100 text-red-800 border-red-200',
        label: 'BLOCKED',
        iconColor: 'text-red-600'
      };
    } else if (policyStatus.decision === 'REQUIRE_APPROVAL') {
      return {
        icon: Clock,
        color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        label: 'APPROVAL NEEDED',
        iconColor: 'text-yellow-600'
      };
    } else {
      return {
        icon: CheckCircle,
        color: 'bg-green-100 text-green-800 border-green-200',
        label: 'ALLOWED',
        iconColor: 'text-green-600'
      };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="inline-flex items-center gap-1">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${config.color} cursor-pointer hover:opacity-80 transition-opacity`}
      >
        <Icon className={`h-3 w-3 mr-1 ${config.iconColor}`} />
        {config.label}
      </button>

      {showDetails && policyStatus.policies_triggered?.length > 0 && (
        <div className="absolute z-10 mt-8 w-64 bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <div className="text-xs font-medium text-gray-900 mb-2">
            Policies Triggered ({policyStatus.policies_triggered.length})
          </div>
          {policyStatus.policies_triggered.map((policy, index) => (
            <div key={index} className="text-xs text-gray-600 mb-1">
              • {policy.policy_name}
            </div>
          ))}
          <div className="text-xs text-gray-500 mt-2 pt-2 border-t">
            Evaluated in {policyStatus.evaluation_time_ms?.toFixed(2)}ms
          </div>
        </div>
      )}
    </div>
  );
};
