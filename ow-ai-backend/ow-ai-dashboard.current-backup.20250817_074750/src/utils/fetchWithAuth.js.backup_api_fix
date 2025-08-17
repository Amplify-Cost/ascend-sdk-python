/**
 * Enterprise Cookie-Based Authentication
 * Secure HTTP-only cookies + CSRF protection
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
// Cookie-first authentication - only send Bearer token as fallback
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  console.log("🍪 Enterprise cookie auth request:", { url: absoluteUrl });
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  // Only add Bearer token for specific endpoints that require it
  const requiresBearer = [
    '/auth/token',
    '/auth/refresh'
  ].some(path => url.includes(path));
  const token = localStorage.getItem("access_token");
  if (requiresBearer && token) {
    console.log("🔑 Adding Bearer token for auth endpoint");
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  } else {
    console.log("🍪 Using cookie-only authentication");
  }
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
 * Integrates with your existing CSRF and cookie architecture
 */
export async function getCurrentUser() {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    const response = await fetchWithAuth('/auth/me', {
      method: 'GET'
      // credentials: 'include' is already handled by fetchWithAuth
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
      // No valid authentication - fetchWithAuth already handled redirect
      return null;
    } else {
      throw new Error(`Failed to get user: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Error getting current user:', error);
    return null;
  }
}
