document.addEventListener("DOMContentLoaded", () => {
    // Intercept clicks on any logout links to show a custom warning modal
    const logoutLinks = document.querySelectorAll('a[href="/logout"]');
    
    logoutLinks.forEach(link => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const logoutUrl = link.href;
            showLogoutConfirmModal(logoutUrl);
        });
    });

    function showLogoutConfirmModal(logoutUrl) {
        // Remove existing modal if any
        const existing = document.querySelector(".logout-modal-overlay");
        if (existing) existing.remove();

        // Inject modal style sheet dynamically
        if (!document.getElementById("logout-modal-styles")) {
            const style = document.createElement("style");
            style.id = "logout-modal-styles";
            style.textContent = `
                .logout-modal-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.7);
                    backdrop-filter: blur(4px);
                    z-index: 100000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    animation: logoutFadeInModal 0.2s ease;
                    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }
                .logout-modal {
                    background: #181818;
                    border: 1px solid #222;
                    border-radius: 20px;
                    padding: 30px;
                    width: 90%;
                    max-width: 440px;
                    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6);
                    text-align: center;
                    box-sizing: border-box;
                }
                @keyframes logoutFadeInModal {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .logout-modal-title {
                    font-size: 20px;
                    font-weight: 700;
                    margin-bottom: 12px;
                    color: #F5F0ED;
                }
                .logout-modal-desc {
                    color: #A89B92;
                    font-size: 14px;
                    line-height: 1.5;
                    margin-bottom: 24px;
                }
                .logout-modal-actions {
                    display: flex;
                    gap: 12px;
                    justify-content: center;
                }
                .logout-modal-btn {
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: none;
                    outline: none;
                }
                .logout-modal-btn.cancel {
                    background: #222;
                    border: 1px solid #333;
                    color: #F5F0ED;
                }
                .logout-modal-btn.cancel:hover {
                    background: #333;
                }
                .logout-modal-btn.confirm {
                    background: #C0172A;
                    color: #F5F0ED;
                }
                .logout-modal-btn.confirm:hover {
                    background: #E8293F;
                }
            `;
            document.head.appendChild(style);
        }

        // Create modal element
        const overlay = document.createElement("div");
        overlay.className = "logout-modal-overlay";
        overlay.innerHTML = `
            <div class="logout-modal">
                <div class="logout-modal-title">Logout</div>
                <div class="logout-modal-desc">Are you sure you want to log out?</div>
                <div class="logout-modal-actions">
                    <button class="logout-modal-btn cancel" id="logout-modal-cancel">Cancel</button>
                    <button class="logout-modal-btn confirm" id="logout-modal-confirm">Logout</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById("logout-modal-cancel").onclick = () => {
            overlay.remove();
        };

        document.getElementById("logout-modal-confirm").onclick = () => {
            window.location.href = logoutUrl;
        };
    }
});
