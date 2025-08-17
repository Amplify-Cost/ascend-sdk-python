import React, { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import { useAlert } from "../context/AlertContext";

import ToastAlert from "./ToastAlert";
import BannerAlert from "./BannerAlert";
import Login from "./Login";
import Register from "./Register";
import ForgotPassword from "./ForgotPassword";
import ResetPassword from "./ResetPassword";
import Analytics from "./Analytics";
import AgentActionsPanel from "./AgentActionsPanel";
import RuleEditor from "./RuleEditor";
import RulesPanel from "./RulesPanel";
import AgentActionSubmitPanel from "./AgentActionSubmitPanel";
import AgentActivityFeed from "./AgentActivityFeed";
import SecurityPanel from "./SecurityPanel";
import Profile from "./Profile";
import Alerts from "./Alerts";

const AppContent = () => {
  const [view, setView] = useState("login");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { toastAlert, bannerAlert, dismissBanner } = useAlert();

  useEffect(() => {
    const storedToken = localStorage.getItem("token");

    if (storedToken) {
      try {
        const decoded = jwtDecode(storedToken);
        const currentTime = Date.now() / 1000;

        if (decoded.exp && decoded.exp < currentTime) {
          handleLogout();
        } else {
          setUser({
            id: decoded.sub,
            email: decoded.email || decoded.sub,
            role: decoded.role,
          });
          setToken(storedToken);
          setView("app");

          const timeUntilExpiry = (decoded.exp - currentTime) * 1000;
          const logoutTimer = setTimeout(() => {
            handleLogout();
          }, timeUntilExpiry);

          return () => clearTimeout(logoutTimer);
        }
      } catch (err) {
        localStorage.removeItem("token");
      }
    }
  }, []);

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    setView("login");
  };

  const getAuthHeaders = () => ({
    Authorization: `Bearer ${token}`,
  });

  if (view === "login") {
    return (
      <Login
        onLoginSuccess={() => setView("app")}
        switchToRegister={() => setView("register")}
        switchToForgot={() => setView("forgot")}
      />
    );
  }

  if (view === "register") {
    return <Register onRegisterSuccess={() => setView("login")} switchToLogin={() => setView("login")} />;
  }

  if (view === "forgot") {
    return (
      <ForgotPassword
        switchToLogin={() => setView("login")}
        switchToReset={(resetToken) => {
          setToken(resetToken);
          setView("reset");
        }}
      />
    );
  }

  if (view === "reset") {
    return <ResetPassword token={token} switchToLogin={() => setView("login")} />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      {toastAlert && <ToastAlert message={toastAlert.message} />}
      {bannerAlert && <BannerAlert message={bannerAlert.message} onClose={dismissBanner} />}

      {/* Sidebar */}
      <div
        className={`fixed z-30 inset-y-0 left-0 w-64 bg-gray-900 text-white transform ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}
      >
        <div className="p-4 flex items-center justify-between lg:block">
          <h1 className="text-xl font-bold mb-4">OW-AI</h1>
          <button className="lg:hidden text-gray-400" onClick={() => setSidebarOpen(false)}>
            ✕
          </button>
        </div>
        <nav className="space-y-1">
          {[
            { key: "dashboard", label: "Dashboard" },
            { key: "analytics", label: "Analytics" },
            { key: "alerts", label: "Alerts" },
            { key: "actions", label: "Agent Actions" },
            { key: "activity", label: "Activity Feed" },
            { key: "rules", label: "Rules" },
            { key: "editor", label: "Rule Editor" },
            { key: "submit", label: "Submit Action" },
            { key: "security", label: "Security Insights" },
            { key: "profile", label: "Profile" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full text-left px-4 py-2 rounded-md ${
                activeTab === tab.key ? "bg-gray-700" : "hover:bg-gray-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
          <button
            onClick={handleLogout}
            className="mt-4 w-full text-left px-4 py-2 text-red-300 hover:bg-red-800 rounded-md"
          >
            Logout
          </button>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="lg:hidden p-2 bg-gray-800 text-white flex justify-between items-center shadow">
          <button onClick={() => setSidebarOpen(true)} className="text-white text-xl">☰</button>
          <span className="font-semibold">OW-AI Dashboard</span>
        </div>

        {/* Scrollable content area */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {activeTab === "dashboard" && <Analytics getAuthHeaders={getAuthHeaders} />}
          {activeTab === "analytics" && <Analytics getAuthHeaders={getAuthHeaders} />}
          {activeTab === "alerts" && <Alerts getAuthHeaders={getAuthHeaders} />}
          {activeTab === "actions" && <AgentActionsPanel getAuthHeaders={getAuthHeaders} user={user} />}
          {activeTab === "activity" && <AgentActivityFeed getAuthHeaders={getAuthHeaders} />}
          {activeTab === "rules" && <RulesPanel getAuthHeaders={getAuthHeaders} />}
          {activeTab === "editor" && <RuleEditor getAuthHeaders={getAuthHeaders} />}
          {activeTab === "submit" && <AgentActionSubmitPanel getAuthHeaders={getAuthHeaders} />}
          {activeTab === "security" && <SecurityPanel getAuthHeaders={getAuthHeaders} />}
          {activeTab === "profile" && <Profile user={user} />}
        </main>
      </div>
    </div>
  );
};

export default AppContent;
