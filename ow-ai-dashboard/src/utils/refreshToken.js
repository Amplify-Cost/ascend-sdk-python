export async function refreshToken() {
    const token = localStorage.getItem("token");
    if (!token) return null;
  
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
  
      if (!response.ok) throw new Error("Failed to refresh token");
  
      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      return data.access_token;
    } catch (error) {
      console.error("Token refresh failed", error);
      return null;
    }
  }
  