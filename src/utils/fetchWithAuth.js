// utils/fetchWithAuth.js — Enhanced Enterprise Token Lifecycle Management
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Enterprise JWT Token Management
class EnterpriseTokenManager {
  static TOKEN_EXPIRY_BUFFER = 60; // 1 minute buffer before expiration
  static MAX_REFRESH_ATTEMPTS = 1;
  
  /**
   * Decode JWT payload safely
   */
  static decodeJWT(token) {
    try {
      if (!token || typeof token !== 'string') return null;
      
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      
      const payload = JSON.parse(atob(parts[1]));
      return payload;
    } catch (error) {
      console.warn("🔍 Enterprise: Invalid JWT format detected");
      return null;
    }
  }
  
  /**
   * Check if JWT token is expired or will expire soon
   */
  static isTokenExpired(token) {
    const payload = this.decodeJWT(token);
    if (!payload || !payload.exp) return true;
    
    const now = Math.floor(Date.now() / 1000);
    const isExpired = payload.exp <= (now + this.TOKEN_EXPIRY_BUFFER);
    
    if (isExpired) {
      console.log("🔄 Enterprise: Token expired or expiring soon");
    }
    
    return isExpired;
  }
  
  /**
   * Get token metadata for audit logging
   */
  static getTokenMetadata(token) {
    const payload = this.decodeJWT(token);
    if (!payload) return null;
    
    return {
      user_id: payload.sub,
      email: payload.email,
      role: payload.role,
      issued_at: payload.iat,
      expires_at: payload.exp,
      issuer: payload.iss,
      audience: payload.aud,
      token_type: payload.type
    };
  }
  
  /**
   * Clear expired or invalid tokens
   */
  static clearInvalidTokens() {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    
    let clearedTokens = false;
    
    if (accessToken && this.isTokenExpired(accessToken)) {
      localStorage.removeItem("access_token");
      console.log("🧹 Enterprise: Cleared expired access token");
      clearedTokens = true;
    }
    
    if (refreshToken && this.isTokenExpired(refreshToken)) {
      localStorage.removeItem("refresh_token");
      console.log("🧹 Enterprise: Cleared expired refresh token");
      clearedTokens = true;
    }
    
    return clearedTokens;
  }
  
  /**
   * Attempt to refresh access token using refresh token
   */
  static async refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    
    if (!refreshToken || this.isTokenExpired(refreshToken)) {
      console.log("❌ Enterprise: No valid refresh token available");
      this.clearInvalidTokens();
      return null;
    }
    
    try {
      console.log("🔄 Enterprise: Attempting token refresh");
      
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Enterprise-Client": "OW-AI-Platform"
        },
        credentials: "include",
        body: JSON.stringify({ 
          refresh_token: refreshToken 
        })
      });
      
      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        
        console.log("✅ Enterprise: Token refresh successful");
        return data.access_token;
      }
      
      throw new Error("Invalid refresh response format");
      
    } catch (error) {
      console.error("❌ Enterprise: Token refresh failed:", error);
      this.clearInvalidTokens();
      return null;
    }
  }
  
  /**
   * Get valid access token (refreshes if needed)
   */
  static async getValidAccessToken() {
    let accessToken = localStorage.getItem("access_token");
    
    // If no token or expired, try to refresh
    if (!accessToken || this.isTokenExpired(accessToken)) {
      accessToken = await this.refreshAccessToken();
    }
    
    return accessToken;
  }
}

// Read a simple cookie value (used for CSRF; session cookie is HttpOnly and not readable)
function getCookie(name) {
  const match = document.cookie.split("; ").find(c => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=", 2)[1]) : null;
}

/**
 * Enterprise hybrid fetch helper with enhanced token lifecycle management:
 * - Automatic token expiration detection and cleanup
 * - Intelligent token refresh attempts
 * - Graceful fallback to cookie authentication
 * - Comprehensive audit logging
 * - CSRF protection for state-changing operations
 */
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  const init = {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Enterprise-Client": "OW-AI-Platform",
      ...(options.headers || {})
    },
    credentials: "include", // Enterprise cookie authentication
    ...options
  };

  const method = (init.method || "GET").toUpperCase();

  // CSRF Protection for state-changing operations
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCookie("owai_csrf");
    if (csrf) {
      init.headers["X-CSRF-Token"] = csrf;
    }
  }

  // ENHANCED ENTERPRISE TOKEN LIFECYCLE MANAGEMENT
  try {
    // 1. Clear any expired tokens first
    EnterpriseTokenManager.clearInvalidTokens();
    
    // 2. Attempt to get a valid access token
    const validToken = await EnterpriseTokenManager.getValidAccessToken();
    
    if (validToken) {
      init.headers.Authorization = `Bearer ${validToken}`;
      console.log("🔐 Enterprise: Using refreshed token authentication");
      
      // Log token metadata for audit trail
      const metadata = EnterpriseTokenManager.getTokenMetadata(validToken);
      if (metadata) {
        console.log(`🔍 Enterprise Audit: ${metadata.email} (${metadata.role}) - Token valid until ${new Date(metadata.expires_at * 1000).toISOString()}`);
      }
    } else {
      console.log("🍪 Enterprise: Falling back to cookie-only authentication");
    }

  } catch (tokenError) {
    console.warn("⚠️ Enterprise: Token management error, proceeding with cookies only:", tokenError);
  }

  // Execute the request
  let response = await fetch(absoluteUrl, init);

  // Handle CSRF token expiration (403 Forbidden)
  if (response.status === 403) {
    try {
      console.log("🔄 Enterprise: CSRF token expired, refreshing");
      await fetch(`${API_BASE_URL}/auth/csrf`, { credentials: "include" });
      
      const newCsrf = getCookie("owai_csrf");
      if (newCsrf && ["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
        init.headers["X-CSRF-Token"] = newCsrf;
        response = await fetch(absoluteUrl, init);
        console.log("✅ Enterprise: CSRF token refreshed successfully");
      }
    } catch (csrfError) {
      console.error("❌ Enterprise: CSRF refresh failed:", csrfError);
    }
  }

  // Handle token expiration during request (401 Unauthorized)
  if (response.status === 401) {
    console.log("🔄 Enterprise: Authentication failed, attempting token refresh");
    
    try {
      const refreshedToken = await EnterpriseTokenManager.refreshAccessToken();
      
      if (refreshedToken) {
        init.headers.Authorization = `Bearer ${refreshedToken}`;
        response = await fetch(absoluteUrl, init);
        console.log("✅ Enterprise: Request retry with refreshed token successful");
      } else {
        console.log("🍪 Enterprise: Token refresh failed, relying on cookie authentication");
      }
    } catch (refreshError) {
      console.error("❌ Enterprise: Token refresh during request failed:", refreshError);
    }
  }

  // Final response validation
  if (!response.ok && response.status === 401) {
    console.log("🚪 Enterprise: Authentication failed completely, user needs to re-login");
    EnterpriseTokenManager.clearInvalidTokens();
  }

  return response;
}

// Enhanced logout with comprehensive cleanup
export async function logout() {
  try {
    console.log("🚪 Enterprise: Initiating secure logout");
    
    // Server-side logout to invalidate server sessions
    await fetchWithAuth("/auth/logout", { method: "POST" });
    
  } catch (error) {
    console.warn("⚠️ Enterprise: Server logout failed, proceeding with client cleanup:", error);
  } finally {
    // Comprehensive client-side cleanup
    EnterpriseTokenManager.clearInvalidTokens();
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.clear();
    
    // Clear any application state
    if (window.appState) {
      window.appState.clear();
    }
    
    console.log("✅ Enterprise: Logout complete - all tokens and sessions cleared");
    window.location.href = "/";
  }
}

// Enhanced user info retrieval with token validation
export async function getCurrentUser() {
  try {
    // Ensure we have a valid token before making the request
    const validToken = await EnterpriseTokenManager.getValidAccessToken();
    
    if (!validToken) {
      console.log("🔍 Enterprise: No valid token available for user info");
      return null;
    }
    
    const response = await fetchWithAuth("/auth/me");
    
    if (response.ok) {
      const userData = await response.json();
      console.log(`✅ Enterprise: User info retrieved for ${userData.email}`);
      return userData;
    }
    
    if (response.status === 401) {
      console.log("🔍 Enterprise: User session expired");
      EnterpriseTokenManager.clearInvalidTokens();
    }
    
    return null;
  } catch (error) {
    console.error("❌ Enterprise: Get current user failed:", error);
    return null;
  }
}

// Export the token manager for direct access if needed
export { EnterpriseTokenManager };