const { ENDPOINTS, STORAGE_KEYS, THEMES } = window.CONFIG;
const API_URL = ENDPOINTS.PLANTS;
const TG_LOGIN_URL = ENDPOINTS.TG_LOGIN;
const TG_REFRESH_URL = ENDPOINTS.TG_REFRESH;
const WEB_REFRESH_URL = ENDPOINTS.WEB_REFRESH;

const state = { saving: false };
const auth = { accessToken: null, refreshToken: null };
let telegramLoginAttempted = false;

const elements = {
  back: document.getElementById('back-btn'),
  themeToggle: document.getElementById('theme-toggle'),
  form: document.getElementById('create-form'),
  status: document.getElementById('create-status'),
  createButton: document.getElementById('create-plant'),
  cancel: document.getElementById('cancel-create'),
  fieldName: document.getElementById('field-name'),
  fieldScientific: document.getElementById('field-scientific'),
  fieldDescription: document.getElementById('field-description'),
};

const loadTokens = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.AUTH);
    if (!stored) return;
    const parsed = JSON.parse(stored);
    auth.accessToken = parsed?.accessToken || null;
    auth.refreshToken = parsed?.refreshToken || null;
  } catch (error) {
    console.warn('Не удалось прочитать токены', error);
  }
};

const saveTokens = () => {
  try {
    localStorage.setItem(
      STORAGE_KEYS.AUTH,
      JSON.stringify({ accessToken: auth.accessToken, refreshToken: auth.refreshToken }),
    );
  } catch (error) {
    console.warn('Не удалось сохранить токены', error);
  }
};

const setTokens = (accessToken, refreshToken) => {
  auth.accessToken = accessToken || null;
  auth.refreshToken = refreshToken || null;
  saveTokens();
};

const authHeaders = () => (auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {});

const getCookieValue = (name) => {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
};

const getTelegramInitData = () => {
  const sdkData = window.Telegram?.WebApp?.initData;
  if (sdkData) return sdkData;

  const params = new URLSearchParams(window.location.search);
  return (
    params.get('tgWebAppData') ||
    params.get('tgwebappdata') ||
    params.get('init_data')
  );
};

const authMode = getTelegramInitData() ? 'telegram' : 'web';

const loginWithTelegram = async () => {
  if (telegramLoginAttempted) return false;
  const initData = getTelegramInitData();
  if (!initData) return false;
  telegramLoginAttempted = true;

  try {
    const response = await fetch(TG_LOGIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData }),
    });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    const data = await response.json();
    setTokens(data.access_token || data.accessToken, data.refresh_token || data.refreshToken);
    return true;
  } catch (error) {
    console.error('Telegram login failed', error);
    return false;
  }
};

const refreshTokens = async () => {
  if (authMode === 'telegram') {
    if (!auth.refreshToken) return false;
    try {
      const response = await fetch(TG_REFRESH_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: auth.refreshToken }),
      });

      if (!response.ok) {
        throw new Error(`Refresh failed with status ${response.status}`);
      }

      const data = await response.json();
      setTokens(data.access_token || data.accessToken, data.refresh_token || data.refreshToken);
      return true;
    } catch (error) {
      console.error('Refresh error', error);
      setTokens(null, null);
      return false;
    }
  }

  const csrfToken = getCookieValue('csrf_token');
  if (!csrfToken) return false;

  try {
    const response = await fetch(WEB_REFRESH_URL, {
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Refresh failed with status ${response.status}`);
    }

    const data = await response.json();
    setTokens(data.access_token || data.accessToken, null);
    return true;
  } catch (error) {
    console.error('Refresh error', error);
    setTokens(null, null);
    return false;
  }
};

const ensureAuth = async () => {
  if (authMode === 'telegram') {
    if (auth.accessToken) return true;
    if (await refreshTokens()) return true;
    if (await loginWithTelegram()) return true;
    return false;
  }

  if (auth.accessToken) return true;
  if (await refreshTokens()) return true;
  return false;
};

const authFetch = async (url, options = {}) => {
  const makeRequest = () => {
    const headers = { ...(options.headers || {}), ...authHeaders() };
    const nextOptions = { ...options, headers };
    if (authMode === 'web') {
      nextOptions.credentials = 'include';
    }
    return fetch(url, nextOptions);
  };

  await ensureAuth();
  let response = await makeRequest();
  if (response.status !== 401) return response;

  const refreshed = await refreshTokens();
  if (refreshed) {
    response = await makeRequest();
    if (response.status !== 401) return response;
  }

  if (authMode === 'telegram') {
    const loggedIn = await loginWithTelegram();
    if (loggedIn) {
      response = await makeRequest();
    }
  }

  return response;
};

const applyTheme = (theme) => {
  document.body.classList.toggle('theme-dark', theme === THEMES.DARK);
  localStorage.setItem(STORAGE_KEYS.THEME, theme);
};

const initTheme = () => {
  const stored = localStorage.getItem(STORAGE_KEYS.THEME);
  const theme = stored === THEMES.LIGHT ? THEMES.LIGHT : THEMES.DARK;
  applyTheme(theme);
};

const setStatus = (message = '', tone = 'muted') => {
  if (!elements.status) return;
  elements.status.textContent = message;
  elements.status.classList.remove('edit-status--ok', 'edit-status--error');
  if (tone === 'ok') elements.status.classList.add('edit-status--ok');
  if (tone === 'error') elements.status.classList.add('edit-status--error');
};

const normalizeText = (value) => {
  const trimmed = (value || '').trim();
  return trimmed || null;
};

const handleCreate = async (event) => {
  event?.preventDefault();
  if (state.saving) return;

  const name = (elements.fieldName?.value || '').trim();
  if (!name) {
    setStatus('Введите название растения.', 'error');
    elements.fieldName?.focus();
    return;
  }

  const payload = {
    name,
    scientific_name: normalizeText(elements.fieldScientific?.value),
    description: normalizeText(elements.fieldDescription?.value),
  };

  state.saving = true;
  elements.createButton?.setAttribute('disabled', 'disabled');
  setStatus('Сохраняем карточку...');

  try {
    const response = await authFetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`Create failed with status ${response.status}`);
    const data = await response.json();
    setStatus('Растение создано', 'ok');
    if (data?.id) {
      window.location.href = `plant.html?id=${encodeURIComponent(data.id)}`;
    }
  } catch (error) {
    console.error('Create error', error);
    setStatus('Не удалось создать растение', 'error');
  } finally {
    state.saving = false;
    elements.createButton?.removeAttribute('disabled');
  }
};

const bootstrap = async () => {
  if (authMode === 'telegram' && window.Telegram?.WebApp?.ready) {
    window.Telegram.WebApp.ready();
  }
  initTheme();
  loadTokens();

  elements.back?.addEventListener('click', () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = 'index.html';
    }
  });
  elements.cancel?.addEventListener('click', () => {
    window.location.href = 'index.html';
  });
  elements.themeToggle?.addEventListener('click', () => {
    const current = document.body.classList.contains('theme-dark') ? THEMES.DARK : THEMES.LIGHT;
    applyTheme(current === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
  });
  elements.form?.addEventListener('submit', handleCreate);

  const ok = await ensureAuth();
  if (!ok) {
    if (authMode === 'web') {
      window.location.href = 'index.html';
      return;
    }
    setStatus('Не удалось авторизоваться.', 'error');
  }
};

bootstrap();
