const apiBase = (window.API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_URL = `${apiBase}/api/v1/plants`;
const LOGIN_URL = `${apiBase}/api/auth/login_doc`;
const REFRESH_URL = `${apiBase}/api/auth/refresh`;

const state = { loading: true, error: null, plant: null };
const auth = { accessToken: null, refreshToken: null };

const loadTokens = () => {
  try {
    const stored = localStorage.getItem('authTokens');
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
      'authTokens',
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

const loginDoc = async () => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', 'doc');
    formData.append('password', '123');

    const response = await fetch(LOGIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Auth failed with status ${response.status}`);
    }

    const data = await response.json();
    setTokens(data.access_token || data.accessToken, data.refresh_token || data.refreshToken);
    return true;
  } catch (error) {
    console.error('Auth error', error);
    state.error = 'Не удалось авторизоваться. Обновите страницу.';
    return false;
  }
};

const refreshTokens = async () => {
  if (!auth.refreshToken) return false;

  try {
    const response = await fetch(REFRESH_URL, {
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
};

const ensureAuth = async () => {
  if (auth.accessToken) return true;
  if (await refreshTokens()) return true;
  return loginDoc();
};

const authFetch = async (url, options = {}) => {
  const makeRequest = () =>
    fetch(url, { ...options, headers: { ...(options.headers || {}), ...authHeaders() } });

  await ensureAuth();
  let response = await makeRequest();
  if (response.status !== 401) return response;

  const refreshed = await refreshTokens();
  if (refreshed) {
    response = await makeRequest();
    if (response.status !== 401) return response;
  }

  const loggedIn = await loginDoc();
  if (loggedIn) {
    response = await makeRequest();
  }

  return response;
};

const THEMES = { LIGHT: 'light', DARK: 'dark' };

const applyTheme = (theme) => {
  document.body.classList.toggle('theme-dark', theme === THEMES.DARK);
  localStorage.setItem('theme', theme);
};

const initTheme = () => {
  const stored = localStorage.getItem('theme');
  const theme = stored === THEMES.DARK ? THEMES.DARK : THEMES.LIGHT;
  applyTheme(theme);
};

const formatDate = (value) => {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '-';
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

const formatMonthDay = (value) => {
  if (!value || typeof value.day !== 'number' || typeof value.month !== 'number') return null;
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

const daysUntil = (value) => {
  if (!value) return Infinity;
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) return Infinity;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  return Math.floor((target - today) / 86400000);
};

const statusBadge = (plant) => {
  const watering = daysUntil(plant.next_watering_at);
  const fertilizing = daysUntil(plant.next_fertilizing_at);
  const minDiff = Math.min(watering, fertilizing);

  if (minDiff <= 0) return { text: 'Нужно внимание', cls: 'badge--due' };
  if (minDiff <= 2) return { text: 'Скоро задачи', cls: 'badge--soon' };
  return { text: 'Всё хорошо', cls: 'badge--ok' };
};

const elements = {
  heroImage: document.getElementById('hero-image'),
  name: document.getElementById('plant-name'),
  scientific: document.getElementById('plant-scientific'),
  description: document.getElementById('plant-description'),
  badges: document.getElementById('plant-badges'),
  grid: document.getElementById('detail-grid'),
  note: document.getElementById('detail-note'),
  back: document.getElementById('back-btn'),
  themeToggle: document.getElementById('theme-toggle'),
};

const renderBadges = (plant) => {
  const badges = [];
  badges.push(statusBadge(plant));
  badges.push({ text: `Полив: ${formatDate(plant.next_watering_at)}`, cls: 'badge--ok' });
  badges.push({ text: `Подкормка: ${formatDate(plant.next_fertilizing_at)}`, cls: 'badge--soon' });

  elements.badges.innerHTML = badges
    .map((b) => `<span class="badge ${b.cls}">${b.text}</span>`)
    .join('');
};

const renderGrid = (plant) => {
  const fertilizingPeriod = formatPeriod(plant.fertilizing);
  const warmPeriod = formatPeriod(plant.warm_period);
  const coldPeriod = formatPeriod(plant.cold_period);

  const items = [
    { label: 'Следующий полив', value: formatDate(plant.next_watering_at) },
    { label: 'Следующая подкормка', value: formatDate(plant.next_fertilizing_at) },
    { label: 'Последний полив', value: formatDate(plant.last_watered_at) },
    { label: 'Последняя подкормка', value: formatDate(plant.last_fertilized_at) },
    { label: 'Тёплый период', value: warmPeriod || '—' },
    { label: 'Холодный период', value: coldPeriod || '—' },
    { label: 'Период подкормки', value: fertilizingPeriod || '—' },
    {
      label: 'Частота подкормки',
      value:
        plant.fertilizing?.frequency && plant.fertilizing?.type
          ? `${plant.fertilizing.frequency} ${plant.fertilizing.type}`
          : '—',
    },
  ];

  elements.grid.innerHTML = items
    .map(
      (item) => `
        <article class="detail-card">
          <div class="label">${item.label}</div>
          <div class="value">${item.value}</div>
        </article>
      `,
    )
    .join('');
};

const renderPlant = (plant) => {
  elements.name.textContent = plant.name || 'Без названия';
  elements.scientific.textContent = plant.scientific_name || '';
  elements.description.textContent = plant.description || 'Описание отсутствует.';

  if (plant.image_url) {
    elements.heroImage.classList.add('has-image');
    elements.heroImage.style.backgroundImage = `url('${plant.image_url}')`;
  } else {
    elements.heroImage.classList.remove('has-image');
    elements.heroImage.style.backgroundImage = '';
  }

  renderBadges(plant);
  renderGrid(plant);

  const note =
    plant.warm_period?.note ||
    plant.cold_period?.note ||
    plant.fertilizing?.note ||
    '';
  if (note) {
    elements.note.hidden = false;
    elements.note.textContent = note;
  } else {
    elements.note.hidden = true;
  }
};

const showError = (message) => {
  elements.name.textContent = 'Ошибка';
  elements.description.textContent = message;
  elements.badges.innerHTML = '';
  elements.grid.innerHTML = `<div class="detail-empty">${message}</div>`;
  elements.note.hidden = true;
};

const fetchPlant = async (plantId) => {
  state.loading = true;
  state.error = null;
  try {
    const response = await authFetch(`${API_URL}/${plantId}`);
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const data = await response.json();
    state.plant = data;
    renderPlant(data);
  } catch (error) {
    console.error(error);
    state.error = 'Не удалось загрузить растение.';
    showError(state.error);
  } finally {
    state.loading = false;
  }
};

const bootstrap = async () => {
  initTheme();
  loadTokens();

  const params = new URLSearchParams(window.location.search);
  const plantId = params.get('id');
  if (!plantId) {
    showError('Не указан идентификатор растения.');
    return;
  }

  elements.themeToggle?.addEventListener('click', () => {
    const current = document.body.classList.contains('theme-dark') ? THEMES.DARK : THEMES.LIGHT;
    applyTheme(current === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
  });

  elements.back?.addEventListener('click', () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = 'index.html';
    }
  });

  const ok = await ensureAuth();
  if (!ok) return;

  fetchPlant(plantId);
};

bootstrap();
