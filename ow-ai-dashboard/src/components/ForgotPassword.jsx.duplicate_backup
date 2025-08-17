// ForgotPassword.jsx
import React, { useState } from "react";

const ForgotPassword = ({ switchToLogin }) => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const API_BASE_URL = import.meta.env.VITE_API_URL;

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE_URL}/auth/request-reset`, {
        method: "POST",
        credentials: "include",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to send reset email.");
      }

      setMessage("Reset link sent! Check your email.");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Forgot Password</h2>
      <form onSubmit={handleRequestReset}>
        <input
          className="w-full p-2 border rounded mb-4"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          type="submit"
        >
          Send Reset Link
        </button>
      </form>
      {message && <p className="mt-4 text-green-600">{message}</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}
      <p className="mt-4 text-sm">
        Remembered your password?{' '}
        <button className="text-blue-600 underline" onClick={switchToLogin}>
          Go back to login
        </button>
      </p>
    </div>
  );
};

export default ForgotPassword;
