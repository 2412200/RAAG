document.addEventListener("DOMContentLoaded", () => {
    console.log("Seller Dashboard JS Loaded");

    // Elements
    const menuItems = document.querySelectorAll(".menu-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const specSelect = document.getElementById("specification");
    const form = document.getElementById("productform");
    const sections = document.querySelectorAll(".spec-section");

    // Dynamic stats elements
    const totalCountEl = document.getElementById("stat-total-count");
    const activeCountEl = document.getElementById("stat-active-count");
    const hiddenCountEl = document.getElementById("stat-hidden-count");

    // Products table container
    const productsListEl = document.getElementById("products-list-container");
    const pendingOrdersListEl = document.getElementById("orders-pending-container");
    const processingOrdersListEl = document.getElementById("orders-processing-container");
    const completedOrdersListEl = document.getElementById("orders-completed-container");

    const pendingCountEl = document.getElementById("pending-orders-count");
    const processingCountEl = document.getElementById("processing-orders-count");
    const completedCountEl = document.getElementById("completed-orders-count");

    // Search and filter elements
    const searchInput = document.getElementById("product-search");
    const categoryFilter = document.getElementById("product-category-filter");
    const visibilityFilterEl = document.getElementById("product-visibility-filter");



    // Global products store
    let allProducts = [];

    // Initialize custom Toast notification system
    const toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);

    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let icon = "✓";
        if (type === "error") icon = "✕";
        if (type === "warning") icon = "⚠";
        
        toast.innerHTML = `<span style="font-weight:bold">${icon}</span> <span>${message}</span>`;
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = "slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Custom Confirmation Modal
    function showConfirmModal(title, desc, onConfirm) {
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">${title}</div>
                <div class="modal-desc">${desc}</div>
                <div class="modal-actions">
                    <button class="modal-btn cancel" id="modal-cancel">Cancel</button>
                    <button class="modal-btn confirm" id="modal-confirm">Delete</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        document.getElementById("modal-cancel").onclick = () => {
            overlay.remove();
        };

        document.getElementById("modal-confirm").onclick = () => {
            onConfirm();
            overlay.remove();
        };
    }

    // Sidebar toggle for mobile
    const sidebarToggleBtn = document.getElementById("sidebar-toggle");
    const sidebarEl = document.querySelector(".sidebar");

    if (sidebarToggleBtn && sidebarEl) {
        sidebarToggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebarEl.classList.toggle("show");
        });

        // Close sidebar if clicking outside of it on mobile
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 992 && sidebarEl.classList.contains("show")) {
                if (!sidebarEl.contains(e.target) && e.target !== sidebarToggleBtn) {
                    sidebarEl.classList.remove("show");
                }
            }
        });
    }

    // Global filter states
    let visibilityFilter = "all";

    function switchTab(targetTab) {
        menuItems.forEach(mi => mi.classList.remove("active"));
        menuItems.forEach(mi => {
            if (mi.getAttribute("data-tab") === targetTab) {
                mi.classList.add("active");
            }
        });

        tabPanes.forEach(pane => {
            pane.classList.remove("active");
            if (pane.id === targetTab) {
                pane.classList.add("active");
            }
        });

        // Close sidebar on mobile after tab select
        if (sidebarEl && sidebarEl.classList.contains("show")) {
            sidebarEl.classList.remove("show");
        }

        if (targetTab === "tab-products" || targetTab === "tab-overview") {
            fetchProducts();
        } else if (targetTab === "tab-orders") {
            fetchOrders();
        }
    }

    // Navigation (Tab switching)
    menuItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");
            if (targetTab === "tab-products") {
                visibilityFilter = "all";
                if (visibilityFilterEl) visibilityFilterEl.value = "all";
            }
            switchTab(targetTab);
        });
    });

    // Overview stats cards click handlers
    const totalListingsCard = document.querySelector(".stat-card.total-listings");
    const activeListingsCard = document.querySelector(".stat-card.active-listings");
    const hiddenListingsCard = document.querySelector(".stat-card.hidden-listings");

    if (totalListingsCard) {
        totalListingsCard.addEventListener("click", () => {
            visibilityFilter = "all";
            if (visibilityFilterEl) visibilityFilterEl.value = "all";
            switchTab("tab-products");
        });
    }

    if (activeListingsCard) {
        activeListingsCard.addEventListener("click", () => {
            visibilityFilter = "active";
            if (visibilityFilterEl) visibilityFilterEl.value = "visible";
            switchTab("tab-products");
        });
    }

    if (hiddenListingsCard) {
        hiddenListingsCard.addEventListener("click", () => {
            visibilityFilter = "hidden";
            if (visibilityFilterEl) visibilityFilterEl.value = "hidden";
            switchTab("tab-products");
        });
    }

    // Listen to changes on the My Products visibility filter dropdown
    if (visibilityFilterEl) {
        visibilityFilterEl.addEventListener("change", function () {
            const val = this.value;
            if (val === "all") {
                visibilityFilter = "all";
            } else if (val === "visible") {
                visibilityFilter = "active";
            } else if (val === "hidden") {
                visibilityFilter = "hidden";
            }
            renderProductsList();
        });
    }



    // Specification Section Visibility in Form
    function setSectionActive(section, active) {
        section.hidden = !active;
        const fields = section.querySelectorAll("input, select, textarea");
        fields.forEach(field => {
            field.disabled = !active;
            if (!active) {
                // If it is a generic field or not spec, we don't clear it yet, but standard html forms do.
            }
        });
    }

    function showSection(specValue) {
        sections.forEach(section => {
            const isMatch = section.dataset.spec === specValue;
            setSectionActive(section, isMatch);
        });
    }

    if (specSelect) {
        // Hide all initially
        sections.forEach(section => setSectionActive(section, false));

        specSelect.addEventListener("change", function () {
            showSection(this.value);
        });

        // Trigger showSection if a category spec is already pre-selected
        if (specSelect.value) {
            showSection(specSelect.value);
        }
    }

    // Fetch orders from backend
    async function fetchOrders() {
        try {
            const response = await fetch("/GET/seller/orders");
            if (!response.ok) throw new Error("Failed to fetch orders");
            
            const data = await response.json();
            renderOrdersList(data.orders || []);
        } catch (error) {
            console.error("Error fetching orders:", error);
            showToast("Failed to load customer orders", "error");
        }
    }

        function renderSectionOrders(containerEl, ordersList, statusName) {
        if (!containerEl) return;
        containerEl.innerHTML = "";

        if (ordersList.length === 0) {
            containerEl.innerHTML = `
                <div class="empty-state" style="padding: 30px 10px; min-height: 150px; border-style: dashed; background: transparent; border-radius: 12px; box-shadow: none;">
                    <div class="empty-icon" style="font-size: 24px; margin-bottom: 8px;">📋</div>
                    <div class="empty-title" style="font-size: 13px;">No ${statusName.toLowerCase()} orders</div>
                </div>
            `;
            return;
        }

        ordersList.forEach(order => {
            const card = document.createElement("div");
            card.className = "order-card";

            let productsHtml = "";
            order.products.forEach(p => {
                productsHtml += `
                    <div class="order-product-item">
                        <span>📦 ${p.product_name}</span>
                        <span>Qty: <strong>${p.quantity}</strong> &nbsp;|&nbsp; ₹${p.price.toFixed(2)} each</span>
                    </div>
                `;
            });

            const status = (order.order_status || "Pending");
            const statusLower = status.toLowerCase();

            card.innerHTML = `
                <div class="order-header">
                    <div class="order-id-date">
                        <div class="order-id-lbl">Order #${order.order_id.slice(-6).toUpperCase()}</div>
                        <div class="order-date-lbl">Ordered: ${order.created_at}</div>
                    </div>
                    <select class="order-status-select ${statusLower}" data-order-id="${order.order_id}">
                        <option value="Pending" ${statusLower === "pending" ? "selected" : ""}>Pending</option>
                        <option value="Processing" ${statusLower === "processing" ? "selected" : ""}>Processing</option>
                        <option value="Completed" ${statusLower === "completed" ? "selected" : ""}>Completed</option>
                    </select>
                </div>
                <div class="order-buyer-details">
                    <div><strong>Customer:</strong> ${order.customer_name}</div>
                    <div><strong>Phone:</strong> +${order.customer_number}</div>
                </div>
                <div class="order-products-list">
                    ${productsHtml}
                </div>
                <div class="order-footer">
                    <div class="order-subtotal-lbl">Subtotal:</div>
                    <div class="order-total-amt">₹${parseFloat(order.total_amount).toFixed(2)}</div>
                </div>
            `;

            containerEl.appendChild(card);
        });
    }

    // Render Orders Card List
    function renderOrdersList(orders) {
        const pendingOrders = orders.filter(o => (o.order_status || "").toLowerCase() === "pending" || !(o.order_status));
        const processingOrders = orders.filter(o => (o.order_status || "").toLowerCase() === "processing");
        const completedOrders = orders.filter(o => (o.order_status || "").toLowerCase() === "completed");

        if (pendingCountEl) pendingCountEl.textContent = pendingOrders.length;
        if (processingCountEl) processingCountEl.textContent = processingOrders.length;
        if (completedCountEl) completedCountEl.textContent = completedOrders.length;

        renderSectionOrders(pendingOrdersListEl, pendingOrders, "Pending");
        renderSectionOrders(processingOrdersListEl, processingOrders, "Processing");
        renderSectionOrders(completedOrdersListEl, completedOrders, "Completed");
    }

    // Fetch products from backend
    async function fetchProducts() {
        try {
            const response = await fetch("/GET/seller/products");
            if (!response.ok) throw new Error("Failed to fetch products");
            
            const data = await response.json();
            allProducts = data.products || [];
            updateStatsAndRender();
        } catch (error) {
            console.error("Error fetching products:", error);
            showToast("Failed to load products list", "error");
        }
    }

    // Calculate stats and render HTML list
    function updateStatsAndRender() {
        const total = allProducts.length;
        const hidden = allProducts.filter(p => p.is_hidden).length;
        const active = total - hidden;

        // Update Overview widget counters
        if (totalCountEl) totalCountEl.textContent = total;
        if (activeCountEl) activeCountEl.textContent = active;
        if (hiddenCountEl) hiddenCountEl.textContent = hidden;

        renderProductsList();
    }

    // Render Product Row List
    function renderProductsList() {
        if (!productsListEl) return;

        const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const catFilter = categoryFilter ? categoryFilter.value : "all";

        const filtered = allProducts.filter(product => {
            const name = (product.product_name || "").toLowerCase();
            const matchesQuery = name.includes(query);
            const matchesCategory = catFilter === "all" || product.specification === catFilter;
            
            let matchesVisibility = true;
            if (visibilityFilter === "active") {
                matchesVisibility = !product.is_hidden;
            } else if (visibilityFilter === "hidden") {
                matchesVisibility = product.is_hidden;
            }
            
            return matchesQuery && matchesCategory && matchesVisibility;
        });

        if (filtered.length === 0) {
            productsListEl.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📦</div>
                    <div class="empty-title">No products found</div>
                    <div class="empty-desc">Try modifying your search or filters, or add a new product.</div>
                </div>
            `;
            return;
        }

        productsListEl.innerHTML = "";

        filtered.forEach(product => {
            const row = document.createElement("div");
            row.className = "product-row";

            // Image Thumbnail fallback
            let imgSrc = "/static/images/default.webp";
            let targetImage = null;
            if (product.images && Array.isArray(product.images) && product.images.length > 0) {
                targetImage = product.images[0];
            } else if (product.image) {
                targetImage = product.image;
            }

            if (targetImage) {
                if (targetImage.startsWith("http://") || targetImage.startsWith("https://")) {
                    imgSrc = targetImage;
                } else {
                    imgSrc = `/static/images/${targetImage}`;
                }
            } else {
                // Category defaults
                if (product.specification === "apparel") {
                    imgSrc = product.gender === "Male" ? "/static/images/menjeans.webp" : "/static/images/womentshirt.webp";
                } else if (product.specification === "fmcg") {
                    imgSrc = "/static/images/groceries.webp";
                } else if (product.specification === "mobile_accessories") {
                    imgSrc = "/static/images/mobile.webp";
                } else if (product.specification === "steel_work") {
                    imgSrc = "/static/images/furniture.webp";
                } else if (product.specification === "home_appliances") {
                    imgSrc = "/static/images/computer.webp";
                } else if (product.specification === "pharmacy") {
                    imgSrc = "/static/images/pharma.webp";
                }
            }

            // Specs descriptions
            let specDetailsHtml = "";
            if (product.specification === "apparel") {
                const sizesStr = Array.isArray(product.size) ? product.size.join(", ") : product.size;
                specDetailsHtml = `Sizes: <strong>${sizesStr}</strong> | Fabric: <strong>${product.fabric}</strong> | GSM: <strong>${product.gsm}</strong> | MOQ: <strong>${product.moq || 1}</strong>`;
            } else if (product.specification === "fmcg") {
                specDetailsHtml = `Brand: <strong>${product.brand}</strong> | Stock Qty: <strong>${product.quantity}</strong>`;
            } else if (product.specification === "mobile_accessories") {
                specDetailsHtml = `Brand: <strong>${product.brand}</strong> | Model: <strong>${product.compatible_model}</strong> | Color: <strong>${product.color}</strong>`;
            } else if (product.specification === "steel_work") {
                specDetailsHtml = `Grade: <strong>${product.steel_grade}</strong> | Thick: <strong>${product.thickness}mm</strong> | Wt: <strong>${product.weight}kg</strong>`;
            }

            const isChecked = !product.is_hidden;

            row.innerHTML = `
                <div class="product-image-container">
                    <img src="${imgSrc}" alt="${product.product_name}" onerror="this.onerror=null;this.src='/static/images/default.webp'">
                </div>
                <div class="product-info-col">
                    <div class="product-name-txt">${product.product_name}</div>
                    <div class="product-desc-txt">${product.description || 'No description provided.'}</div>
                </div>
                <div class="product-meta-item">
                    ${specDetailsHtml}
                </div>
                <div class="product-badge-spec">
                    ${product.specification.replace("_", " ")}
                </div>
                <div class="product-price-col">
                    ₹${parseFloat(product.mrp).toFixed(2)}
                </div>
                <div class="switch-container">
                    <label class="switch">
                        <input type="checkbox" class="visibility-toggle" data-id="${product._id}" data-spec="${product.specification}" ${isChecked ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <span class="status-label ${isChecked ? 'visible' : 'hidden'}">${isChecked ? 'Visible' : 'Hidden'}</span>
                </div>
                <button class="delete-btn" data-id="${product._id}" data-spec="${product.specification}" title="Delete Product">
                    ✕
                </button>
            `;

            productsListEl.appendChild(row);
        });

        // Add event listeners to toggles
        document.querySelectorAll(".visibility-toggle").forEach(toggle => {
            toggle.addEventListener("change", async (e) => {
                const productId = e.target.getAttribute("data-id");
                const specName = e.target.getAttribute("data-spec");
                const isVisible = e.target.checked;
                const isHidden = !isVisible;

                // Update text label instantly
                const label = e.target.closest(".switch-container").querySelector(".status-label");
                if (isVisible) {
                    label.textContent = "Visible";
                    label.className = "status-label visible";
                } else {
                    label.textContent = "Hidden";
                    label.className = "status-label hidden";
                }

                try {
                    const response = await fetch("/POST/seller/product/toggle-visibility", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            product_id: productId,
                            specification: specName,
                            is_hidden: isHidden
                        })
                    });

                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || "Request failed");

                    showToast(data.message || `Product visibility updated!`, "success");
                    // update local product state
                    const found = allProducts.find(p => p._id === productId);
                    if (found) found.is_hidden = isHidden;
                    
                    // Recalculate stats counts
                    const total = allProducts.length;
                    const hiddenCount = allProducts.filter(p => p.is_hidden).length;
                    const activeCount = total - hiddenCount;
                    if (totalCountEl) totalCountEl.textContent = total;
                    if (activeCountEl) activeCountEl.textContent = activeCount;
                    if (hiddenCountEl) hiddenCountEl.textContent = hiddenCount;

                } catch (error) {
                    console.error(error);
                    showToast("Failed to toggle visibility", "error");
                    // Revert UI check
                    e.target.checked = !isVisible;
                    if (!isVisible) {
                        label.textContent = "Visible";
                        label.className = "status-label visible";
                    } else {
                        label.textContent = "Hidden";
                        label.className = "status-label hidden";
                    }
                }
            });
        });

        // Add event listeners to delete buttons
        document.querySelectorAll(".delete-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const productId = btn.getAttribute("data-id");
                const specName = btn.getAttribute("data-spec");

                showConfirmModal(
                    "Delete Product",
                    "Are you sure you want to delete this product? This action is permanent and cannot be undone.",
                    async () => {
                        try {
                            const response = await fetch("/POST/seller/product/delete", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    product_id: productId,
                                    specification: specName
                                })
                            });

                            const data = await response.json();
                            if (!response.ok) throw new Error(data.detail || "Deletion failed");

                            showToast("Product deleted successfully", "success");
                            allProducts = allProducts.filter(p => p._id !== productId);
                            updateStatsAndRender();
                        } catch (error) {
                            console.error(error);
                            showToast("Failed to delete product", "error");
                        }
                    }
                );
            });
        });
    }

    // Hook search and filter events
    if (searchInput) searchInput.addEventListener("input", renderProductsList);
    if (categoryFilter) categoryFilter.addEventListener("change", renderProductsList);

    // Handle order status change
    const tabOrdersPane = document.getElementById("tab-orders");
    if (tabOrdersPane) {
        tabOrdersPane.addEventListener("change", async (e) => {
            if (e.target.classList.contains("order-status-select")) {
                const orderId = e.target.getAttribute("data-order-id");
                const newStatus = e.target.value;
                
                const oldClassList = Array.from(e.target.classList);
                e.target.className = `order-status-select ${newStatus.toLowerCase()}`;
                
                try {
                    const response = await fetch("/POST/order/update-status", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            order_id: orderId,
                            status: newStatus
                        })
                    });
                    
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || "Failed to update order status");
                    
                    showToast(data.message || `Order status updated to ${newStatus}`, "success");
                    fetchOrders();
                } catch (error) {
                    console.error(error);
                    showToast("Failed to update status: " + error.message, "error");
                    e.target.className = oldClassList.join(" ");
                    fetchOrders();
                }
            }
        });
    }

    // Form submission
    if (form) {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();

            if (!specSelect.value) {
                showToast("Please select a Product Specification", "warning");
                return;
            }

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    showToast(data.message || "Product added successfully!", "success");
                    form.reset();
                    


                    // Hide specifications sections in form
                    sections.forEach(section => setSectionActive(section, false));
                    if (specSelect) specSelect.value = "";

                    // Switch back to Products List tab and refresh
                    const productsMenuItem = document.querySelector('[data-tab="tab-products"]');
                    if (productsMenuItem) {
                        productsMenuItem.click();
                    }
                } else {
                    showToast("Error: " + (data.detail || "Unable to add product."), "error");
                }
            } catch (error) {
                console.error(error);
                showToast("Network error. Please try again.", "error");
            }
        });
    }

    // Initial Fetch on load
    fetchProducts();
});