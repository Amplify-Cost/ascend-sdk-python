import React, { useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";
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
import { fetchWithAuth, logout } from "./utils/fetchWithAuth";

// Consistent API URL handling
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error: error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('🚨 Frontend Error Caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
            <div className="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">
              The application encountered an error. Please refresh the page or contact support.
            </p>
            <div className="space-y-2">
              <button 
                onClick={() => window.location.reload()} 
                className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Refresh Page
              </button>
              <button 
                onClick={() => this.setState({ hasError: false, error: null })} 
                className="w-full bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
              >
                Try Again
              </button>
            </div>
            <details className="mt-4 text-left">
              <summary className="cursor-pointer text-sm text-gray-500">Technical Details</summary>
              <pre className="text-xs text-red-600 mt-2 p-2 bg-red-50 rounded overflow-auto">
                {this.state.error?.toString()}
              </pre>
            </details>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const Profile = ({ user, onUpdateProfile }) => {
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
      return;
    }

    if (password && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      await onUpdateProfile({ email, password });
      setMessage("Profile updated successfully.");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError("Failed to update profile. Please try again.");
    }
  };

  return (
    <div className="text-gray-700 p-4 max-w-md mx-auto">
      <h2 className="text-xl font-semibold mb-4">Profile Settings</h2>
      
      {message && <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">{message}</div>}
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input
            type="email"
            className="w-full p-2 border rounded"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter new email"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">New Password</label>
          <input
            type="password"
            className="w-full p-2 border rounded"
            value=REDACTED-CREDENTIAL
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter new password"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">Confirm New Password</label>
          <input
            type="password"
            className="w-full p-2 border rounded"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
          />
        </div>
        
        <button
          onClick={handleUpdate}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition duration-200"
        >
          Update Profile
        </button>
      </div>
    </div>
  );
};

const App = () => {
  const [view, setView] = useState("login");
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);

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

  const renderAppContent = () => {
    console.log("🎯 Rendering tab:", activeTab);
    console.log("🎯 User role:", user?.role);
    
    try {
      switch (activeTab) {
        case "dashboard":
          return <Dashboard getAuthHeaders={getAuthHeaders} user={user} />;
        case "actions":
          return <AgentActionsPanel getAuthHeaders={getAuthHeaders} user={user} />;
        case "activity":
          return <AgentActivityFeed getAuthHeaders={getAuthHeaders} />;
        case "analytics":
          return <SecurityInsights getAuthHeaders={getAuthHeaders} />;
        case "alerts":
          return user?.role === "admin" ? (
            <AlertPanel getAuthHeaders={getAuthHeaders} user={user} />
          ) : (
            <div className="p-6 text-center">
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">🔒 Admin Access Required</h3>
                <p className="text-yellow-700">You need administrator privileges to access Security Alerts.</p>
                <p className="text-sm text-yellow-600 mt-2">Current role: {user?.role || "unknown"}</p>
              </div>
            </div>
          );
        case "rules":
          return user?.role === "admin" ? (
            <RulesPanel getAuthHeaders={getAuthHeaders} user={user} />
          ) : (
            <div className="p-6 text-center">
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">🔒 Admin Access Required</h3>
                <p className="text-yellow-700">You need administrator privileges to access Security Rules.</p>
                <p className="text-sm text-yellow-600 mt-2">Current role: {user?.role || "unknown"}</p>
              </div>
            </div>
          );
        case "authorization":
          return user?.role === "admin" ? (
            <AgentAuthorizationDashboard getAuthHeaders={getAuthHeaders} user={user} />
          ) : (
            <div className="p-6 text-center">
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">🔒 Admin Access Required</h3>
                <p className="text-yellow-700">You need administrator privileges to access the Authorization Center.</p>
                <p className="text-sm text-yellow-600 mt-2">Current role: {user?.role || "unknown"}</p>
              </div>
            </div>
          );
        case "support":
          return <SubmitActionForm getAuthHeaders={getAuthHeaders} user={user} />;
        case "profile":
          return <Profile user={user} onUpdateProfile={handleProfileUpdate} />;
        case "insights":
          return <SecurityInsights getAuthHeaders={getAuthHeaders} />;
        case "smartRules":
          return user?.role === "admin" ? (
            <SmartRuleGen getAuthHeaders={getAuthHeaders} />
          ) : (
            <div className="p-6 text-center">
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">🔒 Admin Access Required</h3>
                <p className="text-yellow-700">You need administrator privileges to access Smart Rule Generation.</p>
                <p className="text-sm text-yellow-600 mt-2">Current role: {user?.role || "unknown"}</p>
              </div>
            </div>
          );
        default:
          return <div className="p-6 text-center text-gray-500">Page not found</div>;
      }
    } catch (error) {
      console.error('Error rendering content:', error);
      return (
        <div className="p-6 text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <h3 className="font-bold">Error Loading Content</h3>
            <p>There was an error loading this section. Please try refreshing the page.</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm"
            >
              Refresh
            </button>
          </div>
        </div>
      );
    }
  };

  // Show loading screen while checking auth status
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading OW-AI...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 flex flex-col lg:flex-row">
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
              onLogout={handleLogout}
              onSupport={() => setShowSupportModal(true)}
              onNavigate={(tab) => setActiveTab(tab)}
              activeTab={activeTab}
            />
            <main className="flex-1 p-4 space-y-8 overflow-y-auto">
              <div className="text-sm text-gray-600">
                Logged in as: {user?.email} ({user?.role})
                <span className="ml-4 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                  API: {API_BASE_URL}
                </span>
              </div>
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
    </ErrorBoundary>
  );
};

export default App;