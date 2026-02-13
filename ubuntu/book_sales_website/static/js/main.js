// Main JavaScript file for Book Sales Website

document.addEventListener('DOMContentLoaded', function() {
    // Sliding Sidebar functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', openSidebar);
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // PayPal payment processing
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show loading state
            checkoutBtn.disabled = true;
            checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            // Create payment through the backend
            fetch('/create-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    // Handle error
                    alert('Error: ' + data.error);
                    checkoutBtn.disabled = false;
                    checkoutBtn.innerHTML = 'Proceed to Payment';
                } else {
                    // Redirect to PayPal for payment
                    window.location.href = data.approval_url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = 'Proceed to Payment';
            });
        });
    }

    // Quantity update in cart
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const form = this.closest('form');
            form.submit();
        });
    });

    // Book search auto-submit
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    if (searchForm && searchInput) {
        searchInput.addEventListener('input', function() {
            if (this.value.length >= 3) {
                // Only submit if at least 3 characters entered
                searchForm.submit();
            }
        });
    }
});
