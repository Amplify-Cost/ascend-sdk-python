const API_BASE_URL = import.meta.env.VITE_API_URL;

import React, { useState } from "react";

const Login = ({ onLoginSuccess, switchToRegister, switchToForgotPassword }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false); // ✅ Added

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch("${API_BASE_URL}/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      console.log("Login response:", data);

      if (!res.ok || !data.access_token) {
        setError(data.detail || "Login failed");
        return;
      }

      localStorage.setItem("token", data.access_token);
      onLoginSuccess(data.access_token);
    } catch (err) {
      console.error("Login error:", err);
      setError("An error occurred during login");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Login to OW-AI</h2>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full px-4 py-2 border rounded-lg"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type={showPassword ? "text" : "password"} // ✅ toggle visibility
            placeholder="Password"
            className="w-full px-4 py-2 border rounded-lg"
            value=REDACTED-CREDENTIAL
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="text-sm text-gray-600 flex items-center">
            <input
              type="checkbox"
              id="showPassword"
              className="mr-2"
              checked={showPassword}
              onChange={() => setShowPassword(!showPassword)}
            />
            <label htmlFor="showPassword">Show Password</label>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Login
          </button>
        </form>
        <div className="flex justify-between mt-4 text-sm text-gray-600">
          <button onClick={switchToRegister} className="hover:underline">
            Register
          </button>
          <button onClick={switchToForgotPassword} className="hover:underline">
            Forgot Password?
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
