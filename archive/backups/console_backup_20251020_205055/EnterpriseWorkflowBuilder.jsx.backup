import React, { useState } from 'react';

const EnterpriseWorkflowBuilder = ({ 
  newWorkflow, 
  setNewWorkflow, 
  createWorkflow, 
  onCancel,
  workflows = {}
}) => {
  const [showPolicyEditor, setShowPolicyEditor] = useState(false);

  return (
    <div className="space-y-6">
      {/* Policy Rules Editor */}
      <div className="flex justify-between items-center">
        <h4 className="text-lg font-semibold text-gray-900">Enterprise Workflow Builder</h4>
        <button
          onClick={() => setShowPolicyEditor(!showPolicyEditor)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm"
        >
          {showPolicyEditor ? "Hide Policy Editor" : "Policy Rules Editor"}
        </button>
      </div>

      {/* Policy Editor Section */}
      {showPolicyEditor && (
        <div className="p-4 bg-purple-50 rounded-lg border">
          <h5 className="font-semibold text-purple-900 mb-3">Edit Existing Policy Rules</h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(workflows).map(([workflowId, workflow]) => (
              <div key={workflowId} className="p-3 bg-white rounded border">
                <h6 className="font-medium text-gray-900 mb-2">{workflow.name}</h6>
                <div className="space-y-1 text-sm">
                  <div>Auto-Deny: {workflow.policy_rules?.auto_deny_conditions?.length || 0} conditions</div>
                  <div>Auto-Approve: {workflow.policy_rules?.auto_approve_conditions?.length || 0} conditions</div>
                  <div>Compliance: {workflow.policy_rules?.compliance_checks?.join(", ") || "None"}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Enhanced Workflow Creation Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input
          type="text"
          placeholder="Workflow Name (e.g., SOX Financial Approval)"
          value={newWorkflow.name || ""}
          onChange={(e) => setNewWorkflow({...newWorkflow, name: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={newWorkflow.riskLevel || ""}
          onChange={(e) => setNewWorkflow({...newWorkflow, riskLevel: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select Risk Level</option>
          <option value="risk_90_100">Critical Risk (90-100)</option>
          <option value="risk_70_89">High Risk (70-89)</option>
          <option value="risk_50_69">Medium Risk (50-69)</option>
          <option value="risk_0_49">Low Risk (0-49)</option>
        </select>
      </div>

      <textarea
        placeholder="Workflow Description: Purpose, triggers, business requirements..."
        value={newWorkflow.description || ""}
        onChange={(e) => setNewWorkflow({...newWorkflow, description: e.target.value})}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows="3"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Approval Levels</label>
          <select
            value={newWorkflow.approvalLevels || 1}
            onChange={(e) => setNewWorkflow({...newWorkflow, approvalLevels: parseInt(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="1">Single Approval</option>
            <option value="2">Dual Approval</option>
            <option value="3">Triple Approval</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (Hours)</label>
          <input
            type="number"
            placeholder="24"
            value={newWorkflow.timeoutHours || ""}
            onChange={(e) => setNewWorkflow({...newWorkflow, timeoutHours: parseInt(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Compliance Requirements</label>
        <div className="flex flex-wrap gap-3">
          {["SOX", "GDPR", "HIPAA", "PCI-DSS", "ISO-27001"].map(compliance => (
            <label key={compliance} className="flex items-center">
              <input
                type="checkbox"
                checked={newWorkflow.complianceChecks?.includes(compliance) || false}
                onChange={(e) => {
                  const current = newWorkflow.complianceChecks || [];
                  const updated = e.target.checked
                    ? [...current, compliance]
                    : current.filter(c => c !== compliance);
                  setNewWorkflow({...newWorkflow, complianceChecks: updated});
                }}
                className="mr-2"
              />
              <span className="text-sm">{compliance}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => {
            const enterpriseWorkflow = {
              ...newWorkflow,
              policy_rules: {
                auto_deny_conditions: [],
                auto_approve_conditions: [],
                compliance_checks: newWorkflow.complianceChecks || [],
                business_justification_required: newWorkflow.approvalLevels > 1
              }
            };
            console.log("Creating enterprise workflow:", enterpriseWorkflow);
            createWorkflow(enterpriseWorkflow);
          }}
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md font-medium"
        >
          Create Enterprise Workflow
        </button>
        <button
          onClick={() => {
            setNewWorkflow({ 
              name: "", 
              description: "", 
              riskLevel: "", 
              approvalLevels: 1, 
              timeoutHours: 24, 
              complianceChecks: [] 
            });
            onCancel();
          }}
          className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default EnterpriseWorkflowBuilder;
