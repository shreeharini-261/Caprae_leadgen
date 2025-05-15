from flask import Blueprint, request, render_template, redirect, url_for, flash
from controllers.auth_controller import AuthController
from flask_login import login_required, current_user
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