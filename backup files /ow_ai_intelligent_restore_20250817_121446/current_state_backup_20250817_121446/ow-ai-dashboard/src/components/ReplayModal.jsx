import React from "react";

const ReplayModal = ({ action, onClose }) => {
  if (!action) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-md p-6 rounded-lg shadow-lg relative">
        <h2 className="text-xl font-semibold mb-4">Replay Agent Action</h2>

        <div className="text-sm space-y-2">
          <p><strong>Agent:</strong> {action.agent_id}</p>
          <p><strong>Tool:</strong> {action.tool_name}</p>
          <p><strong>Action Type:</strong> {action.action_type}</p>
          <p><strong>Description:</strong> {action.description}</p>
          <p><strong>Risk Level:</strong> {action.risk_level}</p>
          <p><strong>Timestamp:</strong> {new Date(action.timestamp * 1000).toLocaleString()}</p>
          {action.is_false_positive && (
            <p className="text-yellow-600 text-xs">⚠ Marked as False Positive</p>
          )}
        </div>

        <button
          className="absolute top-2 right-3 text-gray-500 hover:text-red-500"
          onClick={onClose}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default ReplayModal;
