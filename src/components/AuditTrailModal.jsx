import React, { useEffect, useState, useCallback } from "react";

const AuditTrailModal = ({ token, actionId, onClose }) => {
  const [auditLogs, setAuditLogs] = useState([]);
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const fetchAuditLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/audit-trail`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      const filtered = data.filter((log) => log.action_id === actionId);
      setAuditLogs(filtered);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    }
  }, [API_BASE_URL, token, actionId]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white w-full max-w-xl p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Audit Trail for Action #{actionId}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-black text-sm"
          >
            ✖
          </button>
        </div>
        {auditLogs.length === 0 ? (
          <p className="text-sm text-gray-600">No audit trail found.</p>
        ) : (
          <table className="w-full text-sm table-auto">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-3 py-2 text-left">Decision</th>
                <th className="px-3 py-2 text-left">Reviewer</th>
                <th className="px-3 py-2 text-left">Time</th>
                <th className="px-3 py-2 text-left">MITRE</th>
                <th className="px-3 py-2 text-left">NIST</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} className="border-t">
                  <td className="px-3 py-1">{log.decision}</td>
                  <td className="px-3 py-1">{log.reviewed_by}</td>
                  <td className="px-3 py-1">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-3 py-1">{log.mitre_technique || "-"}</td>
                  <td className="px-3 py-1">{log.nist_control || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AuditTrailModal;
