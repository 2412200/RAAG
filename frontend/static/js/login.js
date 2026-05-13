(() => {
  'use strict';

  // CONFIG ------------------------------------------------------
  // Point this at your real backend. The login page is plain HTML
  // so it can be hosted anywhere (CDN, S3, Vercel static, etc.).
  const API_BASE = 'http://localhost:8001/api';
  const LOGIN_PATH = '/auth/login';
  // ------------------------------------------------------------

  // DOM
  const form = document.getElementById('login-form');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const emailError = document.getElementById('email-error');
  const passwordError = document.getElementById('password-error');
  const submitBtn = document.getElementById('submit-btn');
  const togglePwBtn = document.getElementById('toggle-password');
  const status = document.getElementById('status');
  const roleDisplay = document.getElementById('role-display');
  const roleButtons = document.querySelectorAll('.role-btn');

  let selectedRole = 'manufacturer';

  // Role toggle ------------------------------------------------
  roleButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      roleButtons.forEach((b) => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');
      selectedRole = btn.dataset.role;
      roleDisplay.textContent =
        selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1);
    });
  });

  // Show / hide password ---------------------------------------
  togglePwBtn.addEventListener('click', () => {
    const isPw = passwordInput.type === 'password';
    passwordInput.type = isPw ? 'text' : 'password';
    togglePwBtn.textContent = isPw ? 'hide' : 'show';
    togglePwBtn.setAttribute('aria-label', isPw ? 'Hide password' : 'Show password');
  });

  // Validation -------------------------------------------------
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setError(input, errorEl, message) {
    if (message) {
      input.classList.add('is-invalid');
      input.parentElement.classList.add('has-error');
      errorEl.textContent = message;
    } else {
      input.classList.remove('is-invalid');
      input.parentElement.classList.remove('has-error');
      errorEl.textContent = '';
    }
  }

  function validate() {
    let ok = true;
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email) {
      setError(emailInput, emailError, 'Email is required.');
      ok = false;
    } else if (!EMAIL_RE.test(email)) {
      setError(emailInput, emailError, 'Enter a valid email.');
      ok = false;
    } else {
      setError(emailInput, emailError, '');
    }

    if (!password) {
      setError(passwordInput, passwordError, 'Password is required.');
      ok = false;
    } else if (password.length < 6) {
      setError(passwordInput, passwordError, 'Password must be at least 6 characters.');
      ok = false;
    } else {
      setError(passwordInput, passwordError, '');
    }

    return ok;
  }

  // Live revalidate on input
  [emailInput, passwordInput].forEach((el) => {
    el.addEventListener('input', () => {
      if (el.classList.contains('is-invalid')) validate();
    });
  });

  // Status helpers ---------------------------------------------
  function showStatus(message, type = 'error') {
    status.hidden = false;
    status.className = `status ${type === 'success' ? 'is-success' : 'is-error'}`;
    status.textContent = message;
  }

  function clearStatus() {
    status.hidden = true;
    status.className = 'status';
    status.textContent = '';
  }

  // Submit -----------------------------------------------------
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearStatus();
    if (!validate()) return;

    submitBtn.disabled = true;
    const originalLabel = submitBtn.querySelector('.cta-label').textContent;
    submitBtn.querySelector('.cta-label').textContent = 'Authenticating…';

    const payload = {
      email: emailInput.value.trim().toLowerCase(),
      password: passwordInput.value,
      role: selectedRole, // sent for analytics; backend determines real role
    };

    try {
      const res = await fetch(`${API_BASE}${LOGIN_PATH}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let msg = 'Invalid email or password.';
        try {
          const data = await res.json();
          if (typeof data.detail === 'string') msg = data.detail;
          else if (Array.isArray(data.detail)) msg = data.detail.map((d) => d.msg).join(' ');
        } catch (_) {
          /* keep default */
        }
        showStatus(msg, 'error');
        return;
      }

      const data = await res.json();

      // Store token if API returned one (Bearer flow)
      if (data.access_token) {
        const remember = document.getElementById('remember').checked;
        (remember ? localStorage : sessionStorage).setItem('access_token', data.access_token);
      }

      const userRole = data.user?.role || selectedRole;
      showStatus(`Authenticated as ${userRole}. Redirecting…`, 'success');

      // Optional redirect to your app
      // window.location.href = '/dashboard';
    } catch (err) {
      console.error(err);
      showStatus('Network error. Please try again.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.querySelector('.cta-label').textContent = originalLabel;
    }
  });
})();
