import React, { useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";
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
import AgentActionsPanel from "./components/AgentActionsPanel";
import AgentActivityFeed from "./components/AgentActivityFeed";
import Dashboard from "./components/Dashboard";
import SubmitActionForm from "./components/SubmitActionForm";
import AlertPanel from "./components/AlertPanel";
import SmartRuleGen from "./components/SmartRuleGen";
import RulesPanel from "./components/RulesPanel";
import SecurityInsights from "./components/SecurityInsights";
import AgentAuthorizationDashboard from "./components/AgentAuthorizationDashboard";
import AIAlertManagementSystem from "./components/AIAlertManagementSystem";
import EnterpriseUserManagement from "./components/EnterpriseUserManagement";
import EnterpriseSettings from "./components/EnterpriseSettings";
import { fetchWithAuth, logout } from "./utils/fetchWithAuth";
import { useTheme } from "./contexts/ThemeContext";

// Consistent API URL handling
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Enhanced Loading Screen (accessibility added to existing)
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
          🛡️ OW-AI Platform
        </div>
        <p className={`transition-colors duration-300 ${
          isDarkMode ? 'text-slate-300' : 'text-gray-600'
        }`}>
          Loading OW-AI...
        </p>
        {/* Hidden live region for status updates */}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          Loading enterprise security platform. Please wait.
        </div>
      </div>
    </div>
  );
};

// Original Profile component with accessibility enhancements
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
        Profile Settings
      </h2>
      
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
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);

  // Page transition state (accessibility enhancement)
  const [pageTransition, setPageTransition] = useState(false);

  // Check for existing token on app load
  useEffect(() => {
    const checkAuthStatus = () => {
      const storedToken = localStorage.getItem("access_token");
      
      if (storedToken) {
        try {
          const decoded = jwtDecode(storedToken);
          const currentTime = Date.now() / 1000;
          
          // Check if token is expired
          if (decoded.exp && decoded.exp < currentTime) {
            console.warn("Stored token is expired. Logging out.");
            handleLogout();
          } else {
            // Token is valid, set user state
            setUser({
              id: Number(decoded.sub),
              email: decoded.email || decoded.sub,
              role: decoded.role,
            });
            setToken(storedToken);
            setView("app");
            
            // Set up automatic logout when token expires
            const timeUntilExpiry = (decoded.exp - currentTime) * 1000;
            const logoutTimer = setTimeout(() => {
              console.warn("Token has expired. Logging out.");
              handleLogout();
            }, timeUntilExpiry);
            
            return () => clearTimeout(logoutTimer);
          }
        } catch (err) {
          console.error("Invalid token found:", err);
          handleLogout();
        }
      }
      
      setLoading(false);
    };
    
    checkAuthStatus();
  }, []);

  const handleLoginSuccess = (receivedToken, refreshToken = null) => {
    try {
      // Store tokens
      localStorage.setItem("access_token", receivedToken);
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }
      
      // Decode and set user info
      const decoded = jwtDecode(receivedToken);
      setUser({
        id: Number(decoded.sub),
        email: decoded.email || decoded.sub,
        role: decoded.role,
      });
      setToken(receivedToken);
      setView("app");
      
      console.log("✅ Login successful");
    } catch (err) {
      console.error("Login token processing error:", err);
      handleLogout();
    }
  };

  const handleLogout = () => {
    logout();
    setToken("");
    setUser(null);
    setView("login");
    setActiveTab("dashboard");
    console.log("✅ Logged out successfully");
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

  const getAuthHeaders = () => {
    return { Authorization: `Bearer ${token}` };
  };

  // Enhanced tab navigation with accessibility
  const handleTabChange = (newTab) => {
    if (newTab === activeTab) return;
    
    setPageTransition(true);
    announce(`Navigating to ${newTab.replace(/([A-Z])/g, ' $1').toLowerCase()}`, 'polite');
    
    setTimeout(() => {
      setActiveTab(newTab);
      setPageTransition(false);
      
      // Focus management - focus main content after navigation
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
        return contentWithTransition(<SecurityInsights getAuthHeaders={getAuthHeaders} />);
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
                🆘 Support Center
              </h3>
              <p className={`mb-4 ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                Need help? Contact our support team.
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
                Open Support Ticket
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
                  isDarkMode 
                    ? 'bg-green-900/30 text-green-300' 
                    : 'bg-green-100 text-green-800'
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