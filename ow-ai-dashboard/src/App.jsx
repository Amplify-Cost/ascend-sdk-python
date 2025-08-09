// App.jsx - Updated for secure cookie authentication (PHASE 2)
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

// Consistent API URL handling
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Enhanced Loading Screen
const LoadingScreen = () => {
  const { isDarkMode } = useTheme();
  
  return (
    <div 
      className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}
      role="status"
      aria-live="polite"
      aria-label="Loading OW-AI Platform"
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
          Loading secure enterprise interface...
        </p>
        <div className="mt-4 text-xs px-3 py-1 bg-green-100 text-green-800 rounded-full inline-block">
          🔒 Cookie-Based Authentication Active
        </div>
      </div>
    </div>
  );
};

// Profile component (updated for cookie auth)
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
      setMessage("Profile updated successfully.");
      announce("Profile updated successfully", 'polite');
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError("Failed to update profile. Please try again.");
      announce("Failed to update profile. Please try again.", 'assertive');
    }
  };

  return (
    <div className={`p-4 max-w-md mx-auto transition-colors duration-300 ${
      isDarkMode ? 'text-white' : 'text-gray-700'
    }`}>
      <h2 className={`text-xl font-semibold mb-4 transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        Enterprise Profile Settings
      </h2>
      
      {/* Security Notice */}
      <div className={`mb-4 p-3 rounded-lg border ${
        isDarkMode 
          ? 'bg-blue-900/20 border-blue-400 text-blue-300' 
          : 'bg-blue-50 border-blue-200 text-blue-800'
      }`}>
        <div className="flex items-center text-sm">
          <span className="mr-2">🔒</span>
          Profile updates are secured with enterprise authentication
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
          Update Profile
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
  const [authMode, setAuthMode] = useState("cookie");

  // Page transition state
  const [pageTransition, setPageTransition] = useState(false);

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        console.log("🔍 Checking enterprise authentication status...");
        
        // Try to get current user info via cookie authentication
        const currentUser = await getCurrentUser();
        
        if (currentUser) {
          console.log("✅ Enterprise authentication verified:", currentUser.email);
          setUser({
            id: currentUser.id,
            email: currentUser.email,
            role: currentUser.role,
          });
          setView("app");
          setAuthMode("cookie");
          
          // Clear any legacy localStorage tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          
        } else {
          // Check for legacy token authentication
          const storedToken = localStorage.getItem("access_token");
          
          if (storedToken) {
            console.log("⚠️ Legacy token found, attempting migration...");
            try {
              // Try to decode the legacy token
              const { jwtDecode } = await import("jwt-decode");
              const decoded = jwtDecode(storedToken);
              const currentTime = Date.now() / 1000;
              
              if (decoded.exp && decoded.exp < currentTime) {
                console.warn("Legacy token expired, clearing...");
                handleLogout();
              } else {
                // Use legacy token temporarily
                setUser({
                  id: Number(decoded.sub),
                  email: decoded.email || decoded.sub,
                  role: decoded.role,
                });
                setView("app");
                setAuthMode("token");
                console.log("⚠️ Using legacy token authentication (consider upgrading)");
              }
            } catch (err) {
              console.error("Invalid legacy token:", err);
              handleLogout();
            }
          } else {
            console.log("No authentication found, showing login");
          }
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuthStatus();
  }, []);

  const handleLoginSuccess = async (receivedToken = null, refreshToken = null) => {
    try {
      if (receivedToken) {
        // Legacy token mode
        console.log("⚠️ Legacy token authentication");
        localStorage.setItem("access_token", receivedToken);
        if (refreshToken) {
          localStorage.setItem("refresh_token", refreshToken);
        }
        
        const { jwtDecode } = await import("jwt-decode");
        const decoded = jwtDecode(receivedToken);
        setUser({
          id: Number(decoded.sub),
          email: decoded.email || decoded.sub,
          role: decoded.role,
        });
        setAuthMode("token");
      } else {
        // Cookie mode - get user info from API
        console.log("✅ Enterprise cookie authentication");
        const currentUser = await getCurrentUser();
        
        if (currentUser) {
          setUser({
            id: currentUser.id,
            email: currentUser.email,
            role: currentUser.role,
          });
          setAuthMode("cookie");
        } else {
          throw new Error("Failed to retrieve user information");
        }
      }
      
      setView("app");
      console.log("✅ Login successful");
    } catch (err) {
      console.error("Login processing error:", err);
      handleLogout();
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.warn("Logout error:", error);
    } finally {
      setUser(null);
      setView("login");
      setActiveTab("dashboard");
      setAuthMode("cookie");
      console.log("✅ Logged out successfully");
    }
  };

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

  // For legacy components that still expect getAuthHeaders
  const getAuthHeaders = () => {
    if (authMode === "cookie") {
      return {}; // No headers needed for cookie auth
    }
    // Legacy token fallback
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // Enhanced tab navigation with accessibility
  const handleTabChange = (newTab) => {
    if (newTab === activeTab) return;
    
    setPageTransition(true);
    announce(`Navigating to ${newTab.replace(/([A-Z])/g, ' $1').toLowerCase()}`, 'polite');
    
    setTimeout(() => {
      setActiveTab(newTab);
      setPageTransition(false);
      
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.focus();
      }
    }, 150);
  };

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
    
    switch (activeTab) {
      case "dashboard":
        return contentWithTransition(<Dashboard getAuthHeaders={getAuthHeaders} user={user} />);
      case "analytics":
        return contentWithTransition(<SecurityInsights getAuthHeaders={getAuthHeaders} />);
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

  // Show loading screen while checking auth status
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
            {/* Header with search and breadcrumbs */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Breadcrumb activeTab={activeTab} user={user} />
                </div>
                <GlobalSearch onNavigate={handleTabChange} />
              </div>
              
              <div className={`text-sm transition-colors duration-300 ${
                isDarkMode ? 'text-slate-400' : 'text-gray-600'
              }`}>
                Logged in as: <span className="font-medium">{user?.email}</span> ({user?.role})
                <span className={`ml-4 text-xs px-2 py-1 rounded transition-colors duration-300 ${
                  authMode === "cookie"
                    ? (isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800')
                    : (isDarkMode ? 'bg-yellow-900/30 text-yellow-300' : 'bg-yellow-100 text-yellow-800')
                }`}>
                  {authMode === "cookie" ? "🔒 Secure Cookies" : "⚠️ Legacy Token"}
                </span>
                <span className={`ml-2 text-xs px-2 py-1 rounded transition-colors duration-300 ${
                  isDarkMode 
                    ? 'bg-blue-900/30 text-blue-300' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  API: {API_BASE_URL}
                </span>
              </div>
            </div>
            
            {/* Main content */}
            {renderAppContent()}
          </main>
          
          {showSupportModal && (
            <SupportModal
              onClose={() => setShowSupportModal(false)}
              onSubmit={(message) => {
                console.log("Support message submitted:", message);
                setShowSupportModal(false);
              }}
            />
          )}
        </>
      )}
    </div>
  );
};

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