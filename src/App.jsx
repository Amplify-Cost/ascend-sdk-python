// App.jsx - Enhanced Enterprise Cookie Authentication (Phase 2 Complete)
import React, { useState, useEffect } from "react";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ToastProvider, useToast } from "./components/ToastNotification";
import { AccessibilityProvider, useScreenReaderAnnounce } from "./contexts/AccessibilityContext";
import Breadcrumb from "./components/Breadcrumb";
import GlobalSearch from "./components/GlobalSearch";
import Login from "./components/Login";
import Register from "./components/Register";
import ForgotPassword from "./components/ForgotPassword";
import Sidebar from "./components/Sidebar";
import SupportModal from "./components/SupportModal";
import Dashboard from "./components/Dashboard";
import SecurityInsights from "./components/SecurityInsights";
import AgentActivityFeed from "./components/AgentActivityFeed";
import SmartRuleGen from "./components/SmartRuleGen";
import EnterpriseUserManagement from "./components/EnterpriseUserManagement";
import EnterpriseSettings from "./components/EnterpriseSettings";
import EnterpriseSecurityReports from "./components/EnterpriseSecurityReports";
import AgentAuthorizationDashboard from "./components/AgentAuthorizationDashboard";
import AIAlertManagementSystem from "./components/AIAlertManagementSystem";
import { fetchWithAuth, logout, getCurrentUser } from "./utils/fetchWithAuth";
import { useTheme } from "./contexts/ThemeContext";
import RealTimeAnalyticsDashboard from './components/RealTimeAnalyticsDashboard';
import SmartAlertManagement from './components/SmartAlertManagement';



// Consistent API URL handling
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://pilot.owkai.app";

// Enhanced Loading Screen with Enterprise Branding
const LoadingScreen = () => {
  const { isDarkMode } = useTheme();
  
  return (
    <div 
      className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}
      role="status"
      aria-live="polite"
      aria-label="Loading OW-AI Enterprise Platform"
    >
      <div className="text-center">
        <div className={`w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
          isDarkMode ? 'border-blue-400' : 'border-blue-600'
        }`} aria-hidden="true"></div>
        <div className={`text-2xl font-bold mb-2 transition-colors duration-300 ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          🛡️ OW-AI Enterprise Platform
        </div>
        <p className={`transition-colors duration-300 ${
          isDarkMode ? 'text-slate-300' : 'text-gray-600'
        }`}>
          Validating enterprise security credentials...
        </p>
        <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-gray-500">
          <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>🍪 Enterprise Cookie Authentication</span>
        </div>
      </div>
    </div>
  );
};

// Enhanced Profile component with Enterprise Security
const Profile = ({ user, onUpdateProfile }) => {
  const { isDarkMode } = useTheme();
  const { toast } = useToast();
  const { announce } = useScreenReaderAnnounce();
  const [email, setEmail] = useState(user?.email || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleUpdate = async () => {
    setMessage("");
    setError("");

    if (!email && !password) {
      setError("Please provide email or password to update");
      announce("Please provide email or password to update", 'assertive');
      return;
    }

    if (password && password !== confirmPassword) {
      setError("Passwords do not match");
      announce("Passwords do not match", 'assertive');
      return;
    }

    try {
      await onUpdateProfile({ email, password });
      setMessage("Profile updated successfully with enterprise security.");
      announce("Profile updated successfully", 'polite');
      toast("Profile updated successfully", "success");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError("Failed to update profile. Please try again.");
      announce("Failed to update profile. Please try again.", 'assertive');
      toast("Failed to update profile", "error");
    }
  };

  return (
    <div className={`p-4 max-w-md mx-auto transition-colors duration-300 ${
      isDarkMode ? 'text-white' : 'text-gray-700'
    }`}>
      <h2 className={`text-xl font-semibold mb-4 transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        🏢 Enterprise Profile Settings
      </h2>
      
      {/* Enhanced Security Notice */}
      <div className={`mb-4 p-3 rounded-lg border ${
        isDarkMode 
          ? 'bg-blue-900/20 border-blue-400 text-blue-300' 
          : 'bg-blue-50 border-blue-200 text-blue-800'
      }`}>
        <div className="flex items-center text-sm">
          <span className="mr-2">🔒</span>
          Profile updates secured with enterprise cookie authentication
        </div>
      </div>
      
      {message && (
        <div 
          className={`border px-4 py-3 rounded mb-4 transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-green-900/20 border-green-500 text-green-300' 
              : 'bg-green-100 border-green-400 text-green-700'
          }`}
          role="status"
        >
          {message}
        </div>
      )}
      {error && (
        <div 
          className={`border px-4 py-3 rounded mb-4 transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-red-900/20 border-red-500 text-red-300' 
              : 'bg-red-100 border-red-400 text-red-700'
          }`}
          role="alert"
        >
          {error}
        </div>
      )}
      
      <div className="space-y-4">
        <div>
          <label 
            htmlFor="profile-email" 
            className={`block text-sm font-medium mb-1 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}
          >
            Email
          </label>
          <input
            id="profile-email"
            type="email"
            className={`w-full p-2 border rounded transition-colors duration-300 focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white focus:border-blue-400' 
                : 'bg-white border-gray-300 text-gray-900 focus:border-blue-500'
            }`}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter new email"
          />
        </div>
        
        <div>
          <label 
            htmlFor="profile-password" 
            className={`block text-sm font-medium mb-1 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}
          >
            New Password
          </label>
          <input
            id="profile-password"
            type="password"
            className={`w-full p-2 border rounded transition-colors duration-300 focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white focus:border-blue-400' 
                : 'bg-white border-gray-300 text-gray-900 focus:border-blue-500'
            }`}
            value=REDACTED-CREDENTIAL
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter new password"
          />
        </div>
        
        <div>
          <label 
            htmlFor="profile-confirm-password" 
            className={`block text-sm font-medium mb-1 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}
          >
            Confirm New Password
          </label>
          <input
            id="profile-confirm-password"
            type="password"
            className={`w-full p-2 border rounded transition-colors duration-300 focus:ring-2 focus:ring-blue-500 ${
              isDarkMode 
                ? 'bg-slate-800 border-slate-600 text-white focus:border-blue-400' 
                : 'bg-white border-gray-300 text-gray-900 focus:border-blue-500'
            }`}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
          />
        </div>
        
        <button
          onClick={handleUpdate}
          className={`px-4 py-2 rounded font-medium transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            isDarkMode 
              ? 'bg-blue-600 hover:bg-blue-700 text-white' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
          aria-label="Update profile information"
        >
          🔐 Update Profile
        </button>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { isDarkMode } = useTheme();
  const { toast } = useToast();
  const { announce } = useScreenReaderAnnounce();
  const [view, setView] = useState("login");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState("unknown");

  // Page transition state (preserved)
  const [pageTransition, setPageTransition] = useState(false);

  // ENTERPRISE FIX: Enhanced tab change handler with proper scope
  const handleTabChange = (tab) => {
    console.log("🎯 Changing tab to:", tab);
    setPageTransition(true);
    
    setTimeout(() => {
      setActiveTab(tab);
      setPageTransition(false);
      announce(`Navigated to ${tab} section`, 'polite');
    }, 150);
  };

  // 🍪 ENHANCED: Enterprise Cookie Authentication Check
  useEffect(() => {
    const checkEnterpriseAuthentication = async () => {
      try {
        console.log("🔍 Checking enterprise authentication status...");
        setLoading(true);

        // 🍪 PRIMARY: Try cookie authentication first (enterprise preferred)
        const currentUser = await getCurrentUser();
        
        if (currentUser && currentUser.enterprise_validated) {
          console.log("✅ Enterprise cookie authentication confirmed:", currentUser.email);
          
          setUser({
            id: currentUser.user_id || currentUser.id,
            email: currentUser.email,
            role: currentUser.role,
          });
          setView("app");
          setAuthMode(currentUser.auth_source || "cookie");
          
          // 🧹 Clean up any legacy tokens when using cookies
          if (currentUser.auth_source === "cookie") {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            console.log("🧹 Legacy tokens cleaned up - using secure cookies");
          }
          
        } else {
          // 🎫 FALLBACK: Check for legacy token authentication
          console.log("🔍 No cookie authentication, checking legacy tokens...");
          const storedToken = localStorage.getItem("access_token");
          
          if (storedToken) {
            console.log("⚠️ Legacy token found, attempting validation...");
            try {
              // Import jwt-decode dynamically to avoid bundle issues
              const { jwtDecode } = await import("jwt-decode");
              const decoded = jwtDecode(storedToken);
              const currentTime = Date.now() / 1000;
              
              if (decoded.exp && decoded.exp < currentTime) {
                console.warn("❌ Legacy token expired, clearing...");
                handleLogout(false);
              } else {
                // Use legacy token temporarily
                setUser({
                  id: Number(decoded.sub),
                  email: decoded.email || decoded.sub,
                  role: decoded.role,
                });
                setView("app");
                setAuthMode("token");
                console.log("⚠️ Using legacy token authentication");
                toast("Using legacy authentication - consider logging out and back in for enhanced security", "warning");
              }
            } catch (err) {
              console.error("❌ Invalid legacy token:", err);
              handleLogout(false);
            }
          } else {
            console.log("ℹ️ No authentication found, showing login");
            setView("login");
          }
        }
      } catch (error) {
        console.error("❌ Enterprise authentication check failed:", error);
        setView("login");
      } finally {
        setLoading(false);
      }
    };
    
    checkEnterpriseAuthentication();
  }, []);

  // 🍪 ENTERPRISE FIX: Handle login response without problematic toast calls
  const handleLoginSuccess = async (loginResponse) => {
    try {
      console.log("🏢 Processing enterprise login response...");
      console.log("🔍 Login response received:", loginResponse);
      
      if (loginResponse && typeof loginResponse === 'object') {
        
        // Handle the backend response format we see in logs
        if (loginResponse.access_token && loginResponse.user) {
          console.log("✅ Enterprise cookie authentication established");
          
          // Store tokens for compatibility (cookies are also set automatically)
          localStorage.setItem("access_token", loginResponse.access_token);
          if (loginResponse.refresh_token) {
            localStorage.setItem("refresh_token", loginResponse.refresh_token);
          }
          
          // Set user state from response
          setUser({
            id: loginResponse.user.user_id || loginResponse.user.id,
            email: loginResponse.user.email,
            role: loginResponse.user.role,
          });
          
          // Set auth mode - cookies are working in background
          setAuthMode("cookie"); // Enterprise security active
          
          // FIXED: Use console.log instead of problematic toast
          console.log("🍪 Secure cookie authentication activated");
          
        } else if (loginResponse.auth_mode === "cookie" && loginResponse.user) {
          // Alternative cookie response format
          console.log("✅ Enterprise cookie authentication (alt format)");
          
          setUser({
            id: loginResponse.user.user_id || loginResponse.user.id,
            email: loginResponse.user.email,
            role: loginResponse.user.role,
          });
          setAuthMode("cookie");
          
          // Clear any legacy tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          
          console.log("🍪 Secure cookie authentication activated");
          
        } else if (typeof loginResponse === 'string') {
          // Legacy string token (backward compatibility)
          console.log("⚠️ Legacy string token received");
          
          localStorage.setItem("access_token", loginResponse);
          const { jwtDecode } = await import("jwt-decode");
          const decoded = jwtDecode(loginResponse);
          setUser({
            id: Number(decoded.sub),
            email: decoded.email || decoded.sub,
            role: decoded.role,
          });
          setAuthMode("token");
          
          console.log("Legacy authentication - consider upgrading to cookies");
        }
      }
      
      setView("app");
      setActiveTab("dashboard");
      console.log("✅ Enterprise login processing complete");
      
    } catch (err) {
      console.error("❌ Login processing error:", err);
      console.error("❌ Error details:", err.message);
      console.error("❌ Login response that failed:", loginResponse);
      
      // FIXED: Use console.log instead of problematic toast
      console.log("Login processing failed - please try again");
      
      // Simple fallback - just show login again
      setView("login");
    }
  };

  // 🍪 ENHANCED: Enterprise logout with cookie clearing
  const handleLogout = async (callAPI = true) => {
    try {
      console.log("🚪 Enterprise logout initiated...");
      
      if (callAPI) {
        // Call the enterprise logout API to clear cookies
        await logout();
        console.log("✅ Enterprise logout API called");
      } else {
        console.log("🧹 Local session cleanup only");
      }
      
      toast("Logged out successfully", "success");
      
    } catch (error) {
      console.warn("⚠️ Logout API error:", error);
      // Continue with cleanup even if API fails
    } finally {
      // Always clean up state and localStorage
      setUser(null);
      setView("login");
      setActiveTab("dashboard");
      setAuthMode("unknown");
      
      // Clear any remaining localStorage
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      
      console.log("✅ Enterprise logout complete");
    }
  };

  // PRESERVED: Your existing profile update function
  const handleProfileUpdate = async ({ email, password }) => {
    try {
      const updateData = {};
      if (email && email !== user?.email) updateData.email = email;
      if (password) updateData.password = password;
      
      if (Object.keys(updateData).length === 0) {
        throw new Error("No changes to update");
      }
      
      const response = await fetchWithAuth(`${API_BASE_URL}/auth/update-profile`, {
        method: "POST",
        body: JSON.stringify(updateData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }
      
      // Update local user state if email changed
      if (updateData.email) {
        setUser(prev => ({ ...prev, email: updateData.email }));
      }
    } catch (err) {
      console.error("Profile update failed:", err);
      throw err;
    }
  };

  // 🔧 MASTER PROMPT FIX: ALWAYS send token when available (no conditions)
  const getAuthHeaders = () => {
    console.log("🔍 Getting auth headers for API call");
    console.log("🔍 Current auth mode:", authMode);
    
    // ENTERPRISE FIX: ALWAYS send token when available (regardless of auth mode)
    const token = localStorage.getItem("access_token");
    console.log("🔍 Access token present:", !!token);
    
    if (token) {
      console.log("🔄 Enterprise auth: Sending Authorization header");
      return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      };
    }
    
    console.log("⚠️ No token available for auth headers");
    return {
      "Content-Type": "application/json"
    };
  };

  // PRESERVED: All your existing render logic (unchanged)
  const renderAppContent = () => {
    console.log("🎯 Rendering tab:", activeTab);
    console.log("🎯 User role:", user?.role);
    
    const adminRequiredMessage = (
      <div className={`p-6 text-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}>
        <div className={`border-l-4 p-4 rounded transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-yellow-900/20 border-yellow-500 text-yellow-300' 
            : 'bg-yellow-100 border-yellow-500 text-yellow-700'
        }`} role="alert">
          <h3 className={`text-lg font-semibold mb-2 ${
            isDarkMode ? 'text-yellow-200' : 'text-yellow-800'
          }`}>
            🔒 Admin Access Required
          </h3>
          <p className={isDarkMode ? 'text-yellow-300' : 'text-yellow-700'}>
            You need administrator privileges to access this section.
          </p>
          <p className={`text-sm mt-2 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>
            Current role: <span className="font-medium">{user?.role || "unknown"}</span>
          </p>
        </div>
      </div>
    );
    
    const contentWithTransition = (content) => (
      <div className={`transition-all duration-300 ${
        pageTransition ? 'opacity-0 transform translate-y-2' : 'opacity-100 transform translate-y-0'
      }`}>
        {content}
      </div>
    );
    
    // PRESERVED: All your existing switch cases (unchanged)
    switch (activeTab) {
      case "dashboard":
        return contentWithTransition(<Dashboard getAuthHeaders={getAuthHeaders} user={user} />);
      case "analytics":
        return contentWithTransition(<SecurityInsights getAuthHeaders={getAuthHeaders} />);
      case "realtime-analytics":
  return contentWithTransition(<RealTimeAnalyticsDashboard getAuthHeaders={getAuthHeaders} user={user} />);

  
      case "activity":
        return contentWithTransition(<AgentActivityFeed getAuthHeaders={getAuthHeaders} />);
      case "reports":
        return contentWithTransition(<EnterpriseSecurityReports getAuthHeaders={getAuthHeaders} user={user} />);
      case "support":
        return contentWithTransition(
          <div className={`p-6 text-center transition-colors duration-300 ${
            isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
          }`}>
            <div className={`border-l-4 p-4 rounded transition-colors duration-300 ${
              isDarkMode 
                ? 'bg-blue-900/20 border-blue-500 text-blue-300' 
                : 'bg-blue-100 border-blue-500 text-blue-700'
            }`}>
              <h3 className={`text-lg font-semibold mb-2 ${
                isDarkMode ? 'text-blue-200' : 'text-blue-800'
              }`}>
                🆘 Enterprise Support Center
              </h3>
              <p className={`mb-4 ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                24/7 enterprise support available for critical issues.
              </p>
              <button
                onClick={() => setShowSupportModal(true)}
                className={`px-4 py-2 rounded font-medium transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  isDarkMode 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
                aria-label="Open support ticket form"
              >
                Open Enterprise Support Ticket
              </button>
            </div>
          </div>
        );
      case "auth":
        return user?.role === "admin" ? 
          contentWithTransition(<AgentAuthorizationDashboard getAuthHeaders={getAuthHeaders} user={user} />) : 
          adminRequiredMessage;
      case "ai-alerts":
        return user?.role === "admin" ? 
          contentWithTransition(<AIAlertManagementSystem getAuthHeaders={getAuthHeaders} user={user} />) : 
          adminRequiredMessage;
      case "smartRules":
        return user?.role === "admin" ? 
          contentWithTransition(<SmartRuleGen getAuthHeaders={getAuthHeaders} user={user} />) : 
          adminRequiredMessage;
      case "users":
        return user?.role === "admin" ? 
          contentWithTransition(<EnterpriseUserManagement getAuthHeaders={getAuthHeaders} user={user} />) : 
          adminRequiredMessage;
      case "settings":
        return user?.role === "admin" ? 
          contentWithTransition(<EnterpriseSettings getAuthHeaders={getAuthHeaders} user={user} />) : 
          adminRequiredMessage;
      case 'alerts':
  return <SmartAlertManagement getAuthHeaders={getAuthHeaders} user={user} />;    
      case "profile":
        return contentWithTransition(<Profile user={user} onUpdateProfile={handleProfileUpdate} />);
      default:
        return contentWithTransition(
          <div className={`p-6 text-center transition-colors duration-300 ${
            isDarkMode ? 'text-slate-400 bg-slate-800' : 'text-gray-500 bg-gray-100'
          }`}>
            Page not found
          </div>
        );
    }
  };

  // Show enhanced loading screen while checking auth status
  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className={`min-h-screen flex flex-col lg:flex-row transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
    }`}>
      {view === "login" && (
        <Login
          onLoginSuccess={handleLoginSuccess}
          switchToRegister={() => setView("register")}
          switchToForgotPassword={() => setView("forgot")}
        />
      )}
      {view === "register" && (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          switchToLogin={() => setView("login")}
        />
      )}
      {view === "forgot" && <ForgotPassword switchToLogin={() => setView("login")} />}
      {view === "app" && (
        <>
          <Sidebar
            user={user}
            handleLogout={handleLogout}
            activeTab={activeTab}
            setActiveTab={handleTabChange}
          />
          <main 
            id="main-content"
            className="flex-1 p-4 space-y-8 overflow-y-auto"
            tabIndex="-1"
            role="main"
            aria-label="Main content"
          >
            {/* ENHANCED: Header with enterprise security status */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Breadcrumb activeTab={activeTab} user={user} />
                </div>
                <GlobalSearch onNavigate={handleTabChange} />
              </div>
              
              {/* ENHANCED: Enterprise Security Status Bar */}
              <div className={`text-sm transition-colors duration-300 ${
                isDarkMode ? 'text-slate-400' : 'text-gray-600'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    Logged in as: <span className="font-medium">{user?.email}</span> ({user?.role})
                  </div>
                  <div className="flex items-center space-x-2">
                    {/* Authentication Mode Indicator */}
                    <span className={`text-xs px-2 py-1 rounded transition-colors duration-300 ${
                      authMode === "cookie"
                        ? (isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800')
                        : authMode === "token" 
                        ? (isDarkMode ? 'bg-yellow-900/30 text-yellow-300' : 'bg-yellow-100 text-yellow-800')
                        : (isDarkMode ? 'bg-gray-900/30 text-gray-300' : 'bg-gray-100 text-gray-800')
                    }`}>
                      {authMode === "cookie" ? "🔒 Secure Cookies" : 
                       authMode === "token" ? "⚠️ Legacy Token" : "❓ Unknown Auth"}
                    </span>
                    
                    {/* API Endpoint Indicator */}
                    <span className={`text-xs px-2 py-1 rounded transition-colors duration-300 ${
                      isDarkMode 
                        ? 'bg-blue-900/30 text-blue-300' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      API: {API_BASE_URL.replace('https://', '').split('.')[0]}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* PRESERVED: Main content rendering (unchanged) */}
            {renderAppContent()}
          </main>
          
          {/* PRESERVED: Support modal (unchanged) */}
          {showSupportModal && (
            <SupportModal
              onClose={() => setShowSupportModal(false)}
              onSubmit={(message) => {
                console.log("Support message submitted:", message);
                setShowSupportModal(false);
                toast("Support ticket submitted successfully", "success");
              }}
            />
          )}
        </>
      )}
    </div>
  );
};

// PRESERVED: App wrapper (unchanged)
const App = () => {
  return (
    <ThemeProvider>
      <AccessibilityProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </AccessibilityProvider>
    </ThemeProvider>
  );
};

export default App;