import React, { useState } from "react";

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

  const API_BASE_URL = import.meta.env.VITE_API_URL || '';

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
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);

    // Enterprise validation
    if (!businessJustification.trim()) {
      setError("❌ Business justification is required for enterprise compliance");
      setLoading(false);
      return;
    }

    try {
      console.log('🚀 Submitting enterprise agent action...');
      
      const payload = {
        agent_id: agentId,
        action_type: actionType,
        tool_name: toolName,
        description: description,
        risk_level: riskLevel,
        business_justification: businessJustification,
        submitted_via: "enterprise_admin_panel",
        timestamp: Math.floor(Date.now() / 1000),
      };

      console.log('📤 Payload:', payload);

      // Try multiple endpoints to find the working one
      const endpoints = [
        `${API_BASE_URL}/agent-actions`,
        `${API_BASE_URL}/agent-action`,
        `${API_BASE_URL}/agent-control/request-authorization`
      ];

      let success = false;
      let lastError = null;

      for (const endpoint of endpoints) {
        try {
          console.log(`🔍 Trying endpoint: ${endpoint}`);
          
          const res = await fetch(endpoint, {
            method: "POST",
        credentials: "include",
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
            
            setMessage(`✅ Enterprise agent action submitted successfully! 
                       Action ID: ${result.action_id || result.authorization_id || 'Generated'}
                       Status: Pending approval workflow`);
            
            // Clear form after successful submission
            clearForm();
            success = true;
            break;
          } else {
            const errorText = await res.text();
            console.log(`❌ Error response: ${res.status} - ${errorText}`);
            lastError = `${res.status}: ${errorText}`;
          }
        } catch (fetchError) {
          console.log(`🔥 Fetch error for ${endpoint}:`, fetchError);
          lastError = fetchError.message;
        }
      }

      if (!success) {
        throw new Error(`All endpoints failed. Last error: ${lastError}`);
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
              <option value="vulnerability_scan">Vulnerability Scan</option>
              <option value="compliance_check">Compliance Check</option>
              <option value="threat_analysis">Threat Analysis</option>
              <option value="data_backup">Data Backup</option>
              <option value="system_maintenance">System Maintenance</option>
              <option value="forensic_analysis">Forensic Analysis</option>
              <option value="network_monitoring">Network Monitoring</option>
              <option value="access_review">Access Review</option>
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
