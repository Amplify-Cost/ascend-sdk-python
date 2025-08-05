import React, { useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ToastProvider, useToast } from "./components/ToastNotification";
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

// Enhanced Loading Component
const LoadingScreen = () => {
  const { isDarkMode } = useTheme();
  
  return (
    <div className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
    }`}>
      <div className="text-center">
        <div className={`w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
          isDarkMode ? 'border-blue-400' : 'border-blue-600'
        }`}></div>
        <div className={`text-2xl font-bold mb-2 transition-colors duration-300 ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          🛡️ OW-AI Platform
        </div>
        <p className={`transition-colors duration-300 ${
          isDarkMode ? 'text-slate-300' : 'text-gray-600'
        }`}>
          Initializing enterprise security systems...
        </p>
        <div className="mt-4 flex items-center justify-center space-x-1">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full animate-pulse ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-600'
              }`}
              style={{ animationDelay: `${i * 0.3}s` }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
};

const Profile = ({ user, onUpdateProfile }) => {
  const { isDarkMode } = useTheme();
  const { toast } = useToast();
  const [email, setEmail] = useState(user?.email || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpdate = async () => {
    if (!email && !password) {
      toast.warning("Please provide email or password to update");
      return;
    }

    if (password && password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await onUpdateProfile({ email, password });
      toast.success("Profile updated successfully!");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      toast.error("Failed to update profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`p-6 max-w-md mx-auto transition-colors duration-300 ${
      isDarkMode ? 'text-white' : 'text-gray-900'
    }`}>
      <div className={`p-6 rounded-xl border transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-slate-700 border-slate-600' 
          : 'bg-white border-gray-300 shadow-sm'
      }`}>
        <h2 className={`text-xl font-semibold mb-6 transition-colors duration-300 ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          👤 Profile Settings
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}>
              Email Address
            </label>
            <input
              type="email"
              className={`w-full p-3 border rounded-lg transition-all duration-300 focus:ring-2 focus:ring-blue-500 ${
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
            <label className={`block text-sm font-medium mb-2 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}>
              New Password
            </label>
            <input
              type="password"
              className={`w-full p-3 border rounded-lg transition-all duration-300 focus:ring-2 focus:ring-blue-500 ${
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
            <label className={`block text-sm font-medium mb-2 transition-colors duration-300 ${
              isDarkMode ? 'text-slate-200' : 'text-gray-700'
            }`}>
              Confirm New Password
            </label>
            <input
              type="password"
              className={`w-full p-3 border rounded-lg transition-all duration-300 focus:ring-2 focus:ring-blue-500 ${
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
            disabled={loading}
            className={`w-full px-4 py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
              isDarkMode 
                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Updating...</span>
              </div>
            ) : (
              'Update Profile'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { isDarkMode } = useTheme();
  const { toast } = useToast();
  const [view, setView] = useState("login");
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);

  // Page transition state
  const [pageTransition, setPageTransition] = useState(false);

  // Enhanced tab navigation with transitions
  const handleTabChange = (newTab) => {
    if (newTab === activeTab) return;
    
    setPageTransition(true);
    setTimeout(() => {
      setActiveTab(newTab);
      setPageTransition(false);
      // Show success toast for admin features
      if (['auth', 'ai-alerts', 'smartRules', 'users', 'settings'].includes(newTab)) {
        toast.info(`Accessing ${newTab.replace(/([A-Z])/g, ' $1').toLowerCase()}...`, 'Admin Feature');
      }
    }, 150);
  };

  // Check for existing token on app load
  useEffect(() => {
    const checkAuthStatus = () => {
      const storedToken = localStorage.getItem("access_token");
      
      if (storedToken) {
        try {
          const decoded = jwtDecode(storedToken);
          const currentTime = Date.now() / 1000;
          
          if (decoded.exp && decoded.exp < currentTime) {
            console.warn("Stored token is expired. Logging out.");
            handleLogout();
            toast.warning("Session expired. Please log in again.");
          } else {
            setUser({
              id: Number(decoded.sub),
              email: decoded.email || decoded.sub,
              role: decoded.role,
            });
            setToken(storedToken);
            setView("app");
            toast.success(`Welcome back, ${decoded.email || 'User'}!`);
            
            const timeUntilExpiry = (decoded.exp - currentTime) * 1000;
            const logoutTimer = setTimeout(() => {
              console.warn("Token has expired. Logging out.");
              handleLogout();
              toast.error("Session expired. Please log in again.");
            }, timeUntilExpiry);
            
            return () => clearTimeout(logoutTimer);
          }
        } catch (err) {
          console.error("Invalid token found:", err);
          handleLogout();
          toast.error("Invalid session. Please log in again.");
        }
      }
      
      setLoading(false);
    };
    
    checkAuthStatus();
  }, []);

  const handleLoginSuccess = (receivedToken, refreshToken = null) => {
    try {
      localStorage.setItem("access_token", receivedToken);
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }
      
      const decoded = jwtDecode(receivedToken);
      const userData = {
        id: Number(decoded.sub),
        email: decoded.email || decoded.sub,
        role: decoded.role,
      };
      
      setUser(userData);
      setToken(receivedToken);
      setView("app");
      
      toast.success(`Welcome to OW-AI, ${userData.email}!`, 'Login Successful');
      console.log("✅ Login successful");
    } catch (err) {
      console.error("Login token processing error:", err);
      handleLogout();
      toast.error("Login failed. Please try again.");
    }
  };

  const handleLogout = () => {
    logout();
    setToken("");
    setUser(null);
    setView("login");
    setActiveTab("dashboard");
    toast.info("You have been logged out successfully.");
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

  const renderAppContent = () => {
    console.log("🎯 Rendering tab:", activeTab);
    console.log("🎯 User role:", user?.role);
    
    const adminRequiredMessage = (
      <div className={`p-6 text-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}>
        <div className={`max-w-md mx-auto p-6 rounded-xl border transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-yellow-900/20 border-yellow-500 text-yellow-300' 
            : 'bg-yellow-50 border-yellow-200 text-yellow-700'
        }`}>
          <div className="text-4xl mb-4">🔒</div>
          <h3 className={`text-lg font-semibold mb-2 ${
            isDarkMode ? 'text-yellow-200' : 'text-yellow-800'
          }`}>
            Admin Access Required
          </h3>
          <p className={isDarkMode ? 'text-yellow-300' : 'text-yellow-700'}>
            You need administrator privileges to access this section.
          </p>
          <p className={`text-sm mt-2 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>
            Current role: <span className="font-medium">{user?.role || "unknown"}</span>
          </p>
          <button
            onClick={() => handleTabChange('dashboard')}
            className={`mt-4 px-4 py-2 rounded-lg transition-all duration-200 hover:scale-105 ${
              isDarkMode 
                ? 'bg-yellow-600 hover:bg-yellow-700 text-white' 
                : 'bg-yellow-500 hover:bg-yellow-600 text-white'
            }`}
          >
            Return to Dashboard
          </button>
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
            <div className={`max-w-md mx-auto p-6 rounded-xl border transition-colors duration-300 ${
              isDarkMode 
                ? 'bg-blue-900/20 border-blue-500 text-blue-300' 
                : 'bg-blue-50 border-blue-200 text-blue-700'
            }`}>
              <div className="text-4xl mb-4">🆘</div>
              <h3 className={`text-lg font-semibold mb-2 ${
                isDarkMode ? 'text-blue-200' : 'text-blue-800'
              }`}>
                Support Center
              </h3>
              <p className={`mb-4 ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                Need help? Our support team is here to assist you.
              </p>
              <button
                onClick={() => {
                  setShowSupportModal(true);
                  toast.info("Opening support ticket form...");
                }}
                className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105 ${
                  isDarkMode 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
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
            <div className="text-4xl mb-4">🤷‍♂️</div>
            <p className="text-lg">Page not found</p>
            <button
              onClick={() => handleTabChange('dashboard')}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        );
    }
  };

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
          <main className="flex-1 p-4 space-y-4 overflow-y-auto">
            {/* Header with search and breadcrumbs */}
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <Breadcrumb activeTab={activeTab} user={user} />
                <div className={`text-sm transition-colors duration-300 ${
                  isDarkMode ? 'text-slate-400' : 'text-gray-600'
                }`}>
                  Logged in as: <span className="font-medium">{user?.email}</span> ({user?.role})
                  <span className={`ml-4 text-xs px-2 py-1 rounded transition-colors duration-300 ${
                    isDarkMode 
                      ? 'bg-green-900/30 text-green-300' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    API: Connected
                  </span>
                </div>
              </div>
              <GlobalSearch onNavigate={handleTabChange} />
            </div>
            
            {/* Main content */}
            <div className="min-h-[calc(100vh-8rem)]">
              {renderAppContent()}
            </div>
          </main>
          
          {showSupportModal && (
            <SupportModal
              onClose={() => {
                setShowSupportModal(false);
                toast.info("Support ticket form closed.");
              }}
              onSubmit={(message) => {
                console.log("Support message submitted:", message);
                setShowSupportModal(false);
                toast.success("Support ticket submitted successfully!", "We'll get back to you soon");
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
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ThemeProvider>
  );
};

export default App;