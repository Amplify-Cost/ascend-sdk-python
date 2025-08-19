import React, { useEffect, useState } from "react";
import { fetchWithAuth } from "../utils/fetchWithAuth";

const SecurityDetails = ({ log, onClose }) => {
  const [auditTrail, setAuditTrail] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;

  useEffect(() => {
    if (log?.id) {
      const fetchAuditTrail = async () => {
        setLoading(true);
        try {
          // ✅ Using fetchWithAuth for automatic token handling
          const response = await fetchWithAuth(`${API_BASE_URL}/agent-action/${log.id}/audit`);
          
          if (!response.ok) {
            throw new Error("Failed to load audit trail");
          }
          
          const data = await response.json();
          setAuditTrail(Array.isArray(data) ? data : []);
        } catch (err) {
          console.error("Error loading audit trail", err);
          setError("Could not load audit history.");
        } finally {
          setLoading(false);
        }
      };

      fetchAuditTrail();
    }
  }, [log?.id]);

  if (!log) return null;

  return (
    <div className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-40 flex justify-center items-start pt-20 z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full max-h-[80vh] overflow-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Security Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Log Details */}
        <div className="space-y-2 text-sm mb-6">
          <div><strong>Agent ID:</strong> {log.agent_id}</div>
          <div><strong>Action Type:</strong> {log.action_type}</div>
          <div><strong>Description:</strong> {log.description}</div>
          <div><strong>Tool:</strong> {log.tool_name || "—"}</div>
          <div><strong>Risk Level:</strong> 
            <span className={`ml-1 px-2 py-1 rounded text-xs ${
              log.risk_level === 'high' ? 'bg-red-100 text-red-800' :
              log.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {log.risk_level}
            </span>
          </div>
          <div><strong>NIST Control:</strong> {log.nist_control || "—"}</div>
          <div><strong>NIST Description:</strong> {log.nist_description || "—"}</div>
          <div><strong>MITRE Tactic:</strong> {log.mitre_tactic || "—"}</div>
          <div><strong>MITRE Technique:</strong> {log.mitre_technique || "—"}</div>
          <div><strong>Recommendation:</strong> {log.recommendation || "—"}</div>
          <div><strong>Status:</strong> {log.status}</div>
          <div><strong>Timestamp:</strong> {new Date(log.timestamp).toLocaleString()}</div>
        </div>

        {/* Audit History */}
        <h3 className="text-md font-semibold mt-6 mb-2">Audit History</h3>
        {loading && <p className="text-gray-500 text-sm">Loading audit trail...</p>}
        {error && <p className="text-red-500 text-sm">{error}</p>}
        {!loading && !error && auditTrail.length === 0 && (
          <p className="text-sm text-gray-500">No audit trail found.</p>
        )}
        {!loading && auditTrail.length > 0 && (
          <ul className="text-sm space-y-2">
            {auditTrail.map((entry, index) => (
              <li key={index} className="border-b pb-2">
                <div className="font-medium">{entry.decision?.toUpperCase()}</div>
                <div className="text-gray-600">by {entry.reviewed_by}</div>
                <div className="text-gray-500 text-xs">
                  {new Date(entry.timestamp).toLocaleString()}
                </div>
                {entry.notes && (
                  <div className="text-gray-700 mt-1">Note: {entry.notes}</div>
                )}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-6 text-right">
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SecurityDetails;