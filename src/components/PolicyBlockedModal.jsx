import React from 'react';
import { X, Shield, AlertTriangle } from 'lucide-react';

/**
 * Enterprise Policy Blocked Modal
 * 
 * Displays when a policy denies an action before execution.
 * Shows which policy blocked it and why.
 */
export const PolicyBlockedModal = ({ isOpen, onClose, policyDecision }) => {
  if (!isOpen) return null;

  const { policies_triggered = [], decision, security_bridge = {} } = policyDecision || {};

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-red-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-full">
              <Shield className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Action Blocked by Policy
              </h2>
              <p className="text-sm text-gray-600">
                This action cannot be executed due to security policy
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Decision Summary */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-900">
                  Decision: {decision}
                </p>
                <p className="text-sm text-red-700 mt-1">
                  Your action was evaluated against {policyDecision?.policies_evaluated || 0} active policies
                  and was blocked by the following policy rules.
                </p>
              </div>
            </div>
          </div>

          {/* Triggered Policies */}
          {policies_triggered && policies_triggered.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-3">
                Policies Triggered
              </h3>
              <div className="space-y-3">
                {policies_triggered.map((policy, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          Policy #{policy.policy_id}
                        </p>
                        <p className="text-sm text-gray-700 mt-1">
                          {policy.policy_name || 'Security Policy'}
                        </p>
                        <div className="mt-2">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            policy.effect === 'deny' 
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {policy.effect?.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Security Bridge Info */}
          {security_bridge.audit_id && (
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
              <p className="font-medium text-gray-700 mb-1">Audit Trail</p>
              <p>This action was logged for security review.</p>
              <p className="mt-1">Audit ID: {security_bridge.audit_id}</p>
            </div>
          )}

          {/* Next Steps */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-medium text-blue-900 mb-2">What can you do?</p>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Review the policy requirements with your security team</li>
              <li>Request an exception if this action is legitimate</li>
              <li>Modify your action to comply with policy requirements</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
