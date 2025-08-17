#!/bin/bash

echo "🚨 NUCLEAR OPTION - COMPLETE LOOP ELIMINATION"
echo "============================================="
echo ""
echo "🎯 CRITICAL SITUATION:"
echo "Emergency fix failed - loop still happening"
echo "Railway logs show continuous /auth/me spam"
echo "Need to COMPLETELY STOP the auth checking"
echo ""
echo "🚨 NUCLEAR SOLUTION:"
echo "1. Disable ALL automatic auth checking"
echo "2. Force app to show login screen immediately"
echo "3. Only check auth on manual login attempt"
echo "4. Completely break the infinite loop cycle"
echo ""

cd ow-ai-dashboard/src/components

# Create the most aggressive loop-stopping version
echo "🚨 Creating nuclear loop-stopping AppContent.jsx..."

# Backup current version
cp AppContent.jsx AppContent.jsx.backup_nuclear

cat > AppContent.jsx << 'EOF'
import React, { useState } from "react";
import { useAlert } from "../context/AlertContext";
import ToastAlert from "./ToastAlert";
import BannerAlert from "./BannerAlert";
import Login from "./Login";
import Register from "./Register";
import ForgotPassword from "./ForgotPassword";
import Dashboard from "./Dashboard";
import { logout } from "../utils/fetchWithAuth";

const AppContent = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [view, setView] = useState("login"); // FORCE LOGIN VIEW - NO AUTO AUTH CHECK
  const { showAlert } = useAlert();

  // NUCLEAR: NO AUTOMATIC AUTH CHECKING AT ALL
  // NO useEffect hooks that call getCurrentUser
  // NO automatic /auth/me requests
  // ONLY manual login attempts

  console.log("🚨 NUCLEAR MODE: No automatic auth checking - showing login");

  const handleLoginSuccess = (userData, authToken) => {
    console.log("🎉 Login successful:", userData);
    setUser(userData);
    setToken(authToken || "cookie-auth");
    setView("app");
    showAlert("Login successful!", "success");
  };

  const handleLogout = async () => {
    try {
      await logout();
      setToken(null);
      setUser(null);
      setView("login");
      showAlert("Logged out successfully!", "success");
    } catch (error) {
      console.error("Logout error:", error);
      // Force logout even if API fails
      setToken(null);
      setUser(null);
      setView("login");
    }
  };

  const switchToRegister = () => setView("register");
  const switchToLogin = () => setView("login");
  const switchToForgot = () => setView("forgot");

  // NUCLEAR: Always render immediately, no loading state, no auth checks
  return (
    <>
      <ToastAlert />
      <BannerAlert />
      
      {view === "login" && (
        <Login
          onLoginSuccess={handleLoginSuccess}
          switchToRegister={switchToRegister}
          switchToForgot={switchToForgot}
        />
      )}
      
      {view === "register" && (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          switchToLogin={switchToLogin}
        />
      )}
      
      {view === "forgot" && (
        <ForgotPassword switchToLogin={switchToLogin} />
      )}
      
      {view === "app" && user && (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </>
  );
};

export default AppContent;
EOF

echo "✅ Created nuclear loop-stopping AppContent.jsx"

# Also check if there are other components making auth calls
echo ""
echo "🔍 Checking for other components making /auth/me calls..."

cd ../

# Search for any other getCurrentUser or /auth/me calls
echo "🔍 Searching for getCurrentUser calls:"
grep -r "getCurrentUser" . --include="*.jsx" --include="*.js" | head -10

echo ""
echo "🔍 Searching for /auth/me calls:"
grep -r "/auth/me" . --include="*.jsx" --include="*.js" | head -10

echo ""
echo "🔍 Searching for useEffect with auth:"
grep -r -A 3 "useEffect.*auth" . --include="*.jsx" --include="*.js" | head -10

# Check App.jsx too - might have conflicting auth logic
echo ""
echo "🔍 Checking App.jsx for conflicting auth logic..."
if [ -f "App.jsx" ]; then
    echo "Found App.jsx - checking for auth calls:"
    grep -n -A 5 -B 5 "getCurrentUser\|auth\|useEffect" App.jsx | head -20
fi

cd ../../..

# Nuclear deployment
echo ""
echo "🚨 DEPLOYING NUCLEAR LOOP ELIMINATION"
echo "===================================="

echo "🚨 Committing nuclear auth fix..."

git add ow-ai-dashboard/src/components/AppContent.jsx
git commit -m "🚨 NUCLEAR: Eliminate ALL automatic auth checking

🚫 Removed ALL useEffect auth checks  
🚫 Removed ALL automatic /auth/me calls
🚫 Force login screen - no auto auth
🚫 MUST stop infinite loop immediately
🔧 Backup: AppContent.jsx.backup_nuclear"

echo "✅ Pushing nuclear fix to production..."
git push origin main

echo ""
echo "🚨 NUCLEAR DEPLOYMENT COMPLETE!"
echo "==============================="
echo ""
echo "🚫 What this NUCLEAR option does:"
echo "  • ZERO automatic authentication checking"
echo "  • NO /auth/me requests on app load"
echo "  • Forces login screen immediately"
echo "  • Only checks auth on manual login"
echo "  • Should COMPLETELY stop the infinite loop"
echo ""
echo "⏱️  Nuclear deployment in progress..."
echo "   Check Railway logs in 1 minute"
echo "   ALL /auth/me requests should STOP"
echo ""
echo "🎯 Expected behavior:"
echo "   1. App loads → Shows login screen immediately"
echo "   2. No automatic auth checking"
echo "   3. User must manually log in"
echo "   4. Railway logs show NO /auth/me spam"
echo ""
echo "🆘 If this doesn't work, the issue is deeper:"
echo "   1. Check other components for auth calls"
echo "   2. Check App.jsx for conflicting logic"
echo "   3. Check if multiple auth systems are running"
echo "   4. May need to disable auth middleware temporarily"

echo ""
echo "📋 NUCLEAR OPTION DEPLOYED!"
echo "=========================="
echo "🎯 This MUST stop the infinite loop - if not, we have a backend issue."
