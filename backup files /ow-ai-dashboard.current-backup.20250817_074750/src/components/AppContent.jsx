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
