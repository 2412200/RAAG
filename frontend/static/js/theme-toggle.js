// Immediately run this check to prevent page flash before DOM loads
(function() {
    const savedTheme = localStorage.getItem("theme");
    const systemPrefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    if (savedTheme === "light" || (!savedTheme && systemPrefersLight)) {
        document.documentElement.classList.add("light-mode");
    }
})();

document.addEventListener("DOMContentLoaded", () => {
    // 1. Inject Light Mode CSS Overrides dynamically
    const style = document.createElement("style");
    style.id = "theme-toggle-styles";
    style.textContent = `
        /* Transition effect for smooth theme transitions */
        html, body, aside, main, header, footer, nav, div, section, p, h1, h2, h3, table, th, td, a, input, select, textarea {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
        }

        /* ── LIGHT MODE OVERRIDES ── */
        .light-mode {
            /* Variables used in home.html & category.css */
            --black: #F5F0ED;
            --black2: #FFFFFF;
            --black3: #EAE3DF;
            --white: #0D0D0D;
            --muted: #665D57;
            --gold: #B8860B;
            
            /* Variables used in style.css, login.html, signup.html */
            --bg: #F5F0ED;
            --surface: #FFFFFF;
            --surface-2: #EAE3DF;
            --border: #D4CDC9;
            --border-active: #C0172A;
            --text: #0D0D0D;
            --muted-gray: #665D57;
        }

        /* Target the root variables in style.css directly when light-mode is active */
        html.light-mode {
            --bg: #F5F0ED !important;
            --surface: #FFFFFF !important;
            --surface-2: #EAE3DF !important;
            --border: #D4CDC9 !important;
            --border-active: #C0172A !important;
            --text: #0D0D0D !important;
            --muted: #665D57 !important;
        }

        /* Specific element light-mode overrides */
        html.light-mode body {
            background-color: #F5F0ED !important;
            color: #0D0D0D !important;
        }

        .light-mode .sidebar {
            background: #FFFFFF !important;
            border-right: 1px solid #D4CDC9 !important;
        }

        .light-mode .mobile-navbar {
            background: #FFFFFF !important;
            border-bottom: 1px solid #D4CDC9 !important;
        }

        .light-mode .mobile-navbar-brand {
            color: #C0172A !important;
        }

        .light-mode .menu-item {
            color: #665D57 !important;
        }

        .light-mode .menu-item:hover {
            background: #EAE3DF !important;
            color: #0D0D0D !important;
        }

        .light-mode .menu-item.active {
            background: #C0172A !important;
            color: #FFFFFF !important;
        }

        .light-mode .search-wrap {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .search-wrap input {
            color: #0D0D0D !important;
        }

        .light-mode .search-wrap input::placeholder {
            color: #888888 !important;
        }

        .light-mode .search-bar {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .cat-card {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .cat-name {
            color: #0D0D0D !important;
        }

        .light-mode footer {
            background: #FFFFFF !important;
            border-top: 1px solid #D4CDC9 !important;
        }

        .light-mode nav {
            background: #FFFFFF !important;
            border-bottom: 1px solid #D4CDC9 !important;
        }

        .light-mode .nav-links a {
            color: #665D57 !important;
        }

        .light-mode .nav-links a:hover {
            color: #0D0D0D !important;
        }

        .light-mode .nav-right a {
            color: #665D57 !important;
        }

        .light-mode .nav-right a:hover {
            color: #0D0D0D !important;
        }

        .light-mode .page-title {
            color: #0D0D0D !important;
        }

        .light-mode .product-card {
            background: #FFFFFF !important;
            border: 1px solid #D4CDC9 !important;
        }

        .light-mode .product-info {
            border-top: 1px solid #D4CDC9 !important;
        }

        .light-mode .product-name {
            color: #0D0D0D !important;
        }

        .light-mode .dashboard-header {
            border-bottom: 1px solid #D4CDC9 !important;
        }

        .light-mode .dashboard-title p {
            color: #665D57 !important;
        }

        .light-mode .sidebar-toggle-btn {
            border-color: #C0172A !important;
            color: #0D0D0D !important;
        }

        .light-mode .sidebar-toggle-btn:hover {
            background: #EAE3DF !important;
        }

        .light-mode .btn-submit,
        .light-mode .cta {
            color: #FFFFFF !important;
        }

        /* Form styling in light mode */
        .light-mode .role-btn {
            color: #0D0D0D !important;
            background: #FFFFFF !important;
        }

        .light-mode .role-btn.is-active {
            background: rgba(192, 23, 42, 0.08) !important;
            border-color: #C0172A !important;
        }

        .light-mode .field input {
            color: #0D0D0D !important;
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .field input::placeholder {
            color: #888888 !important;
        }

        .light-mode .checkbox {
            color: #665D57 !important;
        }

        .light-mode .form-container,
        .light-mode .panel--form {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        /* Orders Page specific */
        .light-mode .order-item {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .order-summary {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .order-price {
            color: #0D0D0D !important;
        }

        .light-mode .orders-container h1 {
            color: #0D0D0D !important;
        }

        /* Seller Dashboard specific */
        .light-mode .sidebar-profile {
            background: #EAE3DF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .profile-name {
            color: #0D0D0D !important;
        }

        .light-mode .stat-card {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .stat-value {
            color: #0D0D0D !important;
        }

        .light-mode .stat-badge {
            background: #EAE3DF !important;
        }

        .light-mode .panel-card {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .product-row {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .product-name-txt {
            color: #0D0D0D !important;
        }

        .light-mode .product-image-container {
            background: #EAE3DF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .search-input-wrap input {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
            color: #0D0D0D !important;
        }

        .light-mode .filter-select {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
            color: #0D0D0D !important;
        }

        .light-mode .modal {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }

        .light-mode .modal-title {
            color: #0D0D0D !important;
        }

        .light-mode .modal-btn.cancel {
            background: #EAE3DF !important;
            color: #0D0D0D !important;
            border-color: #D4CDC9 !important;
        }

        /* Logout Warning Modal in Light Mode */
        .light-mode .logout-modal {
            background: #FFFFFF !important;
            border-color: #D4CDC9 !important;
        }
        .light-mode .logout-modal-title {
            color: #0D0D0D !important;
        }
        .light-mode .logout-modal-btn.cancel {
            background: #EAE3DF !important;
            border-color: #D4CDC9 !important;
            color: #0D0D0D !important;
        }

        /* Theme Toggle Button Style */
        .theme-toggle-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #F5F0ED;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            flex-shrink: 0;
        }

        .theme-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.25);
            transform: scale(1.05);
        }

        .theme-toggle-btn:active {
            transform: scale(0.95);
        }

        /* Light mode adjustments for the button */
        .light-mode .theme-toggle-btn {
            background: rgba(13, 13, 13, 0.06);
            border: 1px solid rgba(13, 13, 13, 0.12);
            color: #0D0D0D;
        }

        .light-mode .theme-toggle-btn:hover {
            background: rgba(13, 13, 13, 0.12);
            border-color: rgba(13, 13, 13, 0.2);
        }

        /* Fixed placement fallback classes */
        .theme-toggle-btn.fixed-top-right {
            position: fixed;
            top: 13px;
            right: 20px;
            z-index: 200000;
        }
        
        /* Fixed placement for login/signup pages next to content */
        .theme-toggle-btn.fixed-top-right-auth {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 200000;
        }
    `;
    document.head.appendChild(style);

    // 2. Inject Toggle Button dynamically
    function injectToggle() {
        if (document.getElementById("theme-toggle")) return;

        const btn = document.createElement("button");
        btn.id = "theme-toggle";
        btn.className = "theme-toggle-btn";
        btn.setAttribute("aria-label", "Toggle light/dark theme");
        
        // SVGs
        const sunIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
        const moonIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

        function updateIcon() {
            const isLight = document.documentElement.classList.contains("light-mode");
            btn.innerHTML = isLight ? moonIcon : sunIcon;
        }

        updateIcon();

        btn.addEventListener("click", () => {
            const wasLight = document.documentElement.classList.contains("light-mode");
            if (wasLight) {
                document.documentElement.classList.remove("light-mode");
                localStorage.setItem("theme", "dark");
            } else {
                document.documentElement.classList.add("light-mode");
                localStorage.setItem("theme", "light");
            }
            updateIcon();
        });

        let injected = false;

        // Route-specific integration
        // A. Category / Main Nav layout (.nav-right)
        const navRight = document.querySelector(".nav-right");
        if (navRight) {
            navRight.insertBefore(btn, navRight.firstChild);
            injected = true;
        }

        // B. Desktop dashboard header (Insert before logout-btn)
        if (!injected) {
            const logoutBtn = document.querySelector(".logout-btn");
            if (logoutBtn && logoutBtn.parentNode) {
                logoutBtn.parentNode.insertBefore(btn, logoutBtn);
                btn.style.marginRight = "12px";
                injected = true;
            }
        }

        // C. Mobile navbar (Insert before mobile-logout-btn)
        if (!injected) {
            const mobileNav = document.querySelector(".mobile-navbar");
            const mobileLogout = document.querySelector(".mobile-logout-btn");
            if (mobileLogout && mobileNav) {
                mobileNav.insertBefore(btn, mobileLogout);
                btn.style.marginRight = "10px";
                injected = true;
            }
        }

        // D. Fallback (Fixed top-right position)
        if (!injected) {
            const isAuthPage = window.location.pathname === "/" || 
                               window.location.pathname === "/signup" || 
                               window.location.pathname === "/forgot-password";
            
            if (isAuthPage) {
                btn.classList.add("fixed-top-right-auth");
            } else {
                btn.classList.add("fixed-top-right");
            }
            document.body.appendChild(btn);
        }
    }

    injectToggle();
});
