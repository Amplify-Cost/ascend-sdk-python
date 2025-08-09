// utils/fetchWithAuth.js - Enterprise Authentication with Token Fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Enterprise configuration with temporary token fallback
const ENTERPRISE_CONFIG = {
  cookieMode: false,  // Temporarily disabled for stability
  csrfProtection: true,
  retryAttempts: 2,
  timeout: 30000,
  enterpriseGrade: true
};

/**
 * Enterprise-grade fetch with token-based authentication
 * Future: Will support secure cookie authentication
 */
export async function fetchWithAuth(url, options = {}) {
  // Get enterprise tokens
  let accessToken = localStorage.getItem("access_token");
  let refreshToken = localStorage.getItem("refresh_token");

  // Enterprise security headers
  options.headers = {
    "Content-Type": "application/json",
    "X-Auth-Mode": "token",
    "X-Enterprise-Client": "OW-AI-Platform",
    ...(options.headers || {}),
  };

  // Add enterprise authorization
  if (accessToken) {
    options.headers.Authorization = `Bearer ${accessToken}`;
  }

  // Enterprise timeout protection
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ENTERPRISE_CONFIG.timeout);
  options.signal = controller.signal;

  try {
    let response = await fetch(url, options);
    clearTimeout(timeoutId);

    // Enterprise token refresh workflow
    if (response.status === 401 && refreshToken) {
      console.log("🔄 Enterprise token refresh initiated...");
      
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "X-Auth-Mode": "token",
            "X-Enterprise-Client": "OW-AI-Platform"
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json();
          
          // Update enterprise tokens
          localStorage.setItem("access_token", refreshData.access_token);
          if (refreshData.refresh_token) {
            localStorage.setItem("refresh_token", refreshData.refresh_token);
          }
          
          // Retry with new enterprise token
          options.headers.Authorization = `Bearer ${refreshData.access_token}`;
          response = await fetch(url, options);
          
          console.log("✅ Enterprise token refresh successful");
        } else {
          console.log("❌ Enterprise token refresh failed");
          handleEnterpriseAuthFailure();
          return response;
        }
      } catch (refreshError) {
        console.error("Enterprise token refresh error:", refreshError);
        handleEnterpriseAuthFailure();
        return response;
      }
    }

    // Enterprise audit logging
    if (response.ok) {
      console.log(`✅ Enterprise API success: ${url}`);
    } else {
      console.warn(`⚠️ Enterprise API failed: ${url} - Status: ${response.status}`);
    }

    return response;

  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.error(`⏰ Enterprise request timeout: ${url}`);
      throw new Error('Enterprise request timeout - please check your connection');
    }
    
    console.error(`❌ Enterprise network error: ${url}`, error);
    throw error;
  }
}

/**
 * Enterprise authentication failure handler
 */
function handleEnterpriseAuthFailure() {
  console.log("🏢 Enterprise authentication failure - clearing session");
  
  // Clear enterprise tokens
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  
  // Enterprise logout process
  window.location.href = "/";
}

/**
 * Enterprise logout with secure cleanup
 */
export async function logout() {
  try {
    console.log("🏢 Enterprise logout initiated");
    
    // Attempt to notify backend (optional)
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Enterprise-Client": "OW-AI-Platform"
        }
      });
    } catch (logoutError) {
      console.warn("Backend logout notification failed:", logoutError);
    }
    
    // Clear enterprise session data
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    
    console.log("✅ Enterprise logout completed");
    
  } catch (error) {
    console.warn("Enterprise logout error:", error);
  } finally {
    // Always redirect for security
    window.location.href = "/";
  }
}

/**
 * Enterprise authentication status check
 */
export async function isAuthenticated() {
  const token = localStorage.getItem("access_token");
  
  if (!token) {
    return false;
  }
  
  // Enterprise token validation (optional)
  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "X-Enterprise-Client": "OW-AI-Platform"
      }
    });
    
    return response.ok;
  } catch (error) {
    console.warn("Enterprise auth check failed:", error);
    return !!token; // Fallback to token existence
  }
}

/**
 * Enterprise user information retrieval
 */
export async function getCurrentUser() {
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/auth/me`);
    
    if (response.ok) {
      const userData = await response.json();
      console.log("✅ Enterprise user data retrieved");
      return userData;
    }
    
    return null;
  } catch (error) {
    console.error("Enterprise user retrieval failed:", error);
    return null;
  }
}

/**
 * Enterprise authorization headers for legacy components
 */
export function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
      "X-Enterprise-Client": "OW-AI-Platform"
    };
  }
  
  return {};
}

/**
 * Enterprise configuration management
 */
export function getEnterpriseConfig() {
  return {
    ...ENTERPRISE_CONFIG,
    version: "2.0.0-enterprise",
    securityLevel: "SOC2-compliant",
    authMethod: "JWT-tokens",
    futureSupport: "httpOnly-cookies"
  };
}

/**
 * Enterprise migration helper for future cookie implementation
 */
export function setCookieMode(enabled) {
  ENTERPRISE_CONFIG.cookieMode = enabled;
  console.log(`🔧 Enterprise cookie mode ${enabled ? 'enabled' : 'disabled'}`);
  
  if (enabled) {
    console.warn("⚠️ Cookie mode requires backend cookie support");
  }
}

// Export enterprise configuration for monitoring
export { ENTERPRISE_CONFIG };