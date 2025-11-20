import React, { useState, useEffect } from "react";
import { fetchWithAuth } from "../utils/fetchWithAuth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const RuleEditor = ({ getAuthHeaders }) => {
  const [rules, setRules] = useState([]);
  const [newRule, setNewRule] = useState({ condition: "", action: "", risk_level: "medium", recommendation: "" });
  const [message, setMessage] = useState({ type: "", text: "" });
  const [loading, setLoading] = useState(false);
  const [generatedRule, setGeneratedRule] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/rules`);
      if (!response.ok) throw new Error("Failed to fetch rules");
      const data = await response.json();
      setRules(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch rules:", err);
      setMessage({ type: "error", text: "Failed to load rules" });
    }
  };

  const addRule = () => {
    if (!newRule.condition || !newRule.action) {
      setMessage({ type: "error", text: "Condition and action are required" });
      return;
    }
    
    const ruleWithDefaults = {
      ...newRule,
      id: Date.now(), // Temporary ID
      created_at: new Date().toISOString()
    };
    
    setRules([...rules, ruleWithDefaults]);
    setNewRule({ condition: "", action: "", risk_level: "medium", recommendation: "" });
    setMessage({ type: "success", text: "Rule added to list" });
  };

  const removeRule = (index) => {
    setRules(rules.filter((_, i) => i !== index));
    setMessage({ type: "success", text: "Rule removed" });
  };

  const saveRules = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/rules`, {
        method: "POST",
        body: JSON.stringify(rules),
      });
      
      if (!response.ok) throw new Error("Failed to save rules");
      
      setMessage({ type: "success", text: "✅ Rules saved successfully" });
    } catch (err) {
      console.error("Failed to save rules:", err);
      setMessage({ type: "error", text: "❌ Failed to save rules" });
    } finally {
      setLoading(false);
    }
  };

  const generateSmartRule = async () => {
    setGenerating(true);
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/smart-rules/generate`, {
        method: "POST",
        body: JSON.stringify({
          agent_id: "demo-agent",
          action_type: "suspicious_activity",
          description: "Generate a smart rule based on common security patterns"
        }),
      });

      if (!response.ok) throw new Error("Failed to generate smart rule");
      
      const data = await response.json();
      setGeneratedRule(data);
      setMessage({ type: "success", text: "✅ Smart rule generated" });
    } catch (err) {
      console.error("Smart rule generation failed:", err);
      setMessage({ type: "error", text: "❌ Failed to generate smart rule" });
    } finally {
      setGenerating(false);
    }
  };

  const approveGeneratedRule = () => {
    if (generatedRule) {
      setRules([...rules, { ...generatedRule, id: Date.now() }]);
      setGeneratedRule(null);
      setMessage({ type: "success", text: "✅ Smart rule added to list" });
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Rule Editor</h2>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-4 p-3 rounded ${
          message.type === "success" 
            ? "bg-green-100 border border-green-400 text-green-700" 
            : "bg-red-100 border border-red-400 text-red-700"
        }`}>
          {message.text}
        </div>
      )}

      {/* Smart Rule Generation */}
      <div className="mb-6 p-4 bg-gray-50 rounded">
        <h3 className="font-semibold mb-2">AI-Powered Rule Generation</h3>
        <button
          onClick={generateSmartRule}
          disabled={generating}
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {generating ? "🤖 Generating..." : "🚀 Generate Smart Rule"}
        </button>

        {generatedRule && (
          <div className="mt-4 p-3 bg-white border rounded">
            <h4 className="font-medium mb-2">Generated Rule:</h4>
            <div className="text-sm space-y-1">
              <div><strong>Condition:</strong> {generatedRule.condition}</div>
              <div><strong>Action:</strong> {generatedRule.action}</div>
              <div><strong>Risk Level:</strong> {generatedRule.risk_level}</div>
              <div><strong>Recommendation:</strong> {generatedRule.recommendation}</div>
            </div>
            <div className="mt-3 space-x-2">
              <button
                onClick={approveGeneratedRule}
                className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
              >
                ✅ Add to Rules
              </button>
              <button
                onClick={() => setGeneratedRule(null)}
                className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
              >
                ❌ Discard
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Current Rules */}
      <div className="mb-6">
        <h3 className="font-semibold mb-3">Current Rules ({rules.length})</h3>
        {rules.length === 0 ? (
          <p className="text-gray-500 italic">No rules defined yet.</p>
        ) : (
          <div className="space-y-2">
            {rules.map((rule, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-100 rounded">
                <div className="flex-1">
                  <div className="text-sm"><strong>Condition:</strong> {rule.condition}</div>
                  <div className="text-sm"><strong>Action:</strong> {rule.action}</div>
                  <div className="text-sm"><strong>Risk:</strong> {rule.risk_level}</div>
                </div>
                <button
                  onClick={() => removeRule(index)}
                  className="text-red-600 hover:text-red-800 px-2 py-1"
                >
                  ❌
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add New Rule */}
      <div className="border-t pt-6">
        <h3 className="font-semibold mb-3">Add New Rule</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Condition</label>
            <input
              type="text"
              value={newRule.condition}
              onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
              className="w-full p-2 border rounded"
              placeholder="e.g., action_type == 'data_exfiltration'"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Action</label>
            <select
              value={newRule.action}
              onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
              className="w-full p-2 border rounded"
            >
              <option value="">Select action...</option>
              <option value="alert">Alert</option>
              <option value="block">Block</option>
              <option value="quarantine">Quarantine</option>
              <option value="approve">Auto-approve</option>
              <option value="reject">Auto-reject</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Risk Level</label>
            <select
              value={newRule.risk_level}
              onChange={(e) => setNewRule({ ...newRule, risk_level: e.target.value })}
              className="w-full p-2 border rounded"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Recommendation</label>
            <input
              type="text"
              value={newRule.recommendation}
              onChange={(e) => setNewRule({ ...newRule, recommendation: e.target.value })}
              className="w-full p-2 border rounded"
              placeholder="What should admins do?"
            />
          </div>
        </div>
        
        <div className="mt-4 flex gap-3">
          <button
            onClick={addRule}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            ➕ Add Rule
          </button>
          
          <button
            onClick={saveRules}
            disabled={loading || rules.length === 0}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "💾 Saving..." : "💾 Save All Rules"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RuleEditor;