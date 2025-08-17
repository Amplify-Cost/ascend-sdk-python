// Enterprise API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

/**
 * Enterprise Cookie-Based Authentication
 * Master Prompt Compliant: HTTP-only cookies, no localStorage
 */
let csrfToken = null;

// Get CSRF token for state-changing requests
async function getCSRFToken() {
  if (csrfToken) return csrfToken;
  try {
    const response = await fetch(`${API_BASE_URL}/auth/csrf-token`, {
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

// Enterprise cookie-only authentication
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  console.log("🍪 Enterprise cookie auth request:", { url: absoluteUrl });
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // Master Prompt Compliance: NO localStorage, NO Bearer tokens
  console.log("🏢 Using cookie-only authentication (Master Prompt compliant)");

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // Always include cookies
  };

  try {
    const response = await fetch(absoluteUrl, config);
    
    // Handle authentication errors
    if (response.status === 401) {
      console.log("❌ Authentication failed - redirecting to login");
      window.location.href = '/';
      return;
    }
    
    return response;
  } catch (error) {
    console.error("❌ Fetch error:", error);
    throw error;
  }
}

// Enterprise logout
export function logout() {
  // Call logout endpoint to clear cookies
  fetchWithAuth('/auth/logout', { method: 'POST' })
    .then(() => {
      clearCSRFToken();
      window.location.href = '/';
    })
    .catch(error => {
      console.error('Logout error:', error);
      // Force redirect even if logout fails
      window.location.href = '/';
    });
}

/**
 * Get current user information using enterprise cookie authentication
 * Master Prompt Compliant: Cookie-only, no localStorage
 */
export async function getCurrentUser() {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    const response = await fetchWithAuth('/auth/me', {
      method: 'GET'
    });
    
    if (response.ok) {
      const userData = await response.json();
      console.log('✅ User data retrieved via cookies:', userData.email || userData.user_id);
      return {
        ...userData,
        enterprise_validated: true,
        auth_source: 'cookie'
      };
    } else if (response.status === 401) {
      console.log('ℹ️ No valid authentication - user not logged in');
      return null;
    } else {
      throw new Error(`Failed to get user: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Error getting current user:', error);
    return null;
  }
}
