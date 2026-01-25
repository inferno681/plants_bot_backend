const { ENDPOINTS, STORAGE_KEYS, THEMES } = window.CONFIG;
const API_URL = ENDPOINTS.PLANTS;
const STATS_URL = ENDPOINTS.STATS;
const TG_LOGIN_URL = ENDPOINTS.TG_LOGIN;
const TG_REFRESH_URL = ENDPOINTS.TG_REFRESH;
const WEB_LOGIN_URL = ENDPOINTS.WEB_LOGIN;
const WEB_REGISTER_URL = ENDPOINTS.WEB_REGISTER;
const WEB_REFRESH_URL = ENDPOINTS.WEB_REFRESH;

let plants = [];
const filters = { text: '', mode: 'all' };
const state = { loading: true, error: null, stats: null };
const auth = { accessToken: null, refreshToken: null };
let telegramLoginAttempted = false;
const pagination = { cursor: null, hasMore: true, loading: false };

const loadTokens = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.AUTH);
    if (!stored) return;
    const parsed = JSON.parse(stored);
    auth.accessToken = parsed?.accessToken || null;
    auth.refreshToken = parsed?.refreshToken || null;
  } catch (error) {
    console.warn('Не удалось загрузить токены', error);
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

const authHeaders = () => {
  if (!auth.accessToken) return {};
  return { Authorization: `Bearer ${auth.accessToken}` };
};

const getCookieValue = (name) => {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
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
  showLoginModal();
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
      if (response.status !== 401) return response;
    }
  }

  setTokens(null, null);
  if (authMode === 'web') {
    showLoginModal();
  }
  return response;
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

const showLoginModal = () => {
  if (!elements.loginModal) return;
  if (elements.registerModal) elements.registerModal.hidden = true;
  elements.loginModal.hidden = false;
  if (elements.loginError) {
    elements.loginError.hidden = true;
    elements.loginError.textContent = '';
  }
  elements.loginEmail?.focus();
};

const hideLoginModal = () => {
  if (!elements.loginModal) return;
  elements.loginModal.hidden = true;
};

const showRegisterModal = () => {
  if (!elements.registerModal) return;
  if (elements.loginModal) elements.loginModal.hidden = true;
  elements.registerModal.hidden = false;
  if (elements.registerError) {
    elements.registerError.hidden = true;
    elements.registerError.textContent = '';
  }
  elements.registerEmail?.focus();
};

const hideRegisterModal = () => {
  if (!elements.registerModal) return;
  elements.registerModal.hidden = true;
};

const loginWithCredentials = async (email, password) => {
  try {
    const response = await fetch(WEB_LOGIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    const data = await response.json();
    setTokens(data.access_token || data.accessToken, null);
    hideLoginModal();
    return true;
  } catch (error) {
    console.error('Manual login failed', error);
    if (elements.loginError) {
      elements.loginError.hidden = false;
      elements.loginError.textContent = 'Неверный email или пароль';
    }
    return false;
  }
};

const registerWithCredentials = async (email, password, confirmPassword) => {
  if (password !== confirmPassword) {
    if (elements.registerError) {
      elements.registerError.hidden = false;
      elements.registerError.textContent = 'Пароли не совпадают';
    }
    return false;
  }

  try {
    const response = await fetch(WEB_REGISTER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    await response.json();
    hideRegisterModal();
    return loginWithCredentials(email, password);
  } catch (error) {
    console.error('Registration failed', error);
    if (elements.registerError) {
      elements.registerError.hidden = false;
      elements.registerError.textContent = 'Не удалось создать аккаунт';
    }
    return false;
  }
};

const elements = {
  stats: document.getElementById('stats'),
  cards: document.getElementById('cards'),
  timeline: document.getElementById('timeline'),
  search: document.getElementById('search'),
  filterPills: document.querySelectorAll('.pill'),
  refresh: document.getElementById('refresh'),
  themeToggle: document.getElementById('theme-toggle'),
  loadMore: document.getElementById('load-more'),
  loginModal: document.getElementById('login-modal'),
  loginForm: document.getElementById('login-form'),
  loginError: document.getElementById('login-error'),
  loginCancel: document.getElementById('login-cancel'),
  loginEmail: document.getElementById('login-email'),
  loginPassword: document.getElementById('login-password'),
  openRegister: document.getElementById('open-register'),
  registerModal: document.getElementById('register-modal'),
  registerForm: document.getElementById('register-form'),
  registerError: document.getElementById('register-error'),
  registerCancel: document.getElementById('register-cancel'),
  registerEmail: document.getElementById('register-email'),
  registerPassword: document.getElementById('register-password'),
  registerPasswordConfirm: document.getElementById('register-password-confirm'),
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

const formatDate = (value) => {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '-';
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
};

const daysUntil = (value) => {
  if (!value) return Infinity;
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) return Infinity;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  return Math.floor((target - today) / 86400000);
};

const statusBadge = (status) => {
  if (status === 'due') return { text: 'Нужно действие', cls: 'badge--due' };
  if (status === 'soon') return { text: 'Скоро', cls: 'badge--soon' };
  return { text: 'Все ок', cls: 'badge--ok' };
};

const formatMonthDay = (value) => {
  if (!value || typeof value.day !== 'number' || typeof value.month !== 'number') {
    return null;
  }
  return `${String(value.day).padStart(2, '0')}.${String(value.month).padStart(2, '0')}`;
};

const formatPeriod = (period) => {
  if (!period) return null;
  const start = formatMonthDay(period.start);
  const end = formatMonthDay(period.end);

  if (start && end) return `${start} - ${end}`;
  if (start) return `с ${start}`;
  if (end) return `до ${end}`;
  return null;
};

const computeStatus = (plant) => {
  const watering = daysUntil(plant.next_watering_at);
  const fertilizing = daysUntil(plant.next_fertilizing_at);
  const minDiff = Math.min(watering, fertilizing);

  if (minDiff <= 0) return 'due';
  if (minDiff <= 2) return 'soon';
  return 'ok';
};

const mapPlantFromApi = (plant) => {
  const warmPeriod = formatPeriod(plant.warm_period);
  const coldPeriod = formatPeriod(plant.cold_period);
  const note =
    plant.warm_period?.note || plant.cold_period?.note || plant.fertilizing?.note || plant.description || '';

  return {
    id: plant.id,
    name: plant.name || 'Без имени',
    scientificName: plant.scientific_name || '',
    description: plant.description || '',
    imageUrl: plant.image_url || null,
    warmPeriod,
    coldPeriod,
    lastWateredAt: plant.last_watered_at,
    lastFertilizedAt: plant.last_fertilized_at,
    nextWateringAt: plant.next_watering_at,
    nextFertilizingAt: plant.next_fertilizing_at,
    status: computeStatus(plant),
    note,
  };
};

const showNotice = (target, message, tone = 'muted') => {
  if (!target) return;
  target.innerHTML = `<div class="notice notice--${tone}">${message}</div>`;
};

const buildStats = () => {
  const total = state.stats?.total ?? plants.length;
  const attention = state.stats?.attention ?? 0;
  const weekTasks = state.stats?.watering_week ?? 0;
  const blocks = [
    { label: 'Всего растений', value: total },
    { label: 'Требуют внимания', value: attention },
    { label: 'Полив на неделю', value: weekTasks },
    { label: 'Синхронизация', value: 'Онлайн' },
  ];

  elements.stats.innerHTML = blocks
    .map(
      (b) =>
        `<div class="stat-card"><div class="label">${b.label}</div><div class="value">${b.value}</div></div>`,
    )
    .join('');
};

const renderCards = () => {
  if (state.loading) {
    showNotice(elements.cards, 'Загрузка растений...', 'muted');
    return;
  }

  if (state.error) {
    showNotice(elements.cards, state.error, 'danger');
    return;
  }

  const visible = plants.filter((plant) => {
    const matchText = `${plant.name} ${plant.scientificName}`.toLowerCase().includes(filters.text);
    if (!matchText) return false;
    if (filters.mode === 'due')
      return plant.status === 'due' || daysUntil(plant.nextWateringAt) <= 0 || daysUntil(plant.nextFertilizingAt) <= 0;
    if (filters.mode === 'frequent') {
      const minDays = Math.min(daysUntil(plant.nextWateringAt), daysUntil(plant.nextFertilizingAt));
      return Number.isFinite(minDays) && minDays <= 7;
    }
    if (filters.mode === 'rare') {
      const minDays = Math.min(daysUntil(plant.nextWateringAt), daysUntil(plant.nextFertilizingAt));
      return !Number.isFinite(minDays) || minDays >= 14;
    }
    return true;
  });

  if (!visible.length) {
    showNotice(elements.cards, 'Ничего не найдено по текущим фильтрам.', 'muted');
    return;
  }

  elements.cards.innerHTML = '';

  visible.forEach((plant) => {
    const { text, cls } = statusBadge(plant.status);
    const alertBadge = cls;
    const image = plant.imageUrl
      ? `<div class="card__image has-image" style="background-image: url('${plant.imageUrl}')"></div>`
      : '<div class="card__image"></div>';

    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      ${image}
      <div class="card__body">
        <h3 class="card__title">${plant.name}</h3>
        <div class="card__subtitle">${plant.scientificName || '-'}</div>
        <div class="badges">
          <span class="badge ${alertBadge}">${text}</span>
          <span class="badge badge--ok">Полив: ${formatDate(plant.nextWateringAt)}</span>
          <span class="badge badge--soon">Подкормка: ${formatDate(plant.nextFertilizingAt)}</span>
        </div>
        <div class="card__dates">
          <div class="date-chip">Полив: ${formatDate(plant.nextWateringAt)}</div>
          <div class="date-chip">Подкормка: ${formatDate(plant.nextFertilizingAt)}</div>
        </div>
      </div>
    `;
    card.dataset.id = plant.id;
    card.addEventListener('click', () => {
      window.location.href = `plant.html?id=${encodeURIComponent(plant.id)}`;
    });
    elements.cards.appendChild(card);
  });
};

const renderTasks = () => {
  const tasks = state.stats?.tasks || [];
  if (!tasks.length) {
    showNotice(elements.timeline, 'Пока нет запланированных задач.', 'muted');
    return;
  }

  elements.timeline.innerHTML = '';
  tasks.slice(0, 10).forEach((task) => {
    const li = document.createElement('li');
    li.className = 'timeline__item';
    li.innerHTML = `
      <div>
        <div class="title">${task.name}</div>
        <div class="note">${task.type === 'watering_with_fertilizing' ? 'Полив + подкормка' : 'Полив'}</div>
      </div>
      <div class="pill pill--small ${task.type === 'watering' ? 'is-active' : ''}">
        ${formatDate(task.date)}
      </div>
    `;
    li.addEventListener('click', () => {
      window.location.href = `plant.html?id=${encodeURIComponent(task.plant_id)}`;
    });
    elements.timeline.appendChild(li);
  });
};

const updateLoadMoreVisibility = () => {
  if (!elements.loadMore) return;
  elements.loadMore.hidden = !pagination.hasMore;
  elements.loadMore.disabled = pagination.loading;
  elements.loadMore.textContent = pagination.loading ? 'Загрузка...' : 'Загрузить ещё';
};

const fetchPlants = async (reset = false) => {
  if (pagination.loading) return;
  pagination.loading = true;
  state.error = null;
  if (reset) {
    state.loading = true;
    plants = [];
    pagination.cursor = null;
    pagination.hasMore = true;
    renderCards();
  }
  updateLoadMoreVisibility();

  try {
    const url = new URL(API_URL);
    url.searchParams.set('limit', '20');
    url.searchParams.set('order', 'name');
    if (pagination.cursor) {
      url.searchParams.set('cursor', pagination.cursor);
    }

    const response = await authFetch(url.toString());
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    const items = Array.isArray(data?.items) ? data.items : [];
    const mapped = items.map(mapPlantFromApi);
    plants = reset ? mapped : [...plants, ...mapped];
    pagination.cursor = data?.next_cursor || null;
    pagination.hasMore = Boolean(data?.has_more);
  } catch (error) {
    console.error(error);
    state.error = 'Не удалось загрузить данные. Проверьте, что бэкенд запущен.';
    plants = [];
    pagination.cursor = null;
    pagination.hasMore = false;
  } finally {
    state.loading = false;
    buildStats();
    renderCards();
    renderTasks();
    updateLoadMoreVisibility();
    pagination.loading = false;
  }
};

const fetchStats = async () => {
  try {
    const response = await authFetch(STATS_URL);
    if (!response.ok) throw new Error(`Status ${response.status}`);
    state.stats = await response.json();
  } catch (error) {
    console.error('Stats error', error);
    state.stats = null;
  } finally {
    buildStats();
    renderTasks();
  }
};

elements.search?.addEventListener('input', (e) => {
  filters.text = e.target.value.toLowerCase();
  renderCards();
});

elements.filterPills.forEach((pill) => {
  pill.addEventListener('click', () => {
    elements.filterPills.forEach((p) => p.classList.remove('is-active'));
    pill.classList.add('is-active');
    filters.mode = pill.dataset.filter;
    renderCards();
  });
});

elements.refresh?.addEventListener('click', () => {
  pagination.cursor = null;
  pagination.hasMore = true;
  fetchStats();
  fetchPlants(true);
});

elements.themeToggle?.addEventListener('click', () => {
  const current = document.body.classList.contains('theme-dark') ? THEMES.DARK : THEMES.LIGHT;
  applyTheme(current === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
});

elements.loadMore?.addEventListener('click', () => {
  fetchPlants();
});

elements.loginForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = elements.loginEmail?.value?.trim() || '';
  const password = elements.loginPassword?.value || '';
  if (!email || !password) return;
  const ok = await loginWithCredentials(email, password);
  if (ok) {
    fetchStats();
    fetchPlants(true);
  }
});

elements.loginCancel?.addEventListener('click', () => {
  hideLoginModal();
});

elements.openRegister?.addEventListener('click', () => {
  showRegisterModal();
});

elements.registerCancel?.addEventListener('click', () => {
  hideRegisterModal();
  showLoginModal();
});

elements.registerForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = elements.registerEmail?.value?.trim() || '';
  const password = elements.registerPassword?.value || '';
  const confirmPassword = elements.registerPasswordConfirm?.value || '';
  if (!email || !password || !confirmPassword) return;
  const ok = await registerWithCredentials(email, password, confirmPassword);
  if (ok) {
    fetchStats();
    fetchPlants(true);
  }
});

const cardsContainer = elements.cards?.parentElement;
cardsContainer?.addEventListener('scroll', () => {
  if (!pagination.hasMore || pagination.loading) return;
  if (cardsContainer.scrollTop + cardsContainer.clientHeight >= cardsContainer.scrollHeight - 80) {
    fetchPlants();
  }
});

const bootstrap = async () => {
  if (authMode === 'telegram' && window.Telegram?.WebApp?.ready) {
    window.Telegram.WebApp.ready();
  }
  initTheme();
  loadTokens();
  if (authMode === 'web' && !auth.accessToken) {
    showLoginModal();
  }
  const ok = await ensureAuth();
  if (!ok) {
    renderCards();
    renderTasks();
    return;
  }
  buildStats();
  renderCards();
  renderTasks();
  fetchStats();
  fetchPlants(true);
};

bootstrap();
