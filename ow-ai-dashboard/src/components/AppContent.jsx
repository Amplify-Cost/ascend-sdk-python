import React, { useEffect, useState } from "react";
import { useAlert } from "../context/AlertContext";
import ToastAlert from "./ToastAlert";
import BannerAlert from "./BannerAlert";
import Login from "./Login";
import Register from "./Register";
import ForgotPassword from "./ForgotPassword";
import Dashboard from "./Dashboard";
import { getCurrentUser, logout } from "../utils/fetchWithAuth";

const AppContent = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [view, setView] = useState("loading"); // loading, login, register, forgot, app
  const [authChecked, setAuthChecked] = useState(false); // Prevent multiple auth checks
  const { showAlert } = useAlert();

  // EMERGENCY: Single auth check with loop prevention
  useEffect(() => {
    if (authChecked) return; // Prevent multiple checks
    
    let isMounted = true;
    
    const checkAuthOnce = async () => {
      try {
        console.log("🔍 Checking authentication (ONE TIME ONLY)...");
        
        const user = await getCurrentUser();
        
        if (isMounted && user) {
          console.log("✅ User authenticated:", user);
          setUser({
            id: user.user_id || user.id,
            email: user.email,
            role: user.role,
          });
          setToken("cookie-auth");
          setView("app");
        } else if (isMounted) {
          console.log("❌ No authentication - showing login");
          setView("login");
        }
      } catch (error) {
        console.log("🚫 Auth check failed - showing login:", error.message);
        if (isMounted) {
          setView("login");
        }
      } finally {
        if (isMounted) {
          setAuthChecked(true); // Mark as checked to prevent loops
        }
      }
    };

    // Only check auth once
    checkAuthOnce();
    
    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array - run once only

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
      setAuthChecked(false); // Allow auth check on next login
      showAlert("Logged out successfully!", "success");
    } catch (error) {
      console.error("Logout error:", error);
      // Force logout even if API fails
      setToken(null);
      setUser(null);
      setView("login");
      setAuthChecked(false);
    }
  };

  const switchToRegister = () => setView("register");
  const switchToLogin = () => setView("login");
  const switchToForgot = () => setView("forgot");

  // Show loading only briefly
  if (view === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

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
