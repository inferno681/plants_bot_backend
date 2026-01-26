const { ENDPOINTS } = window.CONFIG;
const UI = window.UI;
const API_URL = ENDPOINTS.PLANTS;

const state = { loading: true, error: null, plant: null, saving: false, uploading: false };
const auth = window.Auth;
const authFetch = (...args) => auth.authFetch(...args);
const ensureAuth = () => auth.ensureAuth();
let authMode = 'web';
let plantId = null;
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

const formatDateLong = (value) =>
  UI.formatDate(value, { day: '2-digit', month: '2-digit', year: 'numeric' });

const setEditStatus = (message = '', tone = 'muted') =>
  UI.setStatus(elements.editStatus, message, tone);

const formatMonthDayInput = (value) => UI.formatMonthDay(value) || '';

const statusBadge = (plant) => {
  const watering = UI.daysUntil(plant.next_watering_at);
  const fertilizing = UI.daysUntil(plant.next_fertilizing_at);
  const minDiff = Math.min(watering, fertilizing);

  if (minDiff <= 0) return { text: 'Срочный уход', cls: 'badge--due' };
  if (minDiff <= 2) return { text: 'Скоро полив', cls: 'badge--soon' };
  return { text: 'Все спокойно', cls: 'badge--ok' };
};

const renderBadges = (plant) => {
  const badges = [];
  badges.push(statusBadge(plant));

  elements.badges.innerHTML = badges
    .map((b) => `<span class="badge ${b.cls}">${b.text}</span>`)
    .join('');
};

const renderGrid = (plant) => {
  const fertilizingPeriod = UI.formatPeriod(plant.fertilizing);
  const warmPeriod = UI.formatPeriod(plant.warm_period);
  const coldPeriod = UI.formatPeriod(plant.cold_period);

  const items = [
    { label: 'Следующий полив', value: formatDateLong(plant.next_watering_at) },
    { label: 'Следующая подкормка', value: formatDateLong(plant.next_fertilizing_at) },
    { label: 'Последний полив', value: formatDateLong(plant.last_watered_at) },
    { label: 'Последняя подкормка', value: formatDateLong(plant.last_fertilized_at) },
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

  UI.getWeekdayInputs(weekdayName).forEach((input) => {
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
    elements.fieldLastWateredAt.value = UI.formatDateInput(plant.last_watered_at);
  }
  if (elements.fieldNextWateringAt) {
    elements.fieldNextWateringAt.value = UI.formatDateInput(plant.next_watering_at);
  }
  if (elements.fieldLastFertilizedAt) {
    elements.fieldLastFertilizedAt.value = UI.formatDateInput(plant.last_fertilized_at);
  }
  if (elements.fieldNextFertilizingAt) {
    elements.fieldNextFertilizingAt.value = UI.formatDateInput(plant.next_fertilizing_at);
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

const buildFertilizingPayload = (current) => {
  const start = UI.parseMonthDayField(elements.fieldFertStart?.value, 'Подкормки (начало)', {
    validateDate: false,
  });
  if (start.error) return { error: start.error };
  const end = UI.parseMonthDayField(elements.fieldFertEnd?.value, 'Подкормки (конец)', {
    validateDate: false,
  });
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
      note: UI.normalizeText(elements.fieldFertNote?.value),
    },
  };
};

const updateImagePreview = UI.createImagePreviewer({
  previewWrap: elements.imagePreviewWrap,
  preview: elements.imagePreview,
  filename: elements.imageFilename,
});

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

  const warm = UI.buildWateringPeriodPayload({
    startValue: elements.fieldWarmStart?.value,
    endValue: elements.fieldWarmEnd?.value,
    noteValue: elements.fieldWarmNote?.value,
    scheduleType: elements.fieldWarmScheduleType?.value,
    scheduleMonthday: elements.fieldWarmMonthday?.value,
    scheduleWeekdayName: 'warm-weekday',
    label: 'Тёплый период',
    validateDate: false,
  });
  if (warm?.error) {
    setEditStatus(warm.error, 'error');
    return null;
  }

  const cold = UI.buildWateringPeriodPayload({
    startValue: elements.fieldColdStart?.value,
    endValue: elements.fieldColdEnd?.value,
    noteValue: elements.fieldColdNote?.value,
    scheduleType: elements.fieldColdScheduleType?.value,
    scheduleMonthday: elements.fieldColdMonthday?.value,
    scheduleWeekdayName: 'cold-weekday',
    label: 'Холодный период',
    validateDate: false,
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
    description: UI.normalizeText(elements.fieldDescription?.value),
    warm_period: warm?.value,
    cold_period: cold?.value,
    fertilizing: fertilizing?.value,
    last_watered_at: UI.normalizeDate(elements.fieldLastWateredAt?.value),
    last_fertilized_at: UI.normalizeDate(elements.fieldLastFertilizedAt?.value),
    next_watering_at: UI.normalizeDate(elements.fieldNextWateringAt?.value),
    next_fertilizing_at: UI.normalizeDate(elements.fieldNextFertilizingAt?.value),
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
  UI.initTheme();
  ensureEditPanelClosed();

  const params = new URLSearchParams(window.location.search);
  plantId = params.get('id');
  if (!plantId) {
    showError('Не указан идентификатор растения.');
    return;
  }

  elements.themeToggle?.addEventListener('click', () => {
    UI.toggleTheme();
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
  UI.initCustomSelects();

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

  elements.fieldWarmScheduleType?.addEventListener('change', () =>
    UI.toggleScheduleFields('warm', elements),
  );
  elements.fieldColdScheduleType?.addEventListener('change', () =>
    UI.toggleScheduleFields('cold', elements),
  );
  UI.toggleScheduleFields('warm', elements);
  UI.toggleScheduleFields('cold', elements);

  UI.getWeekdayInputs('warm-weekday').forEach((input) => {
    input.addEventListener('change', (event) => UI.applyWeekdayRules('warm', elements, event.target));
  });
  UI.getWeekdayInputs('cold-weekday').forEach((input) => {
    input.addEventListener('change', (event) => UI.applyWeekdayRules('cold', elements, event.target));
  });

  const handleWarmInput = () => UI.updateComplementPeriod('warm', elements);
  const handleColdInput = () => UI.updateComplementPeriod('cold', elements);
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
