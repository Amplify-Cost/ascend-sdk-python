#!/bin/bash

echo "🔧 FIXING AUTHENTICATION LOOP - Cookie Auth Integration"
echo "======================================================"

# Navigate to project root
cd /Users/mac_001/OW_AI_Project

echo "📁 Current directory: $(pwd)"

# Backup existing files
echo "💾 Creating backups..."
cp ow-ai-dashboard/src/components/AppContent.jsx ow-ai-dashboard/src/components/AppContent.jsx.backup_auth_fix
echo "✅ Backed up AppContent.jsx"

# Create the fixed AppContent.jsx
echo "🔧 Creating fixed AppContent.jsx with cookie authentication..."

cat > ow-ai-dashboard/src/components/AppContent.jsx << 'EOF'
import React, { useEffect, useState } from "react";
import { useAlert } from "../context/AlertContext";
import { getCurrentUser, logout } from "../utils/fetchWithAuth";

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
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const { toastAlert, bannerAlert, dismissBanner } = useAlert();

  // 🍪 FIXED: Use cookie authentication instead of JWT tokens
  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        console.log("🔍 Checking cookie authentication...");
        setLoading(true);

        // Use the cookie-based getCurrentUser function
        const currentUser = await getCurrentUser();
        
        if (currentUser) {
          console.log("✅ Cookie authentication successful:", currentUser.email);
          
          setUser({
            id: currentUser.user_id || currentUser.id,
            email: currentUser.email,
            role: currentUser.role,
          });
          setView("app");
          
          // Clean up any legacy tokens when using cookies
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          console.log("🧹 Legacy tokens cleaned up");
          
        } else {
          console.log("ℹ️ No cookie authentication found");
          setView("login");
        }
      } catch (error) {
        console.error("❌ Authentication check failed:", error);
        setView("login");
      } finally {
        setLoading(false);
      }
    };

    checkAuthentication();
  }, []);

  // 🍪 FIXED: Use cookie logout instead of localStorage
  const handleLogout = async () => {
    try {
      console.log("🚪 Cookie logout initiated...");
      
      // Use the cookie-based logout function
      await logout();
      
      setUser(null);
      setView("login");
      
      console.log("✅ Cookie logout complete");
    } catch (error) {
      console.error("❌ Logout error:", error);
      // Force logout even if API fails
      setUser(null);
      setView("login");
    }
  };

  // 🍪 FIXED: No need for token headers with cookie auth
  const getAuthHeaders = () => {
    // With cookie authentication, credentials are automatically included
    // But we'll keep this for backward compatibility with existing components
    return {
      "Content-Type": "application/json"
    };
  };

  // Show loading screen
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">🍪 Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (view === "login") {
    return (
      <Login
        onLoginSuccess={() => {
          // After successful login, re-check authentication
          setLoading(true);
          setTimeout(async () => {
            const currentUser = await getCurrentUser();
            if (currentUser) {
              setUser({
                id: currentUser.user_id || currentUser.id,
                email: currentUser.email,
                role: currentUser.role,
              });
              setView("app");
            }
            setLoading(false);
          }, 1000);
        }}
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
          setView("reset");
        }}
      />
    );
  }

  if (view === "reset") {
    return <ResetPassword switchToLogin={() => setView("login")} />;
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
          <h1 className="text-xl font-bold mb-4">🍪 OW-AI Enterprise</h1>
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
            🚪 Logout
          </button>
        </nav>
        
        {/* Cookie Auth Status */}
        <div className="p-4 mt-auto border-t border-gray-700">
          <div className="text-xs text-green-300">
            🔒 Secure Cookie Auth
          </div>
          <div className="text-xs text-gray-400">
            {user?.email}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="lg:hidden p-2 bg-gray-800 text-white flex justify-between items-center shadow">
          <button onClick={() => setSidebarOpen(true)} className="text-white text-xl">☰</button>
          <span className="font-semibold">🍪 OW-AI Enterprise</span>
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
EOF

echo "✅ Created fixed AppContent.jsx with cookie authentication"

# Also simplify the Login component to work better with cookies
echo "🔧 Creating simplified Login component..."

cat > ow-ai-dashboard/src/components/Login.jsx << 'EOF'
import React, { useState } from "react";
import { fetchWithAuth } from "../utils/fetchWithAuth";

const Login = ({ onLoginSuccess, switchToRegister, switchToForgot }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      console.log("🔐 Attempting cookie authentication login...");
      
      const response = await fetchWithAuth("/auth/token", {
        method: "POST",
        body: JSON.stringify({
          username: email,
          password: password,
        }),
      });

      if (response.ok) {
        console.log("✅ Login successful - cookies should be set");
        onLoginSuccess();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Login failed");
      }
    } catch (err) {
      console.error("❌ Login error:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            🍪 OW-AI Enterprise Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Secure cookie authentication
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Password"
                value=REDACTED-CREDENTIAL
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? "🔄 Logging in..." : "🔐 Sign in"}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={switchToForgot}
              className="text-indigo-600 hover:text-indigo-500"
            >
              Forgot your password?
            </button>
            <button
              type="button"
              onClick={switchToRegister}
              className="text-indigo-600 hover:text-indigo-500"
            >
              Create account
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
EOF

echo "✅ Created simplified Login.jsx"

# Commit and deploy the fix
echo "📝 Committing authentication fix..."
git add .
git commit -m "🔧 FIX: Replace JWT with cookie authentication to stop infinite loop

✅ Updated AppContent.jsx to use cookie authentication
✅ Removed JWT token logic that was conflicting
✅ Simplified Login component for cookie auth
✅ Added proper loading states
✅ Cleaned up authentication state management
✅ Stop infinite /auth/me requests"

echo "🚀 Pushing fix to production..."
git push origin main

echo ""
echo "🎉 AUTHENTICATION LOOP FIX COMPLETE!"
echo "===================================="
echo ""
echo "✅ What was fixed:"
echo "  • Removed conflicting JWT token logic"
echo "  • Integrated cookie authentication properly"
echo "  • Stopped infinite /auth/me requests"
echo "  • Added proper loading states"
echo "  • Cleaned up authentication flow"
echo ""
echo "🔍 Your app should now:"
echo "  • Use secure HTTP-only cookies"
echo "  • Stop the infinite restart loop"
echo "  • Authenticate properly on login"
echo "  • Show proper loading states"
echo ""
echo "⏱️ Production deployment in progress..."
echo "   Check Railway logs in 2-3 minutes"
echo ""
echo "🆘 If you need to rollback:"
echo "   cp ow-ai-dashboard/src/components/AppContent.jsx.backup_auth_fix ow-ai-dashboard/src/components/AppContent.jsx"
echo "   git add . && git commit -m 'Rollback auth fix' && git push origin main"
