/** Auth utilities — token + user management with auto-refresh */
import API_BASE from './api';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';
const REFRESH_ENDPOINT = '/api/auth/refresh';

let _refreshPromise = null;

export function saveToken(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null;
  try {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn() {
  return !!getToken();
}

/** Try to refresh access token via httpOnly cookie. Returns true on success. */
async function tryRefresh() {
  // Deduplicate concurrent refresh attempts
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}${REFRESH_ENDPOINT}`, {
        method: 'POST',
        credentials: 'include',  // send httpOnly cookie
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.token) {
        // Update stored token, keep existing user data
        const user = getStoredUser();
        saveToken(data.token, user);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();
  return _refreshPromise;
}

/** Fetch wrapper — auto-adds Authorization header + auto-refresh on 401 */
export async function apiFetch(url, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  let res = await fetch(url, { ...options, headers });

  // Token expired — try refresh once
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      const newToken = getToken();
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(url, { ...options, headers });
    }
  }

  // Still 401 after refresh — force login
  if (res.status === 401) {
    clearAuth();
    window.location.href = '/login';
  }

  return res;
}

/** Verify token is still valid, return user */
export async function verifyAuth() {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/api/user/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.status === 401) {
      const refreshed = await tryRefresh();
      if (refreshed) {
        const newToken = getToken();
        const retry = await fetch(`${API_BASE}/api/user/me`, {
          headers: { 'Authorization': `Bearer ${newToken}` },
        });
        if (retry.ok) {
          const user = await retry.json();
          saveToken(newToken, user);
          return user;
        }
      }
      clearAuth();
      return null;
    }
    if (!res.ok) {
      clearAuth();
      return null;
    }
    const user = await res.json();
    saveToken(token, user);
    return user;
  } catch {
    return null;
  }
}
