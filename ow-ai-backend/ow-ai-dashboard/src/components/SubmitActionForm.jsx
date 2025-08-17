import React, { useState, useEffect } from "react";
import { format } from "date-fns";

const SubmitActionForm = ({ user, getAuthHeaders }) => {
  const [tool, setTool] = useState("");
  const [description, setDescription] = useState("");
  const [actionType, setActionType] = useState("data_exfiltration");
  const [riskLevel, setRiskLevel] = useState("low");
  const [agentId, setAgentId] = useState("agent-001");
  const [timestamp, setTimestamp] = useState(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const API_BASE_URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    setTimestamp(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });

    if (!tool || !description || !timestamp) {
      setMessage({ type: "error", text: "All fields are required." });
      return;
    }

    const payload = {
      agent_id: agentId,
      tool_name: tool,
      action_type: actionType,
      risk_level: riskLevel,
      description,
      timestamp: new Date(timestamp).toISOString(),
    };

    console.log("Payload being sent:", payload);

    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/agent-action`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(), // Make sure this returns { Authorization: Bearer <token> }
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Submission failed");
      }

      setMessage({ type: "success", text: "Action submitted successfully!" });
      setTool("");
      setDescription("");
      setTimestamp(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
    } catch (err) {
      console.error("Submission error:", err);
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white shadow-xl rounded-2xl mt-6">
      <h2 className="text-2xl font-bold mb-4">Submit Agent Action</h2>
      {message.text && (
        <div
          className={`mb-4 p-3 rounded ${
            message.type === "success"
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-semibold mb-1">Agent ID</label>
          <input
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            className="w-full px-4 py-2 border rounded"
            placeholder="e.g. agent-001"
          />
        </div>

        <div>
          <label className="block font-semibold mb-1">Tool Name</label>
          <input
            type="text"
            value={tool}
            onChange={(e) => setTool(e.target.value)}
            className="w-full px-4 py-2 border rounded"
            placeholder="e.g. LangChain, ChatGPT Plugin"
          />
        </div>

        <div>
          <label className="block font-semibold mb-1">Action Type</label>
          <input
            type="text"
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            className="w-full px-4 py-2 border rounded"
            placeholder="e.g. data_exfiltration"
          />
        </div>

        <div>
          <label className="block font-semibold mb-1">Risk Level</label>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="w-full px-4 py-2 border rounded"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-2 border rounded"
            rows={4}
            placeholder="Describe what the agent did..."
          ></textarea>
        </div>

        <div>
          <label className="block font-semibold mb-1">Timestamp</label>
          <input
            type="datetime-local"
            value={timestamp}
            onChange={(e) => setTimestamp(e.target.value)}
            className="w-full px-4 py-2 border rounded"
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Submitting..." : "Submit Action"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SubmitActionForm;
