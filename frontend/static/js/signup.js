// frontend/static/js/signup.js - Controls signup validation, role-specific form field changes, OTP request triggering, and new account verification submit processes.
document.addEventListener("DOMContentLoaded", () => {
  'use strict';

  // Clear any token from localStorage when visiting the signup page
  localStorage.removeItem("token");

  const form = document.getElementById('signup-form');
  const roleButtons = document.querySelectorAll('.role-btn');
  const roleDisplay = document.getElementById('role-display');
  const submitBtn = document.getElementById('submit-btn');
  const status = document.getElementById('status');

  const togglePwBtn = document.getElementById('toggle-password');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirm-password');

  const companyInput = document.getElementById('company_name');
  const businessLabel = document.getElementById('business-label');
  const ownerInput = document.getElementById('owner_name');
  const sellerOnlyFields = document.getElementById('seller-only-fields');
  const gstInput = document.getElementById('gst_pan');

  if (gstInput) {
    // Auto-capitalize GST/PAN input value
    gstInput.addEventListener('input', () => {
      gstInput.value = gstInput.value.toUpperCase();
    });
  }

  let selectedRole = 'seller';

  // ------------------------------
  // Role Toggle
  // ------------------------------
  roleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      roleButtons.forEach(b => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });

      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');

      selectedRole = btn.dataset.role;

      roleDisplay.textContent =
        selectedRole.charAt(0).toUpperCase() +
        selectedRole.slice(1);

      if (selectedRole === "seller") {
        businessLabel.textContent = "Company Name";
        companyInput.placeholder = "Acme Industries Ltd.";
        sellerOnlyFields.style.display = 'contents';
      } else {
        businessLabel.textContent = "Shop Name";
        companyInput.placeholder = "ABC Retail Store";
        sellerOnlyFields.style.display = 'none';

        // Clear seller-specific fields
        gstInput.value = '';
        setError(gstInput, 'gst_pan-error', '');
      }
    });
  });

  // ------------------------------
  // Show / Hide Password
  // ------------------------------
  if (togglePwBtn && passwordInput) {
    togglePwBtn.addEventListener('click', () => {
      const show = passwordInput.type === 'password';
      passwordInput.type = show ? 'text' : 'password';
      togglePwBtn.textContent = show ? 'hide' : 'show';
    });
  }

  // ------------------------------
  // Validation Helpers
  // ------------------------------
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

  function validate(checkOtpOnly = false) {
    if (checkOtpOnly) {
      const otpInput = document.getElementById('otp');
      const otpVal = otpInput.value.trim();
      if (!otpVal) {
        setError(otpInput, 'otp-error', 'Verification code is required.');
        return false;
      }
      if (!/^\d{4,8}$/.test(otpVal)) {
        setError(otpInput, 'otp-error', 'Please enter a valid OTP code.');
        return false;
      }
      setError(otpInput, 'otp-error', '');
      return true;
    }

    let valid = true;

    const company = companyInput.value.trim();
    const owner = ownerInput.value.trim();
    const phone = document.getElementById('phone').value.trim();
    const city = document.getElementById('city').value.trim();
    const state = document.getElementById('state').value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmInput.value;

    // Company / Shop
    if (!company) {
      setError(
        companyInput,
        'company-error',
        selectedRole === "seller"
          ? "Company name is required."
          : "Shop name is required."
      );
      valid = false;
    } else {
      setError(companyInput, 'company-error', '');
    }

    // Owner
    if (!owner) {
      setError(ownerInput, 'owner-error', 'Owner name is required.');
      valid = false;
    } else {
      setError(ownerInput, 'owner-error', '');
    }

    // Phone
    if (!phone) {
      setError(
        document.getElementById('phone'),
        'phone-error',
        'Phone number is required.'
      );
      valid = false;
    } else if (!/^[+\d\s\-()]{7,15}$/.test(phone)) {
      setError(
        document.getElementById('phone'),
        'phone-error',
        'Enter a valid phone number.'
      );
      valid = false;
    } else {
      setError(document.getElementById('phone'), 'phone-error', '');
    }

    // City
    if (!city) {
      setError(document.getElementById('city'), 'city-error', 'City is required.');
      valid = false;
    } else {
      setError(document.getElementById('city'), 'city-error', '');
    }

    // State
    if (!state) {
      setError(document.getElementById('state'), 'state-error', 'State is required.');
      valid = false;
    } else {
      setError(document.getElementById('state'), 'state-error', '');
    }

    // Password
    if (!password) {
      setError(passwordInput, 'password-error', 'Password is required.');
      valid = false;
    } else if (password.length < 6) {
      setError(passwordInput, 'password-error', 'Minimum 6 characters.');
      valid = false;
    } else {
      setError(passwordInput, 'password-error', '');
    }

    // Confirm Password
    if (!confirmPassword) {
      setError(confirmInput, 'confirm-error', 'Confirm your password.');
      valid = false;
    } else if (password !== confirmPassword) {
      setError(confirmInput, 'confirm-error', 'Passwords do not match.');
      valid = false;
    } else {
      setError(confirmInput, 'confirm-error', '');
    }

    // Category validation
    const categorySelect = document.getElementById('category');
    if (categorySelect) {
      if (!categorySelect.value) {
        setError(categorySelect, 'category-error', 'Category is required.');
        valid = false;
      } else {
        setError(categorySelect, 'category-error', '');
      }
    }

    // Seller fields validation
    if (selectedRole === 'seller') {
      const gstPanInput = document.getElementById('gst_pan');
      if (gstPanInput) {
        if (!gstPanInput.value.trim()) {
          setError(gstPanInput, 'gst_pan-error', 'GST / PAN number is required.');
          valid = false;
        } else {
          setError(gstPanInput, 'gst_pan-error', '');
        }
      }
    }

    return valid;
  }

  // ------------------------------
  // Status Message
  // ------------------------------
  function showStatus(message, type) {
    status.hidden = false;
    status.className = `status ${type === 'success' ? 'is-success' : 'is-error'}`;
    status.textContent = message;
  }

  function clearStatus() {
    status.hidden = true;
    status.className = 'status';
  }

  // ------------------------------
  // Submit Form
  // ------------------------------
  let otpRequested = false;

  function toggleInputs(disabled) {
    const inputs = form.querySelectorAll('input, select, .role-btn');
    inputs.forEach(el => {
      if (el.id !== 'otp' && el.id !== 'submit-btn') {
        if (el.classList.contains('role-btn')) {
          el.style.pointerEvents = disabled ? 'none' : 'auto';
        } else {
          el.disabled = disabled;
        }
      }
    });
  }

  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      clearStatus();

      const loader = document.getElementById('loader-overlay');
      const loaderText = document.getElementById('loader-text');

      if (!otpRequested) {
        if (!validate(false)) return;

        submitBtn.disabled = true;
        submitBtn.querySelector('.cta-label').textContent = 'Sending verification code...';

        loaderText.textContent = 'Sending verification code...';
        loader.classList.add('is-active');

        const payload = {
          business_name: companyInput.value.trim(),
          owner_name: ownerInput.value.trim(),
          phone: document.getElementById('phone').value.trim(),
          city: document.getElementById('city').value.trim(),
          state: document.getElementById('state').value.trim(),
          password: passwordInput.value,
          role: selectedRole,
          gst_pan: selectedRole === 'seller' ? document.getElementById('gst_pan').value.trim() : null,
          category: document.getElementById('category').value
        };

        try {
          const response = await fetch('/POST/request-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const data = await response.json();

          if (!response.ok) {
            loader.classList.remove('is-active');
            showStatus(data.detail || 'Failed to send OTP.', 'error');
            return;
          }

          otpRequested = true;
          document.getElementById('otp-container').style.display = 'block';
          document.getElementById('otp').focus();
          toggleInputs(true);
          submitBtn.querySelector('.cta-label').textContent = 'Verify & Create Account';
          showStatus('Verification code sent to your phone number!', 'success');

        } catch (error) {
          console.error(error);
          showStatus('Network error requesting OTP.', 'error');
        } finally {
          loader.classList.remove('is-active');
          submitBtn.disabled = false;
        }

      } else {
        if (!validate(true)) return;

        submitBtn.disabled = true;
        submitBtn.querySelector('.cta-label').textContent = 'Verifying account...';

        loaderText.textContent = 'Verifying account...';
        loader.classList.add('is-active');

        const payload = {
          business_name: companyInput.value.trim(),
          owner_name: ownerInput.value.trim(),
          phone: document.getElementById('phone').value.trim(),
          city: document.getElementById('city').value.trim(),
          state: document.getElementById('state').value.trim(),
          password: passwordInput.value,
          role: selectedRole,
          gst_pan: selectedRole === 'seller' ? document.getElementById('gst_pan').value.trim() : null,
          category: document.getElementById('category').value,
          otp: document.getElementById('otp').value.trim()
        };

        try {
          const response = await fetch('/POST/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const data = await response.json();

          if (!response.ok) {
            loader.classList.remove('is-active');
            showStatus(data.detail || 'Signup failed.', 'error');
            return;
          }

          loaderText.textContent = 'Redirecting...';
          showStatus('Account created successfully! Logging you in...', 'success');
          
          if (data.token) {
            localStorage.setItem("token", data.token);
          }

          setTimeout(() => {
            if (data.role === 'seller') {
              window.location.href = '/seller';
            } else {
              window.location.href = '/home';
            }
          }, 1500);

        } catch (error) {
          loader.classList.remove('is-active');
          console.error(error);
          showStatus('Network error.', 'error');
        } finally {
          submitBtn.disabled = false;
        }
      }
    });
  }
});
