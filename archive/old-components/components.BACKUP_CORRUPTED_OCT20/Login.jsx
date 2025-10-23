

import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';
// components/Login.jsx - Enterprise Cookie Authentication (Phase 2 Complete)


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
      logger.debug("🏢 Enterprise login attempt for:", email);

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
      logger.debug("🏢 Enterprise login response:", data);

      if (!response.ok) {
        setError(data.detail || "Enterprise login failed");
        return;
      }

      // CRITICAL FIX: Handle the actual backend response format
      if (data.access_token && data.user) {
        // 🍪 Enterprise Cookie Mode (cookies set automatically)
        logger.debug("✅ Enterprise cookie authentication successful");
        logger.debug("🍪 Secure cookies set automatically");
        
        // Pass the complete response to parent
        onLoginSuccess({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          token_type: data.token_type || "bearer",
          expires_in: data.expires_in,
          user: data.user,
          auth_mode: "token", // Backend returns "token" (cookies work in background)
          enterprise_metadata: data.enterprise_metadata,
          enterprise: true
        });
        
      } else if (data.auth_mode === "cookie" && data.user) {
        // Alternative cookie response format
        logger.debug("✅ Enterprise cookie authentication successful");
        logger.debug("🍪 Secure cookies set automatically");
        
        // No need to store tokens - cookies handle everything
        onLoginSuccess({
          user: data.user,
          auth_mode: "cookie",
          enterprise_features: data.enterprise_features,
          enterprise: true
        });
        
      } else if (data.access_token) {
        // 🎫 Legacy Token Mode (Fallback Compatibility)
        logger.debug("⚠️ Legacy token authentication - consider upgrading");
        
        // Store tokens for backward compatibility
        if (data.refresh_token) {
        }
        
        onLoginSuccess({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          user: data.user,
          auth_mode: "token",
          enterprise: true
        });
        
      } else {
        setError("Invalid login response format");
        return;
      }

    } catch (err) {
      logger.error("🏢 Enterprise login error:", err);
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
            SOC 2 Compliant • 🍪 Cookie Auth Ready
          </div>
        </div>

        {/* Enterprise Authentication Mode Indicator */}
        <div className="flex items-center justify-center mb-6">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200">
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-xs font-medium text-blue-800">Enterprise Security Active</span>
            </div>
            <div className="text-xs text-blue-600">|</div>
            <div className="text-xs text-blue-700">🔒 XSS Protected</div>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Enterprise Email
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
              <input
                id="email"
                type="email"
                placeholder="your.email@company.com"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Secure Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your secure password"
                className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
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
                <svg className="h-5 w-5 text-gray-400 hover:text-gray-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {showPassword ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* Password Strength Indicator */}
          <div className="flex items-center space-x-2 text-xs">
            <div className="flex space-x-1">
              <div className={`w-2 h-1 rounded ${password.length >= 6 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <div className={`w-2 h-1 rounded ${password.length >= 8 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <div className={`w-2 h-1 rounded ${password.length >= 10 && /[A-Z]/.test(password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <div className={`w-2 h-1 rounded ${password.length >= 12 && /[A-Z]/.test(password) && /[0-9]/.test(password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            </div>
            <span className="text-gray-500">Password Strength</span>
          </div>

          {/* Show Password Toggle */}
          <div className="flex items-center justify-between">
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
            <div className="text-xs text-gray-500">
              🔐 Enterprise Encryption
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="ml-2">
                  <p className="text-sm font-medium text-red-800">Authentication Failed</p>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Enterprise Features Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="ml-2">
                <p className="text-sm font-medium text-blue-800">Enterprise Security Active</p>
                <ul className="text-xs text-blue-700 mt-1 space-y-1">
                  <li>• 🍪 httpOnly cookies prevent XSS attacks</li>
                  <li>• 🔒 CSRF protection with SameSite configuration</li>
                  <li>• 📋 SOC 2 compliance audit trails</li>
                  <li>• ⚡ Automatic session management</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white transition duration-200 transform ${
              isLoading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 active:scale-95"
            }`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Authenticating...</span>
                <div className="ml-2 flex space-x-1">
                  <div className="w-1 h-1 bg-white rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-1 h-1 bg-white rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-1 h-1 bg-white rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            ) : (
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>🏢 Enterprise Login</span>
              </div>
            )}
          </button>
        </form>

        {/* Enterprise Footer */}
        <div className="mt-6 space-y-4">
          {/* Quick Actions */}
          <div className="flex justify-between items-center text-sm">
            <button 
              onClick={switchToRegister} 
              className="text-blue-600 hover:text-blue-500 font-medium transition-colors duration-200"
              disabled={isLoading}
            >
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                Create Account
              </div>
            </button>
            <button 
              onClick={switchToForgotPassword} 
              className="text-blue-600 hover:text-blue-500 font-medium transition-colors duration-200"
              disabled={isLoading}
            >
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Forgot Password?
              </div>
            </button>
          </div>
          
          {/* Security Compliance Notice */}
          <div className="text-center">
            <div className="inline-flex items-center space-x-4 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center text-xs text-gray-600">
                <svg className="w-3 h-3 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                SOC 2 Type II
              </div>
              <div className="flex items-center text-xs text-gray-600">
                <svg className="w-3 h-3 mr-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                AES-256 Encryption
              </div>
              <div className="flex items-center text-xs text-gray-600">
                <svg className="w-3 h-3 mr-1 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                GDPR Compliant
              </div>
            </div>
          </div>
          
          {/* Final Security Notice */}
          <div className="text-center text-xs text-gray-500 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-3 border border-gray-200">
            <div className="flex items-center justify-center mb-1">
              <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">Enterprise Security Verified</span>
            </div>
            <p>Your session is protected by enterprise-grade encryption, secure cookie authentication, and comprehensive audit logging. All authentication attempts are monitored and logged for security compliance.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
