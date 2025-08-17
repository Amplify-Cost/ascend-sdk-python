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
