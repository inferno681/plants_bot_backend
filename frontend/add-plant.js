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
  imageUploadBtn: document.getElementById('image-upload-btn'),
  imageInput: document.getElementById('image-input'),
  imageFilename: document.getElementById('image-filename'),
  imagePreviewWrap: document.getElementById('image-preview-wrap'),
  imagePreview: document.getElementById('image-preview'),
  fieldLastWateredAt: document.getElementById('field-last-watered-at'),
  fieldNextWateringAt: document.getElementById('field-next-watering-at'),
  fieldLastFertilizedAt: document.getElementById('field-last-fertilized-at'),
  fieldNextFertilizingAt: document.getElementById('field-next-fertilizing-at'),
  fieldWarmStart: document.getElementById('field-warm-start'),
  fieldWarmEnd: document.getElementById('field-warm-end'),
  fieldWarmNote: document.getElementById('field-warm-note'),
  fieldWarmScheduleType: document.getElementById('field-warm-schedule-type'),
  fieldWarmMonthday: document.getElementById('field-warm-monthday'),
  warmWeekdaysGroup: document.getElementById('warm-weekdays-group'),
  warmMonthdayGroup: document.getElementById('warm-monthday-group'),
  fieldColdStart: document.getElementById('field-cold-start'),
  fieldColdEnd: document.getElementById('field-cold-end'),
  fieldColdNote: document.getElementById('field-cold-note'),
  fieldColdScheduleType: document.getElementById('field-cold-schedule-type'),
  fieldColdMonthday: document.getElementById('field-cold-monthday'),
  coldWeekdaysGroup: document.getElementById('cold-weekdays-group'),
  coldMonthdayGroup: document.getElementById('cold-monthday-group'),
  fieldFertStart: document.getElementById('field-fert-start'),
  fieldFertEnd: document.getElementById('field-fert-end'),
  fieldFertFrequency: document.getElementById('field-fert-frequency'),
  fieldFertType: document.getElementById('field-fert-type'),
  fieldFertNote: document.getElementById('field-fert-note'),
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

const normalizeDate = (value) => {
  const trimmed = (value || '').trim();
  return trimmed || null;
};

let selectedImageFile = null;
let imagePreviewUrl = null;

const isValidMonthDay = (day, month) => {
  const date = new Date(Date.UTC(2000, month - 1, day));
  return date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
};

const parseMonthDayValue = (value) => {
  const raw = (value || '').trim();
  if (!raw) return null;
  const match = raw.match(/^(\d{1,2})\.(\d{1,2})$/);
  const day = match ? Number(match[1]) : null;
  const month = match ? Number(match[2]) : null;
  if (!match || !Number.isInteger(day) || !Number.isInteger(month)) return null;
  if (day < 1 || day > 31 || month < 1 || month > 12) return null;
  if (!isValidMonthDay(day, month)) return null;
  return { day, month };
};

const parseMonthDayField = (value, label) => {
  const raw = (value || '').trim();
  if (!raw) return { value: null, error: null };
  const parsed = parseMonthDayValue(raw);
  if (!parsed) {
    return { value: null, error: `Используйте формат дд.мм для поля "${label}".` };
  }
  return { value: parsed, error: null };
};

const pad2 = (value) => String(value).padStart(2, '0');

const formatMonthDay = (value) => `${pad2(value.day)}.${pad2(value.month)}`;

const shiftMonthDay = (value, deltaDays) => {
  const base = new Date(Date.UTC(2000, value.month - 1, value.day));
  base.setUTCDate(base.getUTCDate() + deltaDays);
  return { day: base.getUTCDate(), month: base.getUTCMonth() + 1 };
};

const readCheckedWeekdays = (name) =>
  Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
    .map((input) => Number(input.value))
    .filter((value) => Number.isInteger(value) && value >= 0 && value <= 6);

const hasAnyWateringInput = (startValue, endValue, noteValue, weekdays, monthdayValue) => {
  const hasText =
    (startValue || '').trim() ||
    (endValue || '').trim() ||
    (noteValue || '').trim() ||
    (monthdayValue || '').trim();
  return Boolean(hasText) || (weekdays && weekdays.length > 0);
};

const buildWateringSchedule = (type, weekdays, monthdayRaw, label) => {
  if (type === 'monthly') {
    const raw = (monthdayRaw || '').trim();
    if (!raw) {
      return { error: `Укажите число месяца для "${label}".` };
    }
    const monthday = Number(raw);
    if (!Number.isFinite(monthday) || monthday < 1 || monthday > 31) {
      return { error: `Число месяца для "${label}" должно быть от 1 до 31.` };
    }
    return { value: { type, monthday } };
  }

  if (!weekdays || weekdays.length === 0) {
    return { error: `Выберите дни недели для "${label}".` };
  }
  const weekdayValue = weekdays.length === 1 ? weekdays[0] : weekdays;
  return { value: { type, weekday: weekdayValue } };
};

const buildWateringPeriodPayload = ({
  startValue,
  endValue,
  noteValue,
  scheduleType,
  scheduleMonthday,
  scheduleWeekdayName,
  label,
}) => {
  const start = parseMonthDayField(startValue, `${label} (начало)`);
  if (start.error) return { error: start.error };
  const end = parseMonthDayField(endValue, `${label} (конец)`);
  if (end.error) return { error: end.error };

  const weekdays = readCheckedWeekdays(scheduleWeekdayName);
  const hasAny = hasAnyWateringInput(
    startValue,
    endValue,
    noteValue,
    weekdays,
    scheduleMonthday,
  );

  if (!hasAny) return { value: null };
  if (!start.value || !end.value) {
    return { error: `Заполните начало и конец для "${label}".` };
  }

  const schedule = buildWateringSchedule(
    scheduleType || 'weekly',
    weekdays,
    scheduleMonthday,
    label,
  );
  if (schedule.error) return { error: schedule.error };

  return {
    value: {
      start: start.value,
      end: end.value,
      schedule: schedule.value,
      note: normalizeText(noteValue),
    },
  };
};

const buildFertilizingPayload = () => {
  const start = parseMonthDayField(elements.fieldFertStart?.value, 'Подкормки (начало)');
  if (start.error) return { error: start.error };
  const end = parseMonthDayField(elements.fieldFertEnd?.value, 'Подкормки (конец)');
  if (end.error) return { error: end.error };

  const rawFrequency = (elements.fieldFertFrequency?.value || '').trim();
  const note = normalizeText(elements.fieldFertNote?.value);
  const hasAny =
    (elements.fieldFertStart?.value || '').trim() ||
    (elements.fieldFertEnd?.value || '').trim() ||
    rawFrequency ||
    note;

  if (!hasAny) return { value: null };
  if (!start.value || !end.value) {
    return { error: 'Заполните начало и конец для подкормок.' };
  }
  if (!rawFrequency) {
    return { error: 'Укажите частоту подкормки.' };
  }

  const frequency = Number(rawFrequency);
  if (!Number.isFinite(frequency) || frequency <= 0) {
    return { error: 'Частота подкормки должна быть положительным числом.' };
  }

  return {
    value: {
      start: start.value,
      end: end.value,
      frequency,
      type: elements.fieldFertType?.value || 'days',
      note,
    },
  };
};

const updateImagePreview = (file) => {
  if (imagePreviewUrl) {
    URL.revokeObjectURL(imagePreviewUrl);
    imagePreviewUrl = null;
  }

  if (!file) {
    if (elements.imagePreviewWrap) elements.imagePreviewWrap.hidden = true;
    if (elements.imagePreview) elements.imagePreview.removeAttribute('src');
    if (elements.imageFilename) elements.imageFilename.textContent = 'Файл не выбран';
    return;
  }

  imagePreviewUrl = URL.createObjectURL(file);
  if (elements.imagePreview) elements.imagePreview.src = imagePreviewUrl;
  if (elements.imagePreviewWrap) elements.imagePreviewWrap.hidden = false;
  if (elements.imageFilename) elements.imageFilename.textContent = file.name || 'Файл выбран';
};

const uploadPlantImage = async (plantId, file) => {
  if (!file) return { ok: true };
  const formData = new FormData();
  formData.append('image', file, file.name);

  const response = await authFetch(`${API_URL}/${plantId}/image`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Image upload failed with status ${response.status}`);
  }
  return { ok: true };
};

const toggleScheduleFields = (kind) => {
  if (kind === 'warm') {
    const type = elements.fieldWarmScheduleType?.value || 'weekly';
    const monthly = type === 'monthly';
    if (elements.warmMonthdayGroup) elements.warmMonthdayGroup.hidden = !monthly;
    if (elements.warmWeekdaysGroup) elements.warmWeekdaysGroup.hidden = monthly;
    return;
  }
  if (kind === 'cold') {
    const type = elements.fieldColdScheduleType?.value || 'weekly';
    const monthly = type === 'monthly';
    if (elements.coldMonthdayGroup) elements.coldMonthdayGroup.hidden = !monthly;
    if (elements.coldWeekdaysGroup) elements.coldWeekdaysGroup.hidden = monthly;
  }
};

let isAutoPeriodUpdate = false;

const updateComplementPeriod = (source) => {
  if (isAutoPeriodUpdate) return;
  const warmStart = parseMonthDayValue(elements.fieldWarmStart?.value);
  const warmEnd = parseMonthDayValue(elements.fieldWarmEnd?.value);
  const coldStart = parseMonthDayValue(elements.fieldColdStart?.value);
  const coldEnd = parseMonthDayValue(elements.fieldColdEnd?.value);

  if (source === 'warm' && warmStart && warmEnd) {
    const nextColdStart = shiftMonthDay(warmEnd, 1);
    const nextColdEnd = shiftMonthDay(warmStart, -1);
    isAutoPeriodUpdate = true;
    if (elements.fieldColdStart) elements.fieldColdStart.value = formatMonthDay(nextColdStart);
    if (elements.fieldColdEnd) elements.fieldColdEnd.value = formatMonthDay(nextColdEnd);
    isAutoPeriodUpdate = false;
  }

  if (source === 'cold' && coldStart && coldEnd) {
    const nextWarmStart = shiftMonthDay(coldEnd, 1);
    const nextWarmEnd = shiftMonthDay(coldStart, -1);
    isAutoPeriodUpdate = true;
    if (elements.fieldWarmStart) elements.fieldWarmStart.value = formatMonthDay(nextWarmStart);
    if (elements.fieldWarmEnd) elements.fieldWarmEnd.value = formatMonthDay(nextWarmEnd);
    isAutoPeriodUpdate = false;
  }
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

  const warm = buildWateringPeriodPayload({
    startValue: elements.fieldWarmStart?.value,
    endValue: elements.fieldWarmEnd?.value,
    noteValue: elements.fieldWarmNote?.value,
    scheduleType: elements.fieldWarmScheduleType?.value,
    scheduleMonthday: elements.fieldWarmMonthday?.value,
    scheduleWeekdayName: 'warm-weekday',
    label: 'Тёплый период',
  });
  if (warm?.error) {
    setStatus(warm.error, 'error');
    return;
  }

  const cold = buildWateringPeriodPayload({
    startValue: elements.fieldColdStart?.value,
    endValue: elements.fieldColdEnd?.value,
    noteValue: elements.fieldColdNote?.value,
    scheduleType: elements.fieldColdScheduleType?.value,
    scheduleMonthday: elements.fieldColdMonthday?.value,
    scheduleWeekdayName: 'cold-weekday',
    label: 'Холодный период',
  });
  if (cold?.error) {
    setStatus(cold.error, 'error');
    return;
  }

  const fertilizing = buildFertilizingPayload();
  if (fertilizing?.error) {
    setStatus(fertilizing.error, 'error');
    return;
  }

  const payload = {
    name,
    scientific_name: normalizeText(elements.fieldScientific?.value),
    description: normalizeText(elements.fieldDescription?.value),
    warm_period: warm?.value,
    cold_period: cold?.value,
    fertilizing: fertilizing?.value,
    last_watered_at: normalizeDate(elements.fieldLastWateredAt?.value),
    last_fertilized_at: normalizeDate(elements.fieldLastFertilizedAt?.value),
    next_watering_at: normalizeDate(elements.fieldNextWateringAt?.value),
    next_fertilizing_at: normalizeDate(elements.fieldNextFertilizingAt?.value),
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
    if (data?.id && selectedImageFile) {
      setStatus('Растение создано. Загружаем изображение...');
      try {
        await uploadPlantImage(data.id, selectedImageFile);
      } catch (error) {
        console.error('Upload error', error);
      }
    }
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

  elements.imageUploadBtn?.addEventListener('click', () => {
    elements.imageInput?.click();
  });
  elements.imageInput?.addEventListener('change', (event) => {
    const file = event.target?.files?.[0] || null;
    if (file && !file.type.startsWith('image/')) {
      setStatus('Выберите файл изображения.', 'error');
      event.target.value = '';
      selectedImageFile = null;
      updateImagePreview(null);
      return;
    }
    selectedImageFile = file;
    updateImagePreview(file);
  });

  elements.fieldWarmScheduleType?.addEventListener('change', () => toggleScheduleFields('warm'));
  elements.fieldColdScheduleType?.addEventListener('change', () => toggleScheduleFields('cold'));
  toggleScheduleFields('warm');
  toggleScheduleFields('cold');

  const handleWarmInput = () => updateComplementPeriod('warm');
  const handleColdInput = () => updateComplementPeriod('cold');
  elements.fieldWarmStart?.addEventListener('input', handleWarmInput);
  elements.fieldWarmEnd?.addEventListener('input', handleWarmInput);
  elements.fieldColdStart?.addEventListener('input', handleColdInput);
  elements.fieldColdEnd?.addEventListener('input', handleColdInput);

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
