import React, { useState } from "react";

const ResetPassword = ({ token, switchToLogin }) => {
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const handleReset = async (e) => {
    e.preventDefault();
    setMessage("");

    try {
      const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage("Password reset successful. You can now login.");
      } else {
        setMessage(data.detail || "Reset failed");
      }
    } catch (err) {
      console.error(err);
      setMessage("Server error");
    }
  };

  return (
    <div className="p-8 max-w-md mx-auto bg-white shadow rounded mt-12">
      <h2 className="text-xl font-bold mb-4">Reset Password</h2>
      <form onSubmit={handleReset} className="space-y-4">
        <input
          type="password"
          className="w-full p-2 border rounded"
          placeholder="Enter new password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />
        <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded">
          Reset Password
        </button>
      </form>

      {message && <p className="mt-4 text-sm text-gray-700">{message}</p>}
      <button onClick={switchToLogin} className="mt-6 text-sm underline text-gray-600">
        Back to Login
      </button>
    </div>
  );
};

export default ResetPassword;
