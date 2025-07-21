import React, { useEffect, useState } from "react";

const SecurityDetails = ({ log, onClose }) => {
  const [auditTrail, setAuditTrail] = useState([]);
  const [error, setError] = useState(null);
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    if (log?.id) {
      fetch(`${API_BASE_URL}/log/${log.id}/audit`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
        .then((res) => res.json())
        .then(setAuditTrail)
        .catch((err) => {
          console.error("Error loading audit trail", err);
          setError("Could not load audit history.");
        });
    }
  }, [log]);

  if (!log) return null;

  return (
    <div className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-40 flex justify-center items-start pt-20 z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full max-h-[80vh] overflow-auto">
        <h2 className="text-xl font-bold mb-4">Log Details</h2>
        <ul className="text-sm space-y-2">
          <li><strong>Agent ID:</strong> {log.agent_id}</li>
          <li><strong>Action Type:</strong> {log.action_type}</li>
          <li><strong>Description:</strong> {log.description}</li>
          <li><strong>Tool:</strong> {log.tool_name || "—"}</li>
          <li><strong>Risk Level:</strong> {log.risk_level}</li>
          <li><strong>NIST Control:</strong> {log.nist_control || "—"}</li>
          <li><strong>NIST Description:</strong> {log.nist_description || "—"}</li>
          <li><strong>MITRE Tactic:</strong> {log.mitre_tactic || "—"}</li>
          <li><strong>MITRE Technique:</strong> {log.mitre_technique || "—"}</li>
          <li><strong>Recommendation:</strong> {log.recommended_action || "—"}</li>
          <li><strong>Status:</strong> {log.status}</li>
          <li><strong>Timestamp:</strong> {new Date(log.timestamp * 1000).toLocaleString()}</li>
        </ul>

        <h3 className="text-md font-semibold mt-6 mb-2">Audit History</h3>
        {error && <p className="text-red-500">{error}</p>}
        {auditTrail.length === 0 ? (
          <p className="text-sm text-gray-500">No audit trail found.</p>
        ) : (
          <ul className="text-sm space-y-1">
            {auditTrail.map((entry, index) => (
              <li key={index} className="border-b pb-1">
                <strong>{entry.status?.toUpperCase()}</strong> by <em>{entry.performed_by}</em> at{" "}
                {new Date(entry.timestamp * 1000).toLocaleString()}<br />
                Note: {entry.notes || "—"}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-6 text-right">
          <button
            onClick={onClose}
            className="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SecurityDetails;