// components/Login.jsx - Enterprise Cookie Authentication (Phase 2)
import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

const Login = ({ onLoginSuccess, switchToRegister, switchToForgotPassword }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      console.log("🏢 Enterprise login attempt for:", email);

      // Enterprise cookie authentication request
      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Enterprise-Client": "OW-AI-Platform",
          "X-Auth-Mode": "cookie", // 🍪 Request cookie authentication
          "X-Platform-Version": "1.0.0"
        },
        credentials: "include", // 🍪 Enable cookie handling
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });

      const data = await response.json();
      console.log("🏢 Enterprise login response:", data);

      if (!response.ok) {
        setError(data.detail || "Enterprise login failed");
        return;
      }

      // Handle different authentication modes
      if (data.auth_mode === "cookie") {
        // 🍪 Enterprise Cookie Mode (Preferred)
        console.log("✅ Enterprise cookie authentication successful");
        console.log("🍪 Secure cookies set automatically");
        
        // No need to store tokens - cookies handle everything
        onLoginSuccess({
          user: data.user,
          auth_mode: "cookie",
          enterprise: true
        });
        
      } else if (data.access_token) {
        // 🎫 Legacy Token Mode (Fallback Compatibility)
        console.log("⚠️ Legacy token authentication - consider upgrading");
        
        // Store tokens for backward compatibility
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        
        onLoginSuccess({
          access_token: data.access_token,
          user: data.user,
          auth_mode: "token",
          enterprise: true
        });
        
      } else {
        setError("Invalid login response format");
        return;
      }

    } catch (err) {
      console.error("🏢 Enterprise login error:", err);
      setError("Network error - please check your connection");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md border border-gray-200">
        
        {/* Enterprise Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-lg mb-4">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">OW-AI Enterprise</h2>
          <p className="text-gray-600 text-sm mt-1">Secure Authentication Portal</p>
        </div>

        {/* Enterprise Security Badge */}
        <div className="flex items-center justify-center mb-6">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            SOC 2 Compliant
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Enterprise Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="your.email@company.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your secure password"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200 pr-10"
                value=REDACTED-CREDENTIAL
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {showPassword ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* Show Password Toggle */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="showPassword"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={showPassword}
              onChange={() => setShowPassword(!showPassword)}
              disabled={isLoading}
            />
            <label htmlFor="showPassword" className="ml-2 block text-sm text-gray-700">
              Show Password
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="ml-2 text-sm text-red-600">{error}</p>
              </div>
            </div>
          )}

          {/* Login Button */}
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white transition duration-200 ${
              isLoading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            }`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Authenticating...
              </div>
            ) : (
              "🏢 Enterprise Login"
            )}
          </button>
        </form>

        {/* Enterprise Footer */}
        <div className="mt-6 space-y-3">
          <div className="flex justify-between items-center text-sm">
            <button 
              onClick={switchToRegister} 
              className="text-blue-600 hover:text-blue-500 font-medium"
              disabled={isLoading}
            >
              Create Account
            </button>
            <button 
              onClick={switchToForgotPassword} 
              className="text-blue-600 hover:text-blue-500 font-medium"
              disabled={isLoading}
            >
              Forgot Password?
            </button>
          </div>
          
          {/* Security Notice */}
          <div className="text-center text-xs text-gray-500 bg-gray-50 rounded p-2">
            🔒 Your session is protected by enterprise-grade encryption and secure cookie authentication
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;