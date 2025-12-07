import React, { useState } from "react";

// SEC-108: Enterprise Action Types aligned with backend cvss_auto_mapper.py (57+ types)
const ACTION_TYPES = [
  // Data Operations
  { value: 'database_read', label: 'Database Read', category: 'Data' },
  { value: 'database_write', label: 'Database Write', category: 'Data' },
  { value: 'database_delete', label: 'Database Delete', category: 'Data' },
  { value: 'data_export', label: 'Data Export', category: 'Data' },
  { value: 'data_import', label: 'Data Import', category: 'Data' },
  { value: 'bulk_write', label: 'Bulk Write', category: 'Data' },
  { value: 'bulk_delete', label: 'Bulk Delete', category: 'Data' },

  // File Operations
  { value: 'file_read', label: 'File Read', category: 'File' },
  { value: 'file_write', label: 'File Write', category: 'File' },
  { value: 'file_delete', label: 'File Delete', category: 'File' },
  { value: 'file_upload', label: 'File Upload', category: 'File' },
  { value: 'file_download', label: 'File Download', category: 'File' },

  // Financial Operations (Banking/FinTech)
  { value: 'execute_trade', label: 'Execute Trade', category: 'Financial' },
  { value: 'funds_transfer', label: 'Funds Transfer', category: 'Financial' },
  { value: 'payment_process', label: 'Payment Process', category: 'Financial' },
  { value: 'credit_decision', label: 'Credit Decision', category: 'Financial' },
  { value: 'loan_approval', label: 'Loan Approval', category: 'Financial' },

  // Healthcare/HIPAA
  { value: 'phi_access', label: 'PHI Access', category: 'Healthcare' },
  { value: 'phi_modify', label: 'PHI Modify', category: 'Healthcare' },
  { value: 'prescription_write', label: 'Prescription Write', category: 'Healthcare' },
  { value: 'medical_record_access', label: 'Medical Record Access', category: 'Healthcare' },

  // PII/Privacy (GDPR/CCPA)
  { value: 'pii_access', label: 'PII Access', category: 'Privacy' },
  { value: 'pii_modify', label: 'PII Modify', category: 'Privacy' },
  { value: 'pii_delete', label: 'PII Delete', category: 'Privacy' },
  { value: 'consent_update', label: 'Consent Update', category: 'Privacy' },

  // System/Infrastructure
  { value: 'shell_execute', label: 'Shell Execute', category: 'System' },
  { value: 'code_execute', label: 'Code Execute', category: 'System' },
  { value: 'config_change', label: 'Config Change', category: 'System' },
  { value: 'system_modification', label: 'System Modification', category: 'System' },
  { value: 'privilege_escalation', label: 'Privilege Escalation', category: 'System' },
  { value: 'credential_access', label: 'Credential Access', category: 'System' },
  { value: 'secret_access', label: 'Secret Access', category: 'System' },
  { value: 'encryption_key_access', label: 'Encryption Key Access', category: 'System' },

  // API Operations
  { value: 'api_call', label: 'API Call', category: 'API' },
  { value: 'api_read', label: 'API Read', category: 'API' },
  { value: 'api_write', label: 'API Write', category: 'API' },
  { value: 'external_api_call', label: 'External API Call', category: 'API' },
  { value: 'webhook_trigger', label: 'Webhook Trigger', category: 'API' },

  // User Management
  { value: 'user_create', label: 'User Create', category: 'User' },
  { value: 'user_modify', label: 'User Modify', category: 'User' },
  { value: 'user_delete', label: 'User Delete', category: 'User' },
  { value: 'permission_grant', label: 'Permission Grant', category: 'User' },
  { value: 'permission_revoke', label: 'Permission Revoke', category: 'User' },
  { value: 'role_assign', label: 'Role Assign', category: 'User' },

  // HR/Employee
  { value: 'employee_record_access', label: 'Employee Record Access', category: 'HR' },
  { value: 'employee_record_modify', label: 'Employee Record Modify', category: 'HR' },
  { value: 'payroll_modify', label: 'Payroll Modify', category: 'HR' },
  { value: 'benefits_modify', label: 'Benefits Modify', category: 'HR' },

  // Security Operations
  { value: 'vulnerability_scan', label: 'Vulnerability Scan', category: 'Security' },
  { value: 'compliance_check', label: 'Compliance Check', category: 'Security' },
  { value: 'threat_analysis', label: 'Threat Analysis', category: 'Security' },
  { value: 'access_review', label: 'Access Review', category: 'Security' },
  { value: 'forensic_analysis', label: 'Forensic Analysis', category: 'Security' },
  { value: 'network_monitoring', label: 'Network Monitoring', category: 'Security' },
  { value: 'audit_log_access', label: 'Audit Log Access', category: 'Security' },

  // Operations
  { value: 'data_backup', label: 'Data Backup', category: 'Operations' },
  { value: 'backup_restore', label: 'Backup Restore', category: 'Operations' },
  { value: 'system_maintenance', label: 'System Maintenance', category: 'Operations' },
  { value: 'service_restart', label: 'Service Restart', category: 'Operations' },
  { value: 'deployment', label: 'Deployment', category: 'Operations' },

  // Custom
  { value: 'custom', label: 'Custom (specify in description)', category: 'Other' },
];

// Group action types by category for dropdown
const getGroupedActionTypes = () => {
  return ACTION_TYPES.reduce((acc, type) => {
    if (!acc[type.category]) acc[type.category] = [];
    acc[type.category].push(type);
    return acc;
  }, {});
};

const AgentActionSubmitPanel = ({ getAuthHeaders }) => {
  const [agentId, setAgentId] = useState("");
  const [actionType, setActionType] = useState("");
  const [toolName, setToolName] = useState("");
  const [description, setDescription] = useState("");
  const [riskLevel, setRiskLevel] = useState("medium");
  const [businessJustification, setBusinessJustification] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  // SEC-107: Track last result for threshold transparency
  const [lastResult, setLastResult] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // Predefined test scenarios for quick testing
  const testScenarios = [
    {
      name: "🔍 Vulnerability Scan",
      agent_id: "security-scanner-test",
      action_type: "vulnerability_scan",
      tool_name: "nessus-scanner",
      description: "Automated security vulnerability assessment of production web servers",
      risk_level: "high",
      justification: "Monthly security compliance scan required for SOX audit"
    },
    {
      name: "📋 Compliance Check", 
      agent_id: "compliance-auditor-test",
      action_type: "compliance_check",
      tool_name: "compliance-checker",
      description: "HIPAA compliance verification of patient data handling systems",
      risk_level: "medium",
      justification: "Quarterly HIPAA compliance validation as required by healthcare regulations"
    },
    {
      name: "🔎 Threat Analysis",
      agent_id: "threat-hunter-test", 
      action_type: "threat_analysis",
      tool_name: "threat-detector",
      description: "Deep packet inspection and behavioral analysis for APT detection",
      risk_level: "high",
      justification: "Proactive threat hunting following recent security intelligence reports"
    },
    {
      name: "💾 Data Backup",
      agent_id: "backup-agent-test",
      action_type: "data_backup", 
      tool_name: "backup-manager",
      description: "Automated backup of critical business and customer data",
      risk_level: "low",
      justification: "Routine data protection backup as per disaster recovery procedures"
    }
  ];

  const loadTestScenario = (scenario) => {
    setAgentId(scenario.agent_id);
    setActionType(scenario.action_type);
    setToolName(scenario.tool_name);
    setDescription(scenario.description);
    setRiskLevel(scenario.risk_level);
    setBusinessJustification(scenario.justification);
    setMessage(null);
    setError(null);
  };

  const clearForm = () => {
    setAgentId("");
    setActionType("");
    setToolName("");
    setDescription("");
    setRiskLevel("medium");
    setBusinessJustification("");
    setMessage(null);
    setError(null);
    setLastResult(null);  // SEC-107: Clear threshold display
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLastResult(null);
    setLoading(true);

    // Enterprise validation
    if (!businessJustification.trim()) {
      setError("❌ Business justification is required for enterprise compliance");
      setLoading(false);
      return;
    }

    try {
      console.log('🚀 Submitting enterprise agent action via unified SDK endpoint...');

      // SEC-108: Fix payload structure - required fields at ROOT level
      // Map risk_level to data_sensitivity for risk calculation
      const sensitivityMapping = {
        "low": "public",
        "medium": "internal",
        "high": "confidential",
        "critical": "restricted"
      };

      const payload = {
        // SEC-108: Required fields at ROOT level (not inside context)
        agent_id: agentId,
        action_type: actionType,
        tool_name: toolName || "manual",                    // ROOT level (was in context)
        description: description,                           // ROOT level (was in context)
        business_justification: businessJustification,      // ROOT level (was in context)
        // Optional fields
        resource_type: "general",
        data_sensitivity: sensitivityMapping[riskLevel] || "internal",
        environment: "production",
        // Context for additional metadata (not required fields)
        context: {
          submitted_via: "enterprise_admin_panel",
          timestamp: Math.floor(Date.now() / 1000),
          requested_risk_level: riskLevel  // For audit trail
        },
        resource_details: {
          resource: `${actionType}/${toolName || 'manual'}`,
          action: actionType
        },
        parameters: {}
      };

      console.log('📤 Unified API Payload:', payload);

      // SEC-107: Use unified v1/actions/submit endpoint
      const endpoint = `${API_BASE_URL}/api/v1/actions/submit`;
      console.log(`🔍 Calling unified endpoint: ${endpoint}`);

      const res = await fetch(endpoint, {
        credentials: "include",
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      console.log(`📊 Response status: ${res.status}`);

      if (res.ok) {
        const result = await res.json();
        console.log('✅ Success response:', result);

        // SEC-107: Store result for threshold display
        setLastResult(result);

        // Build status message with threshold transparency
        const thresholds = result.thresholds || {};
        const statusEmoji = result.status === "approved" ? "✅" :
                           result.status === "denied" ? "❌" : "⏳";

        let statusMessage = `${statusEmoji} Agent action submitted successfully!\n`;
        statusMessage += `Action ID: ${result.action_id || 'Generated'}\n`;
        statusMessage += `Status: ${result.status || 'pending_approval'}\n`;
        statusMessage += `Risk Score: ${result.risk_score || 'N/A'}\n`;

        // SEC-106c: Add threshold transparency
        if (thresholds.auto_approve_below !== undefined) {
          statusMessage += `\n📊 Threshold Info:\n`;
          statusMessage += `• Auto-approve below: ${thresholds.auto_approve_below}\n`;
          statusMessage += `• Max risk threshold: ${thresholds.max_risk_threshold}\n`;
          statusMessage += `• Agent type: ${thresholds.agent_type || 'unregistered'}\n`;
        }

        setMessage(statusMessage);

        // Don't clear form - let user see what was submitted
        // clearForm();
      } else {
        const errorText = await res.text();
        console.log(`❌ Error response: ${res.status} - ${errorText}`);
        throw new Error(`${res.status}: ${errorText}`);
      }

    } catch (err) {
      console.error("💥 Enterprise submission error:", err);
      setError(`❌ Enterprise submission failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Test Scenarios */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-800 mb-3">🚀 Quick Test Scenarios</h5>
        <p className="text-blue-700 text-sm mb-3">
          Load pre-configured test scenarios for rapid workflow validation:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {testScenarios.map((scenario, index) => (
            <button
              key={index}
              onClick={() => loadTestScenario(scenario)}
              className="p-2 text-left bg-white border border-blue-300 rounded hover:bg-blue-50 transition-colors"
            >
              <div className="text-sm font-medium text-blue-900">{scenario.name}</div>
              <div className="text-xs text-blue-600">Risk: {scenario.risk_level}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Status Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 text-sm whitespace-pre-line">{message}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* SEC-106c: Why Pending / Authorization Decision Explanation */}
      {lastResult && (
        <div className={`border rounded-lg p-4 ${
          lastResult.status === "approved" ? "bg-green-50 border-green-200" :
          lastResult.status === "denied" ? "bg-red-50 border-red-200" :
          "bg-amber-50 border-amber-200"
        }`}>
          <h5 className={`font-medium mb-3 ${
            lastResult.status === "approved" ? "text-green-800" :
            lastResult.status === "denied" ? "text-red-800" :
            "text-amber-800"
          }`}>
            {lastResult.status === "approved" ? "✅ Auto-Approved" :
             lastResult.status === "denied" ? "❌ Denied" :
             "⏳ Pending Approval - Why?"}
          </h5>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {/* Risk Assessment */}
            <div>
              <p className="font-medium text-gray-700 mb-1">Risk Assessment</p>
              <ul className="space-y-1 text-gray-600">
                <li>• Risk Score: <span className="font-mono">{lastResult.risk_score || 'N/A'}</span></li>
                <li>• Risk Level: <span className="font-mono">{lastResult.risk_level || 'N/A'}</span></li>
                {lastResult.policy_decision && (
                  <li>• Policy Decision: <span className="font-mono">{lastResult.policy_decision}</span></li>
                )}
              </ul>
            </div>

            {/* Threshold Info */}
            {lastResult.thresholds && (
              <div>
                <p className="font-medium text-gray-700 mb-1">Agent Thresholds</p>
                <ul className="space-y-1 text-gray-600">
                  <li>• Auto-approve below: <span className="font-mono">{lastResult.thresholds.auto_approve_below}</span></li>
                  <li>• Escalate above: <span className="font-mono">{lastResult.thresholds.max_risk_threshold}</span></li>
                  <li>• Agent Type: <span className="font-mono">{lastResult.thresholds.agent_type || 'unregistered'}</span></li>
                  <li>• Registered: <span className="font-mono">{lastResult.thresholds.is_registered ? 'Yes' : 'No'}</span></li>
                </ul>
              </div>
            )}
          </div>

          {/* Explanation */}
          {lastResult.status === "pending_approval" && (
            <div className="mt-3 pt-3 border-t border-amber-200">
              <p className="text-amber-700 text-sm">
                <strong>Why pending?</strong>{' '}
                {lastResult.risk_score >= (lastResult.thresholds?.max_risk_threshold || 70)
                  ? `Risk score (${lastResult.risk_score}) exceeds max threshold (${lastResult.thresholds?.max_risk_threshold || 70}). Requires human approval.`
                  : lastResult.risk_score >= (lastResult.thresholds?.auto_approve_below || 30)
                    ? `Risk score (${lastResult.risk_score}) is in medium range (${lastResult.thresholds?.auto_approve_below || 30}-${lastResult.thresholds?.max_risk_threshold || 70}). Policy requires approval for this risk level.`
                    : 'Policy or smart rules require approval for this action type.'
                }
              </p>
            </div>
          )}

          {lastResult.status === "approved" && (
            <div className="mt-3 pt-3 border-t border-green-200">
              <p className="text-green-700 text-sm">
                <strong>Why approved?</strong>{' '}
                Risk score ({lastResult.risk_score}) is below auto-approve threshold ({lastResult.thresholds?.auto_approve_below || 30}).
              </p>
            </div>
          )}

          {/* Compliance Info */}
          {(lastResult.nist_control || lastResult.mitre_tactic) && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="font-medium text-gray-700 mb-1 text-xs">Compliance Mapping</p>
              <div className="flex gap-4 text-xs text-gray-600">
                {lastResult.nist_control && (
                  <span>NIST: <span className="font-mono">{lastResult.nist_control}</span></span>
                )}
                {lastResult.mitre_tactic && (
                  <span>MITRE: <span className="font-mono">{lastResult.mitre_tactic}</span></span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Submission Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InputField 
            label="Agent ID" 
            value={agentId} 
            onChange={setAgentId} 
            required 
            placeholder="e.g., security-scanner-01"
          />
          <InputField 
            label="Tool Name" 
            value={toolName} 
            onChange={setToolName} 
            placeholder="e.g., nessus-scanner"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Action Type *</label>
            <select
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
              className="w-full mt-1 border border-gray-300 rounded px-3 py-2 text-sm"
              required
            >
              <option value="">Select Action Type</option>
              {/* SEC-108: Grouped action types (70+ enterprise types) */}
              {Object.entries(getGroupedActionTypes()).map(([category, types]) => (
                <optgroup key={category} label={`── ${category} ──`}>
                  {types.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Risk Level *</label>
            <select
              value={riskLevel}
              onChange={(e) => setRiskLevel(e.target.value)}
              className="w-full mt-1 border border-gray-300 rounded px-3 py-2 text-sm"
              required
            >
              <option value="low">🟢 Low Risk (Auto-approve eligible)</option>
              <option value="medium">🟡 Medium Risk (1 approval required)</option>
              <option value="high">🟠 High Risk (2 approvals required)</option>
              <option value="critical">🔴 Critical Risk (3 approvals required)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Technical Description *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full mt-1 border border-gray-300 rounded px-3 py-2 text-sm"
            rows={3}
            placeholder="Detailed technical description of what the agent will do..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Business Justification *</label>
          <textarea
            value={businessJustification}
            onChange={(e) => setBusinessJustification(e.target.value)}
            className="w-full mt-1 border border-gray-300 rounded px-3 py-2 text-sm"
            rows={2}
            placeholder="Business reason, compliance requirement, or operational necessity..."
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Required for enterprise audit trail and compliance documentation
          </p>
        </div>

        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={clearForm}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
          >
            Clear Form
          </button>
          
          <button
            type="submit"
            disabled={loading || !agentId || !actionType || !description || !businessJustification}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "⏳ Submitting..." : "🚀 Submit Agent Action"}
          </button>
        </div>
      </form>

      {/* Enterprise Audit Notice */}
      <div className="bg-gray-50 border border-gray-200 rounded p-3">
        <p className="text-xs text-gray-600">
          🔍 <strong>Audit Trail:</strong> This submission will be logged with your user identity, timestamp, 
          IP address, and all form data for compliance and security review purposes.
        </p>
      </div>
    </div>
  );
};

const InputField = ({ label, value, onChange, required = false, placeholder = "" }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700">
      {label} {required && "*"}
    </label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full mt-1 border border-gray-300 rounded px-3 py-2 text-sm"
      required={required}
      placeholder={placeholder}
    />
  </div>
);

export default AgentActionSubmitPanel;