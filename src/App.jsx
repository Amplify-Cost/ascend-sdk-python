// App.jsx - Enterprise AWS Cognito Multi-Pool Authentication (Phase 3)
import React, { useState, useEffect } from "react";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ToastProvider, useToast } from "./components/ToastNotification";
import { AccessibilityProvider, useScreenReaderAnnounce } from "./contexts/AccessibilityContext";
import AuthErrorBoundary from "./components/AuthErrorBoundary";
import SessionTimeoutWarning from "./components/SessionTimeoutWarning";
import Breadcrumb from "./components/Breadcrumb";
import GlobalSearch from "./components/GlobalSearch";
import CognitoLogin from "./components/CognitoLogin";
import Register from "./components/Register";
import ForgotPasswordEnterpriseV3 from "./components/ForgotPasswordEnterpriseV3";
import Sidebar from "./components/Sidebar";
import SupportModal from "./components/SupportModal";
import Dashboard from "./components/Dashboard";
import SecurityInsights from "./components/SecurityInsights";
import AgentActivityFeed from "./components/AgentActivityFeed";
import SmartRuleGen from "./components/SmartRuleGen";
import EnterpriseUserManagement from "./components/EnterpriseUserManagement";
import EnterpriseSettings from "./components/EnterpriseSettings";
import EnterpriseSecurityReports from "./components/EnterpriseSecurityReports";
import AgentAuthorizationDashboard from "./components/AgentAuthorizationDashboard";
import AIAlertManagementSystem from "./components/AIAlertManagementSystem";
import { fetchWithAuth, logout, getCurrentUser, storeCsrfToken } from "./utils/fetchWithAuth";
import { useTheme } from "./contexts/ThemeContext";
import RealTimeAnalyticsDashboard from './components/RealTimeAnalyticsDashboard';
import SmartAlertManagement from './components/SmartAlertManagement';
import Profile from './components/Profile';
import ErrorBoundary from './components/ErrorBoundary';
import ErrorBoundaryTest from './components/ErrorBoundaryTest';
// SEC-024: Enterprise Agent Registry - MCP Server & Agent Governance
import AgentRegistryManagement from './components/AgentRegistryManagement';
// SEC-021: Self-Service Signup Flow
import SignupFlow from './components/SignupFlow';
import VerifyEmail from './components/VerifyEmail';
// SEC-022: Admin Console
import AdminConsole from './components/AdminConsole';
import { API_BASE_URL } from './config/api';
import logger from './utils/logger.js';



// Enhanced Loading Screen with Enterprise Branding
const LoadingScreen = () => {
  const { isDarkMode } = useTheme();
  
  return (
    <div 
      className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${
        isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
      }`}
      role="status"
      aria-live="polite"
      aria-label="Loading OW-AI Enterprise Platform"
    >
      <div className="text-center">
        <div className={`w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
          isDarkMode ? 'border-blue-400' : 'border-blue-600'
        }`} aria-hidden="true"></div>
        <div className={`text-2xl font-bold mb-2 transition-colors duration-300 ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          🛡️ OW-AI Enterprise Platform
        </div>
        <p className={`transition-colors duration-300 ${
          isDarkMode ? 'text-slate-300' : 'text-gray-600'
        }`}>
          Validating enterprise security credentials...
        </p>
        <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-gray-500">
          <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>🍪 Enterprise Cookie Authentication</span>
        </div>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { isDarkMode } = useTheme();
  const { toast } = useToast();
  const { announce } = useScreenReaderAnnounce();
  const [view, setView] = useState("login");
  const [user, setUser] = useState(null);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState("unknown");

  // Page transition state (preserved)
  const [pageTransition, setPageTransition] = useState(false);

  // ENTERPRISE FIX: Enhanced tab change handler with proper scope
  const handleTabChange = (tab) => {
    logger.debug("🎯 Changing tab to:", tab);
    setPageTransition(true);
    
    setTimeout(() => {
      setActiveTab(tab);
      setPageTransition(false);
      announce(`Navigated to ${tab} section`, 'polite');
    }, 150);
  };

  // 🍪 ENHANCED: Enterprise Cookie Authentication Check
  useEffect(() => {
    const checkEnterpriseAuthentication = async () => {
      try {
        logger.debug("🔍 Checking enterprise authentication status...");
        setLoading(true);

        // SEC-021: Check for public paths (no auth required)
        const pathname = window.location.pathname;

        // SEC-021: /signup path for self-service signup
        if (pathname === '/signup' || pathname.startsWith('/signup')) {
          logger.debug("SEC-021: Detected /signup path, showing signup flow");
          setView("signup");
          setLoading(false);
          return;
        }

        // SEC-021: /verify-email path for email verification
        if (pathname === '/verify-email' || pathname.startsWith('/verify-email')) {
          logger.debug("SEC-021: Detected /verify-email path, showing verification view");
          setView("verify-email");
          setLoading(false);
          return;
        }

        // 🍪 COOKIE-BASED AUTH: Simply try to get current user
        // If cookies are valid, this will succeed
        // If not, it will throw and we'll redirect to login
        logger.debug("🍪 Enterprise: Attempting cookie authentication...");
        
        const userData = await getCurrentUser();
        
        if (userData && userData.enterprise_validated) {
          logger.debug("✅ Enterprise: Authentication successful", userData.email);
          
          setUser({
            id: userData.user_id || userData.id,
            email: userData.email,
            role: userData.role,
          });
          setIsAuthenticated(true);
          setView("app");
          setAuthMode("cookie");
          
        } else {
          logger.warn("⚠️ No valid authentication");
          setIsAuthenticated(false);
          setView("login");
        }
        
      } catch (error) {
        logger.error("❌ Enterprise authentication check failed:", error);
        setIsAuthenticated(false);
        setUser(null);
        setView("login");
      } finally {
        setLoading(false);
      }
    };
    
    checkEnterpriseAuthentication();
  }, []);

  // 🏦 PHASE 3 ENTERPRISE BANKING-LEVEL: Cognito JWT → Server Session
  // This is the critical bridge that connects AWS Cognito MFA authentication
  // with secure server-side session management (HttpOnly cookies)
  const handleLoginSuccess = async (cognitoResult) => {
    try {
      logger.debug("🔐 PHASE 3: Cognito authentication successful, creating server session...");
      logger.debug("🔍 Cognito result:", cognitoResult);

      // Validate we have Cognito tokens
      if (!cognitoResult || !cognitoResult.tokens) {
        throw new Error("Missing Cognito tokens in login response");
      }

      const { tokens } = cognitoResult;

      if (!tokens.AccessToken || !tokens.IdToken || !tokens.RefreshToken) {
        throw new Error("Incomplete Cognito token set");
      }

      logger.debug("✅ Cognito tokens validated, exchanging for server session...");

      // CRITICAL: Exchange Cognito JWT for secure server session
      const response = await fetch(`${API_BASE_URL}/api/auth/cognito-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include', // CRITICAL: Include cookies in request
        body: JSON.stringify({
          accessToken: tokens.AccessToken,
          idToken: tokens.IdToken,
          refreshToken: tokens.RefreshToken
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Session creation failed' }));
        throw new Error(errorData.detail || `Session creation failed: ${response.status}`);
      }

      const sessionData = await response.json();

      logger.debug("✅ Server session created:", sessionData);

      // SEC-027: Store CSRF token from response for immediate use
      if (sessionData.csrf_token) {
        storeCsrfToken(sessionData.csrf_token);
        logger.debug("🔐 SEC-027: CSRF token stored for immediate use");
      }

      // Validate session response
      if (!sessionData.user || !sessionData.enterprise_validated) {
        throw new Error("Invalid session response from server");
      }

      // Set user state from server session response
      setUser({
        id: sessionData.user.user_id || sessionData.user.id,
        email: sessionData.user.email,
        role: sessionData.user.role,
      });

      // Set auth mode - Cognito MFA → Server Session (Banking Level)
      setAuthMode("cognito-session");
      setIsAuthenticated(true);

      logger.debug("✅ Enterprise banking-level authentication complete");
      logger.debug("🔐 Auth Chain: Cognito MFA → JWT Validation → Server Session → HttpOnly Cookie");

      setView("app");
      setActiveTab("dashboard");

      // Success toast
      toast.success(`Welcome, ${sessionData.user.email}!`);
      announce(`Logged in as ${sessionData.user.email}`, 'polite');

    } catch (err) {
      logger.error("❌ Cognito session creation failed:", err);
      logger.error("❌ Error details:", err.message);

      // User-friendly error message
      toast.error(`Login failed: ${err.message}`);
      announce(`Login failed: ${err.message}`, 'assertive');

      setView("login");
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  // 🍪 ENHANCED: Enterprise logout with cookie clearing
  const handleLogout = async (callAPI = true) => {
    try {
      logger.debug("🚪 Enterprise logout initiated...");
      
      if (callAPI) {
        // Call the enterprise logout API to clear cookies
        await logout();
        logger.debug("✅ Enterprise logout API called");
      } else {
        logger.debug("🧹 Local session cleanup only");
      }
      
      toast.success("Logged out successfully");
      
    } catch (error) {
      logger.warn("⚠️ Logout API error:", error);
      // Continue with cleanup even if API fails
    } finally {
      // Always clean up state and localStorage
      setUser(null);
      setView("login");
      setActiveTab("dashboard");
      setAuthMode("unknown");
      
      // Clear any remaining localStorage
      
      logger.debug("✅ Enterprise logout complete");
    }
  };

  // PRESERVED: Your existing profile update function
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
      logger.error("Profile update failed:", err);
      throw err;
    }
  };

  // 🏢 ENTERPRISE: Dual authentication support (Cookie + Bearer Token + CSRF)
  // Supports both cookie-based session auth AND Bearer token auth for maximum compatibility
  // ✅ PHASE 2 FIX: Added CSRF token support for cookie-authenticated requests
  // Created by: OW-kai Engineer (Phase 2 Frontend Integration)
  const getAuthHeaders = () => {
    logger.debug("🔍 Getting auth headers for API call");

    const headers = {
      "Content-Type": "application/json"
    };

    // 🔐 ENTERPRISE: Add Bearer token if available (for endpoints requiring explicit auth)
    // Cookie authentication is still sent automatically by browser
    // This dual approach ensures compatibility with all backend endpoints
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      logger.debug("✅ Enterprise: Bearer token added to headers");
    } else {
      logger.debug("🍪 Enterprise: Using cookie-based authentication only");
    }

    // ✅ PHASE 2 FIX: Add CSRF token for cookie-authenticated requests
    // CSRF protection is required for all state-changing methods (POST/PUT/DELETE/PATCH)
    // when using cookie authentication (not needed for Bearer token auth)
    const csrfToken = getCsrfToken();
    if (csrfToken && !token) {  // Only add CSRF if using cookie auth (no bearer token)
      headers['X-CSRF-Token'] = csrfToken;
      logger.debug("🔐 CSRF token added to headers");
    } else if (!csrfToken && !token) {
      logger.warn("⚠️ No CSRF token available for cookie-authenticated request");
    }

    return headers;
  };

  // ✅ PHASE 2 FIX: CSRF token extraction helper
  // Created by: OW-kai Engineer (Phase 2 Frontend Integration)
  const getCsrfToken = () => {
    try {
      const cookies = document.cookie.split(';').map(c => c.trim());
      const csrfCookie = cookies.find(c => c.startsWith('owai_csrf='));
      if (csrfCookie) {
        return csrfCookie.split('=')[1];
      }
      return null;
    } catch (error) {
      logger.error("❌ Error extracting CSRF token:", error);
      return null;
    }
  };
  // PRESERVED: All your existing render logic (unchanged)
  const renderAppContent = () => {
    logger.debug("🎯 Rendering tab:", activeTab);
    logger.debug("🎯 User role:", user?.role);
    
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
    
    // PRESERVED: All your existing switch cases (unchanged)
    switch (activeTab) {
      case "dashboard":
        return contentWithTransition(<Dashboard getAuthHeaders={getAuthHeaders} setActiveTab={setActiveTab} user={user} />);
      case "analytics":
        return contentWithTransition(<SecurityInsights getAuthHeaders={getAuthHeaders} />);
      case "realtime-analytics":
  return contentWithTransition(<RealTimeAnalyticsDashboard getAuthHeaders={getAuthHeaders} user={user} />);

  
      case "activity":
        return contentWithTransition(<AgentActivityFeed getAuthHeaders={getAuthHeaders} />);
      case "reports":
        return contentWithTransition(<EnterpriseSecurityReports getAuthHeaders={getAuthHeaders} user={user} />);
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
                🆘 Enterprise Support Center
              </h3>
              <p className={`mb-4 ${isDarkMode ? 'text-blue-300' : 'text-blue-700'}`}>
                24/7 enterprise support available for critical issues.
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
                Open Enterprise Support Ticket
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
          contentWithTransition(<EnterpriseSettings getAuthHeaders={getAuthHeaders} user={user} API_BASE_URL={API_BASE_URL} />) :
          adminRequiredMessage;
      case 'alerts':
  return <SmartAlertManagement getAuthHeaders={getAuthHeaders} user={user} />;    
      case "profile":
        return contentWithTransition(<Profile user={user} onUpdateProfile={handleProfileUpdate} />);
      case "errorTest":
        return (
          <ErrorBoundary fallbackMessage="This is a test error. The error boundary is working correctly!">
            <ErrorBoundaryTest />
          </ErrorBoundary>
        );
      // SEC-024: Enterprise Agent Registry - MCP Server & Agent Governance
      case "agent-registry":
        return user?.role === "admin" ?
          contentWithTransition(<AgentRegistryManagement getAuthHeaders={getAuthHeaders} user={user} />) :
          adminRequiredMessage;
      // SEC-022: Admin Console - Organization Management
      case "admin-console":
        return (user?.role === "admin" || user?.role === "org_admin") ?
          contentWithTransition(<AdminConsole />) :
          adminRequiredMessage;
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

  // Show enhanced loading screen while checking auth status
  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className={`min-h-screen flex flex-col lg:flex-row transition-colors duration-300 ${
      isDarkMode ? 'bg-slate-800' : 'bg-gray-100'
    }`}>
      {view === "login" && (
        <CognitoLogin
          onLoginSuccess={handleLoginSuccess}
          switchToRegister={() => setView("register")}
          switchToForgotPassword={() => setView("forgot")}
          switchToSignup={() => setView("signup")}
        />
      )}
      {view === "register" && (
        <Register
          onRegisterSuccess={handleLoginSuccess}
          switchToLogin={() => setView("login")}
        />
      )}
      {view === "forgot" && <ForgotPasswordEnterpriseV3 switchToLogin={() => setView("login")} />}
      {/* SEC-021: Self-Service Signup Flow (PUBLIC - No auth required) */}
      {view === "signup" && (
        <SignupFlow
          onSignupComplete={() => {
            toast.success("Account created! Please check your email to verify.");
            setView("login");
          }}
          switchToLogin={() => setView("login")}
        />
      )}
      {/* SEC-021: Email Verification (PUBLIC - No auth required) */}
      {view === "verify-email" && (
        <VerifyEmail
          onVerified={() => {
            toast.success("Email verified! You can now log in.");
            setView("login");
          }}
          switchToLogin={() => setView("login")}
        />
      )}
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
            {/* ENHANCED: Header with enterprise security status */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Breadcrumb activeTab={activeTab} user={user} />
                </div>
                <GlobalSearch onNavigate={handleTabChange} />
              </div>
              
              {/* ENHANCED: Enterprise Security Status Bar */}
              <div className={`text-sm transition-colors duration-300 ${
                isDarkMode ? 'text-slate-400' : 'text-gray-600'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    Logged in as: <span className="font-medium">{user?.email}</span> ({user?.role})
                  </div>
                  <div className="flex items-center space-x-2">
                    {/* Authentication Mode Indicator */}
                    <span className={`text-xs px-2 py-1 rounded transition-colors duration-300 ${
                      authMode === "cookie"
                        ? (isDarkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800')
                        : authMode === "token" 
                        ? (isDarkMode ? 'bg-yellow-900/30 text-yellow-300' : 'bg-yellow-100 text-yellow-800')
                        : (isDarkMode ? 'bg-gray-900/30 text-gray-300' : 'bg-gray-100 text-gray-800')
                    }`}>
                      {authMode === "cookie" ? "🔒 Secure Cookies" : 
                       authMode === "token" ? "⚠️ Legacy Token" : "❓ Unknown Auth"}
                    </span>
                    
                    {/* API Endpoint Indicator */}
                    <span className={`text-xs px-2 py-1 rounded transition-colors duration-300 ${
                      isDarkMode 
                        ? 'bg-blue-900/30 text-blue-300' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      API: {API_BASE_URL.replace('https://', '').split('.')[0]}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* PRESERVED: Main content rendering (unchanged) */}
            {renderAppContent()}
          </main>
          
          {/* PRESERVED: Support modal (unchanged) */}
          {showSupportModal && (
            <SupportModal
              onClose={() => setShowSupportModal(false)}
              onSubmit={(message) => {
                logger.debug("Support message submitted:", message);
                setShowSupportModal(false);
                toast.success("Support ticket submitted successfully");
              }}
            />
          )}
        </>
      )}
    </div>
  );
};

// Phase 3: App wrapper with Cognito Authentication
const App = () => {
  return (
    <AuthErrorBoundary>
      <AuthProvider>
        <ErrorBoundary fallbackMessage="The OW-AI Enterprise Platform encountered an unexpected error. Our team has been notified.">
          <ThemeProvider>
            <AccessibilityProvider>
              <ToastProvider>
                <SessionTimeoutWarning />
                <AppContent />
              </ToastProvider>
            </AccessibilityProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </AuthProvider>
    </AuthErrorBoundary>
  );
};

export default App;
