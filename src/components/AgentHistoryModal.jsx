import React, { useEffect, useState } from "react";

const AgentHistoryModal = ({ agentId, onClose, getAuthHeaders }) => {
  const [actions, setActions] = useState([]);
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (agentId) {
      fetch(`${API_BASE_URL}/agent-actions?agent_id=${agentId}`, {
        credentials: "include",
        headers: getAuthHeaders(),
      })
        .then((res) => res.json())
        .then(setActions)
        .catch(console.error);
    }
  }, [agentId]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex justify-center items-center">
      <div className="bg-white p-6 rounded shadow-xl w-11/12 max-w-3xl max-h-[90vh] overflow-y-auto relative">
        <h2 className="text-xl font-bold mb-4">History for Agent: {agentId}</h2>
        <button onClick={onClose} className="absolute top-2 right-4 text-gray-600 text-xl">×</button>
        {actions.length === 0 ? (
          <p>No actions found.</p>
        ) : (
          <table className="w-full text-sm table-auto border">
            <thead>
              <tr>
                <th className="text-left p-2 border">Timestamp</th>
                <th className="text-left p-2 border">Action</th>
                <th className="text-left p-2 border">Tool</th>
                <th className="text-left p-2 border">Risk</th>
                <th className="text-left p-2 border">LLM Summary</th>
              </tr>
            </thead>
            <tbody>
              {actions.map((a) => (
                <tr key={a.id}>
                  <td className="p-2 border">{new Date(a.timestamp).toLocaleString()}</td>
                  <td className="p-2 border">{a.description}</td>
                  <td className="p-2 border">{a.tool_name}</td>
                  <td className="p-2 border font-semibold">{a.risk_level}</td>
                  <td className="p-2 border text-xs text-gray-700">
                    {a.summary || <span className="italic text-gray-400">No summary</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AgentHistoryModal;
