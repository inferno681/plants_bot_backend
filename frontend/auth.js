(() => {
  const config = window.CONFIG || {};
  const ENDPOINTS = config.ENDPOINTS || {};
  const STORAGE_KEYS = config.STORAGE_KEYS || {};
  const AUTH_STORAGE_KEY = STORAGE_KEYS.AUTH || 'authTokens';
  const REFRESH_LOCK_KEY = `${AUTH_STORAGE_KEY}:refresh_lock`;
  const CHANNEL_NAME = 'plants-auth';
  const REFRESH_LOCK_TTL = 8000;
  const LAST_REFRESH_KEY = `${AUTH_STORAGE_KEY}:last_refresh`;

  const auth = { accessToken: null, refreshToken: null };
  const tabId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const channel = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel(CHANNEL_NAME) : null;
  let authMode = null;
  let refreshPromise = null;
  let telegramLoginAttempted = false;
  let initialized = false;
  let onAuthRequired = null;

  const safeParse = (raw) => {
    try {
      return JSON.parse(raw);
    } catch (error) {
      return null;
    }
  };

  const applyTokens = (accessToken, refreshToken, { persist = true, broadcast = true } = {}) => {
    auth.accessToken = accessToken || null;
    auth.refreshToken = refreshToken || null;
    if (persist) {
      try {
        localStorage.setItem(
          AUTH_STORAGE_KEY,
          JSON.stringify({ accessToken: auth.accessToken, refreshToken: auth.refreshToken }),
        );
      } catch (error) {
        console.warn('Failed to save tokens', error);
      }
    }
    if (broadcast && channel) {
      channel.postMessage({
        type: 'tokens',
        tokens: { accessToken: auth.accessToken, refreshToken: auth.refreshToken },
      });
    }
  };

  const loadTokens = () => {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return;
      const parsed = safeParse(stored);
      applyTokens(parsed?.accessToken || null, parsed?.refreshToken || null, {
        persist: false,
        broadcast: false,
      });
    } catch (error) {
      console.warn('Failed to load tokens', error);
    }
  };

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

  const computeAuthMode = () => (getTelegramInitData() ? 'telegram' : 'web');

  const authHeaders = () => (auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {});

  const readLock = () => {
    try {
      const raw = localStorage.getItem(REFRESH_LOCK_KEY);
      if (!raw) return null;
      const parsed = safeParse(raw);
      if (!parsed || typeof parsed.expiresAt !== 'number') return null;
      if (parsed.expiresAt <= Date.now()) {
        localStorage.removeItem(REFRESH_LOCK_KEY);
        return null;
      }
      return parsed;
    } catch (error) {
      return null;
    }
  };

  const acquireLock = () => {
    try {
      const existing = readLock();
      if (existing && existing.id !== tabId) {
        return false;
      }
      const lock = { id: tabId, expiresAt: Date.now() + REFRESH_LOCK_TTL };
      localStorage.setItem(REFRESH_LOCK_KEY, JSON.stringify(lock));
      const confirmed = readLock();
      return confirmed && confirmed.id === tabId;
    } catch (error) {
      return true;
    }
  };

  const releaseLock = () => {
    try {
      const lock = readLock();
      if (lock?.id === tabId) {
        localStorage.removeItem(REFRESH_LOCK_KEY);
      }
    } catch (error) {
      // ignore
    }
  };

  const waitForTokensUpdate = (timeoutMs = REFRESH_LOCK_TTL) =>
    new Promise((resolve) => {
      let done = false;
      const finish = (ok) => {
        if (done) return;
        done = true;
        cleanup();
        resolve(ok);
      };

      const handleStorage = (event) => {
        if (event.key !== AUTH_STORAGE_KEY) return;
        loadTokens();
        finish(Boolean(auth.accessToken));
      };

      const handleMessage = (event) => {
        if (event?.data?.type !== 'tokens') return;
        const tokens = event.data.tokens || {};
        applyTokens(tokens.accessToken || null, tokens.refreshToken || null, {
          persist: false,
          broadcast: false,
        });
        finish(Boolean(auth.accessToken));
      };

      const timeoutId = setTimeout(() => finish(false), timeoutMs);
      const cleanup = () => {
        clearTimeout(timeoutId);
        window.removeEventListener('storage', handleStorage);
        if (channel) channel.removeEventListener('message', handleMessage);
      };

      window.addEventListener('storage', handleStorage);
      if (channel) channel.addEventListener('message', handleMessage);
    });

  const loginWithTelegram = async () => {
    if (telegramLoginAttempted) return false;
    const initData = getTelegramInitData();
    if (!initData) return false;
    telegramLoginAttempted = true;

    try {
      const response = await fetch(ENDPOINTS.TG_LOGIN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData }),
      });
      if (!response.ok) throw new Error(`Status ${response.status}`);
      const data = await response.json();
      applyTokens(data.access_token || data.accessToken, data.refresh_token || data.refreshToken);
      return true;
    } catch (error) {
      console.error('Telegram login failed', error);
      return false;
    }
  };

  const refreshTokens = async ({ keepTokensOnFail = false } = {}) => {
    if (refreshPromise) return refreshPromise;
    refreshPromise = (async () => {
      const mode = authMode || computeAuthMode();
      loadTokens();
      if (mode === 'telegram' && !auth.refreshToken) return false;

      let lockAcquired = acquireLock();
      if (!lockAcquired) {
        const updated = await waitForTokensUpdate();
        if (updated) return true;
        lockAcquired = acquireLock();
        if (!lockAcquired) return false;
      }

      try {
        if (mode === 'telegram') {
          const response = await fetch(ENDPOINTS.TG_REFRESH, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: auth.refreshToken }),
          });

          if (!response.ok) {
            throw new Error(`Refresh failed with status ${response.status}`);
          }

          const data = await response.json();
          applyTokens(data.access_token || data.accessToken, data.refresh_token || data.refreshToken);
          try {
            localStorage.setItem(LAST_REFRESH_KEY, String(Date.now()));
          } catch (error) {
            // ignore
          }
          return true;
        }

        const csrfToken = getCookieValue('csrf_token');
        const response = await fetch(ENDPOINTS.WEB_REFRESH, {
          method: 'POST',
          headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`Refresh failed with status ${response.status}`);
        }

        const data = await response.json();
        applyTokens(data.access_token || data.accessToken, null);
        try {
          localStorage.setItem(LAST_REFRESH_KEY, String(Date.now()));
        } catch (error) {
          // ignore
        }
        return true;
      } catch (error) {
        console.error('Refresh error', error);
        if (mode === 'telegram') {
          if (!keepTokensOnFail) {
            applyTokens(null, null);
          }
        }
        return false;
      } finally {
        if (lockAcquired) releaseLock();
        refreshPromise = null;
      }
    })();
    return refreshPromise;
  };

  const ensureAuth = async () => {
    const mode = authMode || computeAuthMode();
    if (mode === 'telegram') {
      if (auth.accessToken) return true;
      if (await refreshTokens()) return true;
      if (await loginWithTelegram()) return true;
      return false;
    }

    if (auth.accessToken) {
      return true;
    }
    if (await refreshTokens()) return true;
    if (onAuthRequired) onAuthRequired();
    return false;
  };

  const authFetch = async (url, options = {}) => {
    const mode = authMode || computeAuthMode();
    const makeRequest = () => {
      const headers = { ...(options.headers || {}), ...authHeaders() };
      const nextOptions = { ...options, headers };
      if (mode === 'web') {
        nextOptions.credentials = 'include';
      }
      return fetch(url, nextOptions);
    };

    const lock = readLock();
    if (lock && lock.id !== tabId) {
      await waitForTokensUpdate();
    }

    if (refreshPromise) {
      await refreshPromise;
    }

    await ensureAuth();
    let response = await makeRequest();

    if (response.status !== 401) return response;

    const refreshed = await refreshTokens();
    if (refreshed) {
      response = await makeRequest();
      if (response.status !== 401) return response;
    }

    if (mode === 'telegram') {
      const loggedIn = await loginWithTelegram();
      if (loggedIn) {
        response = await makeRequest();
        if (response.status !== 401) return response;
      }
    }

    applyTokens(null, null);
    if (mode === 'web' && onAuthRequired) onAuthRequired();
    return response;
  };

  const setOnAuthRequired = (callback) => {
    onAuthRequired = typeof callback === 'function' ? callback : null;
  };

  const init = () => {
    if (initialized) return;
    authMode = computeAuthMode();
    loadTokens();
    window.addEventListener('storage', (event) => {
      if (event.key !== AUTH_STORAGE_KEY) return;
      loadTokens();
    });
    if (channel) {
      channel.addEventListener('message', (event) => {
        if (event?.data?.type !== 'tokens') return;
        const tokens = event.data.tokens || {};
        applyTokens(tokens.accessToken || null, tokens.refreshToken || null, {
          persist: false,
          broadcast: false,
        });
      });
    }
    initialized = true;
  };

  window.Auth = {
    init,
    setOnAuthRequired,
    getAuthMode: () => (authMode ? authMode : computeAuthMode()),
    getAccessToken: () => auth.accessToken,
    getRefreshToken: () => auth.refreshToken,
    setTokens: (accessToken, refreshToken) => applyTokens(accessToken, refreshToken),
    clearTokens: () => applyTokens(null, null),
    ensureAuth,
    refreshTokens,
    authFetch,
    loginWithTelegram,
  };
})();
