// Enterprise API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

/**
 * Enterprise Cookie-Only Authentication
 * Secure HTTP-only cookies + CSRF protection
 * NO localStorage or Bearer tokens (Master Prompt compliance)
 */
let csrfToken = null;

// Get CSRF token for state-changing requests
async function getCSRFToken() {
  if (csrfToken) return csrfToken;
  try {
    const response = await fetch('/auth/csrf-token', {
      credentials: 'include' // Include cookies
    });
    if (response.ok) {
      const data = await response.json();
      csrfToken = data.csrf_token;
      return csrfToken;
    }
  } catch (error) {
    console.warn('Failed to get CSRF token:', error);
  }
  return null;
}

// Clear cached CSRF token on auth errors
function clearCSRFToken() {
  csrfToken = null;
}

// ENTERPRISE COOKIE-ONLY AUTHENTICATION (Master Prompt compliant)
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  console.log("🍪 Enterprise cookie-only auth request:", { url: absoluteUrl });

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // ENTERPRISE: NO Bearer tokens, only cookies (Master Prompt requirement)
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // Always include cookies
  };

  console.log("🏢 Enterprise: Cookie-only authentication (no Bearer tokens)");

  try {
    const response = await fetch(absoluteUrl, config);

    // Handle authentication errors
    if (response.status === 401) {
      console.log("❌ Cookie authentication failed - redirecting to login");
      clearCSRFToken();
      window.location.href = '/';
      return;
    }

    return response;
  } catch (error) {
    console.error("❌ Fetch error:", error);
    throw error;
  }
}

// Enterprise cookie-only logout
export function logout() {
  // Call logout endpoint to clear cookies
  fetchWithAuth('/auth/logout', { method: 'POST' })
    .then(() => {
      clearCSRFToken();
      // Clear any potential localStorage (Master Prompt compliance)
      localStorage.clear();
      window.location.href = '/';
    })
    .catch(error => {
      console.error('Logout error:', error);
      // Force redirect even if logout fails
      localStorage.clear();
      window.location.href = '/';
    });
}

/**
 * Get current user information using enterprise cookie-only authentication
 * Master Prompt compliant - no localStorage, no Bearer tokens
 */
export async function getCurrentUser() {
  try {
    console.log('🔍 Getting current user via enterprise cookie-only auth...');
    const response = await fetchWithAuth('/auth/me', {
      method: 'GET'
      // credentials: 'include' is already handled by fetchWithAuth
    });

    if (response.ok) {
      const userData = await response.json();
      console.log('✅ Cookie-only auth successful:', userData.email || userData.user_id);
      return {
        ...userData,
        enterprise_validated: true,
        auth_source: 'cookie_only'
      };
    } else if (response.status === 401) {
      console.log('ℹ️ No valid cookie authentication - user not logged in');
      return null;
    } else {
      throw new Error(`Failed to get user: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Error getting current user:', error);
    return null;
  }
}
