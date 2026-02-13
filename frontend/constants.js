
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
    USER_EMAIL_CONFIRMATION: `${API_BASE}/api/v1/users/email/confirmation`,
    USER_EMAIL_CONFIRM: `${API_BASE}/api/v1/users/email/confirm`,
    LINK: `${API_BASE}/api/v1/link`,
    WEB_LOGIN_DOC: `${API_BASE}/auth/web/login_doc`,
    TG_LOGIN: `${API_BASE}/auth/telegram/login`,
    TG_LOGOUT: `${API_BASE}/auth/telegram/logout`,
    TG_LOGOUT_OTHERS: `${API_BASE}/auth/telegram/logout_others`,
    TG_LOGOUT_ALL: `${API_BASE}/auth/telegram/logout_all`,
    TG_REFRESH: `${API_BASE}/auth/telegram/refresh`,
    WEB_LOGIN: `${API_BASE}/auth/web/login`,
    WEB_REGISTER: `${API_BASE}/auth/web/registration`,
    WEB_LOGOUT: `${API_BASE}/auth/web/logout`,
    WEB_LOGOUT_OTHERS: `${API_BASE}/auth/web/logout_others`,
    WEB_LOGOUT_ALL: `${API_BASE}/auth/web/logout_all`,
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
