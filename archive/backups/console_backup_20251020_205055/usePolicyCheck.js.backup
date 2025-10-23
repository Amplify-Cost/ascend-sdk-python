import { useState } from 'react';
import axios from 'axios';

/**
 * Enterprise Policy Pre-Execution Check Hook
 * 
 * Checks if an action will be allowed by policies BEFORE executing it.
 * Returns policy decision and handles enforcement UI flow.
 */
export const usePolicyCheck = () => {
  const [checking, setChecking] = useState(false);
  const [lastDecision, setLastDecision] = useState(null);

  const checkPolicy = async (actionData) => {
    setChecking(true);
    
    try {
      
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/governance/policies/enforce`,
        {
          agent_id: actionData.agent_id || 'web-ui-agent',
          action_type: actionData.action_type,
          target: actionData.target,
          context: actionData.context || {}
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const decision = {
        allowed: response.data.allowed,
        decision: response.data.decision,
        policies_triggered: response.data.policies_triggered || [],
        security_bridge: response.data.security_bridge || {},
        evaluation_time_ms: response.data.evaluation_time_ms
      };

      setLastDecision(decision);
      return decision;

    } catch (error) {
      console.error('Policy check failed:', error);
      
      // Fail-safe: On error, allow but log
      const failSafeDecision = {
        allowed: true,
        decision: 'ALLOW',
        policies_triggered: [],
        error: error.message,
        failSafe: true
      };
      
      setLastDecision(failSafeDecision);
      return failSafeDecision;
      
    } finally {
      setChecking(false);
    }
  };

  return {
    checkPolicy,
    checking,
    lastDecision
  };
};
