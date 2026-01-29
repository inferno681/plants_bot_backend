
(() => {
  const defaultBase = 'https://localhost:8000';
  const origin = /^https?:/i.test(window.location.origin)
    ? window.location.origin
    : '';
  const isDevServer = /:\/\/(localhost|127\.0\.0\.1):5173$/i.test(origin);
  const API_BASE = (window.API_BASE_URL || (isDevServer ? defaultBase : origin) || defaultBase)
    .replace(/\/$/, '');

  const ENDPOINTS = {
    PLANTS: `${API_BASE}/api/v1/plants`,
    STATS: `${API_BASE}/api/v1/plants/stats`,
    USER_ME: `${API_BASE}/api/v1/users/me`,
    LINK: `${API_BASE}/api/v1/link`,
    TG_LOGIN: `${API_BASE}/auth/telegram/login`,
    TG_REFRESH: `${API_BASE}/auth/telegram/refresh`,
    WEB_LOGIN: `${API_BASE}/auth/web/login`,
    WEB_REGISTER: `${API_BASE}/auth/web/registration`,
    WEB_REFRESH: `${API_BASE}/auth/web/refresh`,
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
