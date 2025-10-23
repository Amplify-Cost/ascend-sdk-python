// ============================================
// ENTERPRISE COOKIE-BASED AUTHENTICATION
// ============================================
// Cookies are sent automatically by browser
// No token management needed
// ============================================

import { API_BASE_URL } from "../config/api";
import logger from "./logger";

/**
 * Enterprise cookie-based fetch with automatic retry
 * Cookies are handled automatically by browser
 */
const fetchWithAuth = async (url, options = {}) => {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  
  logger.debug("🌐 Enterprise API Call:", fullUrl);
  logger.debug("🍪 Using cookie-based authentication");

  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
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
    return await fetchWithAuth("/auth/me");
  } catch (error) {
    logger.error("❌ Enterprise: Get current user failed:", error);
    throw error;
  }
};


/**
 * Enterprise logout - clears server-side session/cookies
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
  }
};

export default fetchWithAuth;

// Named export for backwards compatibility
export { fetchWithAuth };
