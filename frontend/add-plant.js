const { ENDPOINTS } = window.CONFIG;
const UI = window.UI;
const API_URL = ENDPOINTS.PLANTS;

const state = { saving: false };
const auth = window.Auth;
const authFetch = (...args) => auth.authFetch(...args);
const ensureAuth = () => auth.ensureAuth();
let authMode = 'web';

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

const requestLogin = () => {
  if (elements.status) {
    elements.status.textContent = 'Сессия истекла. Пожалуйста, войдите снова.';
    elements.status.classList.remove('edit-status--ok');
    elements.status.classList.add('edit-status--error');
  }
};

const setStatus = (message = '', tone = 'muted') => UI.setStatus(elements.status, message, tone);

let selectedImageFile = null;

const updateImagePreview = UI.createImagePreviewer({
  previewWrap: elements.imagePreviewWrap,
  preview: elements.imagePreview,
  filename: elements.imageFilename,
});

const buildFertilizingPayload = () => {
  const start = UI.parseMonthDayField(elements.fieldFertStart?.value, 'Подкормки (начало)');
  if (start.error) return { error: start.error };
  const end = UI.parseMonthDayField(elements.fieldFertEnd?.value, 'Подкормки (конец)');
  if (end.error) return { error: end.error };

  const rawFrequency = (elements.fieldFertFrequency?.value || '').trim();
  const note = UI.normalizeText(elements.fieldFertNote?.value);
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

const handleCreate = async (event) => {
  event?.preventDefault();
  if (state.saving) return;

  const name = (elements.fieldName?.value || '').trim();
  if (!name) {
    setStatus('Введите название растения.', 'error');
    elements.fieldName?.focus();
    return;
  }

  const warm = UI.buildWateringPeriodPayload({
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

  const cold = UI.buildWateringPeriodPayload({
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
    scientific_name: UI.normalizeText(elements.fieldScientific?.value),
    description: UI.normalizeText(elements.fieldDescription?.value),
    warm_period: warm?.value,
    cold_period: cold?.value,
    fertilizing: fertilizing?.value,
    last_watered_at: UI.normalizeDate(elements.fieldLastWateredAt?.value),
    last_fertilized_at: UI.normalizeDate(elements.fieldLastFertilizedAt?.value),
    next_watering_at: UI.normalizeDate(elements.fieldNextWateringAt?.value),
    next_fertilizing_at: UI.normalizeDate(elements.fieldNextFertilizingAt?.value),
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
  auth.init();
  auth.setOnAuthRequired(requestLogin);
  authMode = auth.getAuthMode();
  if (authMode === 'telegram' && window.Telegram?.WebApp?.ready) {
    window.Telegram.WebApp.ready();
  }
  UI.initTheme();

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
    UI.toggleTheme();
  });
  elements.form?.addEventListener('submit', handleCreate);
  UI.initCustomSelects();

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
    setStatus('Не удалось авторизоваться.', 'error');
  }
};

bootstrap();
