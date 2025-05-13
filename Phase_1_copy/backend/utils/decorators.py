from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Usage: @role_required('admin') or @role_required('admin', 'developer')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
                
            if current_user.role not in roles:
                flash(f'Access denied. Required role: {", ".join(roles)}', 'danger')
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 