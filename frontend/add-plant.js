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

const customSelects = new Map();

const closeAllCustomSelects = (except) => {
  customSelects.forEach((instance) => {
    if (instance.wrapper !== except) {
      instance.wrapper.classList.remove('is-open');
      instance.trigger.setAttribute('aria-expanded', 'false');
    }
  });
};

const syncCustomSelect = (selectEl, instance) => {
  const selectedOption = selectEl.options[selectEl.selectedIndex];
  if (selectedOption) {
    instance.trigger.textContent = selectedOption.textContent;
    instance.options.forEach((optionBtn) => {
      optionBtn.classList.toggle('is-selected', optionBtn.dataset.value === selectedOption.value);
    });
  }
};

const enhanceSelect = (selectEl) => {
  if (!selectEl || selectEl.dataset.customized === 'true') return;

  const wrapper = document.createElement('div');
  wrapper.className = 'custom-select';

  const trigger = document.createElement('button');
  trigger.type = 'button';
  trigger.className = 'custom-select__trigger';
  trigger.setAttribute('aria-haspopup', 'listbox');
  trigger.setAttribute('aria-expanded', 'false');

  const menu = document.createElement('div');
  menu.className = 'custom-select__menu';
  menu.setAttribute('role', 'listbox');

  const optionButtons = Array.from(selectEl.options).map((option, index) => {
    const optionBtn = document.createElement('button');
    optionBtn.type = 'button';
    optionBtn.className = 'custom-select__option';
    optionBtn.textContent = option.textContent;
    optionBtn.dataset.value = option.value;
    optionBtn.dataset.index = String(index);
    optionBtn.setAttribute('role', 'option');
    if (selectEl.id) {
      optionBtn.id = `${selectEl.id}-option-${index}`;
    }
    optionBtn.addEventListener('click', () => {
      if (selectEl.value !== option.value) {
        selectEl.value = option.value;
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
      }
      syncCustomSelect(selectEl, instance);
      wrapper.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    });
    optionBtn.addEventListener('mouseenter', () => {
      instance.setActive(index);
    });
    menu.append(optionBtn);
    return optionBtn;
  });

  wrapper.append(trigger, menu);
  selectEl.classList.add('is-hidden');
  selectEl.dataset.customized = 'true';
  selectEl.insertAdjacentElement('afterend', wrapper);

  const setActive = (index) => {
    const nextIndex = Math.max(0, Math.min(optionButtons.length - 1, index));
    instance.activeIndex = nextIndex;
    optionButtons.forEach((optionBtn, idx) => {
      optionBtn.classList.toggle('is-active', idx === nextIndex);
    });
    const activeOption = optionButtons[nextIndex];
    if (activeOption?.id) {
      trigger.setAttribute('aria-activedescendant', activeOption.id);
    }
    activeOption?.scrollIntoView({ block: 'nearest' });
  };

  const chooseActive = () => {
    const activeOption = optionButtons[instance.activeIndex];
    if (!activeOption) return;
    if (selectEl.value !== activeOption.dataset.value) {
      selectEl.value = activeOption.dataset.value;
      selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    }
    syncCustomSelect(selectEl, instance);
    wrapper.classList.remove('is-open');
    trigger.setAttribute('aria-expanded', 'false');
  };

  const instance = { wrapper, trigger, menu, options: optionButtons, activeIndex: 0, setActive };
  customSelects.set(selectEl, instance);

  trigger.addEventListener('click', (event) => {
    event.preventDefault();
    const nextState = !wrapper.classList.contains('is-open');
    closeAllCustomSelects(wrapper);
    wrapper.classList.toggle('is-open', nextState);
    trigger.setAttribute('aria-expanded', String(nextState));
    if (nextState) {
      setActive(selectEl.selectedIndex);
    }
  });

  trigger.addEventListener('keydown', (event) => {
    const isOpen = wrapper.classList.contains('is-open');
    if (event.key === 'Escape') {
      wrapper.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!isOpen) {
        closeAllCustomSelects(wrapper);
        wrapper.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
        setActive(selectEl.selectedIndex);
        return;
      }
      const delta = event.key === 'ArrowDown' ? 1 : -1;
      setActive(instance.activeIndex + delta);
      return;
    }
    if (event.key === 'Home') {
      event.preventDefault();
      setActive(0);
      return;
    }
    if (event.key === 'End') {
      event.preventDefault();
      setActive(optionButtons.length - 1);
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (!isOpen) {
        closeAllCustomSelects(wrapper);
        wrapper.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
        setActive(selectEl.selectedIndex);
      } else {
        chooseActive();
      }
    }
  });

  selectEl.addEventListener('change', () => syncCustomSelect(selectEl, instance));
  syncCustomSelect(selectEl, instance);
};

const initCustomSelects = () => {
  document.querySelectorAll('select').forEach((selectEl) => enhanceSelect(selectEl));
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.custom-select')) {
      closeAllCustomSelects();
    }
  });
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

const getWeekdayInputs = (name) => Array.from(document.querySelectorAll(`input[name="${name}"]`));

const setGroupDisabledVisual = (groupEl, isDisabled) => {
  if (!groupEl) return;
  groupEl.classList.toggle('is-disabled', isDisabled);
};

const applyWeekdayRules = (kind, changedInput = null) => {
  const isWarm = kind === 'warm';
  const scheduleType = isWarm
    ? elements.fieldWarmScheduleType?.value || 'weekly'
    : elements.fieldColdScheduleType?.value || 'weekly';
  const weekdaysName = isWarm ? 'warm-weekday' : 'cold-weekday';
  const inputs = getWeekdayInputs(weekdaysName);
  const group = isWarm ? elements.warmWeekdaysGroup : elements.coldWeekdaysGroup;

  if (scheduleType === 'monthly') {
    inputs.forEach((input) => {
      input.checked = false;
      input.disabled = true;
    });
    setGroupDisabledVisual(group, true);
    return;
  }

  inputs.forEach((input) => {
    input.disabled = false;
  });
  setGroupDisabledVisual(group, false);

  if (scheduleType !== 'biweekly') {
    return;
  }

  if (changedInput && changedInput.checked) {
    inputs.forEach((input) => {
      if (input !== changedInput) {
        input.checked = false;
      }
    });
    return;
  }

  const selected = inputs.find((input) => input.checked);
  if (!selected) {
    return;
  }

  inputs.forEach((input) => {
    if (input !== selected) {
      input.checked = false;
    }
  });
};

const applyMonthdayRules = (kind) => {
  const isWarm = kind === 'warm';
  const scheduleType = isWarm
    ? elements.fieldWarmScheduleType?.value || 'weekly'
    : elements.fieldColdScheduleType?.value || 'weekly';
  const monthdayInput = isWarm ? elements.fieldWarmMonthday : elements.fieldColdMonthday;
  const group = isWarm ? elements.warmMonthdayGroup : elements.coldMonthdayGroup;

  if (monthdayInput) {
    const enabled = scheduleType === 'monthly';
    monthdayInput.disabled = !enabled;
    if (!enabled) {
      monthdayInput.value = '';
    }
    setGroupDisabledVisual(group, !enabled);
  }
};

const toggleScheduleFields = (kind) => {
  if (kind === 'warm') {
    if (elements.warmMonthdayGroup) elements.warmMonthdayGroup.hidden = false;
    if (elements.warmWeekdaysGroup) elements.warmWeekdaysGroup.hidden = false;
    applyMonthdayRules('warm');
    applyWeekdayRules('warm');
    return;
  }
  if (kind === 'cold') {
    if (elements.coldMonthdayGroup) elements.coldMonthdayGroup.hidden = false;
    if (elements.coldWeekdaysGroup) elements.coldWeekdaysGroup.hidden = false;
    applyMonthdayRules('cold');
    applyWeekdayRules('cold');
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
  initCustomSelects();

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

  getWeekdayInputs('warm-weekday').forEach((input) => {
    input.addEventListener('change', (event) => applyWeekdayRules('warm', event.target));
  });
  getWeekdayInputs('cold-weekday').forEach((input) => {
    input.addEventListener('change', (event) => applyWeekdayRules('cold', event.target));
  });

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
