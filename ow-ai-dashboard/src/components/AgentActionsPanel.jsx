import React, { useEffect, useState } from "react";

const AgentActionsPanel = ({ getAuthHeaders, user }) => {
  const [agentActions, setAgentActions] = useState([]);
  const [error, setError] = useState(null);
  const [selectedAction, setSelectedAction] = useState(null);
  const [auditLogs, setAuditLogs] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [generatedRule, setGeneratedRule] = useState(null);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editedRule, setEditedRule] = useState({
    condition: "",
    action: "",
    justification: "",
  });

  const actionsPerPage = 5;
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const fetchAgentActions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agent-actions`, {
        headers: await getAuthHeaders(),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setAgentActions(data);
    } catch (err) {
      setError("Failed to load agent actions.");
    }
  };

  const updateActionStatus = async (id, statusType) => {
    try {
      const res = await fetch(`${API_BASE_URL}/agent-action/${id}/${statusType}`, {
        method: "POST",
        headers: await getAuthHeaders(),
      });
      if (res.ok) {
        await fetchAgentActions();
      } else {
        alert(`❌ Failed to ${statusType.replace("-", " ")} action.`);
      }
    } catch (err) {
      console.error(`Failed to ${statusType} action:`, err);
    }
  };

  const generateSmartRule = async (action) => {
    try {
      const res = await fetch(`${API_BASE_URL}/rules/generate-smart-rule`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(await getAuthHeaders()),
        },
        body: JSON.stringify({
          agent_id: action.agent_id,
          action_type: action.action_type,
          description: action.description || "",
        }),
      });
      if (res.ok) {
        const rule = await res.json();
        setGeneratedRule(rule);
        setEditedRule(rule);
        setShowRuleModal(true);
      }
    } catch (err) {
      console.error("Rule generation failed:", err);
    }
  };

  const approveRule = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/rules`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(await getAuthHeaders()),
        },
        body: JSON.stringify([editedRule]),
      });
      if (res.ok) {
        alert("✅ Rule approved and saved.");
        setShowRuleModal(false);
        setGeneratedRule(null);
      } else {
        alert("❌ Failed to approve rule.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchAgentActions();
  }, []);

  const start = (currentPage - 1) * actionsPerPage;
  const currentActions = agentActions.slice(start, start + actionsPerPage);
  const totalPages = Math.ceil(agentActions.length / actionsPerPage);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Agent Actions</h2>

      {error && <div className="text-red-500">{error}</div>}

      {currentActions.length === 0 ? (
        <p className="text-gray-600">No agent actions found.</p>
      ) : (
        <>
          <table className="w-full bg-white shadow rounded-lg">
            <thead className="bg-gray-100 text-sm text-left text-gray-700">
              <tr>
                <th className="p-3">Agent ID</th>
                <th className="p-3">Action Type</th>
                <th className="p-3">Risk Level</th>
                <th className="p-3">Summary</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentActions.map((action) => (
                <tr key={action.id} className="border-t hover:bg-gray-50 text-sm">
                  <td className="p-3">{action.agent_id}</td>
                  <td className="p-3">{action.action_type}</td>
                  <td className="p-3 capitalize">{action.risk_level}</td>
                  <td className="p-3 text-gray-700">
                    {action.summary || <span className="italic text-gray-400">No summary</span>}
                  </td>
                  <td className="p-3 capitalize">{action.status || "pending"}</td>
                  <td className="p-3 flex gap-2 flex-wrap justify-center">
                    <button
                      onClick={() => setSelectedAction(action)}
                      className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      View
                    </button>
                    {user?.role === "admin" && action.status === "pending" && (
                      <>
                        <button
                          onClick={() => updateActionStatus(action.id, "approve")}
                          className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => updateActionStatus(action.id, "reject")}
                          className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => updateActionStatus(action.id, "false-positive")}
                          className="px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600"
                        >
                          False Positive
                        </button>
                      </>
                    )}
                    {user?.role === "admin" && (
                      <button
                        onClick={() => generateSmartRule(action)}
                        className="px-2 py-1 text-xs bg-indigo-500 text-white rounded hover:bg-indigo-600"
                      >
                        Smart Rule
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex justify-between mt-4 items-center">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              className="px-3 py-1 bg-gray-200 text-gray-800 rounded disabled:opacity-50"
            >
              Prev
            </button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="px-3 py-1 bg-gray-200 text-gray-800 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>

          {selectedAction && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-2xl relative">
                <button
                  onClick={() => setSelectedAction(null)}
                  className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                >
                  ✖
                </button>
                <h3 className="text-xl font-semibold mb-4">Action Details</h3>
                <pre className="text-sm bg-gray-100 p-3 rounded overflow-x-auto">
                  {JSON.stringify(selectedAction, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {showRuleModal && (
            <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded shadow-lg w-full max-w-lg">
                <h3 className="text-lg font-semibold mb-4">Generated Smart Rule</h3>
                <label className="block text-sm mb-1">Condition</label>
                <textarea
                  value={editedRule.condition}
                  onChange={(e) => setEditedRule({ ...editedRule, condition: e.target.value })}
                  className="w-full mb-2 p-2 border rounded"
                />
                <label className="block text-sm mb-1">Action</label>
                <textarea
                  value={editedRule.action}
                  onChange={(e) => setEditedRule({ ...editedRule, action: e.target.value })}
                  className="w-full mb-2 p-2 border rounded"
                />
                <label className="block text-sm mb-1">Justification</label>
                <textarea
                  value={editedRule.justification}
                  onChange={(e) => setEditedRule({ ...editedRule, justification: e.target.value })}
                  className="w-full mb-4 p-2 border rounded"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowRuleModal(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={approveRule}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Approve Rule
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AgentActionsPanel;
