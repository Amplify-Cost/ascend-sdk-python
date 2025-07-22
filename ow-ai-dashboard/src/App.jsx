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
import Analytics from "./components/Analytics";
import SubmitActionForm from "./components/SubmitActionForm";
import AlertPanel from "./components/AlertPanel";
import SmartRuleGen from "./components/SmartRuleGen";
import RulesPanel from "./components/RulesPanel";
import SecurityInsights from "./components/SecurityInsights";
import { fetchWithAuth } from "./utils/fetchWithAuth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

const Profile = ({ user, onUpdateProfile }) => {
  const [email, setEmail] = useState(user?.email || "");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleUpdate = () => {
    if (!email && !password) return;
    onUpdateProfile({ email, password });
    setMessage("Profile updated successfully.");
    setPassword("");
  };

  return (
    <div className="text-gray-700 p-4 max-w-md mx-auto">
      <h2 className="text-xl font-semibold mb-4">Profile Settings</h2>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          type="email"
          className="w-full p-2 border rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">New Password</label>
        <input
          type="password"
          className="w-full p-2 border rounded"
          value=REDACTED-CREDENTIAL
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <button
        onClick={handleUpdate}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Update Profile
      </button>
      {message && <p className="text-green-600 mt-2 text-sm">{message}</p>}
    </div>
  );
};

const App = () => {
  const [view, setView] = useState("login");
  const [token, setToken] = useState(localStorage.getItem("access_token") || "");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    if (storedToken) {
      try {
        const decoded = jwtDecode(storedToken);
        const currentTime = Date.now() / 1000;
        if (decoded.exp && decoded.exp < currentTime) {
          console.warn("Token expired. Logging out.");
          handleLogout();
        } else {
          setUser({
            id: Number(decoded.sub),
            email: decoded.email || decoded.sub,
            role: decoded.role,
          });
          setToken(storedToken);
          setView("app");
          const timeUntilExpiry = (decoded.exp - currentTime) * 1000;
          const logoutTimer = setTimeout(() => {
            console.warn("Token has expired. Logging out.");
            handleLogout();
          }, timeUntilExpiry);
          return () => clearTimeout(logoutTimer);
        }
      } catch (err) {
        console.error("Invalid token", err);
        localStorage.removeItem("access_token");
        setToken("");
        setUser(null);
        setView("login");
      }
    }
  }, []);

  const handleLoginSuccess = (receivedToken) => {
    localStorage.setItem("access_token", receivedToken);
    const decoded = jwtDecode(receivedToken);
    setUser({
      id: decoded.sub,
      email: decoded.email || decoded.sub,
      role: decoded.role,
    });
    setToken(receivedToken);
    setView("app");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken("");
    setUser(null);
    setView("login");
  };

  const handleProfileUpdate = async ({ email, password }) => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/auth/update-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) throw new Error("Failed to update profile");
    } catch (err) {
      console.error("Profile update failed", err);
    }
  };

  const getAuthHeaders = () => ({ Authorization: `Bearer ${token}` });

  const renderAppContent = () => {
    console.log("🎯 Rendering tab:", activeTab);
    console.log("🎯 User role:", user?.role);
    
    switch (activeTab) {
      case "dashboard":
        console.log("📊 Loading Dashboard");
        return <Dashboard getAuthHeaders={getAuthHeaders} user={user} />;
      case "actions":
        console.log("⚡ Loading Agent Actions");
        return <AgentActionsPanel getAuthHeaders={getAuthHeaders} user={user} />;
      case "activity":
        console.log("📋 Loading Activity Feed");
        return <AgentActivityFeed getAuthHeaders={getAuthHeaders} />;
      case "analytics":
        console.log("📈 Loading Analytics");
        return <Analytics getAuthHeaders={getAuthHeaders} />;
      case "alerts":
        console.log("🚨 Loading Alerts - User role:", user?.role);
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
        console.log("📋 Loading Rules - User role:", user?.role);
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
      case "support":
        console.log("💬 Loading Submit Action");
        return <SubmitActionForm getAuthHeaders={getAuthHeaders} user={user} />;
      case "profile":
        console.log("👤 Loading Profile");
        return <Profile user={user} onUpdateProfile={handleProfileUpdate} />;
      case "insights":
        console.log("🔍 Loading Security Insights");
        return <SecurityInsights getAuthHeaders={getAuthHeaders} />;
      case "smartRules":
        console.log("🧠 Loading Smart Rules - User role:", user?.role);
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
        console.log("❓ Unknown tab:", activeTab);
        return <div className="p-6 text-center text-gray-500">Page not found</div>;
    }
  };

  return (
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
            <div className="text-sm text-gray-600">Logged in as: {user?.email} ({user?.role})</div>
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

export default App;