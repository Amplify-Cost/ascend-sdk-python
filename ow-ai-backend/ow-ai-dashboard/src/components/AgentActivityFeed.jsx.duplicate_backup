import React, { useEffect, useState } from "react";
import ReplayModal from "./ReplayModal";

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
  const itemsPerPage = 5;

  // ✅ Added fallback URL
  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

  const fetchActivity = async () => {
    try {
      console.log("🔍 Fetching from:", API_BASE_URL); // Debug log
      const url =
        selectedRisk === "all"
          ? `${API_BASE_URL}/agent-activity`
          : `${API_BASE_URL}/agent-activity?risk=${selectedRisk}`;
      
      console.log("📡 Full URL:", url); // Debug log
      
      const res = await fetch(url, { credentials: "include",
        headers: getAuthHeaders() });
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
        method: "POST",
        credentials: "include",
        credentials: "include",
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
        method: "POST",
        credentials: "include",
        credentials: "include",
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
        method: "POST",
        credentials: "include",
        credentials: "include",
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

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Agent Activity Feed</h2>
      
      {/* Debug info */}
      <div className="mb-2 text-xs text-gray-500">
        API URL: {API_BASE_URL}
      </div>

      <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-4 md:space-y-0 mb-4">
        <div>
          <label className="mr-2 text-sm font-medium">Filter by Risk:</label>
          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="p-2 border border-gray-300 rounded"
          >
            <option value="all">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <input
          type="text"
          placeholder="Search agent, tool, or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="p-2 border border-gray-300 rounded w-full"
        />
      </div>

      {loading && <p className="text-sm text-gray-500">Loading activity...</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {!loading && filteredActivities.length === 0 && !error && (
        <p className="text-sm text-gray-500">No activity found.</p>
      )}

      <div className="space-y-4">
        {paginatedActivities.map((activity) => (
          <div
            key={activity.id}
            className="border border-gray-200 rounded-lg p-4 hover:shadow transition"
          >
            <div className="text-sm text-gray-700">
              <p><strong>Agent:</strong> <span className="text-blue-600">{activity.agent_id}</span></p>
              <p><strong>Action:</strong> {activity.action_type || "—"}</p>
              <p><strong>Tool:</strong> {activity.tool_name || "—"}</p>
              <p><strong>Description:</strong> {activity.description || "—"}</p>
              <p><strong>Risk:</strong> {activity.risk_level || "—"}</p>
              <p><strong>LLM Summary:</strong> {activity.summary || <span className="italic text-gray-400">No summary</span>}</p>
              {activity.is_false_positive && (
                <p className="text-xs text-yellow-600 font-semibold">⚠ Marked as False Positive</p>
              )}
              <button
                onClick={() => toggleFalsePositive(activity.id)}
                className="mt-2 text-xs text-blue-500 underline hover:text-blue-700"
              >
                {activity.is_false_positive ? "Unmark False Positive" : "Mark as False Positive"}
              </button>
              <button
                onClick={() => setReplayAction(activity)}
                className="mt-2 ml-4 text-xs text-green-600 underline hover:text-green-800"
              >
                🔁 Replay Action
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {new Date(activity.timestamp * 1000).toLocaleString()}
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center mt-6 space-x-2">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i + 1}
              onClick={() => setCurrentPage(i + 1)}
              className={`px-3 py-1 rounded text-sm border ${
                currentPage === i + 1 ? "bg-blue-500 text-white" : "bg-white text-gray-800"
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}

      {replayAction && (
        <ReplayModal action={replayAction} onClose={() => setReplayAction(null)} />
      )}

      <div className="mt-10 border-t pt-6">
        <h3 className="text-md font-semibold text-gray-700 mb-2">Need help? Submit a message:</h3>
        <textarea
          className="w-full border border-gray-300 rounded p-2 text-sm"
          rows={4}
          value={supportMessage}
          onChange={(e) => setSupportMessage(e.target.value)}
          placeholder="Describe your issue or ask a question..."
        />
        <button
          onClick={handleSupportSubmit}
          className="mt-2 bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700"
        >
          Submit
        </button>
        {supportStatus && <p className="text-xs mt-2">{supportStatus}</p>}
      </div>

      <div className="mt-8">
        <h3 className="text-md font-semibold text-gray-700 mb-2">Upload Agent Logs (JSON):</h3>
        <input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          className="text-sm"
        />
        {uploadStatus && <p className="text-xs mt-2">{uploadStatus}</p>}
      </div>
    </div>
  );
};

export default AgentActivityFeed;