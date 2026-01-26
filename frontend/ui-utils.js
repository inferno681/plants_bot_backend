(() => {
  const config = window.CONFIG || {};
  const STORAGE_KEYS = config.STORAGE_KEYS || {};
  const THEMES = config.THEMES || { LIGHT: 'light', DARK: 'dark' };
  const THEME_KEY = STORAGE_KEYS.THEME || 'theme';

  const getCurrentTheme = () =>
    document.body.classList.contains('theme-dark') ? THEMES.DARK : THEMES.LIGHT;

  const applyTheme = (theme) => {
    document.body.classList.toggle('theme-dark', theme === THEMES.DARK);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
      // ignore
    }
    return theme;
  };

  const initTheme = () => {
    let stored = null;
    try {
      stored = localStorage.getItem(THEME_KEY);
    } catch (error) {
      // ignore
    }
    const theme = stored === THEMES.LIGHT ? THEMES.LIGHT : THEMES.DARK;
    return applyTheme(theme);
  };

  const toggleTheme = () =>
    applyTheme(getCurrentTheme() === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);

  const formatDate = (value, options = { day: '2-digit', month: '2-digit' }) => {
    if (!value) return '-';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return '-';
    return d.toLocaleDateString('ru-RU', options);
  };

  const formatDateInput = (value) => {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return '';
    return d.toISOString().slice(0, 10);
  };

  const pad2 = (value) => String(value).padStart(2, '0');

  const formatMonthDay = (value) => {
    if (!value || typeof value.day !== 'number' || typeof value.month !== 'number') {
      return null;
    }
    return `${pad2(value.day)}.${pad2(value.month)}`;
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

  const isValidMonthDay = (day, month) => {
    const date = new Date(Date.UTC(2000, month - 1, day));
    return date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
  };

  const parseMonthDayValue = (value, { validateDate = true } = {}) => {
    const raw = (value || '').trim();
    if (!raw) return null;
    const match = raw.match(/^(\d{1,2})\.(\d{1,2})$/);
    const day = match ? Number(match[1]) : null;
    const month = match ? Number(match[2]) : null;
    if (!match || !Number.isInteger(day) || !Number.isInteger(month)) return null;
    if (day < 1 || day > 31 || month < 1 || month > 12) return null;
    if (validateDate && !isValidMonthDay(day, month)) return null;
    return { day, month };
  };

  const parseMonthDayField = (value, label, options = {}) => {
    const raw = (value || '').trim();
    if (!raw) return { value: null, error: null };
    const parsed = parseMonthDayValue(raw, options);
    if (!parsed) {
      return { value: null, error: `Используйте формат дд.мм для поля "${label}".` };
    }
    return { value: parsed, error: null };
  };

  const shiftMonthDay = (value, deltaDays) => {
    const base = new Date(Date.UTC(2000, value.month - 1, value.day));
    base.setUTCDate(base.getUTCDate() + deltaDays);
    return { day: base.getUTCDate(), month: base.getUTCMonth() + 1 };
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
    validateDate = true,
  }) => {
    const start = parseMonthDayField(startValue, `${label} (начало)`, { validateDate });
    if (start.error) return { error: start.error };
    const end = parseMonthDayField(endValue, `${label} (конец)`, { validateDate });
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

  const getWeekdayInputs = (name) =>
    Array.from(document.querySelectorAll(`input[name="${name}"]`));

  const setGroupDisabledVisual = (groupEl, isDisabled) => {
    if (!groupEl) return;
    groupEl.classList.toggle('is-disabled', isDisabled);
  };

  const applyWeekdayRules = (kind, elements, changedInput = null) => {
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

  const applyMonthdayRules = (kind, elements) => {
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

  const toggleScheduleFields = (kind, elements) => {
    if (kind === 'warm') {
      if (elements.warmMonthdayGroup) elements.warmMonthdayGroup.hidden = false;
      if (elements.warmWeekdaysGroup) elements.warmWeekdaysGroup.hidden = false;
      applyMonthdayRules('warm', elements);
      applyWeekdayRules('warm', elements);
      return;
    }
    if (kind === 'cold') {
      if (elements.coldMonthdayGroup) elements.coldMonthdayGroup.hidden = false;
      if (elements.coldWeekdaysGroup) elements.coldWeekdaysGroup.hidden = false;
      applyMonthdayRules('cold', elements);
      applyWeekdayRules('cold', elements);
    }
  };

  let isAutoPeriodUpdate = false;

  const updateComplementPeriod = (source, elements) => {
    if (isAutoPeriodUpdate) return;
    const warmStart = parseMonthDayValue(elements.fieldWarmStart?.value);
    const warmEnd = parseMonthDayValue(elements.fieldWarmEnd?.value);
    const coldStart = parseMonthDayValue(elements.fieldColdStart?.value);
    const coldEnd = parseMonthDayValue(elements.fieldColdEnd?.value);

    if (source === 'warm' && warmStart && warmEnd) {
      const nextColdStart = shiftMonthDay(warmEnd, 1);
      const nextColdEnd = shiftMonthDay(warmStart, -1);
      isAutoPeriodUpdate = true;
      if (elements.fieldColdStart) {
        elements.fieldColdStart.value = formatMonthDay(nextColdStart);
      }
      if (elements.fieldColdEnd) {
        elements.fieldColdEnd.value = formatMonthDay(nextColdEnd);
      }
      isAutoPeriodUpdate = false;
    }

    if (source === 'cold' && coldStart && coldEnd) {
      const nextWarmStart = shiftMonthDay(coldEnd, 1);
      const nextWarmEnd = shiftMonthDay(coldStart, -1);
      isAutoPeriodUpdate = true;
      if (elements.fieldWarmStart) {
        elements.fieldWarmStart.value = formatMonthDay(nextWarmStart);
      }
      if (elements.fieldWarmEnd) {
        elements.fieldWarmEnd.value = formatMonthDay(nextWarmEnd);
      }
      isAutoPeriodUpdate = false;
    }
  };

  const createImagePreviewer = ({ previewWrap, preview, filename }) => {
    let previewUrl = null;

    return (file) => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
      }

      if (!file) {
        if (previewWrap) previewWrap.hidden = true;
        if (preview) preview.removeAttribute('src');
        if (filename) filename.textContent = 'Файл не выбран';
        return;
      }

      previewUrl = URL.createObjectURL(file);
      if (preview) preview.src = previewUrl;
      if (previewWrap) previewWrap.hidden = false;
      if (filename) filename.textContent = file.name || 'Файл выбран';
    };
  };

  const setStatus = (element, message = '', tone = 'muted') => {
    if (!element) return;
    element.textContent = message;
    element.classList.remove('edit-status--ok', 'edit-status--error');
    if (tone === 'ok') element.classList.add('edit-status--ok');
    if (tone === 'error') element.classList.add('edit-status--error');
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

  window.UI = {
    applyTheme,
    initTheme,
    toggleTheme,
    formatDate,
    formatDateInput,
    formatMonthDay,
    formatPeriod,
    daysUntil,
    parseMonthDayValue,
    parseMonthDayField,
    shiftMonthDay,
    normalizeText,
    normalizeDate,
    readCheckedWeekdays,
    hasAnyWateringInput,
    buildWateringSchedule,
    buildWateringPeriodPayload,
    getWeekdayInputs,
    applyWeekdayRules,
    applyMonthdayRules,
    toggleScheduleFields,
    updateComplementPeriod,
    createImagePreviewer,
    setStatus,
    initCustomSelects,
  };
})();
