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
import RulesPanel from "./components/RulesPanel"; // ✅ NEW import
import { fetchWithAuth } from "./utils/fetchWithAuth";
import SecurityInsights from "./components/SecurityInsights";


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
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
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
        localStorage.removeItem("token");
        setToken("");
        setUser(null);
        setView("login");
      }
    }
  }, []);

  const handleLoginSuccess = (receivedToken) => {
    localStorage.setItem("token", receivedToken);
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
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setView("login");
  };

  const handleProfileUpdate = async ({ email, password }) => {
    try {
      const res = await fetchWithAuth(`${import.meta.env.VITE_API_URL}/auth/update-profile`, {
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
    switch (activeTab) {
      case "dashboard":
        return <Dashboard getAuthHeaders={getAuthHeaders} user={user} />;
      case "actions":
        return <AgentActionsPanel getAuthHeaders={getAuthHeaders} user={user} />;
      case "activity":
        return <AgentActivityFeed getAuthHeaders={getAuthHeaders} />;
      case "analytics":
        return <Analytics getAuthHeaders={getAuthHeaders} />;
      case "alerts":
        return user?.role === "admin" ? <AlertPanel getAuthHeaders={getAuthHeaders} /> : null;
      case "rules":
        return user?.role === "admin" ? <RulesPanel getAuthHeaders={getAuthHeaders} /> : null; // ✅ Real panel
      case "support":
        return <SubmitActionForm getAuthHeaders={getAuthHeaders} user={user} />;
      case "profile":
        return <Profile user={user} onUpdateProfile={handleProfileUpdate} />;
      case "insights":
        return <SecurityInsights getAuthHeaders={getAuthHeaders} />;

      case "smartRules":
        return user?.role === "admin" ? <SmartRuleGen getAuthHeaders={getAuthHeaders} /> : null;
      default:
        return null;
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


