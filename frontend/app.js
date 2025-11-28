const apiBase = 'http://localhost:8000';
const API_URL = `${apiBase}/api/v1/plants`;

let plants = [];
const filters = { text: '', mode: 'all' };
const state = { loading: true, error: null };

const elements = {
  stats: document.getElementById('stats'),
  cards: document.getElementById('cards'),
  timeline: document.getElementById('timeline'),
  search: document.getElementById('search'),
  filterPills: document.querySelectorAll('.pill'),
  refresh: document.getElementById('refresh'),
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
  if (status === 'due') return { text: 'Needs action', cls: 'badge--due' };
  if (status === 'soon') return { text: 'Coming up soon', cls: 'badge--soon' };
  return { text: 'All good', cls: 'badge--ok' };
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
  if (start) return `from ${start}`;
  if (end) return `until ${end}`;
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
    name: plant.name || 'No name',
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
  const total = plants.length;
  const dueToday = plants.filter(
    (p) => daysUntil(p.nextWateringAt) <= 0 || daysUntil(p.nextFertilizingAt) <= 0,
  ).length;
  const weekTasks = plants.filter(
    (p) => daysUntil(p.nextWateringAt) <= 7 || daysUntil(p.nextFertilizingAt) <= 7,
  ).length;
  const blocks = [
    { label: 'Plants total', value: total },
    { label: 'Need attention', value: dueToday },
    { label: 'This week', value: weekTasks },
    { label: 'Data source', value: 'backend' },
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
    showNotice(elements.cards, 'Loading plants...', 'muted');
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
    if (filters.mode === 'warm') return Boolean(plant.warmPeriod);
    if (filters.mode === 'cold') return Boolean(plant.coldPeriod);
    return true;
  });

  if (!visible.length) {
    showNotice(elements.cards, 'Nothing matches the current filters.', 'muted');
    return;
  }

  elements.cards.innerHTML = '';

  visible.forEach((plant) => {
    const { text, cls } = statusBadge(plant.status);
    const daysToWater = daysUntil(plant.nextWateringAt);
    const daysToFert = daysUntil(plant.nextFertilizingAt);
    const soon = Math.min(daysToWater, daysToFert) <= 2;
    const alertBadge = soon && plant.status === 'ok' ? 'badge--soon' : cls;
    const image = plant.imageUrl
      ? `<div class="card__image has-image" style="background-image: url('${plant.imageUrl}')"></div>`
      : '<div class="card__image"><span>No photo yet</span></div>';

    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      ${image}
      <div class="card__body">
        <h3 class="card__title">${plant.name}</h3>
        <div class="card__subtitle">${plant.scientificName || '-'}</div>
        <div class="badges">
          <span class="badge ${alertBadge}">${text}</span>
          <span class="badge badge--ok">Watering: ${formatDate(plant.nextWateringAt)}</span>
          <span class="badge badge--soon">Fertilizing: ${formatDate(plant.nextFertilizingAt)}</span>
        </div>
      </div>
      <div class="card__details">
        <div class="meta-grid">
          <div class="meta"><span class="label">Last watering</span>${formatDate(plant.lastWateredAt)}</div>
          <div class="meta"><span class="label">Last fertilizing</span>${formatDate(plant.lastFertilizedAt)}</div>
          <div class="meta"><span class="label">Warm period</span>${plant.warmPeriod || '-'}</div>
          <div class="meta"><span class="label">Cold period</span>${plant.coldPeriod || '-'}</div>
        </div>
        <p class="note">${plant.description || 'Description will be added later.'}</p>
        ${plant.note ? `<p class="note">${plant.note}</p>` : ''}
      </div>
    `;
    elements.cards.appendChild(card);
  });
};

const buildTimelineFromPlants = () => {
  if (state.loading) {
    showNotice(elements.timeline, 'Building schedule...', 'muted');
    return;
  }

  const items = [];
  plants.forEach((p) => {
    if (p.nextWateringAt) {
      items.push({
        title: `${p.name}: watering`,
        meta: `Next watering - ${formatDate(p.nextWateringAt)}`,
        date: p.nextWateringAt,
        type: 'watering',
      });
    }
    if (p.nextFertilizingAt) {
      items.push({
        title: `${p.name}: fertilizing`,
        meta: `Next fertilizing - ${formatDate(p.nextFertilizingAt)}`,
        date: p.nextFertilizingAt,
        type: 'fertilizing',
      });
    }
  });

  if (!items.length || state.error) {
    showNotice(elements.timeline, state.error || 'No scheduled tasks yet.', 'muted');
    return;
  }

  items.sort((a, b) => new Date(a.date) - new Date(b.date));
  const upcoming = items.slice(0, 6);

  elements.timeline.innerHTML = '';
  upcoming.forEach((item) => {
    const li = document.createElement('li');
    li.className = 'timeline__item';
    li.innerHTML = `
      <div>
        <div class="title">${item.title}</div>
        <div class="note">${item.meta}</div>
      </div>
      <div class="pill pill--small ${item.type === 'watering' ? 'is-active' : ''}">
        ${formatDate(item.date)}
      </div>
    `;
    elements.timeline.appendChild(li);
  });
};

const fetchPlants = async () => {
  state.loading = true;
  state.error = null;
  renderCards();
  buildTimelineFromPlants();

  try {
    const response = await fetch(API_URL);
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    plants = Array.isArray(data) ? data.map(mapPlantFromApi) : [];
  } catch (error) {
    console.error(error);
    state.error = 'Could not load data. Please check that the backend is running.';
    plants = [];
  } finally {
    state.loading = false;
    buildStats();
    renderCards();
    buildTimelineFromPlants();
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
  fetchPlants();
});

buildStats();
renderCards();
buildTimelineFromPlants();
fetchPlants();
