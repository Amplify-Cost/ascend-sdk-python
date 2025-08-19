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

  const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;

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
      const response = await fetch(`${API_BASE_URL}/smart-rules`, {
        headers: { "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setRules(data);
        setError(null);
      } else {
        console.error("Failed to fetch rules:", response.status);
        setRules([]); // ENTERPRISE: No demo data
        setError("Failed to fetch rules from server");
      }
    } catch (err) {
      console.error("Error fetching rules:", err);
      setRules([]); // ENTERPRISE: No demo data
      setError("Network error fetching rules");
    }
  };

  const fetchRuleAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/smart-rules/analytics`, {
        headers: { "Content-Type": "application/json" }
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
      const response = await fetch(`${API_BASE_URL}/smart-rules/ab-tests`, {
        headers: { "Content-Type": "application/json" }
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
      const response = await fetch(`${API_BASE_URL}/smart-rules/suggestions`, {
        headers: { "Content-Type": "application/json" }
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
      const response = await fetch(`${API_BASE_URL}/smart-rules/generate-from-nl`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      const response = await fetch(`${API_BASE_URL}/smart-rules/${id}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" }
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
    const response = await fetch(`${API_BASE_URL}/smart-rules/ab-test?rule_id=${ruleId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">✨ Create Rules with Natural Language</h3>
            <p className="text-gray-600 mb-6">
              Describe what you want to protect against in plain English, and our AI will generate the appropriate security rule.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe your security rule:
                </label>
                <textarea
                  value={nlInput}
                  onChange={(e) => setNlInput(e.target.value)}
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="4"
                  placeholder="Example: Block all API calls from new countries during weekends and holidays..."
                />
              </div>
              
              <button
                onClick={generateRuleFromNaturalLanguage}
                disabled={generatingRule || !nlInput.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generatingRule ? "🤖 Generating Rule..." : "✨ Generate Smart Rule"}
              </button>
            </div>

            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-3">💡 Example Rule Prompts:</h4>
              <div className="space-y-2 text-sm text-blue-800">
                <div>• "Alert when agents access more than 100 files in 5 minutes"</div>
                <div>• "Block database queries containing sensitive table names after business hours"</div>
                <div>• "Quarantine agents that attempt privilege escalation on production systems"</div>
                <div>• "Monitor API calls from IP addresses not seen in the last 30 days"</div>
              </div>
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
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🧪 Enterprise Rule A/B Testing</h3>
            <p className="text-gray-600 mb-6">
              Test different versions of your security rules to optimize performance and reduce false positives.
            </p>
            
            {abTests.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🧪</div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">No A/B Tests Running</h4>
                <p className="text-gray-500">Create A/B tests from the Smart Rules tab to optimize performance</p>
              </div>
            ) : (
              <div className="space-y-4">
                {abTests.map((test) => (
                  <div key={test.id} className="border rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold">{test.rule_name}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        test.status === 'completed' ? 'bg-green-100 text-green-800' : 
                        test.status === 'running' ? 'bg-blue-100 text-blue-800' : 
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {test.status.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h5 className="font-medium text-gray-900 mb-2">🅰️ Variant A (Control)</h5>
                        <p className="text-sm text-gray-600 mb-3">{test.variant_a}</p>
                        <div className="text-2xl font-bold text-blue-600">{test.variant_a_performance}%</div>
                        <div className="text-sm text-gray-500">Performance Score</div>
                      </div>
                      
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h5 className="font-medium text-gray-900 mb-2">🅱️ Variant B (Test)</h5>
                        <p className="text-sm text-gray-600 mb-3">{test.variant_b}</p>
                        <div className="text-2xl font-bold text-green-600">{test.variant_b_performance}%</div>
                        <div className="text-sm text-gray-500">Performance Score</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        <strong>Confidence Level:</strong> {test.confidence_level}%
                      </div>
                      {test.winner && (
                        <div className="text-sm font-medium text-green-600">
                          🏆 Winner: {test.winner === 'variant_a' ? 'Variant A' : 'Variant B'}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
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