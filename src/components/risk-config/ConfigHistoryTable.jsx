import React, { useState } from "react";

/**
 * ConfigHistoryTable Component
 * Displays configuration version history with activation controls
 *
 * Features:
 * - Sortable by date
 * - Shows active configuration
 * - Quick activate button for previous configs
 * - Factory default indicator
 */
const ConfigHistoryTable = ({ history = [], onActivate, loading = false }) => {
  const [showAll, setShowAll] = useState(false);

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const displayedHistory = showAll ? history : history.slice(0, 5);

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span>Loading configuration history...</span>
        </div>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-2">📜 Configuration History</h4>
        <p className="text-gray-500 text-sm">No configuration history available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h4 className="text-lg font-semibold mb-4">📜 Configuration History</h4>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Version
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Algorithm
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Activated
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                By
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayedHistory.map((config) => (
              <tr
                key={config.id}
                className={config.is_active ? "bg-green-50" : "hover:bg-gray-50"}
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {config.config_version}
                  </div>
                  {config.description && (
                    <div className="text-xs text-gray-500 truncate max-w-xs">
                      {config.description}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {config.algorithm_version}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(config.created_at)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {config.activated_at ? formatDate(config.activated_at) : "—"}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {config.activated_by || config.created_by}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {config.is_active && (
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                        Active
                      </span>
                    )}
                    {config.is_default && (
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                        Default
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {!config.is_active && (
                    <button
                      onClick={() => onActivate(config.id)}
                      className="text-blue-600 hover:text-blue-700 hover:underline"
                      aria-label={`Activate configuration ${config.config_version}`}
                    >
                      Activate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show More/Less Toggle */}
      {history.length > 5 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
          >
            {showAll
              ? "Show Less"
              : `Show All (${history.length - 5} more)`}
          </button>
        </div>
      )}
    </div>
  );
};

export default ConfigHistoryTable;
