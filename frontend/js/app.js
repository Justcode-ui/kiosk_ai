/**
 * KioskAI Frontend Application
 * Main JavaScript logic for SPA functionality and API integration
 */

// ==================== CONFIGURATION ====================
// Determine API Base URL based on environment
let API_BASE_URL = '';

if (window.location.protocol === 'file:') {
    API_BASE_URL = 'http://127.0.0.1:8000';
} else if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
    if (window.location.port === '8000') {
        API_BASE_URL = '';
    } else {
        API_BASE_URL = 'http://127.0.0.1:8000';
    }
} else {
    API_BASE_URL = '';
}
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// ==================== API CLIENT ====================
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                // Unauthorized - clear token and redirect to login
                this.logout();
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            showNotification(error.message, 'error');
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    logout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('authToken');
        window.location.href = 'landing.html';
    }
}

const api = new APIClient(API_BASE_URL);

// ==================== DASHBOARD LOGIC ====================
async function loadDashboard() {
    // Load initial data
    await loadOverviewData();
}

// ==================== NAVIGATION ====================
function navigateToPage(pageName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // Update pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`page-${pageName}`).classList.add('active');

    // Load page data
    switch (pageName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'customers':
            loadCustomers();
            break;
        case 'messages':
            loadConversations();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'details':
            loadDetails();
            break;
    }
}

// ==================== OVERVIEW PAGE ====================
async function loadOverviewData() {
    try {
        const analytics = await api.get('/api/analytics/overview');

        if (analytics) {
            document.getElementById('metric-customers').textContent = analytics.total_customers;
            document.getElementById('metric-conversations').textContent = analytics.active_conversations;
            document.getElementById('metric-orders').textContent = analytics.total_orders;
            document.getElementById('metric-revenue').textContent = `₦${analytics.total_revenue.toLocaleString()}`;

            document.getElementById('insight-response-time').textContent = `${Math.round(analytics.average_response_time)}s`;
            document.getElementById('insight-leads').textContent = analytics.leads_this_week;
            document.getElementById('insight-attention').textContent = analytics.customers_needing_attention;
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// ==================== CUSTOMERS PAGE ====================
async function loadCustomers() {
    try {
        const customers = await api.get('/api/customers');

        const tbody = document.getElementById('customers-table-body');
        tbody.innerHTML = '';

        if (customers && customers.length > 0) {
            customers.forEach(customer => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${customer.name}</td>
                    <td>${customer.phone_number}</td>
                    <td>${customer.email || '-'}</td>
                    <td>${customer.total_orders}</td>
                    <td>₦${customer.total_spent.toLocaleString()}</td>
                    <td>${new Date(customer.last_contact_date).toLocaleDateString()}</td>
                    <td>
                        <button class="btn-secondary" onclick="viewCustomer('${customer.id}')">View</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">No customers yet</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load customers:', error);
    }
}

// ==================== MESSAGES PAGE ====================
async function loadConversations() {
    try {
        const conversations = await api.get('/api/conversations');

        const list = document.getElementById('conversations-list');
        list.innerHTML = '';

        if (conversations && conversations.length > 0) {
            conversations.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'conversation-item';
                const name = conv.customer_name || 'Customer';
                const initial = name.charAt(0).toUpperCase();
                // Random bg color for avatar based on name length
                const colors = ['#1B6EA8', '#4CD7B4', '#E63946', '#F4A261', '#2A9D8F'];
                const bg = colors[name.length % colors.length];

                item.innerHTML = `
                    <div class="conversation-avatar" style="background: ${bg}">${initial}</div>
                    <div class="conversation-info">
                        <div class="conversation-top">
                            <strong>${name}</strong>
                            <span class="conversation-time">${new Date(conv.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div class="conversation-bottom">
                            <span class="conversation-platform badge-${conv.platform}">${conv.platform}</span>
                            <span class="conversation-id-preview">...${conv.customer_id.slice(-4)}</span>
                        </div>
                    </div>
                `;
                item.onclick = () => {
                    // Remove active from all
                    document.querySelectorAll('.conversation-item').forEach(i => i.classList.remove('active'));
                    // Add to clicked
                    item.classList.add('active');
                    loadMessages(conv.id);
                };
                list.appendChild(item);
            });
        } else {
            list.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--color-text-secondary);">No conversations yet</div>';
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}

async function loadMessages(conversationId) {
    try {
        const messages = await api.get(`/api/conversations/${conversationId}/messages`);

        const thread = document.getElementById('message-thread');
        thread.innerHTML = '';

        if (messages && messages.length > 0) {
            messages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${msg.is_from_customer ? 'customer' : 'ai'}`;
                msgDiv.innerHTML = `
                    <div class="message-content">${msg.content}</div>
                    <div class="message-time">${new Date(msg.created_at).toLocaleTimeString()}</div>
                `;
                thread.appendChild(msgDiv);
            });
        }
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

// ==================== ORDERS PAGE ====================
// ==================== ORDERS PAGE ====================
async function loadOrders() {
    try {
        const orders = await api.get('/api/orders');

        const tbody = document.getElementById('orders-table-body');
        tbody.innerHTML = '';

        if (orders && orders.length > 0) {
            orders.forEach(order => {
                const row = document.createElement('tr');
                const productSummary = Array.isArray(order.items)
                    ? order.items.map(i => `${i.name} (x${i.quantity})`).join(', ')
                    : 'Unknown Item';

                row.innerHTML = `
                    <td>${order.order_number}</td>
                    <td>
                        <div class="font-medium">${order.customer_name || 'Customer'}</div>
                        <div class="text-xs text-secondary" title="${productSummary}">${productSummary.substring(0, 30)}${productSummary.length > 30 ? '...' : ''}</div>
                    </td>
                    <td>₦${order.total_amount.toLocaleString()}</td>
                    <td><span class="status-badge status-${order.status}">${order.status}</span></td>
                    <td>${new Date(order.created_at).toLocaleDateString()}</td>
                    <td>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-secondary btn-sm" onclick="viewOrder('${order.id}')">View</button>
                            ${order.status === 'pending' ? `
                                <button class="btn-primary btn-sm" onclick="updateOrderStatus('${order.id}', 'shipped')" style="background: #1B6EA8; border: none;">Sent</button>
                            ` : ''}
                            ${order.status === 'shipped' ? `
                                <button class="btn-primary btn-sm" onclick="updateOrderStatus('${order.id}', 'completed')" style="background: #4CD7B4; border: none;">Finish</button>
                            ` : ''}
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">No orders yet</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

// Update order status
window.updateOrderStatus = async (orderId, newStatus) => {
    const statusText = newStatus === 'shipped' ? 'Order Sent' : 'Order Finished';
    if (!confirm(`Are you sure you want to mark this as ${statusText}?`)) return;

    try {
        await api.put(`/api/orders/${orderId}`, { status: newStatus });
        showNotification(`Order marked as ${newStatus}`, 'success');
        loadOrders();
    } catch (error) {
        console.error('Failed to update order status:', error);
        showNotification('Failed to update order status', 'error');
    }
};

// View Order Details
window.viewOrder = async (orderId) => {
    try {
        const order = await api.get(`/api/orders/${orderId}`);
        const modal = document.getElementById('view-order-modal');
        const content = document.getElementById('order-details-content');

        const itemsHtml = order.items.map(i => `
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                <span>${i.name} (x${i.quantity})</span>
                <span>₦${i.price.toLocaleString()}</span>
            </div>
        `).join('');

        content.innerHTML = `
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Order Information</h3>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                    <p><strong>Order #:</strong> ${order.order_number}</p>
                    <p><strong>Customer:</strong> ${order.customer_name}</p>
                    <p><strong>Status:</strong> <span class="status-badge status-${order.status}">${order.status}</span></p>
                    <p><strong>Date:</strong> ${new Date(order.created_at).toLocaleString()}</p>
                </div>
            </div>

            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Items</h3>
                <div style="margin-top: 0.5rem;">
                    ${itemsHtml}
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; font-weight: bold; border-top: 2px solid #eee;">
                        <span>Total</span>
                        <span>₦${order.total_amount.toLocaleString()}</span>
                    </div>
                </div>
            </div>

            ${order.receipt_url ? `
                <div style="margin-bottom: 1.5rem;">
                    <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Payment Receipt</h3>
                    <div style="margin-top: 0.5rem; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
                        <img src="${order.receipt_url}" alt="Receipt" style="width: 100%; display: block;">
                        <div style="padding: 10px; background: #f8f9fa; text-align: center;">
                            <a href="${order.receipt_url}" target="_blank" style="color: var(--color-primary); text-decoration: none; font-size: 0.9rem;">View Full Image</a>
                        </div>
                    </div>
                </div>
            ` : '<p style="color: #666; font-style: italic;">No receipt attached to this order.</p>'}

            ${order.notes ? `
                <div>
                    <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Notes</h3>
                    <p style="margin-top: 0.5rem; background: #fffbeb; padding: 10px; border-radius: 8px; border: 1px solid #fef3c7;">${order.notes}</p>
                </div>
            ` : ''}
        `;

        modal.classList.add('show');
    } catch (error) {
        console.error('Failed to load order details:', error);
        showNotification('Failed to load order details', 'error');
    }
};

// View Customer Profile
window.viewCustomer = async (customerId) => {
    try {
        const customer = await api.get(`/api/customers/${customerId}`);
        const modal = document.getElementById('view-customer-modal');
        const content = document.getElementById('customer-details-content');

        content.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div>
                    <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Contact Info</h3>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        <p><strong>Name:</strong> ${customer.name}</p>
                        <p><strong>Phone:</strong> ${customer.phone_number}</p>
                        <p><strong>Email:</strong> ${customer.email || '-'}</p>
                        <p><strong>Last Contact:</strong> ${new Date(customer.last_contact_date).toLocaleDateString()}</p>
                    </div>
                </div>
                <div>
                    <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Order History</h3>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        <p><strong>Total Orders:</strong> ${customer.total_orders}</p>
                        <p><strong>Total Spent:</strong> ₦${customer.total_spent.toLocaleString()}</p>
                    </div>
                </div>
            </div>

            <div style="margin-top: 1.5rem;">
                <h3 style="color: var(--color-text-secondary); font-size: 0.8rem; text-transform: uppercase;">Tags / Info</h3>
                <div style="margin-top: 0.5rem;">
                    ${customer.tags && customer.tags.length > 0 ? customer.tags.map(t => `<span class="badge" style="margin-right:5px">${t}</span>`).join('') : '<p>No tags</p>'}
                    <p style="margin-top: 1rem;"><strong>Business Context:</strong></p>
                    <p style="background: #fff; padding: 10px; border: 1px solid #eee; border-radius: 4px;">${customer.business_info || 'No extra info'}</p>
                </div>
            </div>
        `;

        modal.classList.add('show');
    } catch (error) {
        console.error('Failed to load customer profile:', error);
        showNotification('Failed to load customer profile', 'error');
    }
};

// ==================== INVOICES PAGE ====================
// ==================== SETTINGS PAGE ====================
// ==================== DETAILS PAGE ====================
async function loadDetails() {
    try {
        const user = await api.get('/api/users/me');
        if (user) {
            // Populate View Mode (Card)
            document.getElementById('view-profile-name').textContent = user.business_name || 'Business Name';
            document.getElementById('view-business-name').textContent = user.business_name || 'Not Set';
            document.getElementById('view-phone-number').textContent = user.phone_number || 'Not Set';
            document.getElementById('view-email').textContent = user.email || 'Not Set';

            document.getElementById('view-bank-name').textContent = user.bank_name || 'Not Set';
            document.getElementById('view-account-number').textContent = user.account_number || '****';
            document.getElementById('view-account-name').textContent = user.account_name || 'Not Set';

            // Telegram Bot Status
            if (user.telegram_bot_token) {
                const badge = document.getElementById('telegram-connected-badge');
                if (badge) badge.classList.remove('hidden');
                const btn = document.getElementById('btn-connect-telegram');
                if (btn) btn.textContent = 'Update Bot';

                // Pre-fill Telegram Form
                if (document.getElementById('telegramBotToken')) {
                    document.getElementById('telegramBotToken').value = user.telegram_bot_token || '';
                    document.getElementById('telegramBotUsername').value = user.telegram_bot_username || '';
                }

                // Show Disconnect button
                const btnDisconnect = document.getElementById('btn-disconnect-telegram');
                if (btnDisconnect) btnDisconnect.style.display = 'block';

                // Update Diagnostic Link
                const statusCheck = document.getElementById('telegram-status-check');
                if (statusCheck) statusCheck.classList.remove('hidden');

                const diagLink = document.getElementById('link-diagnostic');
                if (diagLink) {
                    // Try to guess browser-visible base URL or use relative
                    // Actually, the diagnostic endpoint is authenticated or public?
                    // It's public /api/webhooks/telegram/{user_id}
                    diagLink.href = `${API_BASE_URL}/api/webhooks/telegram/${user.id}`;
                }

            } else {
                // Not connected
                const badge = document.getElementById('telegram-connected-badge');
                if (badge) badge.classList.add('hidden');
                const btn = document.getElementById('btn-connect-telegram');
                if (btn) btn.textContent = 'Connect Bot';

                // Hide Disconnect button since nothing to disconnect
                const btnDisconnect = document.getElementById('btn-disconnect-telegram');
                if (btnDisconnect) btnDisconnect.style.display = 'none';

                // Hide Diagnostic Link
                const statusCheck = document.getElementById('telegram-status-check');
                if (statusCheck) statusCheck.classList.add('hidden');

                // Clear Form
                if (document.getElementById('telegramBotToken')) {
                    document.getElementById('telegramBotToken').value = '';
                    document.getElementById('telegramBotUsername').value = '';
                }
            }

            // Business Context
            if (document.getElementById('businessContext')) {
                document.getElementById('businessContext').value = user.business_context || '';
            }

            // Populate Edit Form
            if (document.getElementById('businessName')) {
                document.getElementById('businessName').value = user.business_name || '';
            }
            if (document.getElementById('businessPhone')) {
                document.getElementById('businessPhone').value = user.phone_number || '';
            }

            // Populate Edit Form (Pre-fill)
            // Bank Details
            if (user.bank_name) document.getElementById('bankName').value = user.bank_name;
            if (user.account_number) document.getElementById('accountNumber').value = user.account_number;
            if (user.account_name) document.getElementById('accountName').value = user.account_name;

            // Business Profile
            if (user.business_name) document.getElementById('businessName').value = user.business_name;
            if (user.phone_number) document.getElementById('businessPhone').value = user.phone_number;
        }
    } catch (error) {
        console.error('Failed to load user details:', error);
    }
}

// Toggle Logic for Profile Page



// ==================== NOTIFICATIONS ====================
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// ==================== EVENT LISTENERS ====================
document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in - if not, likely should redirect to login
    // BUT since this is a dev/demo env, we might want to allow viewing without strict auth 
    // or simulate auth. For now let's enforce:
    if (!authToken) {
        // Redirect to login if no token
        window.location.href = 'login.html';
        return;
    }

    // Mobile Navigation Logic
    const mobileBtn = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    function toggleSidebar() {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('show');
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.classList.remove('show');
    }

    if (mobileBtn) mobileBtn.addEventListener('click', toggleSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // Close sidebar when clicking nav items on mobile
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) closeSidebar();
        });
    });

    // Navigation
    // Profile Edit Toggles (Restored)
    const btnEditProfile = document.getElementById('btn-edit-profile');
    const btnCancelEdit = document.getElementById('btn-cancel-edit');
    const profileView = document.getElementById('profile-view');
    const profileEditForm = document.getElementById('profile-edit-form');

    if (btnEditProfile) {
        btnEditProfile.addEventListener('click', () => {
            profileView.classList.add('hidden');
            profileEditForm.classList.remove('hidden');
        });
    }

    if (btnCancelEdit) {
        btnCancelEdit.addEventListener('click', () => {
            profileEditForm.classList.add('hidden');
            profileView.classList.remove('hidden');
        });
    }

    // Generic Modal Close Logic
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('close-modal') || e.target.classList.contains('close-modal-btn')) {
            const modal = e.target.closest('.modal');
            if (modal) modal.classList.remove('show');
        }
        // Close modal when clicking background
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });

    // New Message Logic (Restored)
    const btnNewMsg = document.getElementById('btn-new-message');
    const newMsgModal = document.getElementById('new-message-modal');
    const closeNewMsgBtn = document.querySelector('.close-new-msg');
    const closeNewMsgBtn2 = document.querySelector('.close-new-msg-btn');
    const newMsgForm = document.getElementById('new-message-form');

    if (btnNewMsg) {
        btnNewMsg.addEventListener('click', () => {
            if (newMsgModal) newMsgModal.classList.add('show');
        });
    }

    [closeNewMsgBtn, closeNewMsgBtn2].forEach(btn => {
        if (btn) btn.addEventListener('click', () => {
            if (newMsgModal) newMsgModal.classList.remove('show');
        });
    });

    if (newMsgForm) {
        newMsgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const phone = document.getElementById('newMsgPhone').value;
                const content = document.getElementById('newMsgContent').value;

                // 1. Create Customer
                const customer = await api.post('/api/customers', {
                    name: 'Customer ' + phone,
                    phone_number: phone
                });

                // 2. Send Message
                await api.post('/api/messages/send', {
                    customer_id: customer.id,
                    content: content,
                    platform: 'telegram'
                });

                showNotification('Message sent!', 'success');
                if (newMsgModal) newMsgModal.classList.remove('show');
                newMsgForm.reset();
                if (window.loadConversations) loadConversations();

            } catch (error) {
                console.error('Failed to send message:', error);
                showNotification('Failed to send. Check number.', 'error');
            }
        });
    }

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            navigateToPage(page);
        });
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        api.logout();
    });

    // Add Customer Modal Logic
    const addCustomerModal = document.getElementById('add-customer-modal');
    const addCustomerBtn = document.getElementById('add-customer-btn');
    const closeCustomerBtn = document.querySelector('.close-modal');
    const cancelCustomerBtn = document.querySelector('.close-modal-btn');

    if (addCustomerBtn) {
        addCustomerBtn.addEventListener('click', () => {
            addCustomerModal.classList.add('show');
        });
    }

    if (closeCustomerBtn) {
        closeCustomerBtn.addEventListener('click', () => {
            addCustomerModal.classList.remove('show');
        });
    }

    if (cancelCustomerBtn) {
        cancelCustomerBtn.addEventListener('click', () => {
            addCustomerModal.classList.remove('show');
        });
    }

    const addCustomerForm = document.getElementById('add-customer-form');
    if (addCustomerForm) {
        addCustomerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('customerName').value;
            const phone = document.getElementById('customerPhone').value;
            const email = document.getElementById('customerEmail').value;

            try {
                // Call API to create customer
                await api.post('/api/customers', {
                    name,
                    phone_number: phone,
                    email: email || null
                });

                showNotification('Customer added successfully!', 'success');
                addCustomerModal.classList.remove('show');
                addCustomerForm.reset();
                loadCustomers();
            } catch (error) {
                console.error('Failed to add customer:', error);
                showNotification('Failed to add customer', 'error');
            }
        });
    }

    // Bank Details Form Logic
    const bankForm = document.getElementById('bank-details-form');
    if (bankForm) {
        bankForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await api.put('/api/users/me', {
                    bank_name: document.getElementById('bankName').value,
                    account_number: document.getElementById('accountNumber').value,
                    account_name: document.getElementById('accountName').value
                });
                showNotification('Bank details updated successfully!', 'success');
                // Reload details to update card view
                await loadDetails();
                // Switch back to view mode
                document.getElementById('profile-edit-form').classList.add('hidden');
                document.getElementById('profile-view').classList.remove('hidden');
            } catch (error) {
                console.error('Failed to update bank details:', error);
                showNotification('Failed to update details', 'error');
            }
        });
    }

    // Telegram Bot Connect Logic
    const btnConnectTelegram = document.getElementById('btn-connect-telegram');
    const telegramModal = document.getElementById('telegram-modal');
    const closeTelegramBtn = document.querySelector('.close-modalTelegram');
    const closeTelegramBtn2 = document.querySelector('.close-modalTelegram-btn');
    const telegramForm = document.getElementById('telegram-connect-form');

    if (btnConnectTelegram) {
        btnConnectTelegram.addEventListener('click', () => {
            if (telegramModal) telegramModal.classList.add('show');
        });
    }

    // Close logic
    [closeTelegramBtn, closeTelegramBtn2].forEach(btn => {
        if (btn) btn.addEventListener('click', () => {
            if (telegramModal) telegramModal.classList.remove('show');
        });
    });

    if (telegramForm) {
        telegramForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const botToken = document.getElementById('telegramBotToken').value;
                const botUsername = document.getElementById('telegramBotUsername').value;

                await api.put('/api/users/me', {
                    telegram_bot_token: botToken,
                    telegram_bot_username: botUsername
                });

                showNotification('Bot connected successfully!', 'success');
                if (telegramModal) telegramModal.classList.remove('show');

                // Update Badge
                const badge = document.getElementById('telegram-connected-badge');
                if (badge) badge.classList.remove('hidden');

                const btn = document.getElementById('btn-connect-telegram');
                if (btn) btn.textContent = 'Update Bot';

                // Refresh details to show diagnostic link
                await loadDetails();

            } catch (error) {
                console.error('Telegram Bot connect failed:', error);
                showNotification('Failed to connect bot. Check credentials.', 'error');
            }
        });

        // Handle Disconnect
        const btnDisconnect = document.getElementById('btn-disconnect-telegram');
        if (btnDisconnect) {
            btnDisconnect.addEventListener('click', async () => {
                if (!confirm('Are you sure you want to disconnect your bot? This will stop the AI from replying.')) return;

                try {
                    await api.put('/api/users/me', {
                        telegram_bot_token: null,
                        telegram_bot_username: null
                    });
                    showNotification('Bot disconnected successfully.', 'info');
                    if (telegramModal) telegramModal.classList.remove('show');
                    loadDetails();
                } catch (error) {
                    console.error('Failed to disconnect:', error);
                    showNotification('Failed to disconnect bot', 'error');
                }
            });
        }

    }

    // Business Profile Form Logic
    const businessProfileForm = document.getElementById('business-profile-form');
    if (businessProfileForm) {
        businessProfileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await api.put('/api/users/me', {
                    business_name: document.getElementById('businessName').value,
                    phone_number: document.getElementById('businessPhone').value,
                    business_context: document.getElementById('businessContext').value
                });
                showNotification('Business profile updated successfully!', 'success');
                // Reload details to update card view
                await loadDetails();
                // Optional: Switch back to view mode automatically? 
                // Let's let the user decide or click cancel/back. 
                // Actually, usually save -> view.
                document.getElementById('profile-edit-form').classList.add('hidden');
                document.getElementById('profile-view').classList.remove('hidden');
            } catch (error) {
                console.error('Failed to update business profile:', error);
                showNotification('Failed to update profile', 'error');
            }
        });
    }

    // Create Order Modal Logic
    const createOrderModal = document.getElementById('create-order-modal');
    const createOrderBtn = document.getElementById('create-order-btn');

    // Close buttons for create order modal
    // We need to be specific or use a general class handler. 
    // Since we have multiple modals, let's select the close button INSIDE the specific modal
    const closeOrderBtn = createOrderModal.querySelector('.close-modal');
    const cancelOrderBtn = createOrderModal.querySelector('.close-modal-btn');

    if (createOrderBtn) {
        createOrderBtn.addEventListener('click', () => {
            createOrderModal.classList.add('show');
        });
    }

    if (closeOrderBtn) {
        closeOrderBtn.addEventListener('click', () => {
            createOrderModal.classList.remove('show');
        });
    }

    if (cancelOrderBtn) {
        cancelOrderBtn.addEventListener('click', () => {
            createOrderModal.classList.remove('show');
        });
    }

    const createOrderForm = document.getElementById('create-order-form');
    if (createOrderForm) {
        createOrderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const customerName = document.getElementById('orderCustomerName').value;
            const amount = parseFloat(document.getElementById('orderAmount').value);
            const status = document.getElementById('orderStatus').value;
            const notes = document.getElementById('orderNotes').value;

            try {
                // 1. Find or Create Customer
                const customers = await api.get('/api/customers');
                let customerId = null;

                const existingCustomer = customers.find(c => c.name.toLowerCase() === customerName.toLowerCase());

                if (existingCustomer) {
                    customerId = existingCustomer.id;
                } else {
                    // Create new customer
                    const newCustomer = await api.post('/api/customers', {
                        name: customerName,
                        phone_number: '0000000000', // Placeholder if not provided
                        email: null
                    });
                    customerId = newCustomer.id;
                }

                // 2. Create Order
                // Backend expects items list, we'll create a dummy item for the total amount
                await api.post('/api/orders', {
                    customer_id: customerId,
                    items: [{
                        name: notes || "Manual Order",
                        quantity: 1,
                        price: amount
                    }],
                    status: status,
                    notes: notes
                });

                showNotification('Order recorded successfully!', 'success');
                createOrderModal.classList.remove('show');
                createOrderForm.reset();
                loadOrders(); // Refresh table
            } catch (error) {
                console.error('Failed to record order:', error);
                showNotification('Failed to record order', 'error');
            }
        });
    }

    // Load Dashboard
    loadDashboard();
});
