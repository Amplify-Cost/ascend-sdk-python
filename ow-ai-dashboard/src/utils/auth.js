// src/utils/auth.js

export function getAuthHeaders() {
  const token = localStorage.getItem("token");
  if (!token) {
    return {}; // No token, no Authorization header
  }
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}
