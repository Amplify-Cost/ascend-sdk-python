// utils/fetchWithAuth.js — Hybrid Cookie + Token (Enterprise Phase 1.5)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Read a simple cookie value (used for CSRF; session cookie is HttpOnly and not readable)
function getCookie(name) {
  const match = document.cookie.split("; ").find(c => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=", 2)[1]) : null;
}

/**
 * Enterprise hybrid fetch helper:
 * - Prefers cookies (session + refresh) for security
 * - Falls back to tokens for backward compatibility
 * - Adds X-CSRF-Token for write methods using the owai_csrf cookie
 * - On 403 (expired CSRF), refreshes CSRF once and retries
 */
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
  const init = {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    credentials: "include", // send cookies
    ...options
  };

  const method = (init.method || "GET").toUpperCase();

  // Add CSRF header for mutating requests
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCookie("owai_csrf");
    if (csrf) init.headers["X-CSRF-Token"] = csrf;
  }

  // ENTERPRISE FIX: Proper hybrid auth - ALWAYS send token if available
  // Cookies are sent automatically via credentials: "include"
  const token = localStorage.getItem("access_token");
  if (token) {
    init.headers.Authorization = `Bearer ${token}`;
    console.log("🔄 Enterprise hybrid auth: Sending token + cookies");
  } else {
    console.log("🍪 Enterprise cookie-only auth");
  }

  let res = await fetch(absoluteUrl, init);

  // If CSRF expired, get a fresh one and retry once
  if (res.status === 403) {
    try {
      await fetch(`${API_BASE_URL}/auth/csrf`, { credentials: "include" });
      const csrf = getCookie("owai_csrf");
      if (csrf && ["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
        init.headers["X-CSRF-Token"] = csrf;
      }
      res = await fetch(absoluteUrl, init);
    } catch {
      // fall through
    }
  }

  return res;
}

// Optional helpers (kept minimal)

export async function logout() {
  try {
    await fetchWithAuth("/auth/logout", { method: "POST" });
  } finally {
    // Clean up any legacy tokens if they exist
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.clear();
    window.location.href = "/";
  }
}

export async function getCurrentUser() {
  try {
    const res = await fetchWithAuth("/auth/me");
    if (res.ok) return await res.json();
    return null;
  } catch {
    return null;
  }
}