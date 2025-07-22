export async function fetchWithAuth(url, options = {}) {
  let accessToken = localStorage.getItem("access_token");
  let refreshToken = localStorage.getItem("refresh_token");

  // Set default headers
  options.headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Add authorization header if token exists
  if (accessToken) {
    options.headers.Authorization = `Bearer ${accessToken}`;
  }

  let response = await fetch(url, options);

  // Handle 401 unauthorized - try to refresh token
  if (response.status === 401 && refreshToken) {
    console.log("🔄 Access token expired, attempting refresh...");
    
    try {
      const refreshResponse = await fetch(`${import.meta.env.VITE_API_URL || 'https://owai-production.up.railway.app'}/auth/refresh-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        
        // Update stored tokens
        localStorage.setItem("access_token", refreshData.access_token);
        if (refreshData.refresh_token) {
          localStorage.setItem("refresh_token", refreshData.refresh_token);
        }
        
        // Retry original request with new token
        options.headers.Authorization = `Bearer ${refreshData.access_token}`;
        response = await fetch(url, options);
        
        console.log("✅ Token refreshed successfully");
      } else {
        console.log("❌ Token refresh failed, redirecting to login");
        // Clear invalid tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        
        // Redirect to login
        window.location.href = "/";
        return response;
      }
    } catch (refreshError) {
      console.error("Token refresh error:", refreshError);
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/";
      return response;
    }
  }

  return response;
}

// Helper function for components that need auth headers
export function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Check if user is authenticated
export function isAuthenticated() {
  return !!localStorage.getItem("access_token");
}

// Logout helper
export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/";
}