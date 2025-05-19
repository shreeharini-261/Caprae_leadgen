
const stripe = Stripe('pk_test_51RNp9cFS9KhotLbMiJM95rAjhuxjTwgjPpRLObOd1ghpwZHwZHOLDIVuxbp4wfXCJBHSLtZhoL99CdaTpOpWAY1L00GcymT5Xj', {
    stripeAccount: undefined,
    betas: ['checkout_beta_4'],
    apiVersion: '2020-08-27'
});

document.addEventListener('DOMContentLoaded', function() {
    const userTier = window.userTier || 'free';
    const userRole = window.userRole || 'user';

    // Skip all restrictions for admin users
    if (userRole === 'admin') {
        return;
    }

    window.showSubscriptionModal = function(message) {
        const modal = document.getElementById('subscriptionModal');
        const messageEl = document.getElementById('subscriptionMessage');
        if (messageEl) messageEl.textContent = message;
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    // Feature access control
    function checkFeatureAccess(feature) {
        const tierFeatures = {
            'free': ['basic_filters'],
            'bronze': ['basic_filters', 'advanced_filters', 'export_csv'],
            'silver': ['basic_filters', 'advanced_filters', 'export_csv', 'phone_numbers'],
            'gold': ['basic_filters', 'advanced_filters', 'export_csv', 'phone_numbers', 'api_access', 'priority_support']
        };
        
        return tierFeatures[userTier]?.includes(feature) || false;
    }

    // Advanced filters access
    const advancedFiltersBtn = document.querySelector('.toggle-advanced');
    if (advancedFiltersBtn) {
        advancedFiltersBtn.addEventListener('click', function(e) {
            if (!checkFeatureAccess('advanced_filters')) {
                e.preventDefault();
                e.stopPropagation();
                showSubscriptionModal('Advanced filters require a Bronze plan or higher');
                return false;
            }
        });
    }

    // Prevent using filters for free users
    const filterInputs = document.querySelectorAll('.filter-select, .filter-input, #searchInput');
    if (userTier === 'free') {
        filterInputs.forEach(input => {
            input.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                showSubscriptionModal('Filtering requires a paid plan');
                return false;
            });
            input.disabled = true;
        });
    }

    // Export handling
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            if (!checkFeatureAccess('export_csv')) {
                e.preventDefault();
                e.stopPropagation();
                showSubscriptionModal('Export feature requires a Bronze plan or higher');
                return false;
            }
        });
    }

    // Phone number access
    const phoneFields = document.querySelectorAll('.phone-field');
    if (phoneFields.length > 0) {
        phoneFields.forEach(field => {
            if (!checkFeatureAccess('phone_numbers')) {
                field.textContent = '********';
                field.style.cursor = 'pointer';
                field.addEventListener('click', () => {
                    showSubscriptionModal('Phone numbers require a Silver plan or higher');
                });
            }
        });
    }

    // Show subscription badge on successful payment
    const subscriptionBadge = document.getElementById('subscriptionBadge');
    if (subscriptionBadge && userTier !== 'free') {
        subscriptionBadge.textContent = `${userTier.charAt(0).toUpperCase() + userTier.slice(1)} Plan`;
        subscriptionBadge.style.display = 'block';
        setTimeout(() => {
            subscriptionBadge.style.display = 'none';
        }, 5000);
    }
});

window.selectPlan = async function(planType) {
    try {
        const response = await fetch('/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                plan_type: planType
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const { sessionId } = await response.json();

        const result = await stripe.redirectToCheckout({
            sessionId: sessionId
        });

        if (result.error) {
            alert('Payment failed: ' + result.error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Payment failed: ' + error.message);
    }
}
