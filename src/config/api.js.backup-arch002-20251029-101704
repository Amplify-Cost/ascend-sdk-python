/**
 * API Configuration
 * Central configuration for all API endpoints
 */

// Base API URL - uses environment variable or falls back to localhost
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// API endpoints (can add more as needed)
export const API_ENDPOINTS = {
  auth: {
    login: "/auth/login",
    logout: "/auth/logout",
    refresh: "/auth/refresh",
    csrf: "/auth/csrf",
    updateProfile: "/auth/update-profile"
  },
  agentActions: {
    list: "/agent-actions",
    submit: "/agent-action",
    approve: (id) => `/agent-action/${id}/approve`,
    reject: (id) => `/agent-action/${id}/reject`
  }
};

export default API_BASE_URL;
