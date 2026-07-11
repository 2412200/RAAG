/* ── RAAG Shared Shopping Cart Logic ── */

function toggleCartFold() {
  const folded = localStorage.getItem('cartFolded') === 'true';
  localStorage.setItem('cartFolded', !folded);
  updateSidebarCart();
}

function addToCartFromEl(el) {
  const name = el.getAttribute('data-name');
  const image = el.getAttribute('data-image');
  const quantity = parseInt(el.getAttribute('data-quantity') || el.getAttribute('data-moq') || 1);
  const price = parseFloat(el.getAttribute('data-price') || 0);
  addToOrder({ name, image, quantity, price });
}

// Global cart management functions
function updateSidebarCart() {
  const cartEl = document.getElementById('sidebar-cart');
  if (!cartEl) return;

  const orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  
  // Update mobile badge if it exists
  const mobileBadge = document.getElementById('mobile-cart-count');
  if (mobileBadge) {
    const totalCount = orders.reduce((sum, item) => sum + (item.qty || 1), 0);
    if (totalCount > 0) {
      mobileBadge.textContent = totalCount;
      mobileBadge.style.display = 'flex';
    } else {
      mobileBadge.style.display = 'none';
    }
  }

  const isFolded = localStorage.getItem('cartFolded') === 'true';
  const chevron = isFolded ? '🔽' : '🔼';

  if (orders.length === 0) {
    cartEl.innerHTML = `
      <div class="cart-title-container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <span class="cart-title">🛒 My Cart</span>
        <button class="cart-fold-toggle-btn" onclick="toggleCartFold()" style="background: transparent; border: none; color: var(--cart-text); cursor: pointer; font-size: 11px; padding: 2px;" title="Fold / Unfold Cart">
          ${chevron}
        </button>
      </div>
      <div class="cart-empty-text" style="${isFolded ? 'display: none !important;' : ''}">Your cart is empty.</div>
    `;
    return;
  }

  let itemsHtml = '';
  let subtotal = 0;

  orders.forEach((item, index) => {
    const qty = item.qty || 1;
    const price = item.price;
    const itemTotal = price * qty;
    subtotal += itemTotal;

    const moqVal = parseInt(item.moq || 1);
    const maxVal = moqVal + 100;
    const imageSrc = item.image.startsWith('http') % 1 === 0 ? item.image : (item.image.startsWith('/') ? item.image : `/static/images/${item.image}`);

    itemsHtml += `
      <div class="cart-item-card-wrapper">
        <div class="cart-item-card">
          <img src="${imageSrc}" class="cart-item-img" alt="${item.name}" onerror="this.onerror=null;this.src='/static/images/default.webp'">
          <div class="cart-item-details">
            <span class="cart-item-name" title="${item.name}">${item.name}</span>
            <span class="cart-item-price">₹${price.toLocaleString()}</span>
            <div class="cart-item-controls">
              <button class="cart-qty-btn" onclick="changeSidebarQty(${index}, -1)">-</button>
              <span id="cart-card-qty-${index}" class="cart-item-qty">${qty}</span>
              <button class="cart-qty-btn" onclick="changeSidebarQty(${index}, 1)">+</button>
            </div>
          </div>
          <button class="cart-remove-btn" onclick="changeSidebarQty(${index}, -9999)" title="Remove item">✕</button>
        </div>
      </div>
    `;
  });

  cartEl.innerHTML = `
    <div class="cart-title-container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
      <span class="cart-title">🛒 My Cart</span>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="cart-count-badge">${orders.length}</span>
        <button class="cart-fold-toggle-btn" onclick="toggleCartFold()" style="background: transparent; border: none; color: var(--cart-text); cursor: pointer; font-size: 11px; padding: 2px; display: flex; align-items: center;" title="Fold / Unfold Cart">
          ${chevron}
        </button>
      </div>
    </div>
    <div class="cart-items-list" style="${isFolded ? 'display: none !important;' : ''}">
      ${itemsHtml}
    </div>
    <div class="cart-footer-section" style="${isFolded ? 'display: none !important;' : ''}">
      <div class="cart-total-row">
        <span>Subtotal:</span>
        <span id="cart-total-amount" class="cart-total-amount">₹${subtotal.toLocaleString()}</span>
      </div>
      <button class="cart-checkout-btn" onclick="openCartPaymentModal()">Checkout</button>
    </div>
  `;
}

function changeSidebarQty(index, delta) {
  let orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  if (!orders[index]) return;

  const item = orders[index];
  const moqVal = parseInt(item.moq || 1);
  const currentQty = item.qty || moqVal;

  if (delta === -9999) {
    orders.splice(index, 1);
  } else {
    const newQty = currentQty + delta;
    if (newQty < moqVal) {
      alert(`Minimum order quantity for this item is ${moqVal} units.`);
      item.qty = moqVal;
    } else {
      item.qty = newQty;
    }
  }

  localStorage.setItem('orderItems', JSON.stringify(orders));
  updateSidebarCart();

  // Sync main checkout page if we are on orders.html
  if (typeof loadOrders === 'function') {
    loadOrders();
  }
}

function changeSidebarSliderQty(index, val) {
  let orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  if (!orders[index]) return;

  const item = orders[index];
  const moqVal = parseInt(item.moq || 1);
  let newQty = parseInt(val);

  if (newQty < moqVal) {
    newQty = moqVal;
  }
  item.qty = newQty;

  // Update in-memory values for drag smoothness
  const qtyLabel = document.getElementById(`cart-qty-val-${index}`);
  const cardQtyLabel = document.getElementById(`cart-card-qty-${index}`);
  const totalAmountEl = document.getElementById('cart-total-amount');

  if (qtyLabel) qtyLabel.textContent = newQty;
  if (cardQtyLabel) cardQtyLabel.textContent = newQty;

  // Temporarily update total sum label
  orders[index].qty = newQty;
  const subtotal = orders.reduce((sum, it) => sum + (it.price * (it.qty || 1)), 0);
  if (totalAmountEl) {
    totalAmountEl.textContent = `₹${subtotal.toLocaleString()}`;
  }
}

function saveSidebarSliderQty(index, val) {
  let orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  if (!orders[index]) return;

  const item = orders[index];
  const moqVal = parseInt(item.moq || 1);
  let newQty = parseInt(val);

  if (newQty < moqVal) {
    newQty = moqVal;
  }
  item.qty = newQty;

  localStorage.setItem('orderItems', JSON.stringify(orders));
  updateSidebarCart();

  // Sync main checkout page if we are on orders.html
  if (typeof loadOrders === 'function') {
    loadOrders();
  }
}

function toggleCartSlider(index) {
  const drawer = document.getElementById(`cart-slider-drawer-${index}`);
  const chevron = document.getElementById(`cart-chevron-${index}`);
  if (!drawer) return;

  if (drawer.style.display === 'none') {
    drawer.style.display = 'block';
    if (chevron) chevron.textContent = '🔼';
  } else {
    drawer.style.display = 'none';
    if (chevron) chevron.textContent = '🔽';
  }
}

function addToOrder(product) {
  let orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  
  const moqVal = parseInt(product.quantity || product.moq || 1);
  const existing = orders.find(item => item.name === product.name);
  if (existing) {
    existing.qty = (existing.qty || 1) + 1;
  } else {
    orders.push({
      name: product.name,
      image: product.image,
      price: parseFloat(product.price),
      qty: moqVal,
      moq: moqVal
    });
  }
  localStorage.setItem('orderItems', JSON.stringify(orders));

  // Refresh cart UI
  updateSidebarCart();

  // Sync main checkout page if we are on orders.html
  if (typeof loadOrders === 'function') {
    loadOrders();
  }

  // Show dynamic premium toast
  showCartToast("Item added to cart!");
}

function showCartToast(message) {
  let toast = document.getElementById('cart-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'cart-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--red, var(--accent, #C0172A));
      color: #fff;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.5px;
      box-shadow: 0 8px 24px rgba(192, 23, 42, 0.4);
      z-index: 10000;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    `;
    document.body.appendChild(toast);
  }
  
  toast.textContent = "✅ " + message;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';
  
  clearTimeout(toast.timeoutId);
  toast.timeoutId = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
  }, 2500);
}

// Payment Checkout Modal dynamic injection
function injectPaymentModal() {
  if (document.getElementById('cart-payment-modal')) return;

  const modalHtml = `
    <div id="cart-payment-modal" class="cart-modal-overlay">
      <div class="cart-modal-card">
        <h3 class="cart-modal-title">Secure Checkout</h3>
        <p class="cart-modal-desc">Please complete the mock payment details below to authorize this transaction.</p>
        
        <div class="cart-modal-fields">
          <div class="cart-modal-field">
            <label class="cart-modal-label">Cardholder Name</label>
            <input type="text" id="cart-card-name" value="Buyer Customer" class="cart-modal-input">
          </div>
          <div class="cart-modal-field">
            <label class="cart-modal-label">Card Number</label>
            <input type="text" id="cart-card-number" value="4111 5555 6666 7777" class="cart-modal-input">
          </div>
          <div class="cart-modal-row">
            <div class="cart-modal-field" style="flex: 1;">
              <label class="cart-modal-label">Expiry Date</label>
              <input type="text" id="cart-card-expiry" value="12/28" class="cart-modal-input" placeholder="MM/YY">
            </div>
            <div class="cart-modal-field" style="flex: 1;">
              <label class="cart-modal-label">CVV</label>
              <input type="password" id="cart-card-cvv" value="999" class="cart-modal-input" placeholder="123">
            </div>
          </div>
        </div>
        
        <div class="cart-modal-footer">
          <button id="cart-modal-cancel-btn" class="cart-modal-cancel">Cancel</button>
          <button id="cart-modal-submit-btn" class="cart-modal-submit">Pay & Place Order</button>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);

  // Bind events
  document.getElementById('cart-modal-cancel-btn').addEventListener('click', closeCartPaymentModal);
  document.getElementById('cart-modal-submit-btn').addEventListener('click', processCartOrder);
}

function openCartPaymentModal() {
  const modal = document.getElementById('cart-payment-modal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

function closeCartPaymentModal() {
  const modal = document.getElementById('cart-payment-modal');
  if (modal) {
    modal.style.display = 'none';
  }
}

async function processCartOrder() {
  const submitBtn = document.getElementById('cart-modal-submit-btn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Processing...';

  const orders = JSON.parse(localStorage.getItem('orderItems') || '[]');
  if (orders.length === 0) {
    closeCartPaymentModal();
    submitBtn.disabled = false;
    submitBtn.textContent = 'Pay & Place Order';
    return;
  }

  const products = orders.map(item => ({
    product_name: item.name,
    quantity: parseInt(item.qty || item.quantity || 1),
    price: parseFloat(item.price)
  }));
  const total_amount = orders.reduce((sum, item) => sum + (item.price * (item.qty || item.quantity || 1)), 0);

  const payload = {
    customer_name: document.getElementById('cart-card-name').value || "Buyer Customer",
    customer_number: 9999999999,
    products: products,
    total_amount: total_amount
  };

  try {
    const res = await fetch('/POST/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      localStorage.removeItem('orderItems');
      closeCartPaymentModal();
      alert('Order confirmed and mock payment processed successfully!');
      
      updateSidebarCart();
      
      // If we are on orders page, sync the main lists
      if (typeof loadOrders === 'function') {
        loadOrders();
      }
      if (typeof switchTab === 'function') {
        switchTab('history');
      } else {
        // Redirect home page/categories to orders history page
        window.location.href = '/orders?tab=history';
      }
    } else {
      const data = await res.json();
      alert('Failed to place order: ' + (data.detail || 'Please try again.'));
    }
  } catch (err) {
    console.error(err);
    alert('Network error. Please try again.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Pay & Place Order';
  }
}

// Initialise resources
document.addEventListener('DOMContentLoaded', () => {
  // Inject payment modal onto page
  injectPaymentModal();
  
  // Render current cart in sidebar
  updateSidebarCart();

  // Mobile sidebar togglers mapping
  const sidebarToggleBtn = document.getElementById("sidebar-toggle");
  const mobileCartToggle = document.getElementById("mobile-cart-toggle");
  const sidebarEl = document.querySelector(".sidebar");
  
  if (sidebarToggleBtn && sidebarEl) {
    sidebarToggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      sidebarEl.classList.toggle("show");
    });
  }

  if (mobileCartToggle && sidebarEl) {
    mobileCartToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      sidebarEl.classList.toggle("show");
    });
  }

  // Click outside to close sidebar
  document.addEventListener("click", (e) => {
    if (sidebarEl && window.innerWidth <= 768 && sidebarEl.classList.contains("show")) {
      if (!sidebarEl.contains(e.target) && e.target !== sidebarToggleBtn && e.target !== mobileCartToggle) {
        sidebarEl.classList.remove("show");
      }
    }
  });

  // Highlight current page active state in menu
  const path = window.location.pathname;
  const menuItems = document.querySelectorAll(".sidebar-menu .menu-item");
  menuItems.forEach(item => {
    const href = item.getAttribute("href");
    if (href === path) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
});
