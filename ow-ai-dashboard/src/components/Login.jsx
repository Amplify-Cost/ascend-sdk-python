// components/Login.jsx - Updated for secure cookie authentication (PHASE 2)
import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

const Login = ({ onLoginSuccess, switchToRegister, switchToForgotPassword }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Enterprise: Use cookie-based authentication
      const res = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Auth-Mode": "cookie"  // Signal cookie preference
        },
        credentials: "include",  // Include cookies in request
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      console.log("Login response:", data);

      if (!res.ok) {
        setError(data.detail || "Login failed");
        return;
      }

      // Enterprise Security: Validate response
      if (data.token_type === "cookie") {
        // Cookie-based authentication successful
        // Tokens are now stored in secure httpOnly cookies
        console.log("✅ Enterprise cookie authentication successful");
        
        // Clear any legacy localStorage tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        
        // No token to pass - authentication is handled via cookies
        onLoginSuccess(null, null);
        
      } else if (data.access_token) {
        // Legacy token mode fallback
        console.log("⚠️ Fallback to legacy token authentication");
        
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        
        onLoginSuccess(data.access_token, data.refresh_token);
        
      } else {
        setError("Authentication response invalid");
        return;
      }

    } catch (err) {
      console.error("Login error:", err);
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
        {/* Enterprise Security Badge */}
        <div className="flex items-center justify-center mb-4">
          <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium flex items-center">
            <span className="mr-2">🔒</span>
            Enterprise Security Enabled
          </div>
        </div>
        
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Login to OW-AI
        </h2>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                value=REDACTED-CREDENTIAL
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="showPassword"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={showPassword}
                onChange={() => setShowPassword(!showPassword)}
                disabled={loading}
              />
              <label htmlFor="showPassword" className="ml-2 block text-sm text-gray-700">
                Show Password
              </label>
            </div>
            
            <button 
              type="button"
              onClick={switchToForgotPassword} 
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
              disabled={loading}
            >
              Forgot Password?
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              <div className="flex items-center">
                <span className="mr-2">⚠️</span>
                {error}
              </div>
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Logging in...
              </div>
            ) : (
              "Login to Enterprise Platform"
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <div className="text-sm text-gray-600 mb-3">
            Don't have an account?
          </div>
          <button 
            onClick={switchToRegister} 
            className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
            disabled={loading}
          >
            Create Enterprise Account
          </button>
        </div>
        
        {/* Enterprise Features Notice */}
        <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
          <div className="flex items-start">
            <span className="mr-2 mt-0.5">🛡️</span>
            <div>
              <div className="font-semibold mb-1">Enterprise Security Features:</div>
              <ul className="list-disc list-inside space-y-0.5 text-blue-700">
                <li>Secure httpOnly cookie authentication</li>
                <li>Automatic CSRF protection</li>
                <li>Session management and rotation</li>
                <li>SOC 2 compliant audit logging</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;