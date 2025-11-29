
(() => {
  const defaultBase = /^https?:/i.test(window.location.origin)
    ? window.location.origin
    : 'http://localhost:8000';
  const API_BASE = (window.API_BASE_URL || defaultBase).replace(/\/$/, '');

  const ENDPOINTS = {
    PLANTS: `${API_BASE}/api/v1/plants`,
    STATS: `${API_BASE}/api/v1/plants/stats`,
    TG_LOGIN: `${API_BASE}/api/auth/login`,
    LOGIN: `${API_BASE}/api/auth/login_doc`,
    REFRESH: `${API_BASE}/api/auth/refresh`,
  };

  const STORAGE_KEYS = {
    AUTH: 'authTokens',
    THEME: 'theme',
  };

  const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
  };

  window.CONFIG = { API_BASE, ENDPOINTS, STORAGE_KEYS, THEMES };
})();
