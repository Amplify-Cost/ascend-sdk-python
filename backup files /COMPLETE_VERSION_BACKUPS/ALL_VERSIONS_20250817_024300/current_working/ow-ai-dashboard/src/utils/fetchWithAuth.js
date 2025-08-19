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

export async function fetchWithAuth(url, options = {}) {
  const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  
  // Prepare headers
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  
  // Add CSRF token for state-changing requests
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
    const csrf = await getCSRFToken();
    if (csrf) {
      headers['X-CSRF-Token'] = csrf;
    }
  }
  
  // Always include credentials for cookie authentication
  const fetchOptions = {
    ...options,
    headers,
    credentials: 'include'  // Critical: Include cookies in all requests
  };
  
  console.log('🍪 Enterprise cookie auth request:', {
    url: absoluteUrl,
    method: options.method || 'GET',
    hasCSRF: !!headers['X-CSRF-Token']
  });
  
  let response = await fetch(absoluteUrl, fetchOptions);
  
  // Handle auth errors
  if (response.status === 401) {
    console.warn('🍪 Authentication failed - redirecting to login');
    clearCSRFToken();
    window.location.href = '/login';
    return response;
  }
  
  // Handle CSRF errors
  if (response.status === 403) {
    console.warn('🛡️ CSRF validation failed - refreshing token');
    clearCSRFToken();
    
    // Retry with fresh CSRF token
    const freshCSRF = await getCSRFToken();
    if (freshCSRF && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
      headers['X-CSRF-Token'] = freshCSRF;
      fetchOptions.headers = headers;
      response = await fetch(absoluteUrl, fetchOptions);
    }
  }
  
  return response;
}

// Helper functions for compatibility
export function isAuthenticated() {
  // With cookies, we can't check client-side
  // The server will validate on each request
  return true; // Assume authenticated, let server decide
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
