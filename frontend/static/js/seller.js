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

    // Search and filter elements
    const searchInput = document.getElementById("product-search");
    const categoryFilter = document.getElementById("product-category-filter");

    // Image upload choice toggle elements
    const imageUploadChoice = document.getElementById("image-upload-choice");
    const imageUrlChoice = document.getElementById("image-url-choice");
    const fileInputGroup = document.getElementById("file-input-group");
    const urlInputGroup = document.getElementById("url-input-group");

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

    // Navigation (Tab switching)
    menuItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");

            menuItems.forEach(mi => mi.classList.remove("active"));
            item.classList.add("active");

            tabPanes.forEach(pane => {
                pane.classList.remove("active");
                if (pane.id === targetTab) {
                    pane.classList.add("active");
                }
            });

            if (targetTab === "tab-products" || targetTab === "tab-overview") {
                fetchProducts();
            }
        });
    });

    // Image Input Option Toggle
    if (imageUploadChoice && imageUrlChoice) {
        imageUploadChoice.addEventListener("click", () => {
            imageUploadChoice.classList.add("active");
            imageUrlChoice.classList.remove("active");
            fileInputGroup.style.display = "block";
            urlInputGroup.style.display = "none";
            document.getElementById("image_url").value = "";
        });

        imageUrlChoice.addEventListener("click", () => {
            imageUrlChoice.classList.add("active");
            imageUploadChoice.classList.remove("active");
            urlInputGroup.style.display = "block";
            fileInputGroup.style.display = "none";
            document.getElementById("image_file").value = "";
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
            return matchesQuery && matchesCategory;
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
            if (product.image) {
                if (product.image.startsWith("http://") || product.image.startsWith("https://")) {
                    imgSrc = product.image;
                } else {
                    imgSrc = `/static/images/${product.image}`;
                }
            } else {
                // Category defaults
                if (product.specification === "apparel") {
                    imgSrc = product.gender === "Male" ? "/static/images/menjeans.webp" : "/static/images/womentshirt.webp";
                } else if (product.specification === "fmcg") {
                    imgSrc = "/static/images/groceries.webp";
                }
            }

            // Specs descriptions
            let specDetailsHtml = "";
            if (product.specification === "apparel") {
                specDetailsHtml = `Size: <strong>${product.size}</strong> | Fabric: <strong>${product.fabric}</strong> | GSM: <strong>${product.gsm}</strong>`;
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
                    <img src="${imgSrc}" alt="${product.product_name}" onerror="this.src='/static/images/default.webp'">
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
                    
                    // Reset upload toggle views
                    if (imageUploadChoice) {
                        imageUploadChoice.click();
                    }

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