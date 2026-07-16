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

    // Helper: Client-Side Image Compression using Canvas
    async function compressImage(file, maxDimension = 1200, quality = 0.8) {
        if (!file || !file.type || !file.type.startsWith("image/")) {
            return file;
        }
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = function (event) {
                const img = new Image();
                img.onload = function () {
                    const canvas = document.createElement("canvas");
                    let width = img.width;
                    let height = img.height;

                    if (width > height) {
                        if (width > maxDimension) {
                            height = Math.round((height * maxDimension) / width);
                            width = maxDimension;
                        }
                    } else {
                        if (height > maxDimension) {
                            width = Math.round((width * maxDimension) / height);
                            height = maxDimension;
                        }
                    }

                    canvas.width = width;
                    canvas.height = height;

                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob(
                        (blob) => {
                            if (!blob) {
                                resolve(file);
                                return;
                            }
                            resolve(new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".jpg", {
                                type: "image/jpeg",
                                lastModified: Date.now()
                            }));
                        },
                        "image/jpeg",
                        quality
                    );
                };
                img.onerror = () => resolve(file);
                img.src = event.target.result;
            };
            reader.onerror = () => resolve(file);
            reader.readAsDataURL(file);
        });
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
            if (targetTab === "tab-overview") {
                fetchAnalytics();
            }
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

    const apparelCategorySelect = document.getElementById("category_app");
    const standardSizesGroup = document.getElementById("standard-sizes-group");
    const numericSizesGroup = document.getElementById("numeric-sizes-group");
    const gsmGroup = document.getElementById("gsm-group");
    const gsmInput = document.getElementById("gsm");

    function updateApparelFields() {
        if (!apparelCategorySelect) return;
        const val = apparelCategorySelect.value.toLowerCase();
        // Check if value is one of jeans, trouser, lower
        const isJeansTrouserLower = val.includes("jeans") || val.includes("trouser") || val.includes("lower");

        if (isJeansTrouserLower) {
            // Remove/hide GSM and size fields
            if (gsmGroup) gsmGroup.style.display = "none";
            if (gsmInput) {
                gsmInput.required = false;
                gsmInput.disabled = true;
            }
            if (standardSizesGroup) {
                standardSizesGroup.style.display = "none";
                standardSizesGroup.querySelectorAll("input").forEach(cb => cb.disabled = true);
            }
            // Show numeric size field
            if (numericSizesGroup) {
                numericSizesGroup.style.display = "block";
                numericSizesGroup.querySelectorAll("input").forEach(cb => cb.disabled = false);
            }
        } else {
            // Show GSM and default size fields
            if (gsmGroup) gsmGroup.style.display = "block";
            if (gsmInput) {
                gsmInput.required = true;
                gsmInput.disabled = false;
            }
            if (standardSizesGroup) {
                standardSizesGroup.style.display = "block";
                standardSizesGroup.querySelectorAll("input").forEach(cb => cb.disabled = false);
            }
            // Hide numeric size field
            if (numericSizesGroup) {
                numericSizesGroup.style.display = "none";
                numericSizesGroup.querySelectorAll("input").forEach(cb => cb.disabled = true);
            }
        }
    }

    if (apparelCategorySelect) {
        apparelCategorySelect.addEventListener("change", updateApparelFields);
        updateApparelFields();
    }

    // Global orders store
    let allOrders = [];
    let activeOrderTab = "pending";

    // Dispatch helper
    function getDispatchDate(order) {
        if (!order.created_at) return null;
        try {
            const created = new Date(order.created_at.replace(" ", "T"));
            if (isNaN(created.getTime())) return null;
            const hr = created.getHours();
            const dispatch = new Date(created);
            if (hr < 15) {
                dispatch.setDate(dispatch.getDate() + 1);
            } else {
                dispatch.setDate(dispatch.getDate() + 2);
            }
            return dispatch;
        } catch(e) { return null; }
    }

    // Days helper
    function orderWithinDays(order, days) {
        if (!order.created_at) return false;
        try {
            const created = new Date(order.created_at.replace(" ", "T"));
            if (isNaN(created.getTime())) return false;
            const diffDays = (new Date() - created) / (1000 * 60 * 60 * 24);
            return diffDays <= days;
        } catch(e) { return false; }
    }

    // Fetch orders from backend
    async function fetchOrders() {
        try {
            const response = await fetch("/GET/seller/orders");
            if (!response.ok) throw new Error("Failed to fetch orders");
            
            const data = await response.json();
            allOrders = data.orders || [];
            renderOrders();
        } catch (error) {
            console.error("Error fetching orders:", error);
            showToast("Failed to load customer orders", "error");
        }
    }

    window.updateOrderStatusDirect = async function(orderId, newStatus) {
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
            if (typeof fetchAnalytics === "function") fetchAnalytics();
        } catch (error) {
            console.error(error);
            showToast("Failed to update status: " + error.message, "error");
        }
    };

    window.printShippingLabel = function(orderId) {
        const order = allOrders.find(o => o.order_id === orderId);
        if (!order) return;
        
        const printWindow = window.open('', '_blank', 'width=600,height=800');
        
        let itemsListHtml = '';
        order.products.forEach(p => {
            itemsListHtml += `<li>${p.product_name} (Qty: ${p.quantity})</li>`;
        });
        
        const html = `
            <html>
            <head>
                <title>Shipping Label - ${order.order_id}</title>
                <style>
                    body {
                        font-family: 'Courier New', Courier, monospace;
                        padding: 20px;
                        color: #000;
                        background: #fff;
                    }
                    .label-card {
                        border: 3px double #000;
                        padding: 20px;
                        max-width: 500px;
                        margin: 0 auto;
                    }
                    .header {
                        text-align: center;
                        border-bottom: 2px solid #000;
                        padding-bottom: 10px;
                        margin-bottom: 15px;
                    }
                    .section {
                        border-bottom: 1px dashed #000;
                        padding-bottom: 12px;
                        margin-bottom: 12px;
                    }
                    .barcode {
                        font-family: 'Courier New', monospace;
                        font-size: 16px;
                        text-align: center;
                        margin: 15px 0;
                        border: 1px solid #000;
                        padding: 8px;
                        letter-spacing: 4px;
                    }
                    .meta {
                        display: flex;
                        justify-content: space-between;
                        font-size: 12px;
                    }
                    .title {
                        font-size: 18px;
                        font-weight: bold;
                        text-transform: uppercase;
                    }
                </style>
            </head>
            <body onload="window.print(); window.close();">
                <div class="label-card">
                    <div class="header">
                        <div class="title">RAAG Logistics</div>
                        <div style="font-size: 11px; margin-top:4px;">PRIORITY SHIPPING LABEL</div>
                    </div>
                    
                    <div class="section">
                        <strong>SHIP TO:</strong><br>
                        <span style="font-size: 16px; font-weight: bold;">${order.customer_name || 'Recipient'}</span><br>
                        Phone: +${order.customer_number}<br>
                        Address: ${order.delivery_address || 'N/A'}<br>
                        ${order.delivery_city || ''}, ${order.delivery_state || ''}
                    </div>
                    
                    <div class="section">
                        <strong>ITEMS:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            ${itemsListHtml}
                        </ul>
                    </div>
                    
                    <div class="barcode">
                        *${order.order_id.slice(-8).toUpperCase()}*
                    </div>
                    
                    <div class="meta">
                        <span>ORDER ID: ${order.order_id}</span>
                        <span>Date: ${order.created_at}</span>
                    </div>
                </div>
            </body>
            </html>
        `;
        
        printWindow.document.write(html);
        printWindow.document.close();
    };

    function renderOrders() {
        const tbody = document.getElementById("orders-table-body");
        const emptyMsg = document.getElementById("orders-empty-msg");
        const countPendingEl = document.getElementById("count-pending");
        const countProcessingEl = document.getElementById("count-processing");
        const countOutForDeliveryEl = document.getElementById("count-out-for-delivery");
        const countCompletedEl = document.getElementById("count-completed");

        if (!tbody) return;

        // Calculate counts for active tabs
        const pendingCount = allOrders.filter(o => {
            const s = (o.order_status || "").toLowerCase();
            return s === "pending" || !s;
        }).length;

        const processingCount = allOrders.filter(o => {
            const s = (o.order_status || "").toLowerCase();
            return s === "processing";
        }).length;

        const outForDeliveryCount = allOrders.filter(o => {
            const s = (o.order_status || "").toLowerCase();
            return s === "out for delivery";
        }).length;

        const completedCount = allOrders.filter(o => {
            const s = (o.order_status || "").toLowerCase();
            return s === "completed";
        }).length;

        if (countPendingEl) countPendingEl.textContent = pendingCount;
        if (countProcessingEl) countProcessingEl.textContent = processingCount;
        if (countOutForDeliveryEl) countOutForDeliveryEl.textContent = outForDeliveryCount;
        if (countCompletedEl) countCompletedEl.textContent = completedCount;

        // 1. Filter by active tab status
        let filtered = allOrders.filter(o => {
            const s = (o.order_status || "").toLowerCase();
            if (activeOrderTab === "pending") return s === "pending" || !s;
            if (activeOrderTab === "processing") return s === "processing";
            if (activeOrderTab === "out for delivery") return s === "out for delivery";
            if (activeOrderTab === "completed") return s === "completed";
            return false;
        });

        // 2. Filter by Dispatch date
        const dispatchFilter = document.getElementById("filter-dispatch")?.value;
        if (dispatchFilter) {
            filtered = filtered.filter(o => {
                const dispDate = getDispatchDate(o);
                if (!dispDate) return false;
                const yyyy = dispDate.getFullYear();
                const mm = String(dispDate.getMonth() + 1).padStart(2, '0');
                const dd = String(dispDate.getDate()).padStart(2, '0');
                return `${yyyy}-${mm}-${dd}` === dispatchFilter;
            });
        }

        // 3. Filter by Order Date
        const dateFilter = document.getElementById("filter-order-date")?.value;
        if (dateFilter) {
            filtered = filtered.filter(o => {
                if (!o.created_at) return false;
                return o.created_at.substring(0, 10) === dateFilter;
            });
        }

        // 4. Search
        const searchVal = document.getElementById("orders-search-input")?.value.toLowerCase().trim();
        if (searchVal) {
            filtered = filtered.filter(o => 
                o.order_id.toLowerCase().includes(searchVal) ||
                (o.customer_name || "").toLowerCase().includes(searchVal) ||
                o.products.some(p => 
                    (p.product_name || "").toLowerCase().includes(searchVal) ||
                    (p.product_id || "").toLowerCase().includes(searchVal)
                )
            );
        }

        tbody.innerHTML = "";

        // Display empty state or list
        if (filtered.length === 0) {
            if (emptyMsg) emptyMsg.style.display = "block";
            return;
        }
        if (emptyMsg) emptyMsg.style.display = "none";

        filtered.forEach(order => {
            const products = order.products || [];
            const rowSpan = products.length || 1;
            
            // Format order date & time
            let orderDate = 'N/A';
            let orderTime = 'N/A';
            let dispatchDateStr = 'N/A';
            
            if (order.created_at) {
                const parts = order.created_at.trim().split(' ');
                if (parts.length >= 2) {
                    orderDate = parts[0];
                    orderTime = parts[1];
                } else {
                    orderDate = order.created_at;
                }
            }
            
            const dispDate = getDispatchDate(order);
            if (dispDate) {
                const yyyy = dispDate.getFullYear();
                const mm = String(dispDate.getMonth() + 1).padStart(2, '0');
                const dd = String(dispDate.getDate()).padStart(2, '0');
                dispatchDateStr = `${yyyy}-${mm}-${dd}`;
            }

            products.forEach((prod, prodIndex) => {
                const row = document.createElement('tr');
                
                if (prodIndex === 0) {
                    row.className = 'order-group-start';
                    
                    // Accept / Cancel actions
                    let actionHtml = '';
                    const status = (order.order_status || 'Pending').toLowerCase();
                    if (status === 'pending') {
                        actionHtml = `
                            <div style="display:flex; gap:6px;">
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Processing')" style="padding:6px 10px; background:#06d6a0; border:none; color:#181818; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Accept</button>
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Cancelled')" style="padding:6px 10px; background:#e8293f; border:none; color:#fff; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Cancel</button>
                            </div>
                        `;
                    } else if (status === 'processing') {
                        actionHtml = `
                            <div style="display:flex; gap:6px;">
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Out for Delivery')" style="padding:6px 10px; background:#06d6a0; border:none; color:#181818; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Ship</button>
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Cancelled')" style="padding:6px 10px; background:#e8293f; border:none; color:#fff; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Cancel</button>
                            </div>
                        `;
                    } else if (status === 'out for delivery') {
                        actionHtml = `
                            <div style="display:flex; gap:6px;">
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Completed')" style="padding:6px 10px; background:#D4A847; border:none; color:#181818; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Complete</button>
                                <button onclick="updateOrderStatusDirect('${order.order_id}', 'Cancelled')" style="padding:6px 10px; background:#e8293f; border:none; color:#fff; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; transition:opacity 0.2s;" onmouseover="this.style.opacity=0.8" onmouseout="this.style.opacity=1">Cancel</button>
                            </div>
                        `;
                    } else {
                        actionHtml = `<span style="color:var(--muted); font-size:12px;">No Actions</span>`;
                    }

                    row.innerHTML = `
                        <td rowspan="${rowSpan}" style="font-weight: 600; color: #F5F0ED; font-family: monospace;">${order.order_id}</td>
                        <td rowspan="${rowSpan}">${order.customer_name || 'Buyer'}</td>
                        <td rowspan="${rowSpan}">+${order.customer_number}</td>
                        <td rowspan="${rowSpan}">${orderDate}</td>
                        <td rowspan="${rowSpan}">${orderTime}</td>
                        <td rowspan="${rowSpan}" style="color: #D4A847; font-weight: 500;">${dispatchDateStr}</td>
                    `;
                }

                const prodTotal = prod.price * prod.quantity;
                row.innerHTML += `
                    <td style="color: #F5F0ED;">${prod.product_name}</td>
                    <td>${prod.quantity}</td>
                    <td>₹${prod.price.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                    <td style="color: #D4A847; font-weight: 600;">₹${prodTotal.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                `;

                if (prodIndex === 0) {
                    let labelHtml = '';
                    if (status === 'processing') {
                        labelHtml = `
                            <button onclick="printShippingLabel('${order.order_id}')" style="padding:6px 10px; background:#111; border:1px solid #333; color:#fff; border-radius:6px; font-size:12px; cursor:pointer; font-weight:600; display:flex; align-items:center; gap:4px; transition:all 0.2s;" onmouseover="this.style.borderColor='#8B0D1C';this.style.color='#E8293F'" onmouseout="this.style.borderColor='#333';this.style.color='#fff'">
                                <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2m-12 0v6h12v-6"/></svg> Print
                            </button>
                        `;
                    } else {
                        labelHtml = `<span style="color:var(--muted); font-size:12px;">—</span>`;
                    }

                    row.innerHTML += `
                        <td rowspan="${rowSpan}">
                            <span class="order-status-badge ${(order.order_status || 'Pending').toLowerCase()}">
                                ${order.order_status || 'Pending'}
                            </span>
                        </td>
                        <td rowspan="${rowSpan}">${actionHtml}</td>
                        <td rowspan="${rowSpan}">${labelHtml}</td>
                    `;
                }

                tbody.appendChild(row);
            });
        });
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
                    <div class="product-id-txt">ID: ${product._id}</div>
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
                <div style="display:flex; align-items:center; gap:8px;">
                    <button class="edit-btn" data-id="${product._id}" data-spec="${product.specification}" title="Edit Product" style="background:#222; border:1px solid #333; color:#D4A847; font-size:12px; padding:6px 12px; border-radius:6px; cursor:pointer; font-weight:600; transition:all 0.2s;">
                        Edit
                    </button>
                    <button class="delete-btn" data-id="${product._id}" data-spec="${product.specification}" title="Delete Product">
                        ✕
                    </button>
                </div>
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

        // Add event listeners to edit buttons
        document.querySelectorAll(".edit-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const productId = btn.getAttribute("data-id");
                const specName = btn.getAttribute("data-spec");
                const product = allProducts.find(p => p._id === productId);
                if (product) {
                    document.getElementById("edit-product-id").value = product._id;
                    document.getElementById("edit-product-spec").value = product.specification;
                    document.getElementById("edit-product-name").value = product.product_name || product.name || "";
                    document.getElementById("edit-product-mrp").value = product.price || product.mrp || 0.0;
                    document.getElementById("edit-product-stock").value = product.stock !== undefined ? product.stock : 100;
                    document.getElementById("edit-product-description").value = product.description || "";
                    
                    document.getElementById("edit-product-modal").style.display = "flex";
                }
            });
        });
    }

    // Hook search and filter events for products
    if (searchInput) searchInput.addEventListener("input", renderProductsList);
    if (categoryFilter) categoryFilter.addEventListener("change", renderProductsList);

    // Bind order tab button click events
    const orderTabBtns = document.querySelectorAll(".order-tab-btn");
    orderTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            orderTabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeOrderTab = btn.getAttribute("data-status");
            renderOrders();
        });
    });

    // Bind order filters and search inputs
    const filterDispatchEl = document.getElementById("filter-dispatch");
    if (filterDispatchEl) filterDispatchEl.addEventListener("change", renderOrders);

    const filterOrderDateEl = document.getElementById("filter-order-date");
    if (filterOrderDateEl) filterOrderDateEl.addEventListener("change", renderOrders);

    const ordersSearchInputEl = document.getElementById("orders-search-input");
    if (ordersSearchInputEl) ordersSearchInputEl.addEventListener("input", renderOrders);

    const clearOrdersFilterBtn = document.getElementById("clear-orders-filter");
    if (clearOrdersFilterBtn) {
        clearOrdersFilterBtn.addEventListener("click", () => {
            if (filterDispatchEl) filterDispatchEl.value = "";
            if (filterOrderDateEl) filterOrderDateEl.value = "";
            if (ordersSearchInputEl) ordersSearchInputEl.value = "";
            renderOrders();
        });
    }

    // Handle order status change via delegation
    const tabOrdersPane = document.getElementById("tab-orders");
    if (tabOrdersPane) {
        tabOrdersPane.addEventListener("change", async (e) => {
            if (e.target.classList.contains("order-status-select")) {
                const orderId = e.target.getAttribute("data-order-id");
                const newStatus = e.target.value;
                
                const oldClassList = Array.from(e.target.classList);
                const statusClass = newStatus.toLowerCase().replace(/\s+/g, '-');
                e.target.className = `order-status-select ${statusClass}`;
                
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

            // Disable submit button during upload
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.textContent : "Add Product";
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Compressing & Uploading...";
            }

            try {
                // Intercept image files and compress them
                const files = formData.getAll("image_file");
                if (files && files.length > 0) {
                    let hasImages = false;
                    for (let j = 0; j < files.length; j++) {
                        if (files[j] instanceof File && files[j].size > 0 && files[j].type.startsWith("image/")) {
                            hasImages = true;
                            break;
                        }
                    }
                    if (hasImages) {
                        showToast("Compressing images to speed up upload...", "info");
                        formData.delete("image_file");
                        for (let j = 0; j < files.length; j++) {
                            const file = files[j];
                            if (file instanceof File && file.size > 0) {
                                if (file.type.startsWith("image/")) {
                                    const compressed = await compressImage(file);
                                    formData.append("image_file", compressed);
                                } else {
                                    formData.append("image_file", file);
                                }
                            }
                        }
                    }
                }

                const response = await fetch(form.action, {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    showToast(data.message || "Product added successfully!", "success");
                    form.reset();

                    // Hide specifications sections in form
                    if (specSelect && specSelect.closest(".form-group").style.display === "none") {
                        showSection(specSelect.value);
                        updateApparelFields();
                    } else {
                        sections.forEach(section => setSectionActive(section, false));
                        if (specSelect) specSelect.value = "";
                    }

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
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            }
        });
    }

    // Fetch and populate overview analytics
    async function fetchAnalytics() {
        try {
            const res = await fetch("/GET/seller/analytics");
            if (!res.ok) throw new Error("Failed to fetch analytics");
            const data = await res.json();
            
            document.getElementById("stat-total-revenue").textContent = "₹" + parseFloat(data.total_revenue).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById("stat-total-orders").textContent = data.total_orders;
            document.getElementById("stat-completed-orders").textContent = data.completed_orders;
            
            const categoryList = document.getElementById("analytics-category-list");
            if (categoryList) {
                categoryList.innerHTML = "";
                if (!data.category_sales || data.category_sales.length === 0) {
                    categoryList.innerHTML = `<div style="color:#A89B92; text-align:center; padding:10px; font-size:13px;">No sales recorded yet.</div>`;
                } else {
                    data.category_sales.forEach(c => {
                        categoryList.innerHTML += `
                            <div style="display:flex; justify-content:space-between; align-items:center; background:#111; padding:10px 14px; border-radius:6px; font-size:13px;">
                                <span style="color:#F5F0ED; font-weight:500;">${c.category}</span>
                                <span style="color:#D4A847; font-weight:600;">₹${parseFloat(c.revenue).toLocaleString()}</span>
                            </div>
                        `;
                    });
                }
            }
            
            const topProductsList = document.getElementById("analytics-top-products");
            if (topProductsList) {
                topProductsList.innerHTML = "";
                if (!data.top_products || data.top_products.length === 0) {
                    topProductsList.innerHTML = `<div style="color:#A89B92; text-align:center; padding:10px; font-size:13px;">No sales recorded yet.</div>`;
                } else {
                    data.top_products.forEach(p => {
                        topProductsList.innerHTML += `
                            <div style="display:flex; justify-content:space-between; align-items:center; background:#111; padding:10px 14px; border-radius:6px; font-size:13px;">
                                <div style="display:flex; flex-direction:column;">
                                    <span style="color:#F5F0ED; font-weight:500;">${p.name}</span>
                                    <span style="color:#A89B92; font-size:11px;">Qty: ${p.quantity} (${p.category})</span>
                                </div>
                                <span style="color:#D4A847; font-weight:600;">₹${parseFloat(p.revenue).toLocaleString()}</span>
                            </div>
                        `;
                    });
                }
            }
        } catch (err) {
            console.error("Error loading analytics:", err);
        }
    }

    // Modal Close Helper
    window.closeEditModal = function() {
        document.getElementById("edit-product-modal").style.display = "none";
        document.getElementById("edit-product-form").reset();
    };

    // Edit Product Submit
    const editProductForm = document.getElementById("edit-product-form");
    if (editProductForm) {
        editProductForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(editProductForm);
            
            try {
                const response = await fetch("/POST/seller/product/edit", {
                    method: "POST",
                    body: formData
                });
                
                const data = await response.json();
                if (response.ok) {
                    showToast("Product updated successfully!", "success");
                    closeEditModal();
                    fetchProducts();
                    fetchAnalytics();
                } else {
                    showToast("Failed to edit product: " + (data.detail || "Error"), "error");
                }
            } catch (error) {
                console.error(error);
                showToast("Network error. Please try again.", "error");
            }
        });
    }

    // Profile Settings Form Submit
    const settingsProfileForm = document.getElementById("settings-profile-form");
    if (settingsProfileForm) {
        settingsProfileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const payload = {
                business_name: document.getElementById("settings-business-name").value,
                owner_name: document.getElementById("settings-owner-name").value,
                city: document.getElementById("settings-city").value,
                state: document.getElementById("settings-state").value
            };
            
            try {
                const response = await fetch("/POST/user/update-profile", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                if (response.ok) {
                    showToast("Profile updated successfully!", "success");
                    const sidebarName = document.querySelector(".sidebar-profile .profile-name");
                    const sidebarBusiness = document.querySelector(".sidebar-profile .profile-business");
                    if (sidebarName) sidebarName.textContent = payload.owner_name;
                    if (sidebarBusiness) sidebarBusiness.textContent = payload.business_name;
                } else {
                    showToast("Failed to update profile: " + (data.detail || "Error"), "error");
                }
            } catch (error) {
                console.error(error);
                showToast("Network error. Please try again.", "error");
            }
        });
    }

    // Initial Fetch on load
    fetchProducts();
    fetchAnalytics();
});