import React, { useState } from "react";
import { fetchWithAuth } from "../utils/fetchWithAuth";

const Profile = ({ user, onUpdateProfile }) => {
  const [email, setEmail] = useState(user?.email || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://pilot.owkai.app";

  const handleUpdateProfile = async () => {
    if (!email && !newPassword) {
      setMessage({ type: "error", text: "Please provide email or password to update" });
      return;
    }

    if (newPassword && newPassword !== confirmPassword) {
      setMessage({ type: "error", text: "New passwords do not match" });
      return;
    }

    if (newPassword && newPassword.length < 8) {
      setMessage({ type: "error", text: "Password must be at least 8 characters" });
      return;
    }

    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      const updateData = {};
      if (email && email !== user?.email) updateData.email = email;
      if (newPassword) updateData.password = newPassword;

      // ✅ Using fetchWithAuth for automatic token handling
      const response = await fetchWithAuth(`${API_BASE_URL}/auth/update-profile`, {
        method: "POST",
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }

      setMessage({ type: "success", text: "Profile updated successfully!" });
      setNewPassword("");
      setConfirmPassword("");
      setCurrentPassword("");
      
      // Update parent component if email changed
      if (onUpdateProfile && updateData.email) {
        onUpdateProfile(updateData);
      }

    } catch (err) {
      console.error("Profile update failed:", err);
      setMessage({ type: "error", text: err.message || "Failed to update profile" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow-lg max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-6">Profile Settings</h2>
      
      <div className="space-y-4">
        {/* Current User Info */}
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm text-gray-600">Current User</p>
          <p className="font-medium">{user?.email}</p>
          <p className="text-sm text-gray-500">Role: {user?.role}</p>
        </div>

        {/* Email Update */}
        <div>
          <label className="block text-sm font-medium mb-1">New Email Address</label>
          <input
            type="email"
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter new email address"
            disabled={loading}
          />
        </div>

        {/* Password Update */}
        <div>
          <label className="block text-sm font-medium mb-1">New Password</label>
          <input
            type="password"
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter new password (min 8 chars)"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Confirm New Password</label>
          <input
            type="password"
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            disabled={loading}
          />
        </div>

        {/* Message Display */}
        {message.text && (
          <div className={`p-3 rounded text-sm ${
            message.type === "success" 
              ? "bg-green-100 border border-green-400 text-green-700" 
              : "bg-red-100 border border-red-400 text-red-700"
          }`}>
            {message.text}
          </div>
        )}

        <button
          onClick={handleUpdateProfile}
          disabled={loading || (!email && !newPassword)}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
        >
          {loading ? "Updating..." : "Update Profile"}
        </button>
      </div>
    </div>
  );
};

export default Profile;