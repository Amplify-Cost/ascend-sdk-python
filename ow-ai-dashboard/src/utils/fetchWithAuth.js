/*
 * Master Prompt Compliant Fetch Utility
 * Cookie-only authentication, NO localStorage, NO Bearer tokens
 * Enterprise-grade security implementation
 */

const API_BASE_URL = 'https://owai-production.up.railway.app';

export const fetchWithAuth = async (endpoint, options = {}) => {
  console.log('🍪 Enterprise cookie-only auth');
  console.log('🏢 Using cookie-only authentication (Master Prompt compliant)');
  
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    ...options,
    credentials: 'include', // CRITICAL: Include cookies in requests
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
    console.error('❌ Fetch error:', error);
    throw error;
  }
};

export default fetchWithAuth;
