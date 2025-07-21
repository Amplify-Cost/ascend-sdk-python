import React, { useState } from "react";

const Profile = ({ username, role }) => {
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const handleChangePassword = async () => {
    if (!newPassword) return;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: username, new_password: newPassword }),
      });

      if (!res.ok) {
        throw new Error("Failed to reset password");
      }

      setMessage("✅ Password updated successfully!");
      setNewPassword("");
    } catch (err) {
      console.error(err);
      setMessage("❌ Failed to update password.");
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Profile</h2>
      <div className="space-y-2 text-sm">
        <div>
          <strong>Username:</strong> {username}
        </div>
        <div>
          <strong>Role:</strong> {role}
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Change Password</h3>
        <input
          type="password"
          className="border p-2 rounded w-full mb-2"
          placeholder="New password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
        <button
          onClick={handleChangePassword}
          className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700 text-sm w-full"
        >
          Update Password
        </button>

        {message && (
          <div className="mt-2 text-center text-sm text-green-600">{message}</div>
        )}
      </div>
    </div>
  );
};

export default Profile;