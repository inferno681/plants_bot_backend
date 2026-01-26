const { ENDPOINTS, STORAGE_KEYS, THEMES } = window.CONFIG;
const API_URL = ENDPOINTS.PLANTS;

const state = { loading: true, error: null, plant: null, saving: false, uploading: false };
const auth = window.Auth;
const authFetch = (...args) => auth.authFetch(...args);
const ensureAuth = () => auth.ensureAuth();
let authMode = 'web';
let plantId = null;
let imagePreviewUrl = null;
let selectedImageFile = null;

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

const formatDateInput = (value) => {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  return d.toISOString().slice(0, 10);
};

const formatMonthDay = (value) => {
  if (!value || typeof value.day !== 'number' || typeof value.month !== 'number') return null;
  return `${String(value.day).padStart(2, '0')}.${String(value.month).padStart(2, '0')}`;
};

const pad2 = (value) => String(value).padStart(2, '0');

const parseMonthDayValue = (value) => {
  const raw = (value || '').trim();
  if (!raw) return null;
  const match = raw.match(/^(\d{1,2})\.(\d{1,2})$/);
  const day = match ? Number(match[1]) : null;
  const month = match ? Number(match[2]) : null;
  if (!match || !Number.isInteger(day) || !Number.isInteger(month)) return null;
  if (day < 1 || day > 31 || month < 1 || month > 12) return null;
  const date = new Date(Date.UTC(2000, month - 1, day));
  if (date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return null;
  return { day, month };
};

const shiftMonthDay = (value, deltaDays) => {
  const base = new Date(Date.UTC(2000, value.month - 1, value.day));
  base.setUTCDate(base.getUTCDate() + deltaDays);
  return { day: base.getUTCDate(), month: base.getUTCMonth() + 1 };
};

const formatMonthDayString = (value) => `${pad2(value.day)}.${pad2(value.month)}`;

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

const getWeekdayInputs = (name) => Array.from(document.querySelectorAll(`input[name="${name}"]`));

const setScheduleFields = (kind, schedule) => {
  const isWarm = kind === 'warm';
  const select = isWarm ? elements.fieldWarmScheduleType : elements.fieldColdScheduleType;
  const monthdayInput = isWarm ? elements.fieldWarmMonthday : elements.fieldColdMonthday;
  const weekdayName = isWarm ? 'warm-weekday' : 'cold-weekday';

  if (select) {
    select.value = schedule?.type || 'weekly';
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }

  if (monthdayInput) {
    monthdayInput.value = schedule?.monthday ? String(schedule.monthday) : '';
  }

  const values = Array.isArray(schedule?.weekday)
    ? schedule.weekday
    : Number.isInteger(schedule?.weekday)
      ? [schedule.weekday]
      : [];

  getWeekdayInputs(weekdayName).forEach((input) => {
    const numericValue = Number(input.value);
    input.checked = values.includes(numericValue);
  });
};

const fillEditForm = (plant) => {
  if (!plant) return;
  if (elements.fieldName) elements.fieldName.value = plant.name || '';
  if (elements.fieldScientific) elements.fieldScientific.value = plant.scientific_name || '';
  if (elements.fieldDescription) elements.fieldDescription.value = plant.description || '';

  if (elements.fieldLastWateredAt) {
    elements.fieldLastWateredAt.value = formatDateInput(plant.last_watered_at);
  }
  if (elements.fieldNextWateringAt) {
    elements.fieldNextWateringAt.value = formatDateInput(plant.next_watering_at);
  }
  if (elements.fieldLastFertilizedAt) {
    elements.fieldLastFertilizedAt.value = formatDateInput(plant.last_fertilized_at);
  }
  if (elements.fieldNextFertilizingAt) {
    elements.fieldNextFertilizingAt.value = formatDateInput(plant.next_fertilizing_at);
  }

  if (elements.fieldWarmStart) elements.fieldWarmStart.value = formatMonthDayInput(plant.warm_period?.start);
  if (elements.fieldWarmEnd) elements.fieldWarmEnd.value = formatMonthDayInput(plant.warm_period?.end);
  if (elements.fieldWarmNote) elements.fieldWarmNote.value = plant.warm_period?.note || '';
  setScheduleFields('warm', plant.warm_period?.schedule);

  if (elements.fieldColdStart) elements.fieldColdStart.value = formatMonthDayInput(plant.cold_period?.start);
  if (elements.fieldColdEnd) elements.fieldColdEnd.value = formatMonthDayInput(plant.cold_period?.end);
  if (elements.fieldColdNote) elements.fieldColdNote.value = plant.cold_period?.note || '';
  setScheduleFields('cold', plant.cold_period?.schedule);

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

const normalizeDate = (value) => {
  const trimmed = (value || '').trim();
  return trimmed || null;
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
    if (elements.fieldColdStart) elements.fieldColdStart.value = formatMonthDayString(nextColdStart);
    if (elements.fieldColdEnd) elements.fieldColdEnd.value = formatMonthDayString(nextColdEnd);
    isAutoPeriodUpdate = false;
  }

  if (source === 'cold' && coldStart && coldEnd) {
    const nextWarmStart = shiftMonthDay(coldEnd, 1);
    const nextWarmEnd = shiftMonthDay(coldStart, -1);
    isAutoPeriodUpdate = true;
    if (elements.fieldWarmStart) elements.fieldWarmStart.value = formatMonthDayString(nextWarmStart);
    if (elements.fieldWarmEnd) elements.fieldWarmEnd.value = formatMonthDayString(nextWarmEnd);
    isAutoPeriodUpdate = false;
  }
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

const requestLogin = () => {
  showError('Сессия истекла. Пожалуйста, войдите снова.');
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
    setEditStatus(warm.error, 'error');
    return null;
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
    last_watered_at: normalizeDate(elements.fieldLastWateredAt?.value),
    last_fertilized_at: normalizeDate(elements.fieldLastFertilizedAt?.value),
    next_watering_at: normalizeDate(elements.fieldNextWateringAt?.value),
    next_fertilizing_at: normalizeDate(elements.fieldNextFertilizingAt?.value),
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
    if (selectedImageFile) {
      setEditStatus('Изменения сохранены. Загружаем фото...');
      await handleUploadImage(selectedImageFile);
      selectedImageFile = null;
      updateImagePreview(null);
    } else {
      setEditStatus('Изменения сохранены', 'ok');
    }
  } catch (error) {
    console.error('Update error', error);
    setEditStatus('Не удалось сохранить изменения', 'error');
  } finally {
    state.saving = false;
    elements.savePlant?.removeAttribute('disabled');
  }
};

const handleUploadImage = async (file) => {
  if (!plantId) {
    setEditStatus('Не найден идентификатор растения', 'error');
    return;
  }
  if (state.uploading) {
    setEditStatus('Загрузка уже выполняется...', 'muted');
    return;
  }
  if (!file) return;

  const formData = new FormData();
  formData.append('image', file);

  state.uploading = true;
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
    if (elements.imageInput) elements.imageInput.value = '';
    updateImagePreview(null);
    setEditStatus('Фото обновлено', 'ok');
  } catch (error) {
    console.error('Upload error', error);
    setEditStatus('Не удалось загрузить фото', 'error');
  } finally {
    state.uploading = false;
  }
};

const bootstrap = async () => {
  auth.init();
  auth.setOnAuthRequired(requestLogin);
  authMode = auth.getAuthMode();
  if (authMode === 'telegram' && window.Telegram?.WebApp?.ready) {
    window.Telegram.WebApp.ready();
  }
  initTheme();
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
  initCustomSelects();

  elements.imageUploadBtn?.addEventListener('click', () => {
    elements.imageInput?.click();
  });
  elements.imageInput?.addEventListener('change', (event) => {
    const file = event.target?.files?.[0] || null;
    if (file && !file.type.startsWith('image/')) {
      setEditStatus('Выберите файл изображения.', 'error');
      event.target.value = '';
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
    showError('Не удалось авторизоваться.');
    return;
  }

  fetchPlant();
};

bootstrap();
