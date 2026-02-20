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

    // Password visibility toggle for login and register forms
    function setupPasswordToggle(passwordId, toggleId, eyeId) {
        const togglePassword = document.getElementById(toggleId);
        const passwordInput = document.getElementById(passwordId);
        const eyeIcon = document.getElementById(eyeId);
        if (togglePassword && passwordInput && eyeIcon) {
            togglePassword.addEventListener('click', function() {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                // Toggle eye/eye-slash icon
                if (type === 'text') {
                    eyeIcon.innerHTML = '<path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.12 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.133 13.133 0 0 1 1.172 8z"/><path d="M10.478 10.304a3 3 0 1 1-4.956-4.608l4.956 4.608z"/><path d="M13.646 14.354a.5.5 0 0 1-.708 0l-12-12a.5.5 0 1 1 .708-.708l12 12a.5.5 0 0 1 0 .708z"/>';
                } else {
                    eyeIcon.innerHTML = '<path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.12 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.133 13.133 0 0 1 1.172 8z"/><path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zm0 1a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z"/>';
                }
            });
        }
    }
    // Setup for login form
    setupPasswordToggle('login-password', 'toggleLoginPassword', 'eyeLoginIcon');
    // Setup for register form
    setupPasswordToggle('register-password', 'toggleRegisterPassword', 'eyeRegisterIcon');

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
