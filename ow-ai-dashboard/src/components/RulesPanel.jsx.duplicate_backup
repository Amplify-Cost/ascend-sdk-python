const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

import React, { useEffect, useState } from "react";

const Rules = ({ getAuthHeaders, user }) => {
  const [rules, setRules] = useState([]);
  const [filter, setFilter] = useState("");
  const [selectedRule, setSelectedRule] = useState(null);
  const [editedRule, setEditedRule] = useState({ condition: "", action: "", justification: "", tags: [] });
  const [newRule, setNewRule] = useState({ condition: "", action: "", justification: "", tags: [] });
  const [message, setMessage] = useState("");
  const [auditLog, setAuditLog] = useState(null);
  const [showAuditModal, setShowAuditModal] = useState(false);
  // ✅ REMOVED: versionHistory state and API call that was causing 404
  const [currentPage, setCurrentPage] = useState(1);
  const rulesPerPage = 5;

  const fetchRules = async () => {
    try {
      console.log("🔍 Fetching rules from:", `${API_BASE_URL}/rules`);
      const res = await fetch(`${API_BASE_URL}/rules`, {
        credentials: "include",
        headers: await getAuthHeaders(),
      });
      const data = await res.json();
      console.log("📋 Rules data:", data);
      setRules(Array.isArray(data) ? data : []); // ✅ Ensure it's an array
    } catch (err) {
      console.error("❌ Failed to fetch rules", err);
      setRules([]); // ✅ Set empty array on error
    }
  };

  // ✅ REMOVED: fetchVersionHistory function that was causing 404

  const updateRules = async (updatedRules) => {
    try {
      const res = await fetch(`${API_BASE_URL}/rules`, {
        method: "POST",
        credentials: "include",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(await getAuthHeaders()),
        },
        body: JSON.stringify(updatedRules),
      });
      if (res.ok) {
        fetchRules();
        setMessage("✅ Rule changes saved successfully");
        setSelectedRule(null);
        setNewRule({ condition: "", action: "", justification: "", tags: [] });
      }
    } catch (err) {
      console.error("Failed to update rules", err);
    }
  };

  const deleteRule = async (ruleToDelete) => {
    const updated = rules.filter((r) => r !== ruleToDelete);
    updateRules(updated);
  };

  const saveNewRule = () => {
    if (!newRule.condition || !newRule.action || !newRule.justification) {
      setMessage("All fields must be filled in before saving.");
      return;
    }
    const enriched = {
      ...newRule,
      created_at: new Date().toISOString(),
      created_by: user?.email || "unknown",
    };
    updateRules([...rules, enriched]);
  };

  const fetchAuditLog = async (ruleId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/feedback/${ruleId}`, {
        credentials: "include",
        headers: await getAuthHeaders(),
      });
      const log = await res.json();
      setAuditLog(log);
      setShowAuditModal(true);
    } catch (err) {
      console.error("Audit log fetch failed", err);
    }
  };

  const exportRules = () => {
    const blob = new Blob([JSON.stringify(rules, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rules_export.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    fetchRules();
    // ✅ REMOVED: fetchVersionHistory() call that was causing 404
  }, []);

  const filteredRules = rules.filter((r) =>
    r.condition?.toLowerCase().includes(filter.toLowerCase()) ||
    r.action?.toLowerCase().includes(filter.toLowerCase()) ||
    r.justification?.toLowerCase().includes(filter.toLowerCase()) ||
    (r.tags || []).some((tag) => tag.toLowerCase().includes(filter.toLowerCase()))
  );

  const paginatedRules = filteredRules.slice((currentPage - 1) * rulesPerPage, currentPage * rulesPerPage);
  const totalPages = Math.ceil(filteredRules.length / rulesPerPage);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Defined Security Rules</h2>
      {message && <div className="text-green-600 mb-4">{message}</div>}

      <div className="flex justify-between items-center mb-4">
        <input
          type="text"
          placeholder="Filter by keyword or tag..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="p-2 border rounded w-full max-w-md"
        />
        <button onClick={exportRules} className="ml-4 px-4 py-2 bg-indigo-600 text-white rounded">Export</button>
      </div>

      {paginatedRules.length === 0 ? (
        <p className="text-gray-500 italic">No rules found.</p>
      ) : (
        paginatedRules.map((rule, index) => (
          <div key={index} className="bg-gray-100 p-4 mb-4 rounded shadow">
            <h3 className="font-semibold text-blue-700 underline">{rule.condition?.split(" and ")[0] || "Untitled Rule"}</h3>
            <p><strong>Condition:</strong> {rule.condition}</p>
            <p><strong>Action:</strong> {rule.action}</p>
            <p><strong>Justification:</strong> {rule.justification}</p>
            {rule.tags && <p><strong>Tags:</strong> {rule.tags.join(", ")}</p>}
            {rule.created_at && <p><strong>Created:</strong> {new Date(rule.created_at).toLocaleString()}</p>}
            {rule.created_by && <p><strong>Created by:</strong> {rule.created_by}</p>}
            <div className="mt-2 flex gap-2">
              <button onClick={() => { setSelectedRule(rule); setEditedRule(rule); }} className="bg-yellow-500 text-white px-2 py-1 rounded text-sm">Edit</button>
              <button onClick={() => deleteRule(rule)} className="bg-red-600 text-white px-2 py-1 rounded text-sm">Delete</button>
              <button onClick={() => fetchAuditLog(index + 1)} className="bg-gray-600 text-white px-2 py-1 rounded text-sm">View Audit Log</button>
            </div>
          </div>
        ))
      )}

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))} className="px-3 py-1 bg-gray-300 rounded">Prev</button>
          <span>Page {currentPage} of {totalPages}</span>
          <button onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))} className="px-3 py-1 bg-gray-300 rounded">Next</button>
        </div>
      )}

      <div className="mt-6 border-t pt-6">
        <h3 className="text-lg font-semibold mb-2">Add New Rule</h3>
        <textarea placeholder="Condition" value={newRule.condition} onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })} className="w-full mb-2 p-2 border rounded" />
        <textarea placeholder="Action" value={newRule.action} onChange={(e) => setNewRule({ ...newRule, action: e.target.value })} className="w-full mb-2 p-2 border rounded" />
        <textarea placeholder="Justification" value={newRule.justification} onChange={(e) => setNewRule({ ...newRule, justification: e.target.value })} className="w-full mb-2 p-2 border rounded" />
        <input type="text" placeholder="Tags (comma separated)" value={newRule.tags?.join(", ") || ""} onChange={(e) => setNewRule({ ...newRule, tags: e.target.value.split(",").map((t) => t.trim()) })} className="w-full mb-2 p-2 border rounded" />
        <button onClick={saveNewRule} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Add Rule</button>
      </div>

      {/* ✅ REMOVED: Version History section that was causing 404 */}

      {selectedRule && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-lg w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Edit Rule</h3>
            <textarea value={editedRule.condition} onChange={(e) => setEditedRule({ ...editedRule, condition: e.target.value })} className="w-full mb-2 p-2 border rounded" />
            <textarea value={editedRule.action} onChange={(e) => setEditedRule({ ...editedRule, action: e.target.value })} className="w-full mb-2 p-2 border rounded" />
            <textarea value={editedRule.justification} onChange={(e) => setEditedRule({ ...editedRule, justification: e.target.value })} className="w-full mb-2 p-2 border rounded" />
            <input type="text" value={editedRule.tags?.join(", ") || ""} onChange={(e) => setEditedRule({ ...editedRule, tags: e.target.value.split(",").map((t) => t.trim()) })} className="w-full mb-4 p-2 border rounded" placeholder="Tags (comma separated)" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setSelectedRule(null)} className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400">Cancel</button>
              <button onClick={() => updateRules(rules.map((r) => (r === selectedRule ? editedRule : r)))} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Save Rule</button>
            </div>
          </div>
        </div>
      )}

      {showAuditModal && auditLog && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-lg w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Justification Audit Log</h3>
            <p><strong>Total Triggered:</strong> {auditLog.total_triggered}</p>
            <p><strong>Approved:</strong> {auditLog.approved_count}</p>
            <p><strong>Rejected:</strong> {auditLog.rejected_count}</p>
            <p><strong>False Positives:</strong> {auditLog.false_positive_count}</p>
            <div className="mt-4 flex justify-end">
              <button onClick={() => setShowAuditModal(false)} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Rules;