/*
 * Enterprise Authentication Utilities - Enhanced Debug Version
 * Cookie-only authentication, NO localStorage, NO Bearer tokens
 * Includes fallback endpoint for form parsing issues
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

// Enhanced login with backend form parsing fix and fallback
export const loginUser = async (credentials) => {
  console.log('🔐 Attempting cookie authentication login...');
  console.log('📝 Credentials being sent:', { 
    username: credentials.username, 
    password: credentials.password ? '[PROVIDED]' : '[MISSING]',
    usernameLength: credentials.username?.length || 0,
    passwordLength: credentials.password?.length || 0
  });
  
  try {
    // Method 1: URLSearchParams (FastAPI Form() dependency)
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
      
      // Method 2: Try fallback endpoint with request.form() parsing
      console.log('🔄 Trying fallback endpoint...');
      
      const response2 = await fetchWithAuth('/auth/token-fallback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });
      
      if (response2.ok) {
        const userData = await response2.json();
        console.log('✅ Fallback login successful - cookies should be set');
        return { success: true, user: userData };
      } else {
        const errorText2 = await response2.text();
        console.log('❌ Fallback also failed:', errorText2);
        
        // Method 3: Try FormData as last resort
        console.log('🔄 Trying FormData approach...');
        
        const formDataObj = new FormData();
        formDataObj.append('username', credentials.username || '');
        formDataObj.append('password', credentials.password || '');
        
        const response3 = await fetchWithAuth('/auth/token', {
          method: 'POST',
          body: formDataObj, // FormData sets its own Content-Type
        });
        
        if (response3.ok) {
          const userData = await response3.json();
          console.log('✅ FormData login successful - cookies should be set');
          return { success: true, user: userData };
        } else {
          const errorText3 = await response3.text();
          console.log('❌ All methods failed:', errorText3);
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
