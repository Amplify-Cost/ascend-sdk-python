// ============================================
// ENTERPRISE COOKIE-BASED AUTHENTICATION
// ============================================
// Cookies are sent automatically by browser
// CSRF protection via double-submit cookie pattern
// ============================================
// SEC-027: Enhanced CSRF token handling with sessionStorage fallback
// Authored-By: OW-KAI Engineer
// Compliance: PCI-DSS 6.5.9, OWASP ASVS 4.2.2
// ============================================

import { API_BASE_URL } from "../config/api";
import logger from "./logger";

// SEC-027: Session storage key for CSRF token fallback
const CSRF_STORAGE_KEY = 'owai_csrf_token';

/**
 * SEC-027: Store CSRF token from login response
 * Called after successful Cognito session creation
 *
 * @param {string} token - CSRF token from server response
 */
export const storeCsrfToken = (token) => {
  if (token) {
    try {
      sessionStorage.setItem(CSRF_STORAGE_KEY, token);
      logger.debug("🔐 SEC-027: CSRF token stored in session");
    } catch (error) {
      logger.warn("⚠️ SEC-027: Failed to store CSRF token:", error);
    }
  }
};

/**
 * SEC-027: Clear CSRF token on logout
 */
export const clearCsrfToken = () => {
  try {
    sessionStorage.removeItem(CSRF_STORAGE_KEY);
    logger.debug("🔐 SEC-027: CSRF token cleared from session");
  } catch (error) {
    // Ignore errors during cleanup
  }
};

/**
 * 🏢 ENTERPRISE: Extract CSRF token with fallback chain
 * Implements double-submit cookie pattern for CSRF protection
 *
 * SEC-027: Enhanced with sessionStorage fallback for cases where
 * cookie isn't immediately readable after login redirect.
 *
 * Priority:
 * 1. Cookie (owai_csrf) - Primary source
 * 2. SessionStorage - Fallback for timing issues
 *
 * @returns {string|null} CSRF token value or null if not found
 */
const getCsrfToken = () => {
  try {
    // Priority 1: Try cookie first (primary source)
    const cookies = document.cookie.split(';').map(c => c.trim());
    const csrfCookie = cookies.find(c => c.startsWith('owai_csrf='));

    if (csrfCookie) {
      const token = csrfCookie.split('=')[1];
      logger.debug("🔐 CSRF token extracted from cookie");
      return token;
    }

    // Priority 2: Fallback to sessionStorage (SEC-027)
    const storedToken = sessionStorage.getItem(CSRF_STORAGE_KEY);
    if (storedToken) {
      logger.debug("🔐 SEC-027: CSRF token retrieved from session storage (fallback)");
      return storedToken;
    }

    logger.debug("⚠️ CSRF token not found - may not be authenticated");
    return null;
  } catch (error) {
    logger.error("❌ Error extracting CSRF token:", error);
    return null;
  }
};

/**
 * Enterprise cookie-based fetch with automatic CSRF protection
 *
 * Features:
 * - Automatic cookie transmission (credentials: "include")
 * - CSRF double-submit token for POST/PUT/PATCH/DELETE
 * - Automatic session expiry handling (401 → redirect to login)
 * - Enterprise-grade error handling
 */
const fetchWithAuth = async (url, options = {}) => {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  const method = (options.method || "GET").toUpperCase();

  logger.debug("🌐 Enterprise API Call:", fullUrl);
  logger.debug("🍪 Using cookie-based authentication");

  // Build headers
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // 🏢 ENTERPRISE: Add CSRF token for mutating methods
  // Double-submit cookie pattern: owai_csrf cookie + X-CSRF-Token header
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();

    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
      logger.debug(`🔐 CSRF token added to ${method} request`);
    } else {
      logger.warn(`⚠️ No CSRF token available for ${method} request - may fail if CSRF is enforced`);
    }
  }

  const config = {
    ...options,
    headers,
    credentials: "include", // CRITICAL: Send cookies with request
  };

  try {
    const response = await fetch(fullUrl, config);

    // Handle 401 - session expired
    if (response.status === 401) {
      logger.warn("⚠️ 401 Unauthorized - Session expired or invalid");
      
      // Redirect to login
      if (window.location.pathname !== "/login") {
        logger.debug("🔄 Redirecting to login...");
        window.location.href = "/login";
      }
      
      throw new Error("Authentication required");
    }

    // ✅ PHASE 2 FIX: Handle CSRF validation failures
    // Created by: OW-kai Engineer (Phase 2 Frontend Integration)
    if (response.status === 403) {
      try {
        const errorData = await response.json();
        if (errorData.detail && errorData.detail.toLowerCase().includes('csrf')) {
          logger.error("🚨 CSRF validation failed - token missing or expired");
          logger.debug("💡 Tip: Ensure CSRF cookie is set after login");
          throw new Error("CSRF validation failed. Please refresh and try again.");
        }
      } catch (jsonError) {
        // If JSON parsing fails, fall through to generic error handler
        logger.debug("Failed to parse 403 error response as JSON");
      }
    }

    // Handle other error responses
    if (!response.ok) {
      const errorText = await response.text();
      logger.error(`❌ API Error ${response.status}:`, errorText);
      throw new Error(`API returned ${response.status}: ${errorText}`);
    }

    // Parse JSON response
    const data = await response.json();
    logger.debug("✅ API Success:", fullUrl);
    return data;

  } catch (error) {
    logger.error("❌ Enterprise fetch error:", error.message);
    throw error;
  }
};

/**
 * Get current authenticated user
 */
export const getCurrentUser = async () => {
  logger.debug("🔍 Getting current user via cookie auth...");
  try {
    return await fetchWithAuth("/api/auth/me");
  } catch (error) {
    logger.error("❌ Enterprise: Get current user failed:", error);
    throw error;
  }
};


/**
 * Enterprise logout - clears server-side session/cookies
 * SEC-027: Also clears CSRF token from sessionStorage
 */
export const logout = async () => {
  logger.debug("🚪 Calling enterprise logout API...");
  try {
    await fetchWithAuth("/auth/logout", {
      method: "POST",
    });
    logger.debug("✅ Enterprise logout successful");
  } catch (error) {
    logger.warn("⚠️ Logout API call failed:", error);
    // Don't throw - allow logout to continue even if API fails
  } finally {
    // SEC-027: Always clear CSRF token on logout
    clearCsrfToken();
  }
};

export default fetchWithAuth;

// Named export for backwards compatibility
export { fetchWithAuth };
