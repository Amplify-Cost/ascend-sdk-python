import React from "react";

/**
 * ActiveConfigCard Component
 * Displays currently active risk scoring configuration
 * Read-only overview card at top of Risk Configuration tab
 */
const ActiveConfigCard = ({ config, onViewHistory, onRollback }) => {
  if (!config) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span>Loading active configuration...</span>
        </div>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-3">
            <h3 className="text-lg font-semibold text-gray-800">
              🎯 Active Risk Scoring Configuration
            </h3>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              Active
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Version:</span>
              <span className="ml-2 font-semibold text-gray-800">
                {config.config_version}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Algorithm:</span>
              <span className="ml-2 font-semibold text-gray-800">
                {config.algorithm_version}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Activated:</span>
              <span className="ml-2 font-semibold text-gray-800">
                {formatDate(config.activated_at)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">By:</span>
              <span className="ml-2 font-semibold text-gray-800">
                {config.activated_by || "System"}
              </span>
            </div>
          </div>

          {config.description && (
            <div className="mt-3 text-sm">
              <span className="text-gray-600">Description:</span>
              <p className="mt-1 text-gray-700 italic">{config.description}</p>
            </div>
          )}

          {config.is_default && (
            <div className="mt-3">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                Factory Default
              </span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col space-y-2 ml-4">
          <button
            onClick={onViewHistory}
            className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 border border-blue-300 rounded transition-colors"
            aria-label="View configuration history"
          >
            📜 View History
          </button>
          {!config.is_default && (
            <button
              onClick={onRollback}
              className="px-4 py-2 text-sm text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50 border border-yellow-300 rounded transition-colors"
              aria-label="Rollback to factory default"
            >
              ⚠️ Rollback
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActiveConfigCard;
