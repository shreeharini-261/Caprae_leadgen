
// Store user's tier from the base template
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

  // Export handling for non-admin users
  const exportBtn = document.getElementById('exportBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', function(e) {
      if (userTier === 'free') {
        e.preventDefault();
        e.stopPropagation();
        showSubscriptionModal('Export feature requires a paid plan');
        return false;
      }
    });
  }

  // When subscription modal is closed, redirect back to leads page if user is free tier
  const subscriptionModal = document.getElementById('subscriptionModal');
  if (subscriptionModal) {
    subscriptionModal.addEventListener('hidden.bs.modal', function () {
      if (userTier === 'free') {
        window.location.href = '/view_leads';
      }
    });
  }
});

window.selectPlan = async function(planType) {
    try {
        const response = await fetch('/subscription/create-checkout-session', {
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
        const stripe = Stripe('pk_test_51RNp9cFS9KhotLbMiJM95rAjhuxjTwgjPpRLObOd1ghpwZHwZHOLDIVuxbp4wfXCJBHSLtZhoL99CdaTpOpWAY1L00GcymT5Xj');

        const { error } = await stripe.redirectToCheckout({
            sessionId: sessionId
        });

        if (error) {
            console.error('Error:', error);
            alert('Payment failed: ' + error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Payment failed: ' + error.message);
    }
}
