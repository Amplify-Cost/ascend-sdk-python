import React, { useState } from "react";

const AgentActionSubmitPanel = ({ getAuthHeaders }) => {
  const [agentId, setAgentId] = useState("");
  const [actionType, setActionType] = useState("");
  const [toolName, setToolName] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/agent-actions`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_id: agentId,
          action_type: actionType,
          tool_name: toolName,
          description,
          timestamp: Math.floor(Date.now() / 1000),
        }),
      });

      if (!res.ok) throw new Error("Failed to submit agent action");

      setMessage("✅ Agent action submitted successfully.");
      setAgentId("");
      setActionType("");
      setToolName("");
      setDescription("");
    } catch (err) {
      console.error("Submit error:", err);
      setError("❌ Submission failed.");
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-xl mx-auto">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Submit Agent Action</h2>

      {message && <p className="text-green-600 text-sm mb-2">{message}</p>}
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField label="Agent ID" value={agentId} onChange={setAgentId} required />
        <InputField label="Action Type" value={actionType} onChange={setActionType} required />
        <InputField label="Tool Name" value={toolName} onChange={setToolName} />
        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full mt-1 border rounded px-3 py-2 text-sm"
            rows={3}
          ></textarea>
        </div>
        <button
          type="submit"
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700"
        >
          Submit Action
        </button>
      </form>
    </div>
  );
};

const InputField = ({ label, value, onChange, required = false }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700">{label}</label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full mt-1 border rounded px-3 py-2 text-sm"
      required={required}
    />
  </div>
);

export default AgentActionSubmitPanel;
