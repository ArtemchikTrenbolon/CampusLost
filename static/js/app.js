function renderNav() {
  const user = API.getUser();

  document.querySelectorAll('.guest-only').forEach(el => el.classList.toggle('d-none', !!user));
  document.querySelectorAll('.auth-only').forEach(el => el.classList.toggle('d-none', !user));

  const nameEl = document.getElementById('navUserName');
  if (nameEl && user) {
    const fullName = `${user.first_name} ${user.last_name}`.trim();
    nameEl.textContent = fullName || user.email;
  }
}

async function logout() {
  try {
    await API.request('/auth/logout/', { method: 'POST' });
  } catch (e) {
    // даже если сервер не ответил, локально всё равно выходим
  }
  API.clearAuth();
  window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', () => {
  renderNav();
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});