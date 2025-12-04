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
    list: "/api/v1/actions",
    submit: "/api/v1/actions/submit",
    get: (id) => `/api/v1/actions/${id}`,
    status: (id) => `/api/v1/actions/${id}/status`,
    approve: (id) => `/api/v1/actions/${id}/approve`,
    reject: (id) => `/api/v1/actions/${id}/reject`
  }
};

export default API_BASE_URL;
