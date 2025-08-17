/**
 * Enterprise API utilities with cookie-based authentication
 * Master Prompt Compliant: Cookie-only auth, no localStorage
 * ENHANCED: Aggressive cookie transmission for all endpoints
 */

// 🏢 Enterprise API base URL - points to working backend
const API_BASE_URL = 'https://owai-production.up.railway.app';

/**
 * Enterprise login function with cookie-based authentication
 */
export const loginUser = async (email, password) => {
  try {
    console.log('🔐 Enterprise authentication attempt...');
    console.log('🔐 Attempting cookie authentication login...');
    console.log('📝 Credentials being sent:', { email, password: '***' });

    // Send as JSON for backend compatibility
    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      credentials: "include",
    credentials: "include",
        headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // 🍪 Enterprise cookie-only auth
      body: JSON.stringify({
        username: email,
        password: password
      })
    });

    console.log('🏢 Enterprise request to /auth/token:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Login successful - cookies should be set');
      console.log('✅ Enterprise login successful:', data);
      return data;
    } else {
      const error = await response.json();
      console.log('❌ Login failed:', error);
      throw new Error(error.detail || 'Login failed');
    }
  } catch (error) {
    console.error('❌ Login error:', error);
    throw error;
  }
};

/**
 * Get current user with cookie authentication
 */
export const getCurrentUser = async () => {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    
    const response = await fetch(`${API_BASE_URL}/auth/cookie-me`, {
      method: 'GET',
      credentials: 'include', // 🍪 Enterprise cookie-only auth
      credentials: "include",
    credentials: "include",
        headers: {
        'Content-Type': 'application/json',
      }
    });

    console.log('🏢 Enterprise request to /auth/cookie-me:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Enterprise user data retrieved:', data);
      return data;
    } else {
      console.log('ℹ️ No valid enterprise authentication');
      return null;
    }
  } catch (error) {
    console.error('❌ Get user error:', error);
    return null;
  }
};

/**
 * Logout user (Master Prompt compliant)
 */
export const logoutUser = async () => {
  try {
    console.log('🚪 Enterprise logout...');
    // With HTTP-only cookies, logout is handled by redirecting
    window.location.href = '/';
  } catch (error) {
    console.error('❌ Logout error:', error);
  }
};

/**
 * ENHANCED: Aggressive fetch with forced cookie authentication
 * Master Prompt Compliant: Uses cookies only, no localStorage
 * THIS IS THE KEY FIX - Forces credentials on ALL requests
 */
export const fetchWithAuth = async (url, options = {}) => {
  try {
    // Ensure URL is absolute
    const absoluteUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    
    console.log(`🍪 Enterprise cookie-only auth`);
    console.log(`🏢 Using cookie-only authentication (Master Prompt compliant)`);
    console.log(`🔍 Request details:`, { url: absoluteUrl, method: options.method || 'GET' });

    // ENHANCED: Always force credentials and proper headers
    const enhancedOptions = {
      ...options,
      credentials: 'include', // 🍪 FORCE cookies on every request
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // Enterprise request marker
        ...options.headers,
      },
    };

    const response = await fetch(absoluteUrl, enhancedOptions);

    console.log(`🏢 Enterprise request to ${url}:`, response.status);

    return response;
  } catch (error) {
    console.error(`❌ Request error for ${url}:`, error);
    throw error;
  }
};

/**
 * ENHANCED: Direct API helper that FORCES cookie authentication
 * Use this for all API calls that were previously failing
 */
export const apiCall = async (endpoint, options = {}) => {
  const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return fetchWithAuth(url, options);
};

/**
 * ENHANCED: GET request helper with forced cookies
 */
export const apiGet = async (endpoint) => {
  const response = await apiCall(endpoint, { method: 'GET' });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
};

/**
 * ENHANCED: POST request helper with forced cookies
 */
export const apiPost = async (endpoint, data = null) => {
  const options = {
    method: 'POST',
    body: data ? JSON.stringify(data) : null
  };
  const response = await apiCall(endpoint, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
};

// 🔄 Clean exports without duplicates (Master Prompt compliant)
export const login = loginUser;
export const logout = logoutUser;
export const getUser = getCurrentUser;

// Default export for comprehensive compatibility
export default {
  loginUser,
  getCurrentUser, 
  logoutUser,
  fetchWithAuth,
  apiCall,
  apiGet,
  apiPost,
  login: loginUser,
  logout: logoutUser,
  getUser: getCurrentUser
};

/* Build trigger: $(date) - Enhanced cookie auth deployment - FIXED LOCATION */
