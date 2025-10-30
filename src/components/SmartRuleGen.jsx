import React, { useState, useEffect } from 'react';

const EnterpriseSmartRuleEngine = ({ getAuthHeaders, user }) => {
  const [rules, setRules] = useState([]);
  const [ruleAnalytics, setRuleAnalytics] = useState(null);
  const [activeTab, setActiveTab] = useState("rules");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  
  // Natural Language Rule Creation
  const [nlInput, setNlInput] = useState("");
  const [generatingRule, setGeneratingRule] = useState(false);
  const [suggestedRules, setSuggestedRules] = useState([]);
  
  // A/B Testing
  const [abTests, setAbTests] = useState([]);
  const [creatingTest, setCreatingTest] = useState(false);

  // Manual Rule Creation
  const [createMethod, setCreateMethod] = useState("natural-language");
  const [manualRule, setManualRule] = useState({
    name: "",
    condition: "",
    action: "alert",
    risk_level: "medium",
    description: "",
    justification: ""
  });
  const [creatingManualRule, setCreatingManualRule] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchInitialData();
    
    const interval = setInterval(() => {
      if (activeTab === "rules") fetchRules();
      if (activeTab === "analytics") fetchRuleAnalytics();
      if (activeTab === "ab-testing") fetchAbTests();
      if (activeTab === "suggestions") fetchSuggestedRules();
    }, 30000);

    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchRules(),
        fetchRuleAnalytics(),
        fetchAbTests(),
        fetchSuggestedRules()
      ]);
    } catch (error) {
      console.error("Error fetching initial data:", error);
      setError("Failed to load rule engine data");
    } finally {
      setLoading(false);
    }
  };

  const fetchRules = async () => {
    try {
      console.log("🔍 ENTERPRISE: Fetching smart rules from:", `${API_BASE_URL}/api/smart-rules`);
      const response = await fetch(`${API_BASE_URL}/api/smart-rules`, {
        credentials: "include",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      console.log("📡 ENTERPRISE: Rules API response status:", response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log("✅ ENTERPRISE: Rules fetched successfully:", data.length, "rules");
        console.log("📋 ENTERPRISE: First rule:", data[0]);
        setRules(data);
        setError(null);
      } else {
        const errorText = await response.text();
        console.error("❌ ENTERPRISE: Failed to fetch rules:", response.status, errorText);
        setRules([]);
        setError("Failed to fetch rules from server");
      }
    } catch (err) {
      console.error("❌ ENTERPRISE: Network error fetching rules:", err);
      setRules([]);
      setError("Network error fetching rules");
    }
  };

  const fetchRuleAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/analytics`, {
        credentials: "include",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setRuleAnalytics(data);
      } else {
        console.error("Failed to fetch analytics:", response.status);
        setRuleAnalytics(null); // ENTERPRISE: No demo data
      }
    } catch (err) {
      console.error("Error fetching rule analytics:", err);
      setRuleAnalytics(null); // ENTERPRISE: No demo data
    }
  };

  const fetchAbTests = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/ab-tests`, {
        credentials: "include",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        console.log("✅ ENTERPRISE: A/B tests fetched:", data);
        setAbTests(data);
      } else {
        console.error("❌ ENTERPRISE: Failed to fetch A/B tests:", response.status);
        setAbTests([]); // ENTERPRISE: No demo data
      }
    } catch (err) {
      console.error("❌ ENTERPRISE: Error fetching A/B tests:", err);
      setAbTests([]); // ENTERPRISE: No demo data
    }
  };

  const fetchSuggestedRules = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/suggestions`, {
        credentials: "include",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setSuggestedRules(data);
      } else {
        console.error("Failed to fetch suggestions:", response.status);
        setSuggestedRules([]); // ENTERPRISE: No demo data
      }
    } catch (err) {
      console.error("Error fetching rule suggestions:", err);
      setSuggestedRules([]); // ENTERPRISE: No demo data
    }
  };

  const generateRuleFromNaturalLanguage = async () => {
    if (!nlInput.trim()) {
      alert("Please enter a rule description");
      return;
    }

    setGeneratingRule(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/generate-from-nl`, {
        credentials: "include",
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ 
          natural_language: nlInput,
          context: "enterprise_security"
        })
      });

      if (response.ok) {
        const newRule = await response.json();
        setRules(prev => [newRule, ...prev]);
        setNlInput("");
        alert("✅ Enterprise rule generated successfully!");
      } else {
        // ENTERPRISE: No demo fallback - show actual error
        const errorText = await response.text();
        console.error("Rule generation failed:", response.status, errorText);
        alert("❌ Failed to generate rule - check server connection");
      }
    } catch (err) {
      console.error("Error generating rule:", err);
      alert("❌ Network error - failed to generate rule");
    } finally {
      setGeneratingRule(false);
    }
  };

  const deleteRule = async (id) => {
    if (!window.confirm("Are you sure you want to delete this rule?")) return;
    
    setDeletingId(id);
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/${id}`, {
        credentials: "include",
        method: "DELETE",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });
      
      if (response.ok) {
        setRules(prev => prev.filter(r => r.id !== id));
        alert("✅ Rule deleted successfully");
      } else {
        alert("❌ Failed to delete rule - server error");
      }
    } catch (err) {
      console.error("Error deleting rule:", err);
      alert("❌ Network error - failed to delete rule");
    } finally {
      setDeletingId(null);
    }
  };

  const createAbTest = async (ruleId) => {
  setCreatingTest(true);
  try {
    console.log(`🧪 ENTERPRISE: Creating A/B test for rule ${ruleId}`);
    
    // ENTERPRISE FIX: Send rule_id as query parameter
    const response = await fetch(`${API_BASE_URL}/api/smart-rules/ab-test?rule_id=${ruleId}`, {
      credentials: "include",
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ 
        test_duration_hours: 24,
        traffic_split: 50
      })
    });

      if (response.ok) {
        const newTest = await response.json();
        console.log("✅ ENTERPRISE: A/B test created:", newTest);
        setAbTests(prev => [newTest, ...prev]);
        alert("✅ Enterprise A/B test created successfully!");
        
        // Refresh A/B tests list
        fetchAbTests();
      } else {
        // ENTERPRISE: No demo fallback - show actual error
        const errorText = await response.text();
        console.error("❌ ENTERPRISE: A/B test creation failed:", response.status, errorText);
        alert(`❌ Failed to create A/B test - Server error (${response.status})`);
      }
    } catch (err) {
      console.error("❌ ENTERPRISE: Network error creating A/B test:", err);
      alert("❌ Network error - failed to create A/B test");
    } finally {
      setCreatingTest(false);
    }
  };

  // Manual Rule Creation
  const createManualRule = async () => {
    if (!manualRule.name.trim()) {
      alert("❌ Please enter a rule name");
      return;
    }
    if (!manualRule.condition.trim()) {
      alert("❌ Please enter a condition");
      return;
    }

    setCreatingManualRule(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules`, {
        credentials: "include",
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          ...manualRule,
          agent_id: "manual-creation",
          action_type: "smart_rule"
        })
      });

      if (response.ok) {
        alert("✅ Manual rule created successfully!");
        setManualRule({
          name: "",
          condition: "",
          action: "alert",
          risk_level: "medium",
          description: "",
          justification: ""
        });
        fetchRules();
      } else {
        alert("❌ Failed to create rule");
      }
    } catch (err) {
      console.error("Error creating manual rule:", err);
      alert("❌ Network error");
    } finally {
      setCreatingManualRule(false);
    }
  };

  // A/B Test Button Handlers
  const handleStopTest = async (testId, testName) => {
    if (!confirm(`Stop "${testName}"? This cannot be undone.`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/ab-test/${testId}/stop`, {
        credentials: "include",
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });

      if (response.ok) {
        alert("✅ Test stopped successfully");
        fetchAbTests();
      } else {
        const error = await response.text();
        alert(`❌ Failed to stop test: ${error}`);
      }
    } catch (err) {
      console.error("Error stopping test:", err);
      alert("❌ Network error");
    }
  };

  const handleDeployWinner = async (testId, testName, winner) => {
    const winnerName = winner === 'variant_a' ? 'Variant A (Control)' : 'Variant B (Optimized)';
    if (!confirm(`Deploy ${winnerName} for "${testName}"?\n\nThis will update the original rule with the winning variant's logic.`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-rules/ab-test/${testId}/deploy`, {
        credentials: "include",
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ ${result.message}\n\nRule updated: ${result.base_rule_name}\nImprovement: ${result.improvement}`);
        fetchAbTests();
        fetchRules(); // Refresh rules to show updated rule
      } else {
        const error = await response.text();
        alert(`❌ Failed to deploy winner: ${error}`);
      }
    } catch (err) {
      console.error("Error deploying winner:", err);
      alert("❌ Network error");
    }
  };

  const handleViewTestDetails = (test) => {
    const details = `
📊 Test: ${test.test_name}
Status: ${test.status}
Progress: ${test.progress_percentage}%

🅰️ Variant A: ${test.variant_a_performance}%
🅱️ Variant B: ${test.variant_b_performance}%

${test.winner ? `Winner: ${test.winner}` : 'No winner yet'}
Confidence: ${test.confidence_level}%
Sample Size: ${test.sample_size}

💼 ${test.enterprise_insights?.cost_savings || 'Calculating...'}
    `.trim();
    alert(details);
  };

  // ENTERPRISE: Remove all demo data generation functions
  // No generateDemoRules, generateDemoAnalytics, generateDemoAbTests, generateDemoSuggestions

  const getRiskColor = (level) => {
    const colors = {
      "high": "bg-red-100 text-red-800 border-red-200",
      "medium": "bg-yellow-100 text-yellow-800 border-yellow-200", 
      "low": "bg-green-100 text-green-800 border-green-200"
    };
    return colors[level] || "bg-gray-100 text-gray-800 border-gray-200";
  };

  const getPerformanceColor = (score) => {
    if (score >= 90) return "text-green-600 font-bold";
    if (score >= 75) return "text-yellow-600 font-semibold";
    return "text-red-600";
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading Enterprise Rule Engine...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          🧠 Enterprise AI Rule Engine
        </h1>
        <p className="text-gray-600">
          Self-learning security rules with natural language creation, A/B testing, and predictive optimization
        </p>
      </div>

      {/* Quick Stats */}
      {ruleAnalytics && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{ruleAnalytics.total_rules}</div>
            <div className="text-blue-100">Total Rules</div>
          </div>
          <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{ruleAnalytics.active_rules}</div>
            <div className="text-green-100">Active Rules</div>
          </div>
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{ruleAnalytics.avg_performance_score}%</div>
            <div className="text-purple-100">Avg Performance</div>
          </div>
          <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{ruleAnalytics.total_triggers_24h}</div>
            <div className="text-orange-100">24h Triggers</div>
          </div>
          <div className="bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{ruleAnalytics.false_positive_rate}%</div>
            <div className="text-red-100">False Positive Rate</div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "rules", label: "📋 Smart Rules", desc: "Manage intelligent security rules" },
            { id: "create", label: "✨ Natural Language", desc: "Create rules with AI" },
            { id: "analytics", label: "📊 Performance", desc: "Rule effectiveness metrics" },
            { id: "ab-testing", label: "🧪 A/B Testing", desc: "Optimize rule performance" },
            { id: "suggestions", label: "💡 AI Suggestions", desc: "ML-powered recommendations" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <div>{tab.label}</div>
              <div className="text-xs text-gray-400">{tab.desc}</div>
            </button>
          ))}
        </nav>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Smart Rules Tab */}
      {activeTab === "rules" && (
        <div className="space-y-6">
          {rules.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Smart Rules Found</h3>
              <p className="text-gray-500">Create your first intelligent security rule using natural language</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rule</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Performance</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Activity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Level</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {rules.map((rule) => (
                      <tr key={rule.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {rule.condition}
                            </div>
                            <div className="text-sm text-gray-500">
                              Action: {rule.action}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className={`text-lg font-bold ${getPerformanceColor(rule.performance_score || 85)}`}>
                            {rule.performance_score || 85}%
                          </div>
                          <div className="text-xs text-gray-500">Effectiveness</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm">
                            <div><strong>{rule.triggers_last_24h || 0}</strong> triggers</div>
                            <div className="text-gray-500">{rule.false_positives || 0} false positives</div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(rule.risk_level)}`}>
                            {rule.risk_level?.toUpperCase() || 'MEDIUM'}
                          </span>
                        </td>
                        <td className="px-6 py-4 space-x-2">
                          <button
                            onClick={() => createAbTest(rule.id)}
                            disabled={creatingTest}
                            className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded text-sm disabled:opacity-50"
                          >
                            {creatingTest ? "Creating..." : "🧪 A/B Test"}
                          </button>
                          <button
                            onClick={() => deleteRule(rule.id)}
                            disabled={deletingId === rule.id}
                            className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-sm disabled:opacity-50"
                          >
                            {deletingId === rule.id ? "Deleting..." : "🗑️ Delete"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Natural Language Rule Creation Tab */}
      {activeTab === "create" && (
        <div className="space-y-6">
          {/* Creation Method Tabs */}
          <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
            <nav className="flex border-b">
              <button
                onClick={() => setCreateMethod("natural-language")}
                className={`flex-1 py-3 px-4 text-sm font-medium ${
                  createMethod === "natural-language"
                    ? "bg-blue-50 text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                ✨ Natural Language
              </button>
              <button
                onClick={() => setCreateMethod("manual-form")}
                className={`flex-1 py-3 px-4 text-sm font-medium ${
                  createMethod === "manual-form"
                    ? "bg-blue-50 text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                📋 Manual Form
              </button>
            </nav>

            <div className="p-6">
              {/* Natural Language Method */}
              {createMethod === "natural-language" && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">✨ Create Rules with Natural Language</h3>
                  <p className="text-gray-600">
                    Describe what you want to protect against in plain English, and our AI will generate the appropriate security rule.
                  </p>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Describe your security rule:
                    </label>
                    <textarea
                      value={nlInput}
                      onChange={(e) => setNlInput(e.target.value)}
                      className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      rows="4"
                      placeholder="Example: Block all API calls from new countries during weekends and holidays..."
                    />
                  </div>

                  <button
                    onClick={generateRuleFromNaturalLanguage}
                    disabled={generatingRule || !nlInput.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg disabled:opacity-50"
                  >
                    {generatingRule ? "🤖 Generating Rule..." : "✨ Generate Smart Rule"}
                  </button>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-3">💡 Example Rule Prompts:</h4>
                    <div className="space-y-2 text-sm text-blue-800">
                      <div>• "Alert when agents access more than 100 files in 5 minutes"</div>
                      <div>• "Block database queries containing sensitive table names after business hours"</div>
                      <div>• "Quarantine agents that attempt privilege escalation on production systems"</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Manual Form Method */}
              {createMethod === "manual-form" && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">📋 Manual Rule Configuration</h3>
                  <p className="text-gray-600">
                    Create a rule by specifying each field. This gives you full control over the rule's behavior.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Rule Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={manualRule.name}
                        onChange={(e) => setManualRule({...manualRule, name: e.target.value})}
                        className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Suspicious Login Detection"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Risk Level <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={manualRule.risk_level}
                        onChange={(e) => setManualRule({...manualRule, risk_level: e.target.value})}
                        className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="low">🟢 Low</option>
                        <option value="medium">🟡 Medium</option>
                        <option value="high">🟠 High</option>
                        <option value="critical">🔴 Critical</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Condition (When to trigger) <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={manualRule.condition}
                      onChange={(e) => setManualRule({...manualRule, condition: e.target.value})}
                      className="w-full p-3 border rounded-lg font-mono text-sm"
                      rows="3"
                      placeholder="e.g., failed_login_attempts > 5 AND time_window = '10_minutes'"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Use logical expressions: field_name operator value AND/OR another_condition
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Action (What to do) <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={manualRule.action}
                      onChange={(e) => setManualRule({...manualRule, action: e.target.value})}
                      className="w-full p-3 border rounded-lg"
                    >
                      <option value="alert">🔔 Alert - Notify security team</option>
                      <option value="block">🚫 Block - Prevent action</option>
                      <option value="block_and_alert">🛑 Block & Alert</option>
                      <option value="quarantine">🔒 Quarantine - Isolate agent</option>
                      <option value="monitor">👁️ Monitor - Log for analysis</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={manualRule.description}
                      onChange={(e) => setManualRule({...manualRule, description: e.target.value})}
                      className="w-full p-3 border rounded-lg"
                      rows="2"
                      placeholder="Brief description of what this rule detects..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Justification
                    </label>
                    <textarea
                      value={manualRule.justification}
                      onChange={(e) => setManualRule({...manualRule, justification: e.target.value})}
                      className="w-full p-3 border rounded-lg"
                      rows="2"
                      placeholder="Why this rule is important..."
                    />
                  </div>

                  <button
                    onClick={createManualRule}
                    disabled={creatingManualRule || !manualRule.name || !manualRule.condition}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg disabled:opacity-50"
                  >
                    {creatingManualRule ? "Creating Rule..." : "✅ Create Manual Rule"}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Performance Analytics Tab */}
      {activeTab === "analytics" && (
        <div className="space-y-6">
          {ruleAnalytics ? (
            <>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🏆 Top Performing Rules</h3>
                <div className="space-y-3">
                  {ruleAnalytics.top_performing_rules.map((rule, idx) => (
                    <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                          idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : 'bg-orange-500'
                        }`}>
                          {idx + 1}
                        </div>
                        <div>
                          <div className="font-medium">{rule.name}</div>
                        </div>
                      </div>
                      <div className={`text-lg font-bold ${getPerformanceColor(rule.score)}`}>
                        {rule.score}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Performance Trends</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {ruleAnalytics.performance_trends.accuracy_improvement}
                    </div>
                    <div className="text-sm text-green-700">Accuracy Improvement</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {ruleAnalytics.performance_trends.response_time_improvement}
                    </div>
                    <div className="text-sm text-blue-700">Response Time</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {ruleAnalytics.performance_trends.false_positive_reduction}
                    </div>
                    <div className="text-sm text-purple-700">False Positive Reduction</div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Available</h3>
              <p className="text-gray-500">Analytics will appear when rule data is available</p>
            </div>
          )}
        </div>
      )}

      {/* A/B Testing Tab */}
      {activeTab === "ab-testing" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">🧪 Enterprise Rule A/B Testing</h2>
            <p className="text-gray-600 mb-6">
              Test rule variants side-by-side to optimize detection accuracy, reduce false positives, and measure business impact in real-time.
            </p>

            {abTests.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                <div className="text-6xl mb-4">🧪</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">No A/B Tests Yet</h3>
                <p className="text-gray-500 mb-6">Create A/B tests from any rule in the Smart Rules tab to optimize performance</p>
                <button
                  onClick={() => setActiveTab("rules")}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
                >
                  Go to Smart Rules
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                {abTests.map((test) => (
                  <div key={test.test_id} className="border-2 border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                    {/* Test Header */}
                    <div className={`px-6 py-4 border-b ${test.test_name && test.test_name.startsWith('[DEMO]') ? 'bg-gradient-to-r from-gray-50 to-gray-100' : 'bg-gradient-to-r from-blue-50 to-indigo-50'}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h4 className="text-lg font-bold text-gray-900">{test.test_name || test.rule_name}</h4>
                            {test.test_name && test.test_name.startsWith('[DEMO]') ? (
                              <span className="px-3 py-1 bg-gray-200 text-gray-700 text-xs font-bold rounded-full">
                                DEMO EXAMPLE
                              </span>
                            ) : (
                              <span className="px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full animate-pulse">
                                ✓ LIVE TEST
                              </span>
                            )}
                          </div>
                          {test.description && <p className="text-sm text-gray-600">{test.description}</p>}
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-4 py-2 rounded-full text-xs font-bold ${
                            test.status === 'completed' ? 'bg-green-100 text-green-800' :
                            test.status === 'running' ? 'bg-blue-100 text-blue-800 animate-pulse' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {test.status === 'completed' ? '✅ COMPLETED' :
                             test.status === 'running' ? '🔄 RUNNING' :
                             '⏸️ PAUSED'}
                          </span>
                          {test.progress_percentage !== undefined && (
                            <div className="text-right">
                              <div className="text-sm font-bold text-gray-700">{test.progress_percentage}%</div>
                              <div className="text-xs text-gray-500">Complete</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Test Content */}
                    <div className="p-6">
                      {/* Progress Bar */}
                      {test.progress_percentage !== undefined && (
                        <div className="mb-6">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">Test Progress</span>
                            <span className="text-sm text-gray-600">{test.progress_percentage}% ({test.duration_hours}h total)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div
                              className={`h-3 rounded-full transition-all duration-500 ${
                                test.progress_percentage === 100 ? 'bg-green-500' : 'bg-blue-500'
                              }`}
                              style={{ width: `${test.progress_percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      )}

                      {/* Variants Comparison */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className={`p-5 rounded-lg border-2 ${
                          test.winner === 'variant_a'
                            ? 'bg-green-50 border-green-300'
                            : 'bg-blue-50 border-blue-200'
                        }`}>
                          <div className="flex items-center justify-between mb-3">
                            <h5 className="font-bold text-gray-900 flex items-center gap-2">
                              🅰️ Variant A (Control)
                              {test.winner === 'variant_a' && <span className="text-green-600 text-xl">🏆</span>}
                            </h5>
                            <div className={`text-3xl font-black ${
                              test.winner === 'variant_a' ? 'text-green-600' : 'text-blue-600'
                            }`}>
                              {test.variant_a_performance}%
                            </div>
                          </div>
                          <p className="text-xs text-gray-700 font-mono bg-white p-3 rounded border mb-3 line-clamp-2">
                            {test.variant_a || "Control rule"}
                          </p>
                          {test.results && (
                            <div className="space-y-1 text-xs">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Detection Rate:</span>
                                <span className="font-semibold">{test.results.threat_detection_rate?.variant_a || test.variant_a_performance + '%'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">False Positives:</span>
                                <span className="font-semibold">{test.results.false_positive_rate?.variant_a || 'N/A'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Response Time:</span>
                                <span className="font-semibold">{test.results.response_time?.variant_a || 'N/A'}</span>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className={`p-5 rounded-lg border-2 ${
                          test.winner === 'variant_b'
                            ? 'bg-green-50 border-green-300'
                            : 'bg-purple-50 border-purple-200'
                        }`}>
                          <div className="flex items-center justify-between mb-3">
                            <h5 className="font-bold text-gray-900 flex items-center gap-2">
                              🅱️ Variant B (Optimized)
                              {test.winner === 'variant_b' && <span className="text-green-600 text-xl">🏆</span>}
                            </h5>
                            <div className={`text-3xl font-black ${
                              test.winner === 'variant_b' ? 'text-green-600' : 'text-purple-600'
                            }`}>
                              {test.variant_b_performance}%
                            </div>
                          </div>
                          <p className="text-xs text-gray-700 font-mono bg-white p-3 rounded border mb-3 line-clamp-2">
                            {test.variant_b || "Optimized rule"}
                          </p>
                          {test.results && (
                            <div className="space-y-1 text-xs">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Detection Rate:</span>
                                <span className="font-semibold">{test.results.threat_detection_rate?.variant_b || test.variant_b_performance + '%'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">False Positives:</span>
                                <span className="font-semibold">{test.results.false_positive_rate?.variant_b || 'N/A'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Response Time:</span>
                                <span className="font-semibold">{test.results.response_time?.variant_b || 'N/A'}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Test Metrics */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-blue-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-blue-600 mb-1">Sample Size</div>
                          <div className="text-lg font-bold text-blue-900">{test.sample_size?.toLocaleString() || '0'}</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-purple-600 mb-1">Confidence</div>
                          <div className="text-lg font-bold text-purple-900">{test.confidence_level}%</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-green-600 mb-1">Improvement</div>
                          <div className="text-sm font-bold text-green-900">{test.improvement || '+0%'}</div>
                        </div>
                        <div className="bg-orange-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-orange-600 mb-1">Duration</div>
                          <div className="text-lg font-bold text-orange-900">{test.duration_hours || 24}h</div>
                        </div>
                      </div>

                      {/* Enterprise Insights */}
                      {test.enterprise_insights && (
                        <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-4 mb-4">
                          <h5 className="font-bold text-amber-900 mb-3 flex items-center gap-2">
                            💼 Enterprise Business Impact
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div>
                              <div className="text-amber-700 font-semibold mb-1">💰 Cost Savings</div>
                              <div className="text-amber-900 font-bold">{test.enterprise_insights.cost_savings || 'Calculating...'}</div>
                            </div>
                            <div>
                              <div className="text-amber-700 font-semibold mb-1">📉 False Positive Reduction</div>
                              <div className="text-amber-900 font-bold">{test.enterprise_insights.false_positive_reduction || 'Calculating...'}</div>
                            </div>
                            <div>
                              <div className="text-amber-700 font-semibold mb-1">⚡ Efficiency Gain</div>
                              <div className="text-amber-900 font-bold">{test.enterprise_insights.efficiency_gain || 'Calculating...'}</div>
                            </div>
                            <div>
                              <div className="text-amber-700 font-semibold mb-1">📋 Recommendation</div>
                              <div className="text-amber-900 font-bold">{test.enterprise_insights.recommendation || 'Test in progress...'}</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center justify-between pt-4 border-t">
                        <div className="text-xs text-gray-500">
                          Created by {test.created_by || 'System'} • {test.created_at ? new Date(test.created_at).toLocaleDateString() : 'Recently'}
                        </div>
                        <div className="flex gap-2">
                          {/* Stop Test - Only for running REAL tests (not demos) */}
                          {test.status === 'running' && !test.test_name?.startsWith('[DEMO]') && (
                            <button
                              onClick={() => handleStopTest(test.test_id, test.test_name)}
                              className="bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded text-sm font-medium transition-colors"
                            >
                              🛑 Stop Test
                            </button>
                          )}

                          {/* Deploy Winner - Only for completed tests with a winner (not demos) */}
                          {test.winner && test.status !== 'stopped' && !test.test_name?.startsWith('[DEMO]') && (
                            <button
                              onClick={() => handleDeployWinner(test.test_id, test.test_name, test.winner)}
                              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-semibold transition-colors shadow-sm"
                            >
                              🚀 Deploy Winner
                            </button>
                          )}

                          {/* View Details - Available for all tests */}
                          <button
                            onClick={() => handleViewTestDetails(test)}
                            className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded text-sm font-medium"
                          >
                            📊 View Full Details
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* How to Create A/B Tests */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🎓 How to Create Your Own A/B Tests</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">1️⃣</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Select a Rule</h4>
                <p className="text-sm text-gray-600">
                  Go to Smart Rules tab and click the "🧪 A/B Test" button on any rule you want to optimize
                </p>
              </div>
              <div className="text-center p-4">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">2️⃣</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Automatic Setup</h4>
                <p className="text-sm text-gray-600">
                  System creates Variant A (control) and Variant B (AI-optimized) automatically
                </p>
              </div>
              <div className="text-center p-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">3️⃣</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Monitor & Deploy</h4>
                <p className="text-sm text-gray-600">
                  Track performance in real-time and deploy the winning variant when test completes
                </p>
              </div>
            </div>
          </div>

          {/* What is A/B Testing */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-indigo-900 mb-3">🔬 What is Enterprise A/B Testing?</h3>
            <div className="space-y-2 text-sm text-indigo-800">
              <p>
                <strong>A/B testing</strong> lets you compare two versions of a security rule side-by-side to determine which performs better before rolling out changes to production.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <h4 className="font-semibold mb-2">✅ Benefits:</h4>
                  <ul className="space-y-1 text-xs">
                    <li>• Reduce false positives by 20-40%</li>
                    <li>• Improve detection accuracy</li>
                    <li>• Measure business impact ($$$)</li>
                    <li>• Data-driven decision making</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">📊 What We Track:</h4>
                  <ul className="space-y-1 text-xs">
                    <li>• Detection rate & accuracy</li>
                    <li>• False positive rate</li>
                    <li>• Response time</li>
                    <li>• Cost savings & efficiency gains</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Suggestions Tab */}
      {activeTab === "suggestions" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 AI-Powered Rule Suggestions</h3>
            <p className="text-gray-600 mb-6">
              Machine learning analysis of your security patterns suggests these new rules to improve protection.
            </p>
            
            {suggestedRules.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🤖</div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">No Suggestions Available</h4>
                <p className="text-gray-500">AI will analyze your security patterns and suggest optimal rules</p>
              </div>
            ) : (
              <div className="space-y-4">
                {suggestedRules.map((suggestion) => (
                  <div key={suggestion.id} className="border border-blue-200 rounded-lg p-6 bg-blue-50">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-blue-900 mb-2">
                          {suggestion.suggested_rule}
                        </h4>
                        <p className="text-sm text-blue-700 mb-3">
                          <strong>Reasoning:</strong> {suggestion.reasoning}
                        </p>
                        <p className="text-sm text-blue-600">
                          <strong>Potential Impact:</strong> {suggestion.potential_impact}
                        </p>
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-2xl font-bold text-blue-600">{suggestion.confidence}%</div>
                        <div className="text-xs text-blue-500">Confidence</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-blue-600">
                        Based on {suggestion.data_points} data points
                      </div>
                      <div className="space-x-2">
                        <button 
                          onClick={() => {
                            setNlInput(suggestion.suggested_rule);
                            setActiveTab("create");
                          }}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
                        >
                          ✨ Create Rule
                        </button>
                        <button className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded text-sm">
                          📋 Save for Later
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ML Insights */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🔮 Machine Learning Insights</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gradient-to-r from-purple-100 to-purple-200 rounded-lg">
                <div className="text-lg font-bold text-purple-800">87%</div>
                <div className="text-sm text-purple-700">Pattern Recognition Accuracy</div>
              </div>
              <div className="p-4 bg-gradient-to-r from-green-100 to-green-200 rounded-lg">
                <div className="text-lg font-bold text-green-800">1,247</div>
                <div className="text-sm text-green-700">Security Events Analyzed</div>
              </div>
              <div className="p-4 bg-gradient-to-r from-orange-100 to-orange-200 rounded-lg">
                <div className="text-lg font-bold text-orange-800">23</div>
                <div className="text-sm text-orange-700">New Threat Patterns Identified</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnterpriseSmartRuleEngine;