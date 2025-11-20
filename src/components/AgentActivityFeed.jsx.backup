import React, { useEffect, useState } from "react";
import ReplayModal from "./ReplayModal";
import EnterpriseCard, { CompactCard } from "./enterprise/EnterpriseCard";
import SkeletonCard, { CompactSkeleton } from "./enterprise/SkeletonCard";
import ErrorCard from "./enterprise/ErrorCard";
import EmptyCard from "./enterprise/EmptyCard";
import ENTERPRISE_THEME, { getRiskColor } from "./enterprise/EnterpriseTheme";

const AgentActivityFeed = ({ getAuthHeaders }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRisk, setSelectedRisk] = useState("all");
  const [replayAction, setReplayAction] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [supportMessage, setSupportMessage] = useState("");
  const [supportStatus, setSupportStatus] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const itemsPerPage = 10; // Increased from 5 for better UX

  // ✅ Added fallback URL
  const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const fetchActivity = async () => {
    try {
      console.log("🔍 Fetching from:", API_BASE_URL); // Debug log
      const url =
        selectedRisk === "all"
          ? `${API_BASE_URL}/api/agent-activity`
          : `${API_BASE_URL}/api/agent-activity?risk=${selectedRisk}`;
      
      console.log("📡 Full URL:", url); // Debug log
      
      const res = await fetch(url, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch agent activity`);
      const data = await res.json();
      setActivities(Array.isArray(data) ? data : []);
      setError(null); // Clear any previous errors
    } catch (err) {
      console.error("❌ Fetch error:", err);
      setError(`Unable to load activity: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
    const interval = setInterval(fetchActivity, 30000);
    return () => clearInterval(interval);
  }, [getAuthHeaders, selectedRisk]);

  const toggleFalsePositive = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/agent-action/false-positive/${id}`, {
        credentials: "include",
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) fetchActivity();
    } catch {
      alert("Failed to update false positive status.");
    }
  };

  const handleSupportSubmit = async () => {
    setSupportStatus("");
    try {
      const res = await fetch(`${API_BASE_URL}/support/submit`, {
        credentials: "include",
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: supportMessage }),
      });
      if (res.ok) {
        setSupportStatus("✅ Message submitted successfully.");
        setSupportMessage("");
      } else {
        setSupportStatus("❌ Failed to submit message.");
      }
    } catch {
      setSupportStatus("❌ Error sending request.");
    }
  };

  const handleFileUpload = async (e) => {
    setUploadStatus("");
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/agent-actions/upload-json`, {
        credentials: "include",
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });

      if (res.ok) {
        setUploadStatus("✅ File uploaded successfully!");
        fetchActivity();
      } else {
        setUploadStatus("❌ Upload failed.");
      }
    } catch {
      setUploadStatus("❌ Error uploading file.");
    }
  };

  // Rest of your component stays the same...
  const filteredActivities = activities.filter((a) =>
    a.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.tool_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.agent_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const paginatedActivities = filteredActivities.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(filteredActivities.length / itemsPerPage);

  // Helper function to get risk badge color
  const getRiskBadge = (riskLevel) => {
    const level = riskLevel?.toLowerCase() || 'unknown';
    const color = getRiskColor(
      level === 'high' ? 7 : level === 'medium' ? 5 : level === 'low' ? 2 : 0
    );
    return (
      <span
        className="px-2 py-1 text-xs font-semibold rounded-md"
        style={{
          backgroundColor: `${color}20`,
          color: color,
          border: `1px solid ${color}40`
        }}
      >
        {riskLevel || 'Unknown'}
      </span>
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonCard variant="list" />
        <SkeletonCard variant="list" />
        <SkeletonCard variant="list" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <ErrorCard
        title="Failed to Load Activity Feed"
        message={error}
        onRetry={fetchActivity}
        showDetails={true}
      />
    );
  }

  // Empty state
  if (activities.length === 0) {
    return (
      <EmptyCard
        title="No Agent Activity"
        message="No agent actions have been recorded yet. Activity will appear here when agents perform actions."
        icon="📋"
        variant="info"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card with Filters */}
      <EnterpriseCard
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        }
        title="Agent Activity Feed"
        subtitle={`${filteredActivities.length} ${filteredActivities.length === 1 ? 'activity' : 'activities'} ${selectedRisk !== 'all' ? `(${selectedRisk} risk)` : ''}`}
        variant="default"
      >
        {/* Filters */}
        <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-3 md:space-y-0 mb-6">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Risk Level:</label>
            <select
              value={selectedRisk}
              onChange={(e) => {
                setSelectedRisk(e.target.value);
                setCurrentPage(1); // Reset to first page
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              style={{ minWidth: '120px' }}
            >
              <option value="all">All Levels</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex-1">
            <input
              type="text"
              placeholder="🔍 Search by agent, tool, or description..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1); // Reset to first page
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
        </div>

        {/* No results after filtering */}
        {filteredActivities.length === 0 && (
          <EmptyCard
            title="No Matching Activities"
            message={`No activities found matching "${searchTerm}" with risk level "${selectedRisk}". Try adjusting your filters.`}
            icon="🔍"
            variant="info"
          />
        )}

        {/* Activity List */}
        {filteredActivities.length > 0 && (
          <div className="space-y-3">
            {paginatedActivities.map((activity) => (
              <div
                key={activity.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-gray-300 transition-all duration-200 bg-white"
              >
                {/* Activity Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-semibold text-gray-900">
                        {activity.agent_id || 'Unknown Agent'}
                      </span>
                      {getRiskBadge(activity.risk_level)}
                      {activity.is_false_positive && (
                        <span className="px-2 py-1 text-xs font-semibold rounded-md bg-yellow-100 text-yellow-800 border border-yellow-300">
                          ⚠ False Positive
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(activity.timestamp * 1000).toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Activity Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                  <div>
                    <span className="text-xs font-medium text-gray-600">Action Type:</span>
                    <p className="text-sm text-gray-900 mt-1">{activity.action_type || '—'}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-gray-600">Tool:</span>
                    <p className="text-sm text-gray-900 mt-1">{activity.tool_name || '—'}</p>
                  </div>
                </div>

                {activity.description && (
                  <div className="mb-3">
                    <span className="text-xs font-medium text-gray-600">Description:</span>
                    <p className="text-sm text-gray-700 mt-1">{activity.description}</p>
                  </div>
                )}

                {activity.summary && (
                  <div className="mb-3 bg-blue-50 border border-blue-200 rounded-md p-3">
                    <span className="text-xs font-medium text-blue-900">AI Summary:</span>
                    <p className="text-sm text-blue-800 mt-1">{activity.summary}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center space-x-3 pt-3 border-t border-gray-100">
                  <button
                    onClick={() => toggleFalsePositive(activity.id)}
                    className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                  >
                    {activity.is_false_positive ? '✓ Unmark False Positive' : '⚠ Mark as False Positive'}
                  </button>
                  <button
                    onClick={() => setReplayAction(activity)}
                    className="text-xs font-medium text-green-600 hover:text-green-800 hover:underline transition-colors"
                  >
                    🔁 Replay Action
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center mt-6 space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 rounded-lg text-sm font-medium border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              ← Previous
            </button>

            <div className="flex space-x-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 rounded-lg text-sm font-medium border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Next →
            </button>
          </div>
        )}
      </EnterpriseCard>

      {/* Support Card */}
      <EnterpriseCard
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        }
        title="Need Help?"
        subtitle="Submit a support message"
        variant="info"
      >
        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          rows={4}
          value={supportMessage}
          onChange={(e) => setSupportMessage(e.target.value)}
          placeholder="Describe your issue or ask a question..."
        />
        <button
          onClick={handleSupportSubmit}
          disabled={!supportMessage.trim()}
          className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          Submit Support Request
        </button>
        {supportStatus && (
          <p className={`text-sm mt-2 ${supportStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
            {supportStatus}
          </p>
        )}
      </EnterpriseCard>

      {/* Upload Card */}
      <EnterpriseCard
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        }
        title="Upload Agent Logs"
        subtitle="Import activity from JSON file"
        variant="default"
      >
        <div className="flex items-center space-x-3">
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition-all"
          />
        </div>
        {uploadStatus && (
          <p className={`text-sm mt-2 ${uploadStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
            {uploadStatus}
          </p>
        )}
      </EnterpriseCard>

      {/* Replay Modal */}
      {replayAction && (
        <ReplayModal action={replayAction} onClose={() => setReplayAction(null)} />
      )}
    </div>
  );
};

export default AgentActivityFeed;