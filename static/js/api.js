// Работа с токеном и запросами к API
const API = {
  getToken() {
    return localStorage.getItem('token');
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('user'));
    } catch (e) {
      return null;
    }
  },

  setAuth(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  // options.auth === false: не отправлять токен (для входа и регистрации)
  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const token = this.getToken();
    if (token && options.auth !== false) {
      headers['Authorization'] = 'Token ' + token;
    }

    const response = await fetch('/api' + path, { ...options, headers });

    let data = null;
    if (response.status !== 204) {
      try {
        data = await response.json();
      } catch (e) {
        data = null;
      }
    }

    if (!response.ok) {
      const error = new Error('Ошибка запроса');
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  },

  // Превращает ответ DRF с ошибками в читаемый текст
  formatError(error) {
    const data = error.data;
    if (!data) return 'Не удалось связаться с сервером';
    if (data.detail) return data.detail;
    return Object.entries(data)
      .map(([field, messages]) => `${field}: ${[].concat(messages).join(' ')}`)
      .join('\n');
  },
};