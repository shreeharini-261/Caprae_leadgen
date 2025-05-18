from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from controllers.auth_controller import AuthController
from flask_login import login_required, current_user
import stripe
from utils.decorators import role_required
from models.user_model import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = AuthController.login(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'developer')
def signup():
    """Handle user registration - Only admin and developer can create accounts"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        company = request.form.get('company', '')  # Get company from form
        
        # Default role is 'user', but admin can change it
        role = request.form.get('role', 'user')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/signup.html')

        success, message = AuthController.register(username, email, password, role, company)
        
        if success:
            flash(message, 'success')
            # If admin creates a user, redirect to user management
            if current_user.is_admin():
                return redirect(url_for('auth.manage_users'))
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    success, message = AuthController.logout()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/manage_users')
@login_required
@role_required('admin', 'developer')
def manage_users():
    """Manage users - accessible to admins and developers"""
    users = User.query.all()
    return render_template('auth/manage_users.html', users=users)

@auth_bp.route('/update_user_role', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def update_user_role():
    """Update user role - only accessible to admins"""
    user_id = request.form.get('user_id')
    role = request.form.get('role')
    
    if not user_id or not role:
        flash('Missing required fields', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    # Validate role
    valid_roles = ['admin', 'developer', 'user']
    if role not in valid_roles:
        flash(f'Invalid role. Must be one of: {", ".join(valid_roles)}', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        user.role = role
        db.session.commit()
        flash(f'Role for {user.username} updated to {role}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating role: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/delete_user')
@login_required
@role_required('admin', 'developer')
def delete_user():
    """Delete user - only accessible to admins"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        # Prevent self-deletion
        if int(user_id) == current_user.id:
            flash('You cannot delete your own account', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_users')) 
@auth_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        plan_type = request.json.get('plan_type')
        price_id = current_app.config['STRIPE_PRICES'].get(plan_type)
        
        if not price_id:
            return jsonify({'error': 'Invalid plan type'}), 400

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        success_url = request.host_url.replace('http://', 'https://') + 'payment/success'
        cancel_url = request.host_url.replace('http://', 'https://') + 'payment/cancel'
        
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(current_user.id),
            payment_method_types=['card']
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
        print(f"Webhook received: {event['type']}")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print(f"Payment successful for user {session.get('client_reference_id')}")
            handle_successful_payment(session)
        elif event['type'] == 'checkout.session.async_payment_failed':
            session = event['data']['object']
            print(f"Payment failed for user {session.get('client_reference_id')}")
            # Handle failed payment
            user_id = session.get('client_reference_id')
            if user_id:
                user = User.query.get(user_id)
                if user:
                    user.subscription_tier = 'free'
                    db.session.commit()
                    
    except ValueError as e:
        print(f"Webhook error: Invalid payload - {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Webhook error: Invalid signature - {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    return jsonify({'status': 'success'})

@auth_bp.route('/payment/success')
@login_required
def payment_success():
    return render_template('auth/payment_success.html')

@auth_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    return render_template('auth/payment_cancel.html')

@auth_bp.route('/manage_subscriptions')
@login_required
@role_required('admin')
def manage_subscriptions():
    """Manage user subscriptions - Admin only"""
    users = User.query.all()
    return render_template('auth/manage_subscriptions.html', users=users)

@auth_bp.route('/update_subscription', methods=['POST'])
@login_required
@role_required('admin')
def update_subscription():
    """Update user subscription tier - Admin only"""
    user_id = request.form.get('user_id')
    subscription_tier = request.form.get('subscription_tier')
    
    try:
        user = User.query.get(user_id)
        if user:
            user.subscription_tier = subscription_tier
            db.session.commit()
            flash(f'Subscription updated for {user.username} to {subscription_tier}', 'success')
        else:
            flash('User not found', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating subscription: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_subscriptions'))

def handle_successful_payment(session):
    try:
        user_id = session.get('client_reference_id')
        if not user_id:
            print("No user_id found in session")
            return
            
        user = User.query.get(int(user_id))
        if not user:
            print(f"User {user_id} not found")
            return

        # Get line items and extract price ID
        line_items = stripe.checkout.Session.list_line_items(session.id)
        if not line_items or not line_items.data:
            print("No line items found")
            return
            
        price_id = line_items.data[0].price.id
        
        # Map price_id to subscription tier
        price_to_tier = {
            current_app.config['STRIPE_PRICES']['gold']: 'gold',
            current_app.config['STRIPE_PRICES']['silver']: 'silver',
            current_app.config['STRIPE_PRICES']['bronze']: 'bronze'
        }
        
        new_tier = price_to_tier.get(price_id)
        if not new_tier:
            print(f"Invalid price_id: {price_id}")
            return
            
        user.subscription_tier = new_tier
        db.session.commit()
        print(f"Successfully updated user {user_id} to tier {new_tier}")
        
    except Exception as e:
        print(f"Error handling payment: {str(e)}")
        db.session.rollback()
