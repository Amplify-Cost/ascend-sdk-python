const API_BASE_URL = import.meta.env.VITE_API_URL;

import React, { useState, useEffect } from "react";

const RuleEditor = ({ getAuthHeaders }) => {
  const [rules, setRules] = useState([]);
  const [newRule, setNewRule] = useState({ condition: "", action: "" });
  const [message, setMessage] = useState("");
  const [versionHistory, setVersionHistory] = useState([]);
  const [previewResult, setPreviewResult] = useState("");
  const [generatedRule, setGeneratedRule] = useState(null);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await fetch("${API_BASE_URL}/rules", {
          headers: getAuthHeaders(),
        });
        const data = await res.json();
        setRules(data);
      } catch {
        setMessage("❌ Failed to load rules");
      }
    };

    const fetchHistory = async () => {
      try {
        const res = await fetch("${API_BASE_URL}/rules/history", {
          headers: getAuthHeaders(),
        });
        const data = await res.json();
        setVersionHistory(data);
      } catch {
        setMessage("❌ Failed to load rule history");
      }
    };

    fetchRules();
    fetchHistory();
  }, [getAuthHeaders]);

  const handleChange = (index, field, value) => {
    const updated = [...rules];
    updated[index][field] = value;
    setRules(updated);
  };

  const addRule = () => {
    if (!newRule.condition || !newRule.action) return;
    setRules([...rules, { ...newRule }]);
    setNewRule({ condition: "", action: "" });
  };

  const removeRule = (index) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const saveRules = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/rules", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(rules),
      });
      const data = await res.json();
      setMessage(data.message || "✅ Rules updated");

      const historyRes = await fetch("${API_BASE_URL}/rules/history", {
        headers: getAuthHeaders(),
      });
      const historyData = await historyRes.json();
      setVersionHistory(historyData);
    } catch {
      setMessage("❌ Failed to update rules");
    }
  };

  const rollbackRules = async (index) => {
    const filename = versionHistory[index];
    try {
      const res = await fetch("${API_BASE_URL}/rules/rollback", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ filename }),
      });
      const data = await res.json();
      setMessage(data.message || "✅ Rolled back");

      const updatedRules = await fetch("${API_BASE_URL}/rules", {
        headers: getAuthHeaders(),
      });
      const rulesData = await updatedRules.json();
      setRules(rulesData);
    } catch {
      setMessage("❌ Rollback failed");
    }
  };

  const previewRules = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/rules/preview", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(rules),
      });
      const data = await res.json();
      setPreviewResult(data.message || "✅ Preview success");
    } catch {
      setPreviewResult("❌ Preview failed");
    }
  };

  const generateSmartRule = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/rules/generate-smart-rule", {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_id: "agent-001",
          action_type: "data_exfiltration",
          description: "Agent accessed sensitive files and attempted to upload to unknown domain."
        }),
      });

      if (!res.ok) {
        const error = await res.text();
        throw new Error(`Failed to generate rule: ${error}`);
      }

      const data = await res.json();
      setGeneratedRule(data);
      setMessage("✅ Smart rule generated");
    } catch (err) {
      console.error("Error:", err);
      setMessage("❌ Failed to generate smart rule");
    }
  };

  const saveGeneratedRule = () => {
    if (!generatedRule) return;
    setRules([...rules, generatedRule]);
    setGeneratedRule(null);
    setMessage("✅ Smart rule added to list");
  };

  const approveSmartRule = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/rules/approve", {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(generatedRule),
      });
      const data = await res.json();
      setRules((prev) => [...prev, data.rule]);
      setGeneratedRule(null);
      setMessage("✅ Smart rule approved and saved");
    } catch {
      setMessage("❌ Failed to approve rule");
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Custom Rule Editor</h2>

      <button
        onClick={generateSmartRule}
        className="bg-indigo-600 text-white px-4 py-2 rounded mb-4"
      >
        🚀 Generate Smart Rule
      </button>

      {generatedRule && (
        <div className="bg-gray-100 p-3 rounded mb-4">
          <pre>{JSON.stringify(generatedRule, null, 2)}</pre>
          <div className="space-x-2 mt-2">
            <button
              onClick={saveGeneratedRule}
              className="bg-green-500 text-white px-3 py-1 rounded"
            >
              ✅ Save to List
            </button>
            <button
              onClick={approveSmartRule}
              className="bg-blue-500 text-white px-3 py-1 rounded"
            >
              ✅ Approve This Rule
            </button>
          </div>
        </div>
      )}

      {rules.map((rule, index) => (
        <div key={index} className="mb-3 flex gap-2">
          <input
            className="border p-1 w-1/2"
            value={rule.condition || ""}
            onChange={(e) => handleChange(index, "condition", e.target.value)}
            placeholder="Condition (e.g. log.risk_level == 'high')"
          />
          <select
            className="border p-1"
            value={rule.action || ""}
            onChange={(e) => handleChange(index, "action", e.target.value)}
          >
            <option value="">--action--</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="pending">pending</option>
          </select>
          <button
            onClick={() => removeRule(index)}
            className="text-red-600 text-sm"
          >
            ❌
          </button>
        </div>
      ))}

      <div className="flex gap-2 my-4">
        <input
          className="border p-1 w-1/2"
          value={newRule.condition}
          onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
          placeholder="New condition"
        />
        <select
          className="border p-1"
          value={newRule.action}
          onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
        >
          <option value="">--action--</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="pending">pending</option>
        </select>
        <button
          onClick={addRule}
          className="bg-green-500 text-white px-3 py-1"
        >
          ➕ Add Rule
        </button>
      </div>

      <div className="flex gap-4 mt-2">
        <button
          onClick={saveRules}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          💾 Save Rules
        </button>
        <button
          onClick={previewRules}
          className="bg-yellow-500 text-white px-4 py-2 rounded"
        >
          🔍 Preview
        </button>
      </div>

      {previewResult && (
        <p className="text-sm mt-2 text-indigo-600">{previewResult}</p>
      )}
      {message && <p className="mt-2 text-sm text-blue-600">{message}</p>}

      <div className="mt-6">
        <h3 className="font-semibold text-md mb-2">Rule Version History</h3>
        {versionHistory.length === 0 ? (
          <p className="text-gray-500">No previous versions saved.</p>
        ) : (
          <ul className="text-sm space-y-1">
            {versionHistory.map((v, idx) => (
              <li key={idx} className="flex justify-between border-b py-1">
                <span>{v}</span>
                <button
                  onClick={() => rollbackRules(idx)}
                  className="text-xs text-red-600 underline"
                >
                  Rollback
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default RuleEditor;
