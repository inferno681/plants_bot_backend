const { ENDPOINTS } = window.CONFIG;
const UI = window.UI;
const USER_ME_URL = ENDPOINTS.USER_ME;
const LINK_URL = ENDPOINTS.LINK;

const auth = window.Auth;
const authFetch = (...args) => auth.authFetch(...args);
const ensureAuth = () => auth.ensureAuth();
let authMode = 'web';

const state = {
  user: null,
  link: null,
  linkTimerId: null,
  linkLoading: false,
  unlinkLoading: false,
  linkPanelOpen: false,
  deleteLoading: false,
};

const elements = {
  back: document.getElementById('back-btn'),
  themeToggle: document.getElementById('theme-toggle'),
  title: document.getElementById('user-title'),
  subtitle: document.getElementById('user-subtitle'),
  description: document.getElementById('user-description'),
  initials: document.getElementById('user-initials'),
  badges: document.getElementById('user-badges'),
  details: document.getElementById('user-details'),
  linkPanel: document.getElementById('link-panel'),
  linkStatus: document.getElementById('link-status'),
  linkCard: document.getElementById('link-card'),
  linkTimer: document.getElementById('link-timer'),
  linkQr: document.getElementById('link-qr'),
  linkUrl: document.getElementById('link-url'),
  linkCode: document.getElementById('link-code'),
  linkHint: document.getElementById('link-hint'),
  linkGenerate: document.getElementById('link-generate'),
  deleteStatus: document.getElementById('delete-status'),
  deleteUser: document.getElementById('delete-user'),
  deleteModal: document.getElementById('delete-modal'),
  deleteConfirm: document.getElementById('delete-confirm'),
  deleteCancel: document.getElementById('delete-cancel'),
  deleteError: document.getElementById('delete-error'),
};

const requestLogin = () => {
  UI.setStatus(elements.linkStatus, 'Сессия истекла. Пожалуйста, войдите снова.', 'error');
};

const setLinkStatus = (message = '', tone = 'muted') => UI.setStatus(elements.linkStatus, message, tone);

const formatIdentity = (user) => {
  if (!user) return { title: 'Пользователь', subtitle: 'Данные недоступны' };
  if (user.public_username) {
    return { title: user.public_username, subtitle: user.email || 'Telegram аккаунт' };
  }
  if (user.email) {
    return { title: user.email, subtitle: 'Веб аккаунт' };
  }
  if (user.telegram_linked || user.telegram_id) {
    return { title: 'Telegram пользователь', subtitle: 'Подключен через Telegram' };
  }
  return { title: 'Пользователь', subtitle: 'Профиль без данных' };
};

const buildBadges = (user) => {
  if (!elements.badges) return;
  elements.badges.innerHTML = '';
  if (!user) return;
  const list = [];
  if (user.email_verified) list.push({ text: 'Email подтвержден', cls: 'badge--ok' });
  if (user.telegram_linked || user.telegram_id) list.push({ text: 'Telegram подключен', cls: 'badge--ok' });
  if (!list.length) return;
  list.forEach((badge) => {
    const span = document.createElement('span');
    span.className = `badge ${badge.cls}`;
    span.textContent = badge.text;
    elements.badges.appendChild(span);
  });
};

const buildDetails = (user) => {
  if (!elements.details) return;
  elements.details.innerHTML = '';
  if (!user) return;
  const emailValue = user.email || '—';
  const emailStatus = user.email
    ? user.email_verified
      ? 'Email подтвержден'
      : 'Email не подтвержден'
    : 'Email не указан';
  const telegramLinked = user.telegram_linked || user.telegram_id;
  const telegramStatus = telegramLinked ? 'Подключен' : 'Не подключен';
  const telegramActionLabel = telegramLinked ? 'Отвязать' : 'Привязать';
  const blocks = [
    {
      label: 'Email',
      value: emailValue,
      meta: emailStatus,
    },
    { label: 'Telegram ID', value: user.telegram_id ? String(user.telegram_id) : '—' },
    {
      label: 'Telegram',
      value: telegramStatus,
      action: telegramActionLabel,
      actionType: telegramLinked ? 'unlink' : 'link',
    },
  ];
  blocks.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'detail-card';
    const isEmail = item.label === 'Email';
    const metaText = item.meta
      ? `<span class="detail-status-text">${item.meta}</span>`
      : '';
    const meta = item.meta && !isEmail ? `<div class="detail-subvalue">${item.meta}</div>` : '';
    const action = item.action
      ? `<button class="button button--ghost button--sm detail-action" data-action="${item.actionType}" type="button">${item.action}</button>`
      : '';
    card.innerHTML = `
      <div class="detail-row">
        <div>
          <div class="label">${item.label}</div>
          <div class="value">${item.value}</div>
        </div>
        <div class="detail-row__actions">
          ${isEmail ? metaText : ''}
          ${action}
        </div>
      </div>
      ${meta}
    `;
    elements.details.appendChild(card);
  });
};

const updateInitials = (value) => {
  if (!elements.initials) return;
  const safe = (value || '').trim();
  if (!safe) {
    elements.initials.textContent = 'U';
    return;
  }
  elements.initials.textContent = safe[0].toUpperCase();
};

const updateUserUI = () => {
  const user = state.user;
  const identity = formatIdentity(user);
  if (elements.title) elements.title.textContent = identity.title;
  if (elements.subtitle) elements.subtitle.textContent = identity.subtitle;
  if (elements.description) {
    elements.description.textContent = user?.telegram_linked
      ? 'Вы получаете уведомления в Telegram и в веб-интерфейсе.'
      : 'Подключите Telegram, чтобы получать уведомления в чате.';
  }
  updateInitials(user?.public_username || user?.email || 'Пользователь');
  buildBadges(user);
  buildDetails(user);
  updateLinkPanelVisibility();
};

const clearTimer = () => {
  if (state.linkTimerId) {
    clearInterval(state.linkTimerId);
    state.linkTimerId = null;
  }
};

const formatRemaining = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.max(0, seconds % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
};

const updateTimer = () => {
  if (!elements.linkTimer || !state.link?.expires_at) return;
  const remaining = Math.max(0, state.link.expires_at * 1000 - Date.now());
  if (remaining <= 0) {
    elements.linkTimer.textContent = 'Код истек';
    if (elements.linkGenerate) elements.linkGenerate.classList.remove('is-cooldown');
    clearTimer();
    return;
  }
  const seconds = Math.ceil(remaining / 1000);
  elements.linkTimer.textContent = `Истекает через ${formatRemaining(seconds)}`;
  if (elements.linkGenerate) {
    elements.linkGenerate.classList.toggle('is-cooldown', seconds > 30);
  }
};

const setLinkData = (link) => {
  state.link = link;
  if (!link) {
    if (elements.linkQr) elements.linkQr.removeAttribute('src');
    if (elements.linkUrl) {
      elements.linkUrl.textContent = '—';
      elements.linkUrl.href = '#';
    }
    if (elements.linkCode) elements.linkCode.textContent = '—';
    if (elements.linkTimer) elements.linkTimer.textContent = '';
    elements.linkGenerate.hidden = false;
    if (elements.linkGenerate) elements.linkGenerate.classList.remove('is-cooldown');
    clearTimer();
    return;
  }

  const qrPayload = link.qr || link.link || link.code;
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrPayload)}`;
  if (elements.linkQr) elements.linkQr.src = qrUrl;
  if (elements.linkUrl) {
    elements.linkUrl.textContent = link.link || link.qr || '—';
    elements.linkUrl.href = link.link || link.qr || '#';
  }
  if (elements.linkCode) elements.linkCode.textContent = link.code || '—';
  elements.linkGenerate.hidden = false;
  if (elements.linkGenerate) elements.linkGenerate.classList.add('is-cooldown');
  clearTimer();
  updateTimer();
  state.linkTimerId = setInterval(updateTimer, 1000);
};

const updateLinkPanelVisibility = () => {
  const linked = Boolean(state.user?.telegram_linked || state.user?.telegram_id);
  if (!elements.linkPanel) return;
  if (linked) {
    elements.linkPanel.hidden = true;
    state.linkPanelOpen = false;
    setLinkData(null);
    return;
  }
  elements.linkPanel.hidden = !state.linkPanelOpen;
  if (!state.linkPanelOpen) {
    setLinkData(null);
  }
};

const fetchUser = async () => {
  try {
    const response = await authFetch(USER_ME_URL);
    if (response.status === 401) {
      state.user = null;
      return;
    }
    if (!response.ok) throw new Error(`Status ${response.status}`);
    state.user = await response.json();
  } catch (error) {
    state.user = null;
  } finally {
    updateUserUI();
  }
};

const createLink = async () => {
  if (state.linkLoading) return;
  if (state.link?.expires_at) {
    const remaining = Math.max(0, state.link.expires_at * 1000 - Date.now());
    const seconds = Math.ceil(remaining / 1000);
    if (seconds > 30) {
      setLinkStatus(`Новый код можно запросить через ${formatRemaining(seconds - 30)}.`, 'muted');
      return;
    }
  }
  state.linkLoading = true;
  if (elements.linkGenerate) elements.linkGenerate.classList.add('is-cooldown');
  setLinkStatus('Получаем код...', 'muted');
  try {
    const response = await authFetch(LINK_URL, { method: 'POST' });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    const data = await response.json();
    setLinkData(data);
    setLinkStatus('Код готов. Отсканируйте QR или откройте ссылку.', 'ok');
  } catch (error) {
    console.error('Link create failed', error);
    setLinkStatus('Не удалось получить код. Попробуйте еще раз.', 'error');
  } finally {
    state.linkLoading = false;
    updateTimer();
  }
};

const unlinkTelegram = async () => {
  if (state.unlinkLoading) return;
  state.unlinkLoading = true;
  setLinkStatus('Отвязываем Telegram...', 'muted');
  try {
    const response = await authFetch(LINK_URL, { method: 'DELETE' });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    setLinkStatus('Telegram отвязан.', 'ok');
    setLinkData(null);
    state.linkPanelOpen = false;
    await fetchUser();
  } catch (error) {
    console.error('Unlink failed', error);
    setLinkStatus('Не удалось отвязать. Попробуйте позже.', 'error');
  } finally {
    state.unlinkLoading = false;
  }
};

const copyCode = async () => {
  const code = state.link?.code;
  if (!code) return;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(code);
    } else {
      const temp = document.createElement('textarea');
      temp.value = code;
      temp.setAttribute('readonly', 'readonly');
      temp.style.position = 'absolute';
      temp.style.left = '-9999px';
      document.body.appendChild(temp);
      temp.select();
      document.execCommand('copy');
      document.body.removeChild(temp);
    }
    if (elements.linkHint) elements.linkHint.textContent = 'Скопировано!';
    setTimeout(() => {
      if (elements.linkHint) elements.linkHint.textContent = 'Нажмите, чтобы скопировать';
    }, 1500);
  } catch (error) {
    setLinkStatus('Не удалось скопировать код.', 'error');
  }
};

const handleDetailAction = (event) => {
  const target = event.target?.closest('[data-action]');
  if (!target) return;
  const action = target.dataset.action;
  if (action === 'link') {
    state.linkPanelOpen = true;
    updateLinkPanelVisibility();
    createLink();
    if (elements.linkPanel) {
      elements.linkPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    return;
  }
  if (action === 'unlink') {
    unlinkTelegram();
  }
};

const showDeleteModal = () => {
  if (!elements.deleteModal) return;
  elements.deleteModal.hidden = false;
  if (elements.deleteError) {
    elements.deleteError.hidden = true;
    elements.deleteError.textContent = '';
  }
};

const hideDeleteModal = () => {
  if (!elements.deleteModal) return;
  elements.deleteModal.hidden = true;
};

const handleDeleteUser = async () => {
  if (state.deleteLoading) return;
  state.deleteLoading = true;
  if (elements.deleteConfirm) elements.deleteConfirm.disabled = true;
  if (elements.deleteCancel) elements.deleteCancel.disabled = true;
  UI.setStatus(elements.deleteStatus, 'Удаляем пользователя...', 'muted');
  try {
    const response = await authFetch(USER_ME_URL, { method: 'DELETE' });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    UI.setStatus(elements.deleteStatus, 'Пользователь удалён.', 'ok');
    hideDeleteModal();
    window.location.href = 'index.html';
  } catch (error) {
    console.error('Delete user failed', error);
    UI.setStatus(elements.deleteStatus, 'Не удалось удалить пользователя.', 'error');
    if (elements.deleteError) {
      elements.deleteError.hidden = false;
      elements.deleteError.textContent = 'Не удалось удалить пользователя.';
    }
  } finally {
    state.deleteLoading = false;
    if (elements.deleteConfirm) elements.deleteConfirm.disabled = false;
    if (elements.deleteCancel) elements.deleteCancel.disabled = false;
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
  elements.themeToggle?.addEventListener('click', () => {
    UI.toggleTheme();
  });
  elements.linkGenerate?.addEventListener('click', createLink);
  elements.linkCode?.addEventListener('click', copyCode);
  elements.details?.addEventListener('click', handleDetailAction);
  elements.deleteUser?.addEventListener('click', showDeleteModal);
  elements.deleteCancel?.addEventListener('click', hideDeleteModal);
  elements.deleteConfirm?.addEventListener('click', handleDeleteUser);

  const ok = await ensureAuth();
  if (!ok) {
    if (authMode === 'web') {
      window.location.href = 'index.html';
      return;
    }
    setLinkStatus('Не удалось авторизоваться.', 'error');
  }
  await fetchUser();
};

bootstrap();
