const API_BASE_URL = import.meta.env.VITE_API_URL;

// SmartRuleGen.jsx
import React, { useEffect, useState } from "react";

const SmartRuleGen = ({ getAuthHeaders }) => {
  const [rules, setRules] = useState([]);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchRules = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/rules", {
        headers: await getAuthHeaders(),
      });
      if (!res.ok) throw new Error("Failed to fetch rules");
      const data = await res.json();
      setRules(data);
    } catch (err) {
      console.error("Error loading smart rules:", err);
      setError("Failed to load smart rules.");
    }
  };

  const deleteRule = async (id) => {
    if (!window.confirm("Are you sure you want to delete this rule?")) return;
    setDeletingId(id);
    try {
      const res = await fetch(`${API_BASE_URL}/rules/${id}`, {
        method: "DELETE",
        headers: await getAuthHeaders(),
      });
      if (!res.ok) throw new Error("Delete failed");
      setRules((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error("Delete failed", err);
      alert("Failed to delete rule.");
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Generated Smart Rules</h2>
      {error && <p className="text-red-500">{error}</p>}

      {rules.length === 0 ? (
        <p className="text-gray-500 italic">No generated rules yet.</p>
      ) : (
        <table className="w-full bg-white shadow rounded text-sm">
          <thead className="bg-gray-100 text-gray-700">
            <tr>
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Condition</th>
              <th className="p-2 text-left">Action</th>
              <th className="p-2 text-left">Justification</th>
              <th className="p-2 text-center">Delete</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className="border-t hover:bg-gray-50">
                <td className="p-2">{rule.id}</td>
                <td className="p-2">{rule.condition}</td>
                <td className="p-2">{rule.action}</td>
                <td className="p-2">{rule.justification}</td>
                <td className="p-2 text-center">
                  <button
                    onClick={() => deleteRule(rule.id)}
                    disabled={deletingId === rule.id}
                    className="px-2 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded disabled:opacity-50"
                  >
                    {deletingId === rule.id ? "Deleting..." : "Delete"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SmartRuleGen;
