const plants = [
  {
    name: "Алоэ вера",
    scientificName: "Aloe vera",
    description: "Суккулент, любит рассеянный свет и редкий полив.",
    warmPeriod: "01.04 — 30.09",
    coldPeriod: "01.10 — 31.03",
    lastWateredAt: "2025-11-24",
    nextWateringAt: "2025-11-30",
    lastFertilizedAt: "2025-10-28",
    nextFertilizingAt: "2025-12-05",
    status: "ok",
    note: "Проветривать, избегать переувлажнения.",
  },
  {
    name: "Монстера",
    scientificName: "Monstera deliciosa",
    description: "Умеренный полив, любит влажный воздух и рассеянный свет.",
    warmPeriod: "01.03 — 15.10",
    coldPeriod: "16.10 — 28.02",
    lastWateredAt: "2025-11-21",
    nextWateringAt: "2025-11-27",
    lastFertilizedAt: "2025-11-01",
    nextFertilizingAt: "2025-11-29",
    status: "soon",
    note: "Опрыскивать листья, следить за опорами.",
  },
  {
    name: "Фикус Бенджамина",
    scientificName: "Ficus benjamina",
    description: "Не любит сквозняков, полив после подсыхания верхнего слоя.",
    warmPeriod: "01.04 — 31.08",
    coldPeriod: "01.09 — 31.03",
    lastWateredAt: "2025-11-18",
    nextWateringAt: "2025-11-25",
    lastFertilizedAt: "2025-09-12",
    nextFertilizingAt: "2025-11-26",
    status: "due",
    note: "Переставить подальше от двери.",
  },
  {
    name: "Пилея",
    scientificName: "Pilea peperomioides",
    description: "Компактная, требует равномерного полива.",
    warmPeriod: "01.03 — 30.09",
    coldPeriod: "01.10 — 28.02",
    lastWateredAt: "2025-11-23",
    nextWateringAt: "2025-11-29",
    lastFertilizedAt: "2025-10-30",
    nextFertilizingAt: "2025-12-10",
    status: "ok",
    note: "Чередовать стороны к свету.",
  },
];

const filters = { text: "", mode: "all" };

const formatDate = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
};

const daysUntil = (value) => {
  if (!value) return Infinity;
  const today = new Date();
  const date = new Date(value);
  const diff = Math.floor((date - today) / 86400000);
  return diff;
};

const statusBadge = (status) => {
  if (status === "due") return { text: "Срочно полить", cls: "badge--due" };
  if (status === "soon") return { text: "Скоро задача", cls: "badge--soon" };
  return { text: "Все ок", cls: "badge--ok" };
};

const buildTimeline = (items) => {
  const timeline = document.getElementById("timeline");
  timeline.innerHTML = "";
  items.sort((a, b) => new Date(a.date) - new Date(b.date));
  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "timeline__item";
    li.innerHTML = `
      <div>
        <div class="title">${item.title}</div>
        <div class="note">${item.meta}</div>
      </div>
      <div class="pill pill--small ${item.type === "watering" ? "is-active" : ""}">
        ${formatDate(item.date)}
      </div>
    `;
    timeline.appendChild(li);
  });
};

const buildStats = () => {
  const statsEl = document.getElementById("stats");
  const total = plants.length;
  const dueToday = plants.filter((p) => daysUntil(p.nextWateringAt) <= 0 || daysUntil(p.nextFertilizingAt) <= 0).length;
  const weekTasks = plants.filter((p) => daysUntil(p.nextWateringAt) <= 7 || daysUntil(p.nextFertilizingAt) <= 7).length;
  const blocks = [
    { label: "Всего растений", value: total },
    { label: "Требуют сегодня", value: dueToday },
    { label: "Задачи на 7 дней", value: weekTasks },
    { label: "Данные мок", value: "demo" },
  ];
  statsEl.innerHTML = blocks
    .map((b) => `<div class="stat-card"><div class="label">${b.label}</div><div class="value">${b.value}</div></div>`)
    .join("");
};

const renderCards = () => {
  const cards = document.getElementById("cards");
  cards.innerHTML = "";
  const visible = plants.filter((plant) => {
    const matchText = `${plant.name} ${plant.scientificName}`.toLowerCase().includes(filters.text);
    if (!matchText) return false;
    if (filters.mode === "due") return plant.status === "due" || daysUntil(plant.nextWateringAt) <= 0;
    if (filters.mode === "warm") return plant.warmPeriod;
    if (filters.mode === "cold") return plant.coldPeriod;
    return true;
  });

  visible.forEach((plant) => {
    const { text, cls } = statusBadge(plant.status);
    const daysToWater = daysUntil(plant.nextWateringAt);
    const daysToFert = daysUntil(plant.nextFertilizingAt);
    const soon = Math.min(daysToWater, daysToFert) <= 2;
    const alertBadge = soon && plant.status === "ok" ? "badge--soon" : cls;

    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="card__image"><span>Фото пока заглушка</span></div>
      <div>
        <h3 class="card__title">${plant.name}</h3>
        <div class="card__subtitle">${plant.scientificName}</div>
        <div class="badges">
          <span class="badge ${alertBadge}">${text}</span>
          <span class="badge badge--ok">Полив: ${formatDate(plant.nextWateringAt)}</span>
          <span class="badge badge--soon">Удобрение: ${formatDate(plant.nextFertilizingAt)}</span>
        </div>
        <div class="meta-grid">
          <div class="meta"><span class="label">Последний полив</span>${formatDate(plant.lastWateredAt)}</div>
          <div class="meta"><span class="label">Последнее удобрение</span>${formatDate(plant.lastFertilizedAt)}</div>
          <div class="meta"><span class="label">Тёплый период</span>${plant.warmPeriod}</div>
          <div class="meta"><span class="label">Холодный период</span>${plant.coldPeriod}</div>
        </div>
        <p class="note">${plant.description}</p>
        <p class="note">${plant.note}</p>
      </div>
    `;
    cards.appendChild(card);
  });
};

const buildTimelineFromPlants = () => {
  const items = [];
  plants.forEach((p) => {
    items.push({ title: `${p.name}: полив`, meta: `Следующий полив — ${formatDate(p.nextWateringAt)}`, date: p.nextWateringAt, type: "watering" });
    items.push({ title: `${p.name}: удобрение`, meta: `Следующее удобрение — ${formatDate(p.nextFertilizingAt)}`, date: p.nextFertilizingAt, type: "fertilizing" });
  });
  buildTimeline(items.slice(0, 6));
};

document.getElementById("search").addEventListener("input", (e) => {
  filters.text = e.target.value.toLowerCase();
  renderCards();
});

document.querySelectorAll(".pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    document.querySelectorAll(".pill").forEach((p) => p.classList.remove("is-active"));
    pill.classList.add("is-active");
    filters.mode = pill.dataset.filter;
    renderCards();
  });
});

buildStats();
renderCards();
buildTimelineFromPlants();
