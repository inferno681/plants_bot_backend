const { ENDPOINTS } = window.CONFIG;
const API_URL = ENDPOINTS.PLANTS;
const STATS_URL = ENDPOINTS.STATS;
const USER_ME_URL = ENDPOINTS.USER_ME;
const WEB_LOGIN_URL = ENDPOINTS.WEB_LOGIN;
const WEB_REGISTER_URL = ENDPOINTS.WEB_REGISTER;

let plants = [];
const filters = { text: '', mode: 'all' };
const state = { loading: true, error: null, stats: null, user: null };
const pagination = { cursor: null, hasMore: true, loading: false };
const auth = window.Auth;
const authFetch = (...args) => auth.authFetch(...args);
const ensureAuth = () => auth.ensureAuth();
const { initTheme, toggleTheme, formatDate, formatPeriod, daysUntil } = window.UI;
let authMode = 'web';

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
    auth.setTokens(data.access_token || data.accessToken, null);
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

const statusBadge = (status) => {
  if (status === 'due') return { text: 'Нужно действие', cls: 'badge--due' };
  if (status === 'soon') return { text: 'Скоро', cls: 'badge--soon' };
  return { text: 'Все ок', cls: 'badge--ok' };
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

const buildUserCard = () => {
  const user = state.user;
  if (!user) return { label: 'Пользователь', value: '—' };
  if (user.email) return { label: 'Пользователь', value: user.email };
  if (user.telegram_linked || user.telegram_id) {
    const value = user.telegram_id ? `Telegram ${user.telegram_id}` : 'Telegram подключен';
    return { label: 'Telegram', value };
  }
  return { label: 'Пользователь', value: '—' };
};

const buildStats = () => {
  const total = state.stats?.total ?? plants.length;
  const attention = state.stats?.attention ?? 0;
  const weekTasks = state.stats?.watering_week ?? 0;
  const userCard = buildUserCard();
  const blocks = [
    { label: 'Всего растений', value: total },
    userCard,
    { label: 'Полив на неделю', value: weekTasks },
    { label: 'Требуют внимания', value: attention },
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
    if (filters.mode === 'week') {
      const days = daysUntil(plant.nextWateringAt);
      return Number.isFinite(days) && days >= 0 && days <= 7;
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
    if (response.status === 401) {
      state.stats = null;
      return;
    }
    if (!response.ok) throw new Error(`Status ${response.status}`);
    state.stats = await response.json();
  } catch (error) {
    state.stats = null;
  } finally {
    buildStats();
    renderTasks();
  }
};

const fetchUser = async () => {
  try {
    const response = await authFetch(USER_ME_URL);
    if (response.status === 401) {
      state.user = null;
      return;
    }
    if (!response.ok) throw new Error(`Status ${response.status}`);
    state.user = await response.json();
  } catch (error) {
    state.user = null;
  } finally {
    buildStats();
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

elements.refresh?.addEventListener('click', async () => {
  pagination.cursor = null;
  pagination.hasMore = true;
  await fetchStats();
  await fetchUser();
  await fetchPlants(true);
});

elements.themeToggle?.addEventListener('click', () => {
  toggleTheme();
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
    await fetchStats();
    await fetchUser();
    await fetchPlants(true);
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
    await fetchStats();
    await fetchUser();
    await fetchPlants(true);
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
  auth.init();
  auth.setOnAuthRequired(showLoginModal);
  authMode = auth.getAuthMode();
  if (authMode === 'telegram' && window.Telegram?.WebApp?.ready) {
    window.Telegram.WebApp.ready();
  }
  initTheme();
  if (authMode === 'web' && !auth.getAccessToken()) {
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
  await fetchStats();
  await fetchUser();
  await fetchPlants(true);
};

bootstrap();
