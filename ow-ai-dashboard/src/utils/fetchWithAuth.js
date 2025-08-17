/*
 * Enterprise Authentication Utilities
 * Cookie-only authentication, NO localStorage, NO Bearer tokens
 * Professional enterprise-grade security implementation
 */

const API_BASE_URL = 'https://owai-production.up.railway.app';

// Enterprise cookie-only fetch utility
export const fetchWithAuth = async (endpoint, options = {}) => {
  console.log('🍪 Enterprise cookie-only auth');
  console.log('🏢 Using cookie-only authentication (Master Prompt compliant)');
  
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    ...options,
    credentials: 'include', // CRITICAL: Include cookies for authentication
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  // Master Prompt Compliance: NO localStorage, NO Bearer tokens
  // Only use HTTP-only cookies for authentication
  
  try {
    const response = await fetch(url, config);
    console.log(`🏢 Enterprise request to ${endpoint}:`, response.status);
    return response;
  } catch (error) {
    console.error('❌ Enterprise fetch error:', error);
    throw error;
  }
};

// Get current user via cookies only
export const getCurrentUser = async () => {
  console.log('🔍 Getting current user via enterprise cookie auth...');
  
  try {
    const response = await fetchWithAuth('/auth/me');
    
    if (response.ok) {
      const userData = await response.json();
      console.log('✅ Enterprise user data retrieved:', userData);
      return userData;
    } else {
      console.log('ℹ️ No valid enterprise authentication');
      return null;
    }
  } catch (error) {
    console.error('❌ Error getting current user:', error);
    return null;
  }
};

// Fixed login with correct field mapping for backend
export const loginUser = async (credentials) => {
  console.log('🔐 Attempting cookie authentication login...');
  
  try {
    // Backend expects 'username' and 'password' fields
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await fetchWithAuth('/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (response.ok) {
      const userData = await response.json();
      console.log('✅ Login successful - cookies should be set');
      return { success: true, user: userData };
    } else {
      const error = await response.json();
      console.log('❌ Login failed:', error);
      return { success: false, error: error.detail || 'Login failed' };
    }
  } catch (error) {
    console.error('❌ Login error:', error);
    return { success: false, error: 'Network error' };
  }
};

// Logout with cookies only
export const logoutUser = async () => {
  console.log('🔓 Enterprise logout...');
  
  try {
    await fetchWithAuth('/auth/logout', { method: 'POST' });
    console.log('✅ Enterprise logout successful');
    return { success: true };
  } catch (error) {
    console.error('❌ Logout error:', error);
    return { success: false, error: 'Logout failed' };
  }
};

// Default export for backwards compatibility
export default fetchWithAuth;
