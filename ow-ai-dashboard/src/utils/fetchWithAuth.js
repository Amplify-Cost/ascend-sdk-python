/**
 * Enterprise Cookie-Based Authentication (OW-AI)
 * - Secure HTTP-only cookies + CSRF protection
 * - No token storage in localStorage/sessionStorage
 * - CORS-safe, AWS-ready
 */

// Prefer explicit env; otherwise fall back to current origin (works behind proxies)
const API_BASE_URL =
  (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) ||
  window.location.origin;

let csrfToken = null;

// Cache in-flight GET /auth/me request to avoid duplicate calls on mount
const inFlight = new Map();

/** Build absolute URL against the API base */
function buildUrl(url) {
  if (/^https?:\/\//i.test(url)) return url;
  return `${API_BASE_URL.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}`;
}

/** Get CSRF token for state-changing requests (always absolute URL) */
async function getCSRFToken() {
  if (csrfToken) return csrfToken;
  try {
    const res = await fetch(buildUrl('/auth/csrf-token'), {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-store',
      },
      mode: 'cors',
    });
    if (res.ok) {
      const data = await res.json();
      csrfToken = data.csrf_token || data.csrf || null;
      return csrfToken;
    }
  } catch (err) {
    console.warn('Failed to get CSRF token:', err);
  }
  return null;
}

/** Clear cached CSRF token (e.g., after 401/403) */
function clearCSRFToken() {
  csrfToken = null;
}

/**
 * Enterprise fetch wrapper with:
 * - credentials: 'include' (cookie auth)
 * - X-Requested-With for CSRF frameworks
 * - No-cache on auth calls
 * - One safe retry on 403 after refreshing CSRF
 * - No redirect loop on initial /auth/me check
 *
 * options.suppressRedirectOn401:
 *   - default true for GET requests; prevents login loop
 */
export async function fetchWithAuth(url, options = {}) {
  const absoluteUrl = buildUrl(url);
  const method = (options.method || 'GET').toUpperCase();

  // Base headers for JSON APIs
  const baseHeaders = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.headers || {}),
  };

  // Never send Bearer to cookie-protected endpoints
  if ('Authorization' in baseHeaders) {
    delete baseHeaders.Authorization;
  }

  // Add CSRF on state-changing requests
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    const csrf = await getCSRFToken();
    if (csrf) baseHeaders['X-CSRF-Token'] = csrf;
  }

  // Avoid Content-Type on requests with no body (helps with CORS preflights & some servers)
  const hasBody = !!options.body;
  let fetchOptionsHeaders;
  if (!hasBody) {
    const { ['Content-Type']: _omit, ...rest } = baseHeaders;
    fetchOptionsHeaders = rest;
  } else {
    fetchOptionsHeaders = baseHeaders;
  }

  const fetchOptions = {
    ...options,
    method,
    headers: fetchOptionsHeaders,
    credentials: 'include',
    mode: 'cors',
    cache: 'no-store',
  };

  // Dedupe GET /auth/me calls to avoid flashing on mount
  const key =
    method === 'GET' && absoluteUrl.endsWith('/auth/me')
      ? `${method}:${absoluteUrl}`
      : null;
  if (key && inFlight.has(key)) {
    return inFlight.get(key);
  }

  const doFetch = async () => {
    let response = await fetch(absoluteUrl, fetchOptions);

    // 403 → try once with fresh CSRF
    if (response.status === 403 && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      console.warn('🛡️ CSRF validation failed — refreshing token and retrying once');
      clearCSRFToken();
      const fresh = await getCSRFToken();
      if (fresh) {
        fetchOptions.headers = { ...fetchOptions.headers, 'X-CSRF-Token': fresh };
        response = await fetch(absoluteUrl, fetchOptions);
      }
    }

    // 401 handling
    const suppressRedirectOn401 =
      options.suppressRedirectOn401 !== undefined
        ? !!options.suppressRedirectOn401
        : method === 'GET';

    if (response.status === 401) {
      console.warn('🍪 Authentication required (401)');
      clearCSRFToken();
      if (!suppressRedirectOn401) {
        window.location.href = '/login';
      }
    }

    return response;
  };

  const promise = doFetch().finally(() => {
    if (key) inFlight.delete(key);
  });

  if (key) inFlight.set(key, promise);
  return promise;
}

/** Helper: App-level auth check (server is the source of truth) */
export function isAuthenticated() {
  return true;
}

/** Enterprise logout */
export function logout() {
  fetchWithAuth('/auth/logout', { method: 'POST', suppressRedirectOn401: true })
    .then(() => {
      clearCSRFToken();
      window.location.href = '/';
    })
    .catch((err) => {
      console.error('Logout error:', err);
      window.location.href = '/';
    });
}

/** Get current user via cookie auth (no redirect loop on 401) */
export async function getCurrentUser() {
  try {
    console.log('🔍 Getting current user via enterprise cookie auth...');
    const res = await fetchWithAuth('/auth/me', {
      method: 'GET',
      suppressRedirectOn401: true,
    });

    if (res.ok) {
      const user = await res.json();
      console.log('✅ User data via cookies:', user.email || user.user_id);
      return { ...user, enterprise_validated: true, auth_source: 'cookie' };
    }

    if (res.status === 401) {
      console.log('ℹ️ Not authenticated — show login');
      return null;
    }

    throw new Error(`Failed to get user: ${res.status}`);
  } catch (err) {
    console.error('❌ Error getting current user:', err);
    return null;
  }
}
