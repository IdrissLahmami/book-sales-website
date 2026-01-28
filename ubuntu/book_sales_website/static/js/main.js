// Main JavaScript file for Book Sales Website

document.addEventListener('DOMContentLoaded', function() {
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
