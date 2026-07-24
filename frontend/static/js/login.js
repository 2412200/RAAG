// frontend/static/js/login.js - Frontend script handling password visibility toggle, role selections, and sign-in request submissions with loader overlays.
document.addEventListener("DOMContentLoaded", () => {
  // Clear any token from localStorage when visiting the login page
  localStorage.removeItem("token");

  let selectedRole = "seller";

  // Handle password visibility toggle
  const togglePwBtn = document.getElementById('toggle-password');
  const passwordInput = document.getElementById('password');

  if (togglePwBtn && passwordInput) {
    togglePwBtn.addEventListener('click', () => {
      const isPw = passwordInput.type === 'password';
      passwordInput.type = isPw ? 'text' : 'password';
      togglePwBtn.textContent = isPw ? 'hide' : 'show';
      togglePwBtn.setAttribute('aria-label', isPw ? 'Hide password' : 'Show password');
    });
  }

  document.querySelectorAll('.role-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.role-btn').forEach((b) => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });

      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');

      selectedRole = btn.dataset.role;

      document.getElementById('role-display').textContent =
        selectedRole.charAt(0).toUpperCase() +
        selectedRole.slice(1);
    });
  });

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const phone = document.getElementById("number").value;
      const password = document.getElementById("password").value;

      const payload = {
        phone: phone,
        password: password,
        role: selectedRole
      };

      const statusDiv = document.getElementById("status");
      statusDiv.hidden = true;

      const loader = document.getElementById("loader-overlay");
      const loaderText = document.getElementById("loader-text");
      loaderText.textContent = "Signing in...";
      loader.classList.add("is-active");

      try {
        const response = await fetch(
          "/POST/login",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
          }
        );

        const data = await response.json();

        if (!response.ok) {
          loader.classList.remove("is-active");
          statusDiv.className = "status is-error";
          statusDiv.textContent = data.detail || "Invalid credentials";
          statusDiv.hidden = false;
          return;
        }

        // Save JWT in localStorage (optional)
        if (data.token) {
          localStorage.setItem(
            "token",
            data.token
          );
        }

        loaderText.textContent = "Redirecting...";

        // Redirect based on role
        if (data.role === "seller") {
          window.location.href = "/seller";
        } else {
          window.location.href = "/home";
        }

      } catch (error) {
        loader.classList.remove("is-active");
        console.error(error);
        statusDiv.className = "status is-error";
        statusDiv.textContent = "Unable to connect to server";
        statusDiv.hidden = false;
      }
    });
  }
});