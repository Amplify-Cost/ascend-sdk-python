/*
 * Enterprise Authentication Utilities - Debug Version
 * Cookie-only authentication, NO localStorage, NO Bearer tokens
 * Enhanced debugging for authentication troubleshooting
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
      'Content-Type': options.headers?.['Content-Type'] || 'application/json',
      ...options.headers,
    },
  };

  // Debug logging
  console.log('🔍 Request details:', {
    url,
    method: config.method || 'GET',
    headers: config.headers,
    hasBody: !!config.body
  });

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

// Enhanced login with multiple format attempts and debugging
export const loginUser = async (credentials) => {
  console.log('🔐 Attempting cookie authentication login...');
  console.log('📝 Credentials being sent:', { 
    username: credentials.username, 
    password: credentials.password ? '[PROVIDED]' : '[MISSING]',
    usernameLength: credentials.username?.length || 0,
    passwordLength: credentials.password?.length || 0
  });
  
  try {
    // Method 1: URLSearchParams (most common for FastAPI OAuth2)
    const formData = new URLSearchParams();
    formData.append('username', credentials.username || '');
    formData.append('password', credentials.password || '');
    
    console.log('🔍 Sending as URLSearchParams:', formData.toString());
    
    const response = await fetchWithAuth('/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    console.log('🔍 Response status:', response.status);
    console.log('🔍 Response headers:', Object.fromEntries(response.headers.entries()));

    if (response.ok) {
      const userData = await response.json();
      console.log('✅ Login successful - cookies should be set');
      return { success: true, user: userData };
    } else {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: errorText };
      }
      
      console.log('❌ Login failed:', errorData);
      console.log('🔍 Raw error response:', errorText);
      
      // Try Method 2: FormData if URLSearchParams failed
      if (response.status === 400) {
        console.log('🔄 Trying FormData approach...');
        
        const formDataObj = new FormData();
        formDataObj.append('username', credentials.username || '');
        formDataObj.append('password', credentials.password || '');
        
        const response2 = await fetchWithAuth('/auth/token', {
          method: 'POST',
          body: formDataObj, // FormData sets its own Content-Type
        });
        
        if (response2.ok) {
          const userData = await response2.json();
          console.log('✅ Login successful with FormData - cookies should be set');
          return { success: true, user: userData };
        } else {
          const errorText2 = await response2.text();
          console.log('❌ FormData also failed:', errorText2);
        }
      }
      
      return { success: false, error: errorData.detail || 'Login failed' };
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
