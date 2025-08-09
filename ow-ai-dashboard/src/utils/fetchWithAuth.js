// utils/fetchWithAuth.js - Updated for secure cookie authentication (PHASE 2)

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Enterprise configuration
const ENTERPRISE_CONFIG = {
  // Enable cookie mode by default for enterprise security
  cookieMode: true,
  
  // CSRF protection for enterprise
  csrfProtection: true,
  
  // Enhanced error handling
  retryAttempts: 2,
  
  // Request timeout
  timeout: 30000
};

/**
 * Enterprise-grade fetch with automatic cookie-based authentication
 * Supports both cookie and legacy token modes for migration
 */
export async function fetchWithAuth(url, options = {}) {
  // Set default headers for enterprise security
  options.headers = {
    "Content-Type": "application/json",
    // Signal cookie preference to backend
    "X-Auth-Mode": ENTERPRISE_CONFIG.cookieMode ? "cookie" : "token",
    ...(options.headers || {}),
  };

  // Enterprise: Include credentials for cookie-based auth
  options.credentials = "include";

  // Enterprise: Add timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ENTERPRISE_CONFIG.timeout);
  options.signal = controller.signal;

  try {
    // Attempt request with cookies
    let response = await fetch(url, options);
    clearTimeout(timeoutId);

    // Handle 401 unauthorized - attempt token refresh
    if (response.status === 401) {
      console.log("🔄 Authentication expired, attempting refresh...");
      
      const refreshSuccess = await refreshAuthToken();
      
      if (refreshSuccess) {
        // Retry original request after successful refresh
        console.log("✅ Token refreshed, retrying request...");
        response = await fetch(url, options);
      } else {
        console.log("❌ Token refresh failed, redirecting to login");
        handleAuthFailure();
        return response;
      }
    }

    // Enterprise logging for security audit
    if (response.ok) {
      console.log(`✅ API call successful: ${url}`);
    } else {
      console.warn(`⚠️ API call failed: ${url} - Status: ${response.status}`);
    }

    return response;

  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.error(`⏰ Request timeout: ${url}`);
      throw new Error('Request timeout - please check your connection');
    }
    
    console.error(`❌ Network error: ${url}`, error);
    throw error;
  }
}

/**
 * Refresh authentication token using secure cookies
 */
async function refreshAuthToken() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
      method: "POST",
      credentials: "include", // Include refresh token cookie
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Mode": "cookie"
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log("✅ Enterprise token refresh successful");
      
      // For cookie mode, tokens are automatically set via httpOnly cookies
      // No need to store anything in localStorage
      
      return true;
    } else {
      console.log("❌ Enterprise token refresh failed");
      return false;
    }
  } catch (error) {
    console.error("❌ Token refresh error:", error);
    return false;
  }
}

/**
 * Handle authentication failure - enterprise logout process
 */
function handleAuthFailure() {
  // Clear any legacy tokens
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  
  // Clear cookies via logout endpoint
  logout();
}

/**
 * Enterprise logout - clears both cookies and localStorage
 */
export async function logout() {
  try {
    // Call backend logout to clear cookies
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Mode": "cookie"
      }
    });
    
    console.log("✅ Enterprise logout successful");
  } catch (error) {
    console.warn("⚠️ Logout request failed (continuing anyway):", error);
  } finally {
    // Clear legacy localStorage tokens
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    
    // Redirect to login
    window.location.href = "/";
  }
}

/**
 * Check if user is authenticated (enterprise method)
 * Note: With httpOnly cookies, we can't directly check authentication
 * This function will make a lightweight API call to verify
 */
export async function isAuthenticated() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/verify`, {
      method: "GET",
      credentials: "include",
      headers: {
        "X-Auth-Mode": "cookie"
      }
    });
    
    return response.ok;
  } catch (error) {
    console.warn("Authentication check failed:", error);
    return false;
  }
}

/**
 * Get auth headers for legacy components
 * In cookie mode, this returns empty object since auth is handled automatically
 */
export function getAuthHeaders() {
  // For cookie-based auth, no manual headers needed
  if (ENTERPRISE_CONFIG.cookieMode) {
    return {};
  }
  
  // Legacy token fallback
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Enterprise: Get current user info from a lightweight API call
 * Since tokens are httpOnly, we need to fetch user data from backend
 */
export async function getCurrentUser() {
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/auth/me`);
    
    if (response.ok) {
      return await response.json();
    }
    
    return null;
  } catch (error) {
    console.error("Failed to get current user:", error);
    return null;
  }
}

/**
 * Migration helper: Enable/disable cookie mode
 * Useful for gradual rollout
 */
export function setCookieMode(enabled) {
  ENTERPRISE_CONFIG.cookieMode = enabled;
  console.log(`🔧 Cookie mode ${enabled ? 'enabled' : 'disabled'}`);
}

// Export configuration for debugging
export { ENTERPRISE_CONFIG };