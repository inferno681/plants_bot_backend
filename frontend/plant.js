const { ENDPOINTS, STORAGE_KEYS, THEMES } = window.CONFIG;
const API_URL = ENDPOINTS.PLANTS;
const LOGIN_URL = ENDPOINTS.LOGIN;
const REFRESH_URL = ENDPOINTS.REFRESH;

const state = { loading: true, error: null, plant: null, saving: false, uploading: false };
const auth = { accessToken: null, refreshToken: null };
let plantId = null;

const elements = {
  heroImage: document.getElementById('hero-image'),
  name: document.getElementById('plant-name'),
  scientific: document.getElementById('plant-scientific'),
  description: document.getElementById('plant-description'),
  badges: document.getElementById('plant-badges'),
  grid: document.getElementById('detail-grid'),
  back: document.getElementById('back-btn'),
  themeToggle: document.getElementById('theme-toggle'),
  editToggle: document.getElementById('edit-toggle'),
  editPanel: document.getElementById('edit-panel'),
  editForm: document.getElementById('edit-form'),
  editStatus: document.getElementById('edit-status'),
  hideEdit: document.getElementById('hide-edit'),
  savePlant: document.getElementById('save-plant'),
  fieldName: document.getElementById('field-name'),
  fieldScientific: document.getElementById('field-scientific'),
  fieldDescription: document.getElementById('field-description'),
  fieldWarmStart: document.getElementById('field-warm-start'),
  fieldWarmEnd: document.getElementById('field-warm-end'),
  fieldWarmNote: document.getElementById('field-warm-note'),
  fieldColdStart: document.getElementById('field-cold-start'),
  fieldColdEnd: document.getElementById('field-cold-end'),
  fieldColdNote: document.getElementById('field-cold-note'),
  fieldFertStart: document.getElementById('field-fert-start'),
  fieldFertEnd: document.getElementById('field-fert-end'),
  fieldFertFrequency: document.getElementById('field-fert-frequency'),
  fieldFertType: document.getElementById('field-fert-type'),
  fieldFertNote: document.getElementById('field-fert-note'),
  fieldImage: document.getElementById('field-image'),
  uploadImage: document.getElementById('upload-image'),
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
    state.error = 'Не удалось авторизоваться. Попробуйте позже.';
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

  if (minDiff <= 0) return { text: 'Срочный уход', cls: 'badge--due' };
  if (minDiff <= 2) return { text: 'Скоро полив', cls: 'badge--soon' };
  return { text: 'Все спокойно', cls: 'badge--ok' };
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
    { label: 'Тёплый период', value: warmPeriod || '-' },
    { label: 'Холодный период', value: coldPeriod || '-' },
    { label: 'Период подкормок', value: fertilizingPeriod || '-' },
    {
      label: 'Частота подкормок',
      value:
        plant.fertilizing?.frequency && plant.fertilizing?.type
          ? `${plant.fertilizing.frequency} ${plant.fertilizing.type}`
          : '-',
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

const setEditStatus = (message = '', tone = 'muted') => {
  if (!elements.editStatus) return;
  elements.editStatus.textContent = message;
  elements.editStatus.classList.remove('edit-status--ok', 'edit-status--error');
  if (tone === 'ok') elements.editStatus.classList.add('edit-status--ok');
  if (tone === 'error') elements.editStatus.classList.add('edit-status--error');
};

const formatMonthDayInput = (value) => formatMonthDay(value) || '';

const fillEditForm = (plant) => {
  if (!plant) return;
  if (elements.fieldName) elements.fieldName.value = plant.name || '';
  if (elements.fieldScientific) elements.fieldScientific.value = plant.scientific_name || '';
  if (elements.fieldDescription) elements.fieldDescription.value = plant.description || '';

  if (elements.fieldWarmStart) elements.fieldWarmStart.value = formatMonthDayInput(plant.warm_period?.start);
  if (elements.fieldWarmEnd) elements.fieldWarmEnd.value = formatMonthDayInput(plant.warm_period?.end);
  if (elements.fieldWarmNote) elements.fieldWarmNote.value = plant.warm_period?.note || '';

  if (elements.fieldColdStart) elements.fieldColdStart.value = formatMonthDayInput(plant.cold_period?.start);
  if (elements.fieldColdEnd) elements.fieldColdEnd.value = formatMonthDayInput(plant.cold_period?.end);
  if (elements.fieldColdNote) elements.fieldColdNote.value = plant.cold_period?.note || '';

  if (elements.fieldFertStart) elements.fieldFertStart.value = formatMonthDayInput(plant.fertilizing?.start);
  if (elements.fieldFertEnd) elements.fieldFertEnd.value = formatMonthDayInput(plant.fertilizing?.end);
  if (elements.fieldFertFrequency) elements.fieldFertFrequency.value = plant.fertilizing?.frequency ?? '';
  if (elements.fieldFertType) elements.fieldFertType.value = plant.fertilizing?.type || 'days';
  if (elements.fieldFertNote) elements.fieldFertNote.value = plant.fertilizing?.note || '';
};

const parseMonthDayField = (value, label) => {
  const raw = (value || '').trim();
  if (!raw) return { value: null, error: null };

  const match = raw.match(/^(\d{1,2})\.(\d{1,2})$/);
  const day = match ? Number(match[1]) : null;
  const month = match ? Number(match[2]) : null;
  if (!match || !Number.isInteger(day) || !Number.isInteger(month)) {
    return { value: null, error: `Используйте формат дд.мм для поля "${label}".` };
  }
  if (day < 1 || day > 31 || month < 1 || month > 12) {
    return { value: null, error: `Введите корректный день и месяц для "${label}".` };
  }
  return { value: { day, month }, error: null };
};

const normalizeText = (value) => {
  const trimmed = (value || '').trim();
  return trimmed || null;
};

const buildWateringPayload = (current, startValue, endValue, noteValue, label) => {
  const start = parseMonthDayField(startValue, `${label} (начало)`);
  if (start.error) return { error: start.error };
  const end = parseMonthDayField(endValue, `${label} (конец)`);
  if (end.error) return { error: end.error };

  return {
    value: {
      start: start.value,
      end: end.value,
      schedule: current?.schedule ?? null,
      note: normalizeText(noteValue),
    },
  };
};

const buildFertilizingPayload = (current) => {
  const start = parseMonthDayField(elements.fieldFertStart?.value, 'Подкормки (начало)');
  if (start.error) return { error: start.error };
  const end = parseMonthDayField(elements.fieldFertEnd?.value, 'Подкормки (конец)');
  if (end.error) return { error: end.error };

  const rawFrequency = elements.fieldFertFrequency?.value ?? '';
  let frequency = null;
  if (rawFrequency !== '') {
    const parsed = Number(rawFrequency);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return { error: 'Частота подкормки должна быть положительным числом.' };
    }
    frequency = parsed;
  }

  return {
    value: {
      start: start.value,
      end: end.value,
      frequency,
      type: elements.fieldFertType?.value || current?.type || 'days',
      note: normalizeText(elements.fieldFertNote?.value),
    },
  };
};

const toggleEditPanel = (open) => {
  if (!elements.editPanel || !elements.editToggle) return;
  const shouldOpen = typeof open === 'boolean' ? open : elements.editPanel.hidden;
  elements.editPanel.hidden = !shouldOpen;
  elements.editPanel.classList.toggle('is-open', shouldOpen);
  elements.editPanel.setAttribute('aria-hidden', String(!shouldOpen));
  elements.editToggle.textContent = shouldOpen ? 'Свернуть' : 'Редактировать';
  elements.editToggle.setAttribute('aria-expanded', String(shouldOpen));
  if (shouldOpen) {
    elements.editPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

const ensureEditPanelClosed = () => {
  if (!elements.editPanel || !elements.editToggle) return;
  elements.editPanel.hidden = true;
  elements.editPanel.classList.remove('is-open');
  elements.editPanel.setAttribute('aria-hidden', 'true');
  elements.editToggle.textContent = 'Редактировать';
  elements.editToggle.setAttribute('aria-expanded', 'false');
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
  fillEditForm(plant);

};

const showError = (message) => {
  elements.name.textContent = 'Ошибка';
  elements.description.textContent = message;
  elements.badges.innerHTML = '';
  elements.grid.innerHTML = `<div class="detail-empty">${message}</div>`;
  setEditStatus(message, 'error');
};

const fetchPlant = async () => {
  if (!plantId) return;
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
    setEditStatus('');
  } catch (error) {
    console.error(error);
    state.error = 'Не удалось загрузить растение.';
    showError(state.error);
  } finally {
    state.loading = false;
  }
};

const buildUpdatePayload = () => {
  if (!state.plant) return null;

  const warm = buildWateringPayload(
    state.plant.warm_period,
    elements.fieldWarmStart?.value,
    elements.fieldWarmEnd?.value,
    elements.fieldWarmNote?.value,
    'Тёплый период',
  );
  if (warm?.error) {
    setEditStatus(warm.error, 'error');
    return null;
  }

  const cold = buildWateringPayload(
    state.plant.cold_period,
    elements.fieldColdStart?.value,
    elements.fieldColdEnd?.value,
    elements.fieldColdNote?.value,
    'Холодный период',
  );
  if (cold?.error) {
    setEditStatus(cold.error, 'error');
    return null;
  }

  const fertilizing = buildFertilizingPayload(state.plant.fertilizing);
  if (fertilizing?.error) {
    setEditStatus(fertilizing.error, 'error');
    return null;
  }

  const name = (elements.fieldName?.value || '').trim() || state.plant.name || '';
  const scientific = (elements.fieldScientific?.value || '').trim();

  return {
    name,
    scientific_name: scientific || null,
    description: normalizeText(elements.fieldDescription?.value),
    warm_period: warm?.value,
    cold_period: cold?.value,
    fertilizing: fertilizing?.value,
  };
};

const handleUpdatePlant = async (event) => {
  event?.preventDefault();
  if (!plantId || !state.plant || state.saving) return;

  const payload = buildUpdatePayload();
  if (!payload) return;

  state.saving = true;
  elements.savePlant?.setAttribute('disabled', 'disabled');
  setEditStatus('Сохраняем изменения...');

  try {
    const response = await authFetch(`${API_URL}/${plantId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Update failed with status ${response.status}`);
    }

    const data = await response.json();
    state.plant = data;
    renderPlant(data);
    setEditStatus('Изменения сохранены', 'ok');
  } catch (error) {
    console.error('Update error', error);
    setEditStatus('Не удалось сохранить изменения', 'error');
  } finally {
    state.saving = false;
    elements.savePlant?.removeAttribute('disabled');
  }
};

const handleUploadImage = async () => {
  if (!plantId) {
    setEditStatus('Не найден идентификатор растения', 'error');
    return;
  }
  if (state.uploading) {
    setEditStatus('Загрузка уже выполняется...', 'muted');
    return;
  }
  if (!elements.fieldImage || !elements.fieldImage.files?.length) {
    setEditStatus('Выберите файл для загрузки', 'error');
    return;
  }

  const file = elements.fieldImage.files[0];
  const formData = new FormData();
  formData.append('image', file);

  state.uploading = true;
  elements.uploadImage?.setAttribute('disabled', 'disabled');
  setEditStatus('Загружаем фото...');

  try {
    const response = await authFetch(`${API_URL}/${plantId}/image`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`Upload failed with status ${response.status}`);
    const data = await response.json();
    state.plant = data;
    renderPlant(data);
    elements.fieldImage.value = '';
    setEditStatus('Фото обновлено', 'ok');
  } catch (error) {
    console.error('Upload error', error);
    setEditStatus('Не удалось загрузить фото', 'error');
  } finally {
    state.uploading = false;
    elements.uploadImage?.removeAttribute('disabled');
  }
};

const bootstrap = async () => {
  initTheme();
  loadTokens();
  ensureEditPanelClosed();

  const params = new URLSearchParams(window.location.search);
  plantId = params.get('id');
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

  elements.editToggle?.addEventListener('click', () => toggleEditPanel());
  elements.hideEdit?.addEventListener('click', () => toggleEditPanel(false));
  elements.editForm?.addEventListener('submit', handleUpdatePlant);
  elements.uploadImage?.addEventListener('click', handleUploadImage);

  const ok = await ensureAuth();
  if (!ok) return;

  fetchPlant();
};

bootstrap();
