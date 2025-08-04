/**
 * Customer Management Dashboard - JavaScript Application
 * Implements all frontend requirements with API integration
 */

class CustomerDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentPage = 1;
        this.pageSize = 10;
        this.searchQuery = '';
        this.customers = [];
        this.totalCustomers = 0;
        this.totalPages = 1;
        this.isLoading = false;
        this.currentCustomer = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkApiConnection();
        this.loadCustomers();
    }

    bindEvents() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', this.debounce((e) => {
            this.searchQuery = e.target.value.trim();
            this.currentPage = 1;
            this.loadCustomers();
        }, 300));

        // Clear search
        document.getElementById('clearSearch').addEventListener('click', () => {
            searchInput.value = '';
            this.searchQuery = '';
            this.currentPage = 1;
            this.loadCustomers();
        });

        // Page size change
        document.getElementById('pageSize').addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadCustomers();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadCustomers();
        });

        // View mode toggle
        document.getElementById('tableView').addEventListener('change', () => {
            this.toggleViewMode('table');
        });

        document.getElementById('cardView').addEventListener('change', () => {
            this.toggleViewMode('card');
        });

        // Modal events
        document.getElementById('viewOrdersBtn').addEventListener('click', () => {
            if (this.currentCustomer) {
                this.loadCustomerOrders(this.currentCustomer.id);
            }
        });

        // Error alert close
        const errorAlert = document.getElementById('errorAlert');
        const closeBtn = errorAlert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideError();
            });
        }
    }

    // Utility function for debouncing search input
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // API Connection Check with retry logic
    async checkApiConnection(retryCount = 0) {
        const maxRetries = 3;
        const retryDelay = 1000; // 1 second
        
        try {
            // Add timeout to prevent hanging requests
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
            
            const response = await fetch(`${this.apiBaseUrl}/health`, {
                signal: controller.signal,
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            const statusElement = document.getElementById('apiStatus');
            if (data.status === 'healthy') {
                statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>API Connected';
                statusElement.className = 'badge bg-success';
                console.log('✅ API Connection successful:', data);
                return true;
            } else {
                throw new Error('API returned unhealthy status');
            }
        } catch (error) {
            console.error(`❌ API connection attempt ${retryCount + 1} failed:`, error.message);
            
            const statusElement = document.getElementById('apiStatus');
            
            // Retry logic
            if (retryCount < maxRetries) {
                statusElement.innerHTML = `<i class="fas fa-sync-alt fa-spin me-1"></i>Retrying... (${retryCount + 1}/${maxRetries})`;
                statusElement.className = 'badge bg-warning';
                
                setTimeout(() => {
                    this.checkApiConnection(retryCount + 1);
                }, retryDelay * (retryCount + 1)); // Exponential backoff
                
                return false;
            }
            
            // Max retries reached
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>API Disconnected';
            statusElement.className = 'badge bg-danger';
            
            let errorMessage = 'Unable to connect to Customer API. ';
            
            if (error.name === 'AbortError') {
                errorMessage += 'Request timed out. ';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage += 'Network error or CORS issue. ';
            } else {
                errorMessage += `Error: ${error.message}. `;
            }
            
            errorMessage += 'Please check if the Flask server is running on http://localhost:5000';
            
            this.showError(errorMessage, true); // Show retry button for connection errors
            return false;
        }
    }

    // Load customers with search and pagination
    async loadCustomers() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        this.hideError();

        try {
            let url = `${this.apiBaseUrl}/customers?page=${this.currentPage}&limit=${this.pageSize}`;
            
            if (this.searchQuery) {
                url += `&search=${encodeURIComponent(this.searchQuery)}`;
            }

            // Add timeout and CORS headers
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(url, {
                signal: controller.signal,
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            this.customers = data.customers || [];
            this.totalCustomers = data.pagination?.total_count || 0;
            this.totalPages = data.pagination?.total_pages || 1;
            this.currentPage = data.pagination?.page || 1;

            this.renderCustomers();
            this.renderPagination();
            this.updateStats();

        } catch (error) {
            console.error('Error loading customers:', error);
            this.showError(`Failed to load customers: ${error.message}`);
            this.renderEmptyState();
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    // Render customers in table or card view
    renderCustomers() {
        const viewMode = document.getElementById('tableView').checked ? 'table' : 'card';
        
        if (viewMode === 'table') {
            this.renderTableView();
        } else {
            this.renderCardView();
        }

        document.getElementById('statsRow').style.display = 'flex';
    }

    // Render table view
    renderTableView() {
        const tbody = document.getElementById('customerTableBody');
        tbody.innerHTML = '';

        if (this.customers.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4">
                        <div class="empty-state">
                            <i class="fas fa-users"></i>
                            <h4>No customers found</h4>
                            <p>Try adjusting your search criteria</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        this.customers.forEach(customer => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            row.innerHTML = `
                <td><strong>#${customer.id}</strong></td>
                <td>
                    <div class="customer-info">
                        <div class="customer-avatar">
                            ${this.getInitials(customer.first_name, customer.last_name)}
                        </div>
                        <div class="customer-details">
                            <h6>${customer.first_name} ${customer.last_name}</h6>
                            <small class="text-muted">ID: ${customer.id}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <a href="mailto:${customer.email}" class="text-decoration-none">
                        ${customer.email}
                    </a>
                </td>
                <td><span class="badge bg-secondary">${customer.age || 'N/A'}</span></td>
                <td>
                    <small>
                        <i class="fas fa-map-marker-alt me-1"></i>
                        ${customer.city || 'N/A'}, ${customer.state || 'N/A'}<br>
                        <strong>${customer.country || 'N/A'}</strong>
                    </small>
                </td>
                <td>
                    <span class="badge order-count-badge">
                        <i class="fas fa-shopping-cart me-1"></i>
                        ${customer.order_count || 0} orders
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="dashboard.viewCustomerDetails(${customer.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn btn-outline-primary btn-sm" onclick="dashboard.loadCustomerOrders(${customer.id})">
                            <i class="fas fa-shopping-cart"></i> Orders
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // Render card view
    renderCardView() {
        const container = document.getElementById('customerCardsContainer');
        container.innerHTML = '';

        if (this.customers.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="empty-state">
                        <i class="fas fa-users"></i>
                        <h4>No customers found</h4>
                        <p>Try adjusting your search criteria</p>
                    </div>
                </div>
            `;
            return;
        }

        this.customers.forEach(customer => {
            const cardCol = document.createElement('div');
            cardCol.className = 'col-md-6 col-lg-4 fade-in';
            cardCol.innerHTML = `
                <div class="card customer-card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <div class="customer-avatar me-3">
                                ${this.getInitials(customer.first_name, customer.last_name)}
                            </div>
                            <div>
                                <h6 class="mb-0">${customer.first_name} ${customer.last_name}</h6>
                                <small>ID: #${customer.id}</small>
                            </div>
                        </div>
                        <span class="badge order-count-badge">
                            ${customer.order_count || 0} orders
                        </span>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <i class="fas fa-envelope me-2 text-primary"></i>
                            <a href="mailto:${customer.email}" class="text-decoration-none">
                                ${customer.email}
                            </a>
                        </div>
                        <div class="mb-3">
                            <i class="fas fa-birthday-cake me-2 text-primary"></i>
                            Age: <span class="badge bg-secondary">${customer.age || 'N/A'}</span>
                        </div>
                        <div class="mb-3">
                            <i class="fas fa-map-marker-alt me-2 text-primary"></i>
                            ${customer.city || 'N/A'}, ${customer.state || 'N/A'}<br>
                            <strong>${customer.country || 'N/A'}</strong>
                        </div>
                        <div class="d-grid gap-2">
                            <button class="btn btn-primary" onclick="dashboard.viewCustomerDetails(${customer.id})">
                                <i class="fas fa-eye me-2"></i>View Details
                            </button>
                            <button class="btn btn-outline-primary" onclick="dashboard.loadCustomerOrders(${customer.id})">
                                <i class="fas fa-shopping-cart me-2"></i>View Orders
                            </button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(cardCol);
        });
    }

    // Get initials for avatar
    getInitials(firstName, lastName) {
        const first = firstName ? firstName.charAt(0).toUpperCase() : '';
        const last = lastName ? lastName.charAt(0).toUpperCase() : '';
        return first + last || '?';
    }

    // Toggle between table and card view
    toggleViewMode(mode) {
        const tableContainer = document.getElementById('tableViewContainer');
        const cardContainer = document.getElementById('cardViewContainer');

        if (mode === 'table') {
            tableContainer.style.display = 'block';
            cardContainer.style.display = 'none';
            this.renderTableView();
        } else {
            tableContainer.style.display = 'none';
            cardContainer.style.display = 'block';
            this.renderCardView();
        }
    }

    // Render pagination
    renderPagination() {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';

        if (this.totalPages <= 1) return;

        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `
            <a class="page-link" href="#" onclick="dashboard.goToPage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i> Previous
            </a>
        `;
        pagination.appendChild(prevLi);

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);

        if (startPage > 1) {
            const firstLi = document.createElement('li');
            firstLi.className = 'page-item';
            firstLi.innerHTML = `<a class="page-link" href="#" onclick="dashboard.goToPage(1)">1</a>`;
            pagination.appendChild(firstLi);

            if (startPage > 2) {
                const dotsLi = document.createElement('li');
                dotsLi.className = 'page-item disabled';
                dotsLi.innerHTML = `<span class="page-link">...</span>`;
                pagination.appendChild(dotsLi);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#" onclick="dashboard.goToPage(${i})">${i}</a>`;
            pagination.appendChild(li);
        }

        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                const dotsLi = document.createElement('li');
                dotsLi.className = 'page-item disabled';
                dotsLi.innerHTML = `<span class="page-link">...</span>`;
                pagination.appendChild(dotsLi);
            }

            const lastLi = document.createElement('li');
            lastLi.className = 'page-item';
            lastLi.innerHTML = `<a class="page-link" href="#" onclick="dashboard.goToPage(${this.totalPages})">${this.totalPages}</a>`;
            pagination.appendChild(lastLi);
        }

        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `
            <a class="page-link" href="#" onclick="dashboard.goToPage(${this.currentPage + 1})">
                Next <i class="fas fa-chevron-right"></i>
            </a>
        `;
        pagination.appendChild(nextLi);
    }

    // Go to specific page
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) return;
        this.currentPage = page;
        this.loadCustomers();
    }

    // Update statistics
    updateStats() {
        document.getElementById('totalCustomers').textContent = this.totalCustomers.toLocaleString();
        document.getElementById('searchResults').textContent = this.customers.length.toLocaleString();
        document.getElementById('currentPage').textContent = this.currentPage;
        document.getElementById('totalPages').textContent = this.totalPages;
    }

    // View customer details
    async viewCustomerDetails(customerId) {
        try {
            this.showLoading();
            const response = await fetch(`${this.apiBaseUrl}/customers/${customerId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to load customer details');
            }

            this.currentCustomer = data.customer;
            this.renderCustomerModal(data);
            
            const modal = new bootstrap.Modal(document.getElementById('customerModal'));
            modal.show();

        } catch (error) {
            console.error('Error loading customer details:', error);
            this.showError(`Failed to load customer details: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    // Render customer details modal
    renderCustomerModal(data) {
        const modalBody = document.getElementById('customerModalBody');
        const customer = data.customer;
        const orderSummary = data.order_summary;

        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-4 text-center mb-4">
                    <div class="customer-avatar mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2rem;">
                        ${this.getInitials(customer.first_name, customer.last_name)}
                    </div>
                    <h4>${customer.full_name}</h4>
                    <p class="text-muted">Customer ID: #${customer.id}</p>
                </div>
                <div class="col-md-8">
                    <div class="row">
                        <div class="col-sm-6 mb-3">
                            <strong><i class="fas fa-envelope me-2 text-primary"></i>Email:</strong><br>
                            <a href="mailto:${customer.email}">${customer.email}</a>
                        </div>
                        <div class="col-sm-6 mb-3">
                            <strong><i class="fas fa-birthday-cake me-2 text-primary"></i>Age:</strong><br>
                            ${customer.age || 'N/A'}
                        </div>
                        <div class="col-sm-6 mb-3">
                            <strong><i class="fas fa-venus-mars me-2 text-primary"></i>Gender:</strong><br>
                            ${customer.gender || 'N/A'}
                        </div>
                        <div class="col-sm-6 mb-3">
                            <strong><i class="fas fa-calendar me-2 text-primary"></i>Registered:</strong><br>
                            ${customer.registered_at ? new Date(customer.registered_at).toLocaleDateString() : 'N/A'}
                        </div>
                        <div class="col-12 mb-3">
                            <strong><i class="fas fa-map-marker-alt me-2 text-primary"></i>Location:</strong><br>
                            ${customer.location.address || 'N/A'}<br>
                            ${customer.location.city}, ${customer.location.state}<br>
                            ${customer.location.country} ${customer.location.zipcode || ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <hr>
            
            <div class="row">
                <div class="col-12">
                    <h5><i class="fas fa-chart-bar me-2"></i>Order Summary</h5>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h3>${orderSummary.total_orders}</h3>
                            <p class="mb-0">Total Orders</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <h3>${orderSummary.orders_by_status.delivered}</h3>
                            <p class="mb-0">Delivered</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card bg-info text-white">
                        <div class="card-body text-center">
                            <h3>${orderSummary.orders_by_status.shipped}</h3>
                            <p class="mb-0">Shipped</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body text-center">
                            <h3>${orderSummary.orders_by_status.pending}</h3>
                            <p class="mb-0">Pending</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <strong><i class="fas fa-shopping-cart me-2 text-primary"></i>Total Items Purchased:</strong><br>
                    <span class="h4">${orderSummary.total_items_purchased}</span>
                </div>
                <div class="col-md-6 mb-3">
                    <strong><i class="fas fa-calendar me-2 text-primary"></i>Order Date Range:</strong><br>
                    ${orderSummary.first_order_date ? new Date(orderSummary.first_order_date).toLocaleDateString() : 'N/A'} - 
                    ${orderSummary.last_order_date ? new Date(orderSummary.last_order_date).toLocaleDateString() : 'N/A'}
                </div>
            </div>
        `;
    }

    // Load customer orders
    async loadCustomerOrders(customerId) {
        try {
            this.showLoading();
            const response = await fetch(`${this.apiBaseUrl}/customers/${customerId}/orders?limit=50`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to load customer orders');
            }

            this.renderOrdersModal(data);
            
            // Hide customer modal if open
            const customerModal = bootstrap.Modal.getInstance(document.getElementById('customerModal'));
            if (customerModal) {
                customerModal.hide();
            }
            
            const ordersModal = new bootstrap.Modal(document.getElementById('ordersModal'));
            ordersModal.show();

        } catch (error) {
            console.error('Error loading customer orders:', error);
            this.showError(`Failed to load customer orders: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    // Render orders modal
    renderOrdersModal(data) {
        const modalBody = document.getElementById('ordersModalBody');
        const customer = data.customer;
        const orders = data.orders;

        modalBody.innerHTML = `
            <div class="mb-4">
                <h5><i class="fas fa-user me-2"></i>${customer.name}</h5>
                <p class="text-muted">Customer ID: #${customer.id} | Total Orders: ${data.pagination.total_count}</p>
            </div>
            
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Order ID</th>
                            <th>Status</th>
                            <th>Items</th>
                            <th>Created</th>
                            <th>Shipped</th>
                            <th>Delivered</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orders.map(order => `
                            <tr>
                                <td><strong>#${order.order_id}</strong></td>
                                <td>
                                    <span class="badge status-${order.status.toLowerCase()}">
                                        ${order.status}
                                    </span>
                                </td>
                                <td>${order.num_of_items}</td>
                                <td>${order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A'}</td>
                                <td>${order.shipped_at ? new Date(order.shipped_at).toLocaleDateString() : '-'}</td>
                                <td>${order.delivered_at ? new Date(order.delivered_at).toLocaleDateString() : '-'}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="dashboard.viewOrderDetails(${order.order_id})">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            ${orders.length === 0 ? `
                <div class="empty-state">
                    <i class="fas fa-shopping-cart"></i>
                    <h4>No orders found</h4>
                    <p>This customer hasn't placed any orders yet.</p>
                </div>
            ` : ''}
        `;
    }

    // View order details
    async viewOrderDetails(orderId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/orders/${orderId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to load order details');
            }

            alert(`Order Details:\n\nOrder ID: #${data.order.order_id}\nStatus: ${data.order.status}\nItems: ${data.order.num_of_items}\nCustomer: ${data.customer.full_name}\nEmail: ${data.customer.email}`);

        } catch (error) {
            console.error('Error loading order details:', error);
            this.showError(`Failed to load order details: ${error.message}`);
        }
    }

    // Show loading state
    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'block';
    }

    // Hide loading state
    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }

    // Show error message with optional retry button
    showError(message, showRetryButton = false) {
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        
        if (showRetryButton) {
            errorMessage.innerHTML = `
                ${message}
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="dashboard.retryConnection()">
                    <i class="fas fa-sync-alt me-1"></i>Retry Connection
                </button>
            `;
        } else {
            errorMessage.textContent = message;
        }
        
        errorAlert.style.display = 'block';
        
        // Auto-hide after 15 seconds (longer for retry button)
        setTimeout(() => {
            this.hideError();
        }, showRetryButton ? 15000 : 10000);
    }
    
    // Manual retry connection
    retryConnection() {
        this.hideError();
        console.log('🔄 Manual retry connection requested');
        this.checkApiConnection();
    }

    // Hide error message
    hideError() {
        document.getElementById('errorAlert').style.display = 'none';
    }

    // Render empty state
    renderEmptyState() {
        const tbody = document.getElementById('customerTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5">
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h4>Unable to load customers</h4>
                        <p>Please check your connection and try again.</p>
                        <button class="btn btn-primary" onclick="dashboard.loadCustomers()">
                            <i class="fas fa-sync-alt me-2"></i>Retry
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Initialize the dashboard when the page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new CustomerDashboard();
});

// Prevent default behavior for pagination links
document.addEventListener('click', (e) => {
    if (e.target.closest('.page-link')) {
        e.preventDefault();
    }
});
