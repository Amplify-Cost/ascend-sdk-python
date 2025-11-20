import React, { useState } from "react";

import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';


const Register = ({ onRegisterSuccess, switchToLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Client-side validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          email, 
          password 
          // ✅ SECURITY FIX: Removed role field - backend assigns role
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // Handle specific validation errors
        if (data.detail && Array.isArray(data.detail)) {
          setError(data.detail.map(err => err.msg).join(", "));
        } else {
          setError(data.detail || "Registration failed");
        }
        return;
      }

      // ✅ Registration includes tokens in response
      if (data.access_token) {
        if (data.refresh_token) {
        }
        onRegisterSuccess(data.access_token, data.refresh_token);
      } else {
        setError("Registration successful but no token received");
      }

    } catch (err) {
      logger.error("Registration error:", err);
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Register for OW-AI</h2>
        
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <input
              type="email"
              placeholder="Email Address"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          
          <div>
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value=REDACTED-CREDENTIAL
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          
          <div>
            <input
              type="password"
              placeholder="Confirm Password"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {/* ✅ SECURITY FIX: Removed role selection - users are always 'user', admins assigned by system */}
          <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
            ℹ️ New accounts are created with standard user permissions. Contact an administrator for elevated access.
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating Account..." : "Register & Login"}
          </button>
        </form>
        
        <div className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <button onClick={switchToLogin} className="text-blue-600 hover:underline">
            Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default Register;
