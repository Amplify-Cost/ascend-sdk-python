const API_BASE_URL = import.meta.env.VITE_API_URL;

import React, { useState } from "react";

const Register = ({ onRegisterSuccess, switchToLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("user"); // 🆕 Role state
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const registerRes = await fetch("${API_BASE_URL}/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role }), // 🆕 Include role
      });

      const registerData = await registerRes.json();

      if (!registerRes.ok) {
        setError(registerData.detail || "Registration failed");
        return;
      }

      // Auto-login after successful registration
      const loginRes = await fetch("${API_BASE_URL}/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const loginData = await loginRes.json();

      if (!loginRes.ok) {
        setError("Registered but login failed. Please try logging in manually.");
        return;
      }

      onRegisterSuccess(loginData.access_token);
    } catch (err) {
      console.error("Registration error:", err);
      setError("An error occurred during registration");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Register for OW-AI</h2>
        <form onSubmit={handleRegister} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full px-4 py-2 border rounded-lg"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            className="w-full px-4 py-2 border rounded-lg"
            value=REDACTED-CREDENTIAL
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm Password"
            className="w-full px-4 py-2 border rounded-lg"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          {/* 🆕 Role Dropdown */}
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg bg-white text-gray-700"
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>

          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit" className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition">
            Register & Login
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
