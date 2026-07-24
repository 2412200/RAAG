// frontend/static/js/forgot_password.js - Handles forgot password form input validation, step toggling (phone submission -> OTP/new password submission), and reset submissions.
document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  const form = document.getElementById('forgot-password-form');
  const roleButtons = document.querySelectorAll('.role-btn');
  const submitBtn = document.getElementById('submit-btn');
  const submitLabel = submitBtn.querySelector('.cta-label');
  const status = document.getElementById('status');
  
  const phoneInput = document.getElementById('phone');
  const otpInput = document.getElementById('otp');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirm-password');
  
  const togglePwBtn = document.getElementById('toggle-password');
  const resetFieldsContainer = document.getElementById('reset-fields-container');

  let selectedRole = 'seller';
  let otpRequested = false;

  // Handle password visibility toggle
  if (togglePwBtn && passwordInput) {
    togglePwBtn.addEventListener('click', () => {
      const isPw = passwordInput.type === 'password';
      passwordInput.type = isPw ? 'text' : 'password';
      togglePwBtn.textContent = isPw ? 'hide' : 'show';
      togglePwBtn.setAttribute('aria-label', isPw ? 'Hide password' : 'Show password');
    });
  }

  // Role button switching
  roleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      if (otpRequested) return; // Lock role selection after code is sent
      
      roleButtons.forEach(b => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });

      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');
      selectedRole = btn.dataset.role;
    });
  });

  // Error setter helper
  function setError(inputEl, errorId, message) {
    const errorEl = document.getElementById(errorId);
    if (!errorEl) return;
    if (message) {
      inputEl.classList.add('is-invalid');
      errorEl.textContent = message;
    } else {
      inputEl.classList.remove('is-invalid');
      errorEl.textContent = '';
    }
  }

  // Status notifications
  function showStatus(message, type) {
    status.hidden = false;
    status.className = `status ${type === 'success' ? 'is-success' : 'is-error'}`;
    status.textContent = message;
  }

  function clearStatus() {
    status.hidden = true;
    status.className = 'status';
    status.textContent = '';
  }

  // Validation logic
  function validateForm() {
    let isValid = true;

    if (!otpRequested) {
      // Validate Phone
      const phone = phoneInput.value.trim();
      if (!phone) {
        setError(phoneInput, 'phone-error', 'Phone number is required.');
        isValid = false;
      } else if (!/^[+\d\s\-()]{7,15}$/.test(phone)) {
        setError(phoneInput, 'phone-error', 'Enter a valid phone number.');
        isValid = false;
      } else {
        setError(phoneInput, 'phone-error', '');
      }
    } else {
      // Validate OTP, Password & Confirm Password
      const otp = otpInput.value.trim();
      if (!otp) {
        setError(otpInput, 'otp-error', 'Verification code is required.');
        isValid = false;
      } else if (!/^\d{4,8}$/.test(otp)) {
        setError(otpInput, 'otp-error', 'Please enter a valid OTP code.');
        isValid = false;
      } else {
        setError(otpInput, 'otp-error', '');
      }

      const password = passwordInput.value;
      if (!password) {
        setError(passwordInput, 'password-error', 'Password is required.');
        isValid = false;
      } else if (password.length < 6) {
        setError(passwordInput, 'password-error', 'Minimum 6 characters required.');
        isValid = false;
      } else {
        setError(passwordInput, 'password-error', '');
      }

      const confirmPassword = confirmInput.value;
      if (!confirmPassword) {
        setError(confirmInput, 'confirm-error', 'Please confirm your password.');
        isValid = false;
      } else if (password !== confirmPassword) {
        setError(confirmInput, 'confirm-error', 'Passwords do not match.');
        isValid = false;
      } else {
        setError(confirmInput, 'confirm-error', '');
      }
    }

    return isValid;
  }

  // Submit handling
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      clearStatus();

      if (!validateForm()) return;

      submitBtn.disabled = true;

      const loader = document.getElementById('loader-overlay');
      const loaderText = document.getElementById('loader-text');

      if (!otpRequested) {
        submitLabel.textContent = 'Sending code...';
        loaderText.textContent = 'Sending verification code...';
        loader.classList.add('is-active');
        const payload = {
          phone: phoneInput.value.trim(),
          role: selectedRole
        };

        try {
          const response = await fetch('/POST/request-forgot-password-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const data = await response.json();

          if (!response.ok) {
            loader.classList.remove('is-active');
            showStatus(data.detail || 'Failed to send verification code.', 'error');
            return;
          }

          // Code sent, show step 2 fields
          otpRequested = true;
          phoneInput.disabled = true;
          
          // Lock role buttons pointer interactions
          roleButtons.forEach(btn => btn.style.pointerEvents = 'none');

          resetFieldsContainer.style.display = 'block';
          otpInput.focus();
          submitLabel.textContent = 'Reset Password';
          showStatus('Verification code sent to your phone number!', 'success');

        } catch (error) {
          console.error(error);
          showStatus('Network error requesting verification code.', 'error');
        } finally {
          loader.classList.remove('is-active');
          submitBtn.disabled = false;
        }
      } else {
        submitLabel.textContent = 'Resetting password...';
        loaderText.textContent = 'Resetting password...';
        loader.classList.add('is-active');
        const payload = {
          phone: phoneInput.value.trim(),
          role: selectedRole,
          otp: otpInput.value.trim(),
          password: passwordInput.value
        };

        try {
          const response = await fetch('/POST/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const data = await response.json();

          if (!response.ok) {
            loader.classList.remove('is-active');
            showStatus(data.detail || 'Password reset failed.', 'error');
            return;
          }

          loaderText.textContent = 'Redirecting...';
          showStatus('Password updated successfully! Redirecting to sign in...', 'success');
          setTimeout(() => {
            window.location.href = '/';
          }, 1500);

        } catch (error) {
          loader.classList.remove('is-active');
          console.error(error);
          showStatus('Network error resetting password.', 'error');
        } finally {
          submitBtn.disabled = false;
        }
      }
    });
  }
});
