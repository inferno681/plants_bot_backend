(() => {
  const { ENDPOINTS } = window.CONFIG;
  const UI = window.UI;
  const CONFIRM_URL = ENDPOINTS.USER_EMAIL_CONFIRM;

  const elements = {
    themeToggle: document.getElementById('theme-toggle'),
    status: document.getElementById('confirm-status'),
    description: document.getElementById('confirm-description'),
    retryBtn: document.getElementById('retry-btn'),
  };

  const setStatus = (message = '', tone = 'muted') => UI.setStatus(elements.status, message, tone);

  const readToken = () => {
    const params = new URLSearchParams(window.location.search);
    return (params.get('token') || '').trim();
  };

  const confirmEmail = async () => {
    const token = readToken();
    if (!token) {
      setStatus('Токен отсутствует.', 'error');
      if (elements.description) {
        elements.description.textContent = 'Откройте страницу по полной ссылке из письма подтверждения.';
      }
      if (elements.retryBtn) elements.retryBtn.hidden = true;
      return;
    }

    setStatus('Подтверждаем email...', 'muted');
    if (elements.description) {
      elements.description.textContent = 'Это может занять несколько секунд.';
    }
    if (elements.retryBtn) elements.retryBtn.hidden = true;

    try {
      const url = new URL(CONFIRM_URL);
      url.searchParams.set('token', token);
      const response = await fetch(url.toString(), { method: 'POST' });
      if (!response.ok) throw new Error(`Status ${response.status}`);
      setStatus('Email успешно подтвержден.', 'ok');
      if (elements.description) {
        elements.description.textContent = 'Можно вернуться в профиль.';
      }
    } catch (error) {
      console.error('Email confirm failed', error);
      setStatus('Не удалось подтвердить email.', 'error');
      if (elements.description) {
        elements.description.textContent = 'Проверьте срок действия ссылки и попробуйте снова.';
      }
      if (elements.retryBtn) elements.retryBtn.hidden = false;
    }
  };

  const bootstrap = () => {
    UI.initTheme();
    elements.themeToggle?.addEventListener('click', () => UI.toggleTheme());
    elements.retryBtn?.addEventListener('click', confirmEmail);
    confirmEmail();
  };

  bootstrap();
})();
