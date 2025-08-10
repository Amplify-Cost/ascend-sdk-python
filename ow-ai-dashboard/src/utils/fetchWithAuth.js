// utils/fetchWithAuth.js - Enterprise Cookie Authentication (Phase 2)
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://owai-production.up.railway.app";

// Enterprise Configuration
const ENTERPRISE_CONFIG = {
  // Enable cookie mode for enterprise security
  cookieMode: true,
  // Fallback to token mode if needed
  fallbackMode: "token", 
  // Enterprise security headers
  enterpriseHeaders: {
    'X-Enterprise-Client': 'OW-AI-Platform',
    'X-Auth-Mode': 'cookie',
    'X-Platform-Version': '1.0.0'
  },
  // Request timeout for enterprise security
  timeout: 30000
};

/**
 * 🏢 Enterprise fetch with automatic cookie authentication
 * Supports both cookie and token modes for seamless migration
 */
export async function fetchWithAuth(url, options = {}) {
  try {
    console.log(`🔍 Enterprise API call: ${url}`);
    
    // Prepare enterprise request configuration
    const enterpriseOptions = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...ENTERPRISE_CONFIG.enterpriseHeaders,
        ...(options.headers || {})
      },
      credentials: 'include', // 🍪 Enable cookie sending
      ...options
    };

    // 🔧 MASTER PROMPT FIX: ALWAYS send token when available (no conditions)
    const token = localStorage.getItem("access_token");
    if (token) {
      console.log('🔄 Enterprise auth: Sending Authorization header');
      enterpriseOptions.headers.Authorization = `Bearer ${token}`;
    } else {
      console.log('⚠️ No token available - API call may fail without proper authentication');
    }

    console.log(`🔍 Request headers:`, enterpriseOptions.headers);

    // Make the enterprise API call
    let response = await fetch(url, enterpriseOptions);
    
    console.log(`📡 Enterprise API response: ${response.status} ${response.statusText}`);

    // Handle 401 Unauthorized - Enterprise token refresh
    if (response.status === 401) {
      console.log('🔄 Enterprise authentication failed, attempting refresh...');
      
      const refreshSuccess = await attemptTokenRefresh();
      
      if (refreshSuccess) {
        console.log('✅ Enterprise token refresh successful, retrying request');
        
        // Retry with updated token
        const retryToken = localStorage.getItem("access_token");
        if (retryToken) {
          enterpriseOptions.headers.Authorization = `Bearer ${retryToken}`;
          console.log('🔄 Retrying with refreshed token');
        }
        
        // Retry the original request
        response = await fetch(url, enterpriseOptions);
      } else {
        console.log('❌ Enterprise token refresh failed, redirecting to login');
        handleAuthenticationFailure();
        return response;
      }
    }

    // Log successful enterprise requests
    if (response.ok) {
      console.log(`✅ Enterprise API success: ${url}`);
    } else {
      console.log(`⚠️ Enterprise API warning: ${url} - ${response.status}`);
    }

    return response;

  } catch (error) {
    console.error(`❌ Enterprise network error: ${url}`, error);
    throw error;
  }
}

/**
 * 🔄 Enterprise token refresh using cookie authentication
 */
async function attemptTokenRefresh() {
  try {
    console.log('🔄 Enterprise token refresh attempt...');
    
    const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...ENTERPRISE_CONFIG.enterpriseHeaders
      },
      credentials: 'include', // 🍪 Send refresh cookie
    });

    if (refreshResponse.ok) {
      const refreshData = await refreshResponse.json();
      console.log('✅ Enterprise token refresh successful');
      
      // 🔧 ENTERPRISE FIX: Always store tokens for compatibility
      if (refreshData.access_token) {
        console.log('🔄 Storing refreshed token for hybrid authentication');
        localStorage.setItem("access_token", refreshData.access_token);
        if (refreshData.refresh_token) {
          localStorage.setItem("refresh_token", refreshData.refresh_token);
        }
        return true;
      }
      
      // Cookie mode: No need to store tokens, cookies are managed automatically
      if (refreshData.auth_mode === 'cookie') {
        console.log('🍪 Enterprise cookies refreshed automatically');
        return true;
      }
      
      return true;
    }

    console.log('❌ Enterprise token refresh failed:', refreshResponse.status);
    return false;

  } catch (error) {
    console.error('❌ Enterprise token refresh error:', error);
    return false;
  }
}

/**
 * 🚨 Handle authentication failure with enterprise cleanup
 */
function handleAuthenticationFailure() {
  console.log('🚨 Enterprise authentication failure - cleaning up session');
  
  // Clear any legacy tokens
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  
  // Clear any enterprise session data
  sessionStorage.clear();
  
  // Redirect to login (enterprise way)
  console.log('🔄 Redirecting to enterprise login...');
  window.location.href = "/";
}

/**
 * 🔍 Get current authentication status (enterprise compatible)
 */
export function isAuthenticated() {
  // In cookie mode, we can't directly check cookies from JavaScript (httpOnly)
  // We'll rely on API calls to /auth/me to verify authentication
  
  // Legacy token mode fallback
  const hasLegacyToken = !!localStorage.getItem("access_token");
  
  if (hasLegacyToken) {
    console.log('🎫 Legacy token found');
    return true;
  }
  
  // For cookie mode, assume authenticated until API call proves otherwise
  console.log('🍪 Cookie mode: Authentication status will be verified by API');
  return true; // Will be verified by actual API calls
}

/**
 * 🚪 Enterprise logout with secure cleanup
 */
export async function logout() {
  try {
    console.log('🚪 Enterprise logout initiated...');
    
    // Call backend logout to clear cookies
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...ENTERPRISE_CONFIG.enterpriseHeaders
      },
      credentials: 'include'
    });

    if (response.ok) {
      console.log('✅ Enterprise server logout successful');
    } else {
      console.log('⚠️ Enterprise server logout warning:', response.status);
    }

  } catch (error) {
    console.error('❌ Enterprise logout error:', error);
  } finally {
    // Always clean up local storage and redirect
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.clear();
    
    console.log('🔄 Enterprise logout complete, redirecting...');
    window.location.href = "/";
  }
}

/**
 * 🔍 Get current user info with enterprise authentication
 */
export async function getCurrentUser() {
  try {
    console.log('🔍 Enterprise user retrieval...');
    
    const response = await fetchWithAuth(`${API_BASE_URL}/auth/me`);
    
    if (response.ok) {
      const userData = await response.json();
      console.log('✅ Enterprise user data retrieved:', userData.email);
      return userData;
    } else {
      console.log('❌ Enterprise user retrieval failed:', response.status);
      return null;
    }
    
  } catch (error) {
    console.error('❌ Enterprise user retrieval error:', error);
    return null;
  }
}

/**
 * 🎫 Legacy compatibility: Get auth headers (for components that still need them)
 */
export function getAuthHeaders() {
  console.log('⚠️ Legacy auth headers requested - consider upgrading to fetchWithAuth');
  
  // 🔧 ENTERPRISE FIX: Always provide token headers when available
  const token = localStorage.getItem("access_token");
  if (token) {
    console.log('🔄 Providing auth headers for legacy compatibility');
    return { Authorization: `Bearer ${token}` };
  }
  
  console.log('🍪 No token available for legacy headers');
  return {};
}

/**
 * 📊 Enterprise configuration info
 */
export function getEnterpriseConfig() {
  return {
    ...ENTERPRISE_CONFIG,
    apiBaseUrl: API_BASE_URL,
    timestamp: new Date().toISOString()
  };
}